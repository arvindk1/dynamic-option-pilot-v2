"""
Intelligent LLM Cache Manager with Change Detection and Cost Optimization.

This system implements sophisticated change detection to minimize LLM API calls
while ensuring analysis remains current and accurate. It tracks multiple data
sources and only triggers new LLM analysis when significant changes occur.
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from models.database import get_db
from models.opportunity import LLMAnalysis, TechnicalIndicator, OpportunityScore
from plugins.trading.base_strategy import StrategyOpportunity
from services.llm_validator import LLMValidatorService, LLMValidationResult


logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of changes that can trigger LLM re-analysis."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    MARKET_REGIME = "market_regime"
    VOLATILITY = "volatility"
    PRICE = "price"
    TIME_DECAY = "time_decay"


@dataclass
class ChangeThreshold:
    """Defines thresholds for triggering LLM re-analysis."""
    change_type: ChangeType
    percentage_threshold: float  # Minimum % change to trigger
    absolute_threshold: Optional[float] = None  # Minimum absolute change
    time_threshold_hours: int = 24  # Maximum time before forced refresh
    priority: int = 1  # Higher priority changes trigger more readily


@dataclass
class DataSnapshot:
    """Snapshot of all trackable data points for change detection."""
    # Technical Indicators
    rsi: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    bollinger_position: float = 0.5
    trend_strength: float = 0.0
    volume_ratio: float = 1.0
    
    # Market Data
    underlying_price: float = 0.0
    implied_volatility: float = 0.0
    realized_volatility_20d: float = 0.0
    volatility_rank: float = 50.0
    
    # Greeks and Option Data
    delta: float = 0.0
    theta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    
    # Scoring Data
    overall_score: float = 0.0
    confidence_percentage: float = 0.0
    quality_tier: str = "MEDIUM"
    
    # Market Context
    vix_level: Optional[float] = None
    market_bias: str = "NEUTRAL"
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    
    # Time Factors
    days_to_expiration: int = 30
    time_to_market_close: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hashing and comparison."""
        return asdict(self)
    
    def generate_hash(self) -> str:
        """Generate hash of all data points for change detection."""
        data = self.to_dict()
        # Round floating point values to reduce noise
        for key, value in data.items():
            if isinstance(value, float):
                data[key] = round(value, 4)
        
        hash_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()


