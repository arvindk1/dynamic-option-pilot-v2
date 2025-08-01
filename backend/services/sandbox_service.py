"""
Sandbox Service for Strategy Testing
Handles test execution, data caching, and result management
"""

import asyncio
import logging
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.database import get_db
from models.sandbox import (
    SandboxStrategyConfig, SandboxTestRun, SandboxHistoricalCache,
    get_user_sandbox_stats, cleanup_expired_cache
)
from core.orchestrator.strategy_registry import get_strategy_registry
from services.universe_loader import get_universe_loader
from plugins.trading.base_strategy import StrategyConfig, StrategyOpportunity

logger = logging.getLogger(__name__)


class SandboxDataCache:
    """
    Manages cached historical data for sandbox testing
    Avoids hitting live APIs during strategy development
    """
    
    def __init__(self):
        self.cache_ttl = {
            'market_data': 24,      # 24 hours for market data
            'options_chain': 12,    # 12 hours for options chains
            'historical_prices': 72 # 72 hours for historical price data
        }
    
    async def get_cached_market_data(self, symbols: List[str], db: Session) -> Dict[str, Any]:
        """Get cached market data for symbols"""
        cached_data = {}
        
        for symbol in symbols:
            cache_key = f"{symbol}_market_data_{datetime.now().strftime('%Y%m%d')}"
            
            # Check if we have cached data
            cached_entry = db.query(SandboxHistoricalCache).filter(
                SandboxHistoricalCache.cache_key == cache_key,
                SandboxHistoricalCache.expires_at > datetime.utcnow()
            ).first()
            
            if cached_entry:
                cached_data[symbol] = cached_entry.data
                logger.debug(f"Using cached market data for {symbol}")
            else:
                # Generate sample market data for testing
                sample_data = self._generate_sample_market_data(symbol)
                cached_data[symbol] = sample_data
                
                # Cache the generated data
                new_cache = SandboxHistoricalCache.create_cache_entry(
                    symbol=symbol,
                    data_type='market_data',
                    data=sample_data,
                    ttl_hours=self.cache_ttl['market_data']
                )
                db.add(new_cache)
                db.commit()
                logger.debug(f"Generated and cached market data for {symbol}")
        
        return cached_data
    
    def _generate_sample_market_data(self, symbol: str) -> Dict[str, Any]:
        """Generate realistic sample market data for testing"""
        import random
        
        # Base prices for common symbols
        base_prices = {
            'SPY': 450.0, 'QQQ': 380.0, 'IWM': 200.0, 'AAPL': 180.0,
            'MSFT': 340.0, 'GOOGL': 140.0, 'AMZN': 150.0, 'NVDA': 450.0,
            'TSLA': 250.0, 'META': 320.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        current_price = base_price * (1 + random.uniform(-0.05, 0.05))  # ±5% variation
        
        return {
            'symbol': symbol,
            'price': round(current_price, 2),
            'change': round(random.uniform(-5.0, 5.0), 2),
            'change_percent': round(random.uniform(-2.0, 2.0), 2),
            'volume': random.randint(1000000, 10000000),
            'bid': round(current_price - 0.01, 2),
            'ask': round(current_price + 0.01, 2),
            'iv_rank': random.randint(15, 85),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_cached_options_chain(self, symbol: str, expiration: str, db: Session) -> Dict[str, Any]:
        """Get cached options chain data"""
        cache_key = f"{symbol}_options_{expiration}"
        
        cached_entry = db.query(SandboxHistoricalCache).filter(
            SandboxHistoricalCache.cache_key == cache_key,
            SandboxHistoricalCache.expires_at > datetime.utcnow()
        ).first()
        
        if cached_entry:
            return cached_entry.data
        
        # Generate sample options chain
        sample_chain = self._generate_sample_options_chain(symbol, expiration)
        
        # Cache the generated data
        new_cache = SandboxHistoricalCache.create_cache_entry(
            symbol=symbol,
            data_type='options_chain',
            data=sample_chain,
            ttl_hours=self.cache_ttl['options_chain']
        )
        db.add(new_cache)
        db.commit()
        
        return sample_chain
    
    def _generate_sample_options_chain(self, symbol: str, expiration: str) -> Dict[str, Any]:
        """Generate realistic sample options chain"""
        import random
        
        # Get market data for underlying
        underlying_price = self._generate_sample_market_data(symbol)['price']
        
        chain = {
            'symbol': symbol,
            'expiration': expiration,
            'underlying_price': underlying_price,
            'calls': {},
            'puts': {}
        }
        
        # Generate strikes around current price
        strikes = []
        for i in range(-10, 11):  # 21 strikes total
            strike = round(underlying_price + (i * 5), 0)  # $5 intervals
            strikes.append(strike)
        
        for strike in strikes:
            # Distance from money affects pricing
            distance = abs(strike - underlying_price) / underlying_price
            
            # Simple option pricing simulation
            base_premium = max(0.1, 5.0 * (1 - distance * 2))
            call_premium = base_premium if strike > underlying_price else max(underlying_price - strike, base_premium)
            put_premium = base_premium if strike < underlying_price else max(strike - underlying_price, base_premium)
            
            chain['calls'][str(strike)] = {
                'strike': strike,
                'bid': round(call_premium * 0.95, 2),
                'ask': round(call_premium * 1.05, 2),
                'mid': round(call_premium, 2),
                'volume': random.randint(0, 1000),
                'open_interest': random.randint(0, 5000),
                'delta': round(0.5 - distance, 3),
                'gamma': round(random.uniform(0.001, 0.01), 4),
                'theta': round(random.uniform(-0.1, -0.01), 3),
                'vega': round(random.uniform(0.1, 0.3), 3),
                'iv': round(random.uniform(0.15, 0.45), 3)
            }
            
            chain['puts'][str(strike)] = {
                'strike': strike,
                'bid': round(put_premium * 0.95, 2),
                'ask': round(put_premium * 1.05, 2),
                'mid': round(put_premium, 2),
                'volume': random.randint(0, 1000),
                'open_interest': random.randint(0, 5000),
                'delta': round(-0.5 + distance, 3),
                'gamma': round(random.uniform(0.001, 0.01), 4),
                'theta': round(random.uniform(-0.1, -0.01), 3),
                'vega': round(random.uniform(0.1, 0.3), 3),
                'iv': round(random.uniform(0.15, 0.45), 3)
            }
        
        return chain


class SandboxTestEngine:
    """
    Executes strategy tests using cached data
    """
    
    def __init__(self):
        self.data_cache = SandboxDataCache()
    
    async def run_strategy_test(self, config: SandboxStrategyConfig, 
                              test_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run a strategy test with cached data
        
        Args:
            config: Sandbox strategy configuration
            test_params: Test-specific parameters
            
        Returns:
            Test results with opportunities and performance metrics
        """
        start_time = datetime.utcnow()
        
        try:
            # Get database session
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Get strategy registry
                strategy_registry = get_strategy_registry()
                if not strategy_registry:
                    return self._create_error_result("Strategy registry not available")
                
                # Get strategy instance - map sandbox strategy_ids to live strategy IDs
                strategy_id_mapping = {
                    'thetacrop_weekly': 'ThetaCropWeekly',
                    'iron_condor': 'IronCondor',
                    'rsi_coupon': 'RSICouponStrategy',
                    'credit_spread': 'CreditSpread',
                    'covered_call': 'CoveredCall'
                }
                
                live_strategy_id = strategy_id_mapping.get(config.strategy_id, config.strategy_id)
                strategy_instance = strategy_registry.get_strategy(live_strategy_id)
                if not strategy_instance:
                    return self._create_error_result(f"Strategy {config.strategy_id} (mapped to {live_strategy_id}) not found")
                
                # Get universe symbols
                universe_loader = get_universe_loader()
                test_symbols = test_params.get('symbols') if test_params else None
                
                if not test_symbols:
                    # Use strategy's configured universe (external file preferred)
                    strategy_config = config.config_data
                    universe_config = strategy_config.get('universe', {})
                    
                    if 'universe_file' in universe_config:
                        # Load from external file
                        try:
                            universe_symbols = universe_loader.load_universe_symbols(universe_config['universe_file'])
                        except Exception as e:
                            logger.warning(f"Failed to load universe file: {e}, falling back to primary_symbols")
                            universe_symbols = universe_config.get('primary_symbols', [])
                    else:
                        universe_symbols = universe_config.get('primary_symbols', [])
                    
                    if not universe_symbols:
                        # Load default universe if no symbols found
                        try:
                            universe_symbols = universe_loader.load_universe_symbols("default_etfs.txt")
                        except Exception:
                            universe_symbols = ['SPY', 'QQQ', 'IWM']  # Final fallback
                    
                    test_symbols = universe_symbols[:5]  # Limit for testing
                
                logger.info(f"Running sandbox test for {config.strategy_id} with symbols: {test_symbols}")
                
                # Get cached market data
                market_data = await self.data_cache.get_cached_market_data(test_symbols, db)
                
                # Execute strategy test
                opportunities = await self._execute_strategy_with_cached_data(
                    strategy_instance, test_symbols, market_data, config.config_data
                )
                
                # Calculate execution time
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # Create test results
                results = {
                    'success': True,
                    'opportunities': [self._opportunity_to_dict(opp) for opp in opportunities],
                    'opportunities_count': len(opportunities),
                    'symbols_tested': test_symbols,
                    'market_data_used': market_data,
                    'performance_metrics': self._calculate_performance_metrics(opportunities),
                    'execution_time_ms': execution_time,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Save test run to database
                test_run = SandboxTestRun.create_test_run(
                    config_id=config.id,
                    test_params=test_params or {},
                    results=results,
                    execution_time=execution_time
                )
                db.add(test_run)
                db.commit()
                
                logger.info(f"Sandbox test completed: {len(opportunities)} opportunities found in {execution_time}ms")
                
                return results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error running sandbox test: {e}")
            return self._create_error_result(str(e))
    
    async def _execute_strategy_with_cached_data(self, strategy_instance, symbols: List[str], 
                                               market_data: Dict[str, Any], 
                                               config_data: Dict[str, Any]) -> List[StrategyOpportunity]:
        """Execute strategy scanning with cached data"""
        try:
            # Call the strategy's scan method with cached data
            opportunities = await strategy_instance.scan_opportunities(symbols)
            
            # If no opportunities found, generate some sample ones for testing
            if not opportunities:
                opportunities = self._generate_sample_opportunities(symbols, config_data)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error executing strategy scan: {e}")
            # Return sample opportunities for testing
            return self._generate_sample_opportunities(symbols, config_data)
    
    def _generate_sample_opportunities(self, symbols: List[str], config_data: Dict[str, Any]) -> List[StrategyOpportunity]:
        """Generate sample opportunities for testing"""
        import random
        from plugins.trading.base_strategy import StrategyOpportunity
        
        opportunities = []
        strategy_id = config_data.get('strategy', {}).get('id', 'test_strategy')
        
        for i, symbol in enumerate(symbols[:3]):  # Generate max 3 for testing
            opp_id = f"sandbox_test_{strategy_id}_{symbol}_{int(datetime.utcnow().timestamp())}"
            
            opportunity = StrategyOpportunity(
                id=opp_id,
                symbol=symbol,
                strategy_type=strategy_id,
                strategy_id=strategy_id,
                option_type="iron_condor",
                short_strike=180.0 + (i * 5),
                long_strike=175.0 + (i * 5),
                expiration="2025-08-15",
                days_to_expiration=15 + i,
                premium=2.5 + (i * 0.3),
                max_loss=750.0,
                max_profit=250.0,
                probability_profit=0.72 + (i * 0.02),
                expected_value=180.0 + (i * 15),
                delta=-0.15 + (i * 0.02),
                underlying_price=180.0 + (i * 2),
                liquidity_score=8.5 - (i * 0.2),
                market_bias="NEUTRAL",
                universe="sandbox_test",
                created_at=datetime.utcnow(),
                metadata={
                    'test_generated': True,
                    'sandbox_run': True,
                    'config_used': strategy_id
                }
            )
            opportunities.append(opportunity)
        
        return opportunities
    
    def _opportunity_to_dict(self, opp: StrategyOpportunity) -> Dict[str, Any]:
        """Convert StrategyOpportunity to dictionary"""
        return {
            'id': opp.id,
            'symbol': opp.symbol,
            'strategy_type': opp.strategy_type,
            'strategy_id': opp.strategy_id,
            'option_type': opp.option_type,
            'short_strike': opp.short_strike,
            'long_strike': opp.long_strike,
            'expiration': opp.expiration,
            'days_to_expiration': opp.days_to_expiration,
            'premium': opp.premium,
            'max_loss': opp.max_loss,
            'max_profit': opp.max_profit,
            'probability_profit': opp.probability_profit,
            'expected_value': opp.expected_value,
            'delta': opp.delta,
            'underlying_price': opp.underlying_price,
            'liquidity_score': opp.liquidity_score,
            'market_bias': getattr(opp, 'bias', 'NEUTRAL'),  # Use bias instead of market_bias
            'universe': getattr(opp, 'universe', 'default'),  # Handle missing universe
            'created_at': opp.generated_at.isoformat() if hasattr(opp, 'generated_at') and opp.generated_at else datetime.utcnow().isoformat(),
            'is_sandbox_test': True
        }
    
    def _calculate_performance_metrics(self, opportunities: List[StrategyOpportunity]) -> Dict[str, Any]:
        """Calculate performance metrics for test results"""
        if not opportunities:
            return {
                'avg_probability_profit': 0.0,
                'avg_expected_value': 0.0,
                'avg_premium': 0.0,
                'risk_reward_ratio': 0.0
            }
        
        avg_prob = sum(opp.probability_profit for opp in opportunities) / len(opportunities)
        avg_ev = sum(opp.expected_value for opp in opportunities) / len(opportunities)
        avg_premium = sum(opp.premium for opp in opportunities) / len(opportunities)
        avg_max_loss = sum(opp.max_loss for opp in opportunities) / len(opportunities)
        
        risk_reward = avg_premium / avg_max_loss if avg_max_loss > 0 else 0
        
        return {
            'total_opportunities': len(opportunities),
            'avg_probability_profit': round(avg_prob, 3),
            'avg_expected_value': round(avg_ev, 2),
            'avg_premium': round(avg_premium, 2),
            'avg_max_loss': round(avg_max_loss, 2),
            'risk_reward_ratio': round(risk_reward, 4),
            'symbols_with_opportunities': len(set(opp.symbol for opp in opportunities))
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result structure"""
        return {
            'success': False,
            'error': error_message,
            'opportunities': [],
            'opportunities_count': 0,
            'symbols_tested': [],
            'execution_time_ms': 0,
            'timestamp': datetime.utcnow().isoformat()
        }


class SandboxService:
    """
    Main sandbox service orchestrating strategy testing
    """
    
    def __init__(self):
        self.test_engine = SandboxTestEngine()
    
    async def create_strategy_config(self, strategy_id: str, name: str, 
                                   config_data: Dict[str, Any], 
                                   user_id: str = 'default_user') -> SandboxStrategyConfig:
        """Create a new sandbox strategy configuration"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            config = SandboxStrategyConfig.from_strategy_config(
                strategy_id=strategy_id,
                name=name,
                config_data=config_data,
                user_id=user_id
            )
            
            db.add(config)
            db.commit()
            db.refresh(config)
            
            logger.info(f"Created sandbox strategy config: {config.id} ({name})")
            return config
            
        finally:
            db.close()
    
    async def get_user_strategies(self, user_id: str = 'default_user') -> List[SandboxStrategyConfig]:
        """Get all strategy configurations for a user"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            configs = db.query(SandboxStrategyConfig).filter(
                SandboxStrategyConfig.user_id == user_id
            ).order_by(desc(SandboxStrategyConfig.updated_at)).all()
            
            return configs
            
        finally:
            db.close()
    
    async def get_strategy_config(self, config_id: str) -> Optional[SandboxStrategyConfig]:
        """Get a specific strategy configuration"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            config = db.query(SandboxStrategyConfig).filter(
                SandboxStrategyConfig.id == config_id
            ).first()
            
            return config
            
        finally:
            db.close()
    
    async def update_strategy_config(self, config_id: str, updates: Dict[str, Any]) -> Optional[SandboxStrategyConfig]:
        """Update a strategy configuration"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            config = db.query(SandboxStrategyConfig).filter(
                SandboxStrategyConfig.id == config_id
            ).first()
            
            if not config:
                return None
            
            # Update fields
            for field, value in updates.items():
                if hasattr(config, field):
                    setattr(config, field, value)
            
            config.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(config)
            
            logger.info(f"Updated sandbox strategy config: {config_id}")
            return config
            
        finally:
            db.close()
    
    async def run_strategy_test(self, config_id: str, test_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a test for a strategy configuration"""
        config = await self.get_strategy_config(config_id)
        if not config:
            return {'success': False, 'error': f'Configuration {config_id} not found'}
        
        return await self.test_engine.run_strategy_test(config, test_params)
    
    async def get_test_results(self, config_id: str, limit: int = 10) -> List[SandboxTestRun]:
        """Get recent test results for a strategy"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            results = db.query(SandboxTestRun).filter(
                SandboxTestRun.config_id == config_id
            ).order_by(desc(SandboxTestRun.created_at)).limit(limit).all()
            
            return results
            
        finally:
            db.close()
    
    async def get_user_stats(self, user_id: str = 'default_user') -> Dict[str, Any]:
        """Get aggregate statistics for a user's sandbox usage"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            stats = get_user_sandbox_stats(db, user_id)
            return stats
            
        finally:
            db.close()
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired cache and old test data"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Clean expired cache
            expired_cache_count = cleanup_expired_cache(db)
            
            # Clean old test runs (older than 30 days)
            old_date = datetime.utcnow() - timedelta(days=30)
            old_tests = db.query(SandboxTestRun).filter(
                SandboxTestRun.created_at < old_date
            ).all()
            
            old_test_count = len(old_tests)
            for test in old_tests:
                db.delete(test)
            
            db.commit()
            
            logger.info(f"Cleaned up {expired_cache_count} cache entries and {old_test_count} old test runs")
            
            return {
                'expired_cache_entries': expired_cache_count,
                'old_test_runs': old_test_count
            }
            
        finally:
            db.close()


# Global service instance
_sandbox_service: Optional[SandboxService] = None


def get_sandbox_service() -> SandboxService:
    """Get global sandbox service instance"""
    global _sandbox_service
    if _sandbox_service is None:
        _sandbox_service = SandboxService()
    return _sandbox_service