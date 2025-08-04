"""
Multi-layer opportunity caching service inspired by v1 SmartOpportunityService.

Provides:
- Memory cache for ultra-fast access
- Database persistence for reliability  
- Live scanning for fresh data
- Demo data fallback for development
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import json
from dataclasses import dataclass, asdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.database import get_db
from models.opportunity import OpportunitySnapshot, ScanSession
from core.orchestrator.plugin_registry import PluginRegistry
from core.orchestrator.strategy_registry import get_strategy_registry
from services.universe_loader import get_universe_loader
from services.error_logging_service import log_critical_error

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache performance statistics."""
    memory_hits: int = 0
    database_hits: int = 0
    live_scans: int = 0
    demo_fallbacks: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate overall cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.memory_hits + self.database_hits) / self.total_requests


class OpportunityCache:
    """
    Multi-layer caching system for trading opportunities.
    
    Cache Layers (in order of preference):
    1. Memory Cache - Ultra-fast in-memory storage
    2. Database Cache - Persistent storage with TTL
    3. Live Scanning - Real-time opportunity generation
    4. Demo Data - Fallback for development/testing
    """
    
    def __init__(self, plugin_registry: PluginRegistry = None):
        self.plugin_registry = plugin_registry
        self.memory_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.stats = CacheStats()
        
        # Cache configuration
        self.memory_ttl_minutes = 2  # Memory cache TTL
        self.database_ttl_minutes = 15  # Database cache TTL 
        self.max_memory_entries = 1000  # Max opportunities in memory
        
        # Strategy-specific cache settings
        self.strategy_ttl = {
            'high_probability': timedelta(minutes=3),
            'quick_scalp': timedelta(minutes=1),
            'swing_trade': timedelta(minutes=10),
            'volatility_play': timedelta(minutes=2),
            'theta_crop': timedelta(minutes=5)
        }
        
        logger.info("OpportunityCache initialized")
    
    async def get_opportunities(self, strategy: str = None, symbols: List[str] = None, 
                              force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get opportunities using multi-layer cache strategy.
        
        Args:
            strategy: Filter by strategy type (optional)
            symbols: Filter by symbols (optional) 
            force_refresh: Skip cache and force live scan
            
        Returns:
            List of opportunity dictionaries
        """
        self.stats.total_requests += 1
        cache_key = self._generate_cache_key(strategy, symbols)
        
        try:
            # Layer 1: Memory Cache (if not forcing refresh)
            if not force_refresh:
                memory_result = self._get_from_memory(cache_key, strategy)
                if memory_result:
                    self.stats.memory_hits += 1
                    logger.debug(f"Memory cache hit for {cache_key}")
                    return self._filter_opportunities(memory_result, strategy, symbols)
            
            # Layer 2: Database Cache
            if not force_refresh:
                db_result = await self._get_from_database(strategy, symbols)
                if db_result:
                    self.stats.database_hits += 1
                    logger.debug(f"Database cache hit for {cache_key}")
                    # Update memory cache
                    self._update_memory_cache(cache_key, db_result)
                    return self._filter_opportunities(db_result, strategy, symbols)
            
            # Layer 3: Live Scanning
            if self.plugin_registry:
                live_result = await self._perform_live_scan(strategy, symbols)
                if live_result:
                    self.stats.live_scans += 1
                    logger.info(f"Live scan completed for {cache_key}: {len(live_result)} opportunities")
                    # Update both caches
                    self._update_memory_cache(cache_key, live_result)
                    await self._update_database_cache(live_result, strategy)
                    return self._filter_opportunities(live_result, strategy, symbols)
            
            # Layer 4: No Demo Data - Return empty list to show true system state
            logger.warning(f"No opportunities found for {cache_key} - all cache layers empty")
            return []
            
        except Exception as e:
            logger.error(f"Error getting opportunities for {cache_key}: {e}")
            # Return empty list on error to show true system state
            return []
    
    async def add_opportunities(self, opportunities: List[Dict[str, Any]], 
                              strategy: str, scan_session_id: str = None):
        """Add opportunities to cache layers."""
        try:
            # Update memory cache
            cache_key = self._generate_cache_key(strategy, None)
            self._update_memory_cache(cache_key, opportunities)
            
            # Update database cache
            await self._update_database_cache(opportunities, strategy, scan_session_id)
            
            logger.info(f"Added {len(opportunities)} opportunities to cache for strategy {strategy}")
            
        except Exception as e:
            logger.error(f"Error adding opportunities to cache: {e}")
    
    async def cleanup_expired(self):
        """Clean up expired opportunities from all cache layers."""
        try:
            # Clean memory cache
            current_time = datetime.utcnow()
            expired_keys = []
            
            for key, timestamp in self.cache_timestamps.items():
                if (current_time - timestamp).total_seconds() > (self.memory_ttl_minutes * 60):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
                del self.cache_timestamps[key]
            
            # Clean database cache
            db_gen = get_db()
            db = next(db_gen)
            try:
                expired_opportunities = db.query(OpportunitySnapshot).filter(
                    OpportunitySnapshot.expires_at < current_time
                ).all()
                
                for opp in expired_opportunities:
                    db.delete(opp)
                
                db.commit()
                
                if expired_keys or expired_opportunities:
                    logger.info(f"Cleaned up {len(expired_keys)} memory entries and "
                              f"{len(expired_opportunities)} database entries")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return {
            "stats": asdict(self.stats),
            "memory_cache": {
                "entries": len(self.memory_cache),
                "strategies": list(self.memory_cache.keys())
            },
            "hit_rate": self.stats.hit_rate,
            "last_cleanup": datetime.utcnow().isoformat()
        }
    
    def _generate_cache_key(self, strategy: str = None, symbols: List[str] = None) -> str:
        """Generate cache key from parameters."""
        key_parts = []
        if strategy:
            key_parts.append(f"strategy:{strategy}")
        if symbols:
            key_parts.append(f"symbols:{','.join(sorted(symbols))}")
        
        return "|".join(key_parts) if key_parts else "all"
    
    def _get_from_memory(self, cache_key: str, strategy: str = None) -> Optional[List[Dict[str, Any]]]:
        """Get opportunities from memory cache."""
        if cache_key not in self.memory_cache:
            return None
        
        # Check TTL
        if cache_key in self.cache_timestamps:
            age_seconds = (datetime.utcnow() - self.cache_timestamps[cache_key]).total_seconds()
            ttl_seconds = self.memory_ttl_minutes * 60
            
            # Use strategy-specific TTL if available
            if strategy and strategy in self.strategy_ttl:
                ttl_seconds = self.strategy_ttl[strategy].total_seconds()
            
            if age_seconds > ttl_seconds:
                # Expired, remove from cache
                del self.memory_cache[cache_key]
                del self.cache_timestamps[cache_key]
                return None
        
        return self.memory_cache[cache_key]
    
    async def _get_from_database(self, strategy: str = None, 
                               symbols: List[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get opportunities from database cache."""
        try:
            db_gen = get_db()
            db = next(db_gen)
            try:
                query = db.query(OpportunitySnapshot).filter(
                    and_(
                        OpportunitySnapshot.expires_at > datetime.utcnow(),
                        OpportunitySnapshot.is_active == True
                    )
                )
                
                # Apply filters
                if strategy:
                    query = query.filter(OpportunitySnapshot.strategy_type == strategy)
                if symbols:
                    query = query.filter(OpportunitySnapshot.symbol.in_(symbols))
                
                # Order by creation time (newest first)
                opportunities = query.order_by(desc(OpportunitySnapshot.created_at)).all()
                
                if opportunities:
                    # Increment cache hit counters and convert to dicts
                    result = []
                    for opp in opportunities:
                        opp.increment_cache_hit()
                        result.append(opp.to_api_response())
                    
                    db.commit()
                    return result
                
                return None
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error querying database cache: {e}")
        
        return None
    
    async def _perform_live_scan(self, strategy: str = None, 
                               symbols: List[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Perform live opportunity scanning using strategy registry."""
        logger.info(f"DEBUG: _perform_live_scan called with strategy={strategy}, symbols={symbols}")
        try:
            # Get strategy registry
            strategy_registry = get_strategy_registry()
            if not strategy_registry:
                logger.warning("No strategy registry available for live scanning")
                # No fallback - log error and fail explicitly
                await log_critical_error(
                    error_type="strategy_registry_unavailable",
                    message=f"Strategy registry not available for {strategy}",
                    details={"strategy": strategy, "symbols": symbols},
                    service="opportunity_cache",
                    severity="HIGH"
                )
                raise RuntimeError(f"Strategy registry not available - system health compromised")
            
            # Get universe loader for symbols
            universe_loader = get_universe_loader()
            if symbols:
                scan_symbols = symbols
            else:
                # Get strategy-specific symbols
                scan_symbols = universe_loader.get_strategy_universe_priority(strategy or 'high_probability')
                scan_symbols = scan_symbols[:8]  # Limit for performance
            
            logger.info(f"Performing live scan for strategy={strategy}, symbols={scan_symbols}")
            
            # If specific strategy requested, use that strategy plugin
            if strategy and strategy != 'high_probability':
                strategy_instance = strategy_registry.get_strategy(strategy)
                if strategy_instance:
                    logger.info(f"Using strategy plugin: {strategy}")
                    opportunities = await strategy_instance.scan_opportunities(scan_symbols)
                    
                    # Convert StrategyOpportunity objects to dict format
                    result = []
                    for opp in opportunities:
                        opp_dict = {
                            "id": opp.id,
                            "symbol": opp.symbol,
                            "strategy_type": opp.strategy_type,
                            "short_strike": opp.short_strike,
                            "long_strike": opp.long_strike,
                            "premium": opp.premium,
                            "max_loss": opp.max_loss,
                            "delta": opp.delta,
                            "probability_profit": opp.probability_profit,
                            "expected_value": opp.expected_value,
                            "days_to_expiration": opp.days_to_expiration,
                            "underlying_price": opp.underlying_price,
                            "liquidity_score": opp.liquidity_score,
                            "bias": getattr(opp, 'market_bias', 'NEUTRAL'),
                            "rsi": getattr(opp, 'rsi', 50.0),
                            "created_at": getattr(opp, 'generated_at', datetime.utcnow()).isoformat(),
                            "is_demo": False,
                            "scan_source": "strategy_plugin",
                            "universe": opp.universe or "default"
                        }
                        result.append(opp_dict)
                    
                    if result:
                        logger.info(f"Strategy plugin scan found {len(result)} opportunities")
                        return result
                    else:
                        logger.info(f"Strategy plugin scan found no opportunities")
                        return None
                else:
                    logger.warning(f"Strategy {strategy} not found in registry, using fallback")
                    # No fallback - log error and fail explicitly
                await log_critical_error(
                    error_type="strategy_registry_unavailable",
                    message=f"Strategy registry not available for {strategy}",
                    details={"strategy": strategy, "symbols": symbols},
                    service="opportunity_cache",
                    severity="HIGH"
                )
                raise RuntimeError(f"Strategy registry not available - system health compromised")
            
            # For generic scans or when strategy not found, scan all strategies
            logger.info("Scanning all registered strategies")
            all_opportunities = await strategy_registry.scan_all_strategies(scan_symbols)
            
            # Flatten results and convert to API format
            result = []
            for strategy_id, opps in all_opportunities.items():
                for opp in opps:
                    opp_dict = {
                        "id": opp.id,
                        "symbol": opp.symbol,
                        "strategy_type": opp.strategy_type,
                        "short_strike": opp.short_strike,
                        "long_strike": opp.long_strike,
                        "premium": opp.premium,
                        "max_loss": opp.max_loss,
                        "delta": opp.delta,
                        "probability_profit": opp.probability_profit,
                        "expected_value": opp.expected_value,
                        "days_to_expiration": opp.days_to_expiration,
                        "underlying_price": opp.underlying_price,
                        "liquidity_score": opp.liquidity_score,
                        "bias": getattr(opp, 'bias', 'NEUTRAL'),
                        "rsi": getattr(opp, 'rsi', 50.0),
                        "created_at": getattr(opp, 'generated_at', datetime.utcnow()).isoformat(),
                        "is_demo": False,
                        "scan_source": "strategy_registry",
                        "universe": opp.universe or "default"
                    }
                    result.append(opp_dict)
            
            if result:
                logger.info(f"Strategy registry scan found {len(result)} opportunities across {len(all_opportunities)} strategies")
                return result
            else:
                logger.info("Strategy registry scan found no opportunities")
                return None
                
        except Exception as e:
            logger.error(f"Error during live scan: {e}")
            # Fallback to simple scan on error
            return await self._fallback_scan(strategy, symbols)
    
    async def _fallback_scan(self, strategy: str = None, symbols: List[str] = None) -> Optional[List[Dict[str, Any]]]:
        """DEPRECATED: No fallback scanning - explicit errors only."""
        # Log critical error instead of providing fallback data
        await log_critical_error(
            error_type="strategy_scan_failure",
            message=f"Strategy scanning failed for {strategy} - no fallback provided",
            details={
                "strategy": strategy,
                "symbols": symbols,
                "reason": "Strategy registry unavailable"
            },
            service="opportunity_cache",
            severity="HIGH"
        )
        logger.error(f"Strategy {strategy} scanning failed - no fallback data provided")
        raise RuntimeError(f"Strategy {strategy} is not available. System health compromised - check strategy registry.")
    
    async def _get_real_price(self, symbol: str) -> float:
        """Get real market price for symbol."""
        try:
            # Try to get real market data
            from plugins.data.yfinance_provider import YFinanceProvider
            provider = YFinanceProvider()
            quote = await provider.get_quote(symbol)
            return quote.price
        except Exception as e:
            # Log critical error - no fallback prices
            await log_critical_error(
                error_type="market_data_unavailable",
                message=f"Real-time price data unavailable for {symbol}",
                details={"symbol": symbol, "error": str(e)},
                service="opportunity_cache",
                severity="HIGH"
            )
            logger.error(f"Market data unavailable for {symbol} - no fallback price provided: {e}")
            raise RuntimeError(f"Market data provider failed for {symbol}. System health compromised.")
    
    def _update_memory_cache(self, cache_key: str, opportunities: List[Dict[str, Any]]):
        """Update memory cache with new opportunities."""
        try:
            # Limit cache size
            if len(opportunities) > self.max_memory_entries:
                opportunities = opportunities[:self.max_memory_entries]
            
            self.memory_cache[cache_key] = opportunities
            self.cache_timestamps[cache_key] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating memory cache: {e}")
    
    async def _update_database_cache(self, opportunities: List[Dict[str, Any]], 
                                   strategy: str, scan_session_id: str = None):
        """Update database cache with new opportunities."""
        try:
            db_gen = get_db()
            db = next(db_gen)
            try:
                for opp_data in opportunities:
                    # Create OpportunitySnapshot - use strategy from opportunity data
                    strategy_type = opp_data.get('strategy_type', strategy or 'high_probability')
                    snapshot = OpportunitySnapshot.from_opportunity_data(
                        opp_data, strategy_type, scan_session_id
                    )
                    
                    # Handle duplicates by updating existing records  
                    existing = db.query(OpportunitySnapshot).filter(
                        OpportunitySnapshot.opportunity_id == snapshot.opportunity_id
                    ).first()
                    
                    if existing:
                        # Update existing opportunity
                        existing.data = snapshot.data
                        existing.last_updated = datetime.utcnow()
                        existing.extend_expiration()
                    else:
                        # Add new opportunity
                        db.add(snapshot)
                
                db.commit()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error updating database cache: {e}")
    
    def _filter_opportunities(self, opportunities: List[Dict[str, Any]], 
                            strategy: str = None, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Apply additional filtering to cached opportunities."""
        result = opportunities.copy()
        
        # Filter by strategy
        if strategy:
            result = [opp for opp in result if opp.get('strategy_type') == strategy]
        
        # Filter by symbols
        if symbols:
            symbol_set = set(symbols)
            result = [opp for opp in result if opp.get('symbol') in symbol_set]
        
        return result
    
    def _get_demo_data(self, strategy: str = None, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Get demo/fallback data when live data is unavailable."""
        demo_opportunities = [
            {
                "id": "demo_opp_1",
                "symbol": "SPY",
                "strategy_type": "high_probability",
                "short_strike": 615,
                "long_strike": 605,
                "premium": 2.85,
                "max_loss": 715,
                "delta": -0.12,
                "probability_profit": 0.78,
                "expected_value": 195.50,
                "days_to_expiration": 28,
                "underlying_price": 627.50,
                "liquidity_score": 9.2,
                "bias": "BULLISH",
                "rsi": 45.3,
                "created_at": datetime.utcnow().isoformat(),
                "is_demo": True
            },
            {
                "id": "demo_opp_2",
                "symbol": "QQQ", 
                "strategy_type": "quick_scalp",
                "strike": 385,
                "premium": 3.20,
                "max_loss": 320,
                "delta": 0.35,
                "probability_profit": 0.58,
                "expected_value": 85.00,
                "days_to_expiration": 6,
                "underlying_price": 382.15,
                "liquidity_score": 8.8,
                "bias": "NEUTRAL",
                "rsi": 52.1,
                "created_at": datetime.utcnow().isoformat(),
                "is_demo": True
            },
            {
                "id": "demo_opp_3",
                "symbol": "NVDA",
                "strategy_type": "swing_trade",
                "strike": 115,
                "premium": 2.75,
                "max_loss": 275,
                "delta": 0.32,
                "probability_profit": 0.65,
                "expected_value": 138.00,
                "days_to_expiration": 42,
                "underlying_price": 118.45,
                "liquidity_score": 9.5,
                "bias": "STRONG",
                "rsi": 28.5,
                "created_at": datetime.utcnow().isoformat(),
                "is_demo": True
            }
        ]
        
        # Apply filters to demo data
        return self._filter_opportunities(demo_opportunities, strategy, symbols)


# Global cache instance
_opportunity_cache: Optional[OpportunityCache] = None


def get_opportunity_cache(plugin_registry: PluginRegistry = None) -> OpportunityCache:
    """Get global opportunity cache instance."""
    global _opportunity_cache
    if _opportunity_cache is None:
        _opportunity_cache = OpportunityCache(plugin_registry)
    return _opportunity_cache


def initialize_opportunity_cache(plugin_registry: PluginRegistry) -> OpportunityCache:
    """Initialize opportunity cache with plugin registry."""
    global _opportunity_cache
    _opportunity_cache = OpportunityCache(plugin_registry)
    return _opportunity_cache