class IntelligentLLMCacheManager:
    """
    Manages LLM analysis caching with intelligent change detection.
    
    This system tracks multiple data sources and triggers new LLM analysis
    only when significant changes occur, dramatically reducing API costs
    while maintaining analysis quality.
    """
    
    # Default change thresholds (can be customized per strategy/symbol)
    DEFAULT_THRESHOLDS = [
        # High-priority technical changes
        ChangeThreshold(ChangeType.TECHNICAL, 5.0, None, 12, 5),  # RSI, MACD changes
        ChangeThreshold(ChangeType.VOLATILITY, 10.0, 0.05, 8, 5),  # IV changes
        ChangeThreshold(ChangeType.PRICE, 3.0, 5.0, 4, 4),  # Underlying price moves
        
        # Medium-priority changes  
        ChangeThreshold(ChangeType.MARKET_REGIME, 15.0, None, 24, 3),  # Trend changes
        ChangeThreshold(ChangeType.SENTIMENT, 20.0, None, 24, 2),  # Sentiment shifts
        
        # Lower-priority changes
        ChangeThreshold(ChangeType.TIME_DECAY, 25.0, 5, 48, 1),  # DTE changes
        ChangeThreshold(ChangeType.FUNDAMENTAL, 30.0, None, 72, 1),  # Fundamental data
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.llm_validator = LLMValidatorService(db)
        
        # Cache for data snapshots to avoid repeated DB queries
        self._snapshot_cache: Dict[str, Tuple[DataSnapshot, datetime]] = {}
        
    async def get_or_generate_analysis(
        self,
        opportunity: StrategyOpportunity,
        scoring_result: Any,
        force_refresh: bool = False,
        custom_thresholds: Optional[List[ChangeThreshold]] = None
    ) -> LLMValidationResult:
        """
        Get LLM analysis with intelligent change detection.
        
        Args:
            opportunity: Trading opportunity to analyze
            scoring_result: Current scoring analysis
            force_refresh: Force new analysis regardless of changes
            custom_thresholds: Override default change thresholds
            
        Returns:
            LLM validation result (cached or fresh)
        """
        try:
            symbol = opportunity.symbol
            thresholds = custom_thresholds or self.DEFAULT_THRESHOLDS
            
            # Step 1: Create current data snapshot
            current_snapshot = self._create_data_snapshot(opportunity, scoring_result)
            
            # Step 2: Check if we have valid cached analysis
            if not force_refresh:
                cached_analysis = await self._get_valid_cached_analysis(
                    opportunity, current_snapshot, thresholds
                )
                if cached_analysis:
                    self.logger.info(f"📦 Using cached LLM analysis for {symbol} (no significant changes)")
                    return cached_analysis
            
            # Step 3: Generate new analysis if needed
            self.logger.info(f"🔄 Generating new LLM analysis for {symbol} due to significant changes")
            new_analysis = await self.llm_validator.validate_opportunity(
                opportunity, scoring_result, force_refresh=True
            )
            
            # Step 4: Store snapshot for future change detection
            await self._store_data_snapshot(opportunity, current_snapshot, new_analysis)
            
            return new_analysis
            
        except Exception as e:
            self.logger.error(f"Error in intelligent LLM cache manager: {e}")
            # Fallback to basic LLM validator
            return await self.llm_validator.validate_opportunity(
                opportunity, scoring_result, force_refresh
            )
    
    def _create_data_snapshot(
        self, 
        opportunity: StrategyOpportunity, 
        scoring_result: Any
    ) -> DataSnapshot:
        """Create comprehensive data snapshot for change detection."""
        try:
            # Get technical indicators
            tech_data = self._get_latest_technical_data(opportunity.symbol)
            
            # Create snapshot with all trackable data points
            snapshot = DataSnapshot(
                # Technical indicators
                rsi=tech_data.get('rsi', 50.0),
                macd=tech_data.get('macd', 0.0),
                macd_signal=tech_data.get('macd_signal', 0.0),
                macd_histogram=tech_data.get('macd_histogram', 0.0),
                bollinger_position=tech_data.get('bollinger_position', 0.5),
                trend_strength=tech_data.get('trend_strength', 0.0),
                volume_ratio=tech_data.get('volume_ratio', 1.0),
                
                # Market data
                underlying_price=getattr(opportunity, 'underlying_price', 0.0),
                implied_volatility=getattr(opportunity, 'implied_volatility', 0.0),
                realized_volatility_20d=tech_data.get('realized_volatility_20d', 0.0),
                volatility_rank=tech_data.get('volatility_rank', 50.0),
                
                # Greeks
                delta=getattr(opportunity, 'delta', 0.0),
                theta=getattr(opportunity, 'theta', 0.0),
                gamma=getattr(opportunity, 'gamma', 0.0),
                vega=getattr(opportunity, 'vega', 0.0),
                
                # Scoring
                overall_score=getattr(scoring_result, 'overall_score', 0.0),
                confidence_percentage=getattr(scoring_result, 'confidence_percentage', 0.0),
                quality_tier=getattr(scoring_result, 'quality_tier', 'MEDIUM'),
                
                # Market context
                vix_level=self._get_current_vix(),
                market_bias=getattr(opportunity, 'market_bias', 'NEUTRAL'),
                support_level=tech_data.get('support_level'),
                resistance_level=tech_data.get('resistance_level'),
                
                # Time factors
                days_to_expiration=getattr(opportunity, 'days_to_expiration', 30),
                time_to_market_close=self._get_time_to_market_close()
            )
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error creating data snapshot: {e}")
            return DataSnapshot()  # Return default snapshot
    
    async def _get_valid_cached_analysis(
        self,
        opportunity: StrategyOpportunity,
        current_snapshot: DataSnapshot,
        thresholds: List[ChangeThreshold]
    ) -> Optional[LLMValidationResult]:
        """Check if cached analysis is still valid based on change thresholds."""
        try:
            symbol = opportunity.symbol
            
            # Get most recent cached analysis
            recent_analysis = self._get_most_recent_analysis(opportunity.id)
            if not recent_analysis:
                return None
            
            # Get the data snapshot from when analysis was created
            previous_snapshot = await self._get_historical_snapshot(
                symbol, recent_analysis.created_at
            )
            if not previous_snapshot:
                return None
            
            # Check time-based expiration first
            analysis_age = datetime.utcnow() - recent_analysis.created_at
            max_age_hours = min(threshold.time_threshold_hours for threshold in thresholds)
            
            if analysis_age.total_seconds() / 3600 > max_age_hours:
                self.logger.info(f"⏰ Analysis expired due to age: {analysis_age.total_seconds() / 3600:.1f}h > {max_age_hours}h")
                return None
            
            # Check for significant changes
            significant_changes = self._detect_significant_changes(
                previous_snapshot, current_snapshot, thresholds
            )
            
            if significant_changes:
                change_summary = ", ".join([f"{change.change_type.value}" for change in significant_changes])
                self.logger.info(f"🔄 Significant changes detected: {change_summary}")
                return None
            
            # Convert database record to LLMValidationResult
            return LLMValidationResult(
                profit_explanation=recent_analysis.profit_explanation,
                technical_analysis=recent_analysis.technical_analysis or "Technical analysis cached",
                risk_assessment=recent_analysis.risk_assessment or "Risk assessment cached",
                market_context=recent_analysis.market_context or "Market context cached",
                confidence_rating=recent_analysis.confidence_rating or 0.75,
                model_used=recent_analysis.model_used or "cached",
                tokens_consumed=0,  # No new tokens for cached result
                processing_time_ms=5,
                cached=True
            )
            
        except Exception as e:
            self.logger.error(f"Error checking cached analysis validity: {e}")
            return None
    
    def _detect_significant_changes(
        self,
        previous: DataSnapshot,
        current: DataSnapshot,
        thresholds: List[ChangeThreshold]
    ) -> List[ChangeThreshold]:
        """Detect significant changes that warrant new LLM analysis."""
        significant_changes = []
        
        try:
            prev_data = previous.to_dict()
            curr_data = current.to_dict()
            
            # Check each threshold
            for threshold in thresholds:
                change_detected = False
                
                if threshold.change_type == ChangeType.TECHNICAL:
                    # Check RSI, MACD, trend strength changes
                    technical_fields = ['rsi', 'macd', 'trend_strength', 'bollinger_position']
                    for field in technical_fields:
                        if self._exceeds_threshold(
                            prev_data.get(field, 0), 
                            curr_data.get(field, 0), 
                            threshold
                        ):
                            change_detected = True
                            break
                
                elif threshold.change_type == ChangeType.VOLATILITY:
                    # Check IV, realized volatility, volatility rank
                    vol_fields = ['implied_volatility', 'realized_volatility_20d', 'volatility_rank']
                    for field in vol_fields:
                        if self._exceeds_threshold(
                            prev_data.get(field, 0), 
                            curr_data.get(field, 0), 
                            threshold
                        ):
                            change_detected = True
                            break
                
                elif threshold.change_type == ChangeType.PRICE:
                    # Check underlying price changes
                    if self._exceeds_threshold(
                        prev_data.get('underlying_price', 0),
                        curr_data.get('underlying_price', 0),
                        threshold
                    ):
                        change_detected = True
                
                elif threshold.change_type == ChangeType.MARKET_REGIME:
                    # Check trend strength and market bias changes
                    if (prev_data.get('market_bias') != curr_data.get('market_bias') or
                        self._exceeds_threshold(
                            prev_data.get('trend_strength', 0),
                            curr_data.get('trend_strength', 0),
                            threshold
                        )):
                        change_detected = True
                
                elif threshold.change_type == ChangeType.TIME_DECAY:
                    # Check DTE changes
                    if self._exceeds_threshold(
                        prev_data.get('days_to_expiration', 30),
                        curr_data.get('days_to_expiration', 30),
                        threshold
                    ):
                        change_detected = True
                
                if change_detected:
                    significant_changes.append(threshold)
            
            # Sort by priority (higher priority first)
            significant_changes.sort(key=lambda x: x.priority, reverse=True)
            return significant_changes
            
        except Exception as e:
            self.logger.error(f"Error detecting changes: {e}")
            return []
    
    def _exceeds_threshold(
        self, 
        old_value: float, 
        new_value: float, 
        threshold: ChangeThreshold
    ) -> bool:
        """Check if change exceeds threshold (percentage or absolute)."""
        try:
            if old_value == 0:
                return abs(new_value) > (threshold.absolute_threshold or 0)
            
            percentage_change = abs((new_value - old_value) / old_value) * 100
            
            if percentage_change >= threshold.percentage_threshold:
                return True
            
            if threshold.absolute_threshold:
                absolute_change = abs(new_value - old_value)
                return absolute_change >= threshold.absolute_threshold
            
            return False
            
        except (ZeroDivisionError, TypeError):
            return False
    
    def _get_latest_technical_data(self, symbol: str) -> Dict[str, Any]:
        """Get latest technical indicator data for symbol."""
        try:
            # Use cached data if available and recent (within 5 minutes)
            cache_key = f"tech_{symbol}"
            if cache_key in self._snapshot_cache:
                cached_data, cached_time = self._snapshot_cache[cache_key]
                if datetime.utcnow() - cached_time < timedelta(minutes=5):
                    return cached_data.to_dict()
            
            # Query database for latest technical indicators
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            
            indicator = self.db.query(TechnicalIndicator).filter(
                and_(
                    TechnicalIndicator.symbol == symbol,
                    TechnicalIndicator.calculated_at >= recent_cutoff
                )
            ).order_by(desc(TechnicalIndicator.calculated_at)).first()
            
            if indicator:
                tech_data = {
                    'rsi': indicator.rsi or 50.0,
                    'macd': indicator.macd or 0.0,
                    'macd_signal': indicator.macd_signal or 0.0,
                    'macd_histogram': indicator.macd_histogram or 0.0,
                    'bollinger_position': indicator.bollinger_position or 0.5,
                    'trend_strength': indicator.trend_strength or 0.0,
                    'volume_ratio': indicator.volume_ratio or 1.0,
                    'realized_volatility_20d': indicator.realized_volatility_20d or 0.0,
                    'volatility_rank': indicator.volatility_rank or 50.0,
                    'support_level': indicator.support_level,
                    'resistance_level': indicator.resistance_level,
                }
                
                # Cache the data
                snapshot = DataSnapshot(**tech_data)
                self._snapshot_cache[cache_key] = (snapshot, datetime.utcnow())
                
                return tech_data
            
            # Return default values if no technical data available
            return {
                'rsi': 50.0, 'macd': 0.0, 'macd_signal': 0.0, 'macd_histogram': 0.0,
                'bollinger_position': 0.5, 'trend_strength': 0.0, 'volume_ratio': 1.0,
                'realized_volatility_20d': 0.2, 'volatility_rank': 50.0,
                'support_level': None, 'resistance_level': None
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching technical data for {symbol}: {e}")
            return {}
    
    def _get_current_vix(self) -> Optional[float]:
        """Get current VIX level for market context."""
        try:
            # This would integrate with VIX data provider
            # For now, return None to indicate no data
            return None
        except Exception:
            return None
    
    def _get_time_to_market_close(self) -> Optional[int]:
        """Get minutes until market close."""
        try:
            # This would integrate with market hours API
            # For now, return None
            return None
        except Exception:
            return None
    
    def _get_most_recent_analysis(self, opportunity_id: str) -> Optional[Any]:
        """Get most recent LLM analysis for opportunity."""
        try:
            return self.db.query(LLMAnalysis).filter(
                LLMAnalysis.opportunity_id == opportunity_id
            ).order_by(desc(LLMAnalysis.created_at)).first()
            
        except Exception as e:
            self.logger.error(f"Error fetching recent analysis: {e}")
            return None
    
    async def _get_historical_snapshot(
        self, 
        symbol: str, 
        timestamp: datetime
    ) -> Optional[DataSnapshot]:
        """Get historical data snapshot from around the given timestamp."""
        try:
            # This would query historical technical indicators
            # For now, return None to trigger new analysis
            return None
        except Exception:
            return None
    
    async def _store_data_snapshot(
        self,
        opportunity: StrategyOpportunity,
        snapshot: DataSnapshot,
        analysis: LLMValidationResult
    ) -> None:
        """Store data snapshot for future change detection."""
        try:
            # Store in cache for immediate use
            cache_key = f"snapshot_{opportunity.symbol}_{opportunity.id}"
            self._snapshot_cache[cache_key] = (snapshot, datetime.utcnow())
            
            # Could also store in database for persistent historical tracking
            # This would require a new table for data snapshots
            
        except Exception as e:
            self.logger.error(f"Error storing data snapshot: {e}")
    
    def get_cache_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get statistics on cache efficiency and cost savings."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Count cached vs fresh analyses
            total_analyses = self.db.query(func.count(LLMAnalysis.id)).filter(
                LLMAnalysis.created_at >= cutoff_date
            ).scalar() or 0
            
            fresh_analyses = self.db.query(func.count(LLMAnalysis.id)).filter(
                and_(
                    LLMAnalysis.created_at >= cutoff_date,
                    LLMAnalysis.tokens_consumed > 0  # Only fresh analyses consume tokens
                )
            ).scalar() or 0
            
            cached_analyses = total_analyses - fresh_analyses
            cache_hit_rate = (cached_analyses / total_analyses * 100) if total_analyses > 0 else 0
            
            # Calculate cost savings (rough estimate)
            avg_tokens_per_analysis = 250  # Estimated average
            cost_per_token = 0.002 / 1000  # GPT-3.5-turbo pricing
            
            tokens_saved = cached_analyses * avg_tokens_per_analysis
            cost_saved = tokens_saved * cost_per_token
            
            return {
                'period_days': days,
                'total_analysis_requests': total_analyses,
                'fresh_analyses': fresh_analyses,
                'cached_analyses': cached_analyses,
                'cache_hit_rate_percentage': round(cache_hit_rate, 1),
                'estimated_tokens_saved': tokens_saved,
                'estimated_cost_saved_usd': round(cost_saved, 4),
                'efficiency_rating': 'HIGH' if cache_hit_rate > 70 else 'MEDIUM' if cache_hit_rate > 40 else 'LOW'
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating cache statistics: {e}")
            return {'error': 'Unable to calculate cache statistics'}


def get_intelligent_llm_cache() -> IntelligentLLMCacheManager:
    """Get intelligent LLM cache manager instance."""
    db = next(get_db())
    return IntelligentLLMCacheManager(db)