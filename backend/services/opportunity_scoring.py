"""
Comprehensive opportunity scoring service with multi-dimensional analysis.

This service provides the 'brain' of the trading platform by scoring opportunities
across multiple dimensions and providing clear explanations for trading decisions.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import math
import statistics
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from models.database import get_db
from models.opportunity import OpportunityScore, TechnicalIndicator
from plugins.trading.base_strategy import StrategyOpportunity


logger = logging.getLogger(__name__)


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of opportunity scoring."""
    technical: float = 0.0
    liquidity: float = 0.0  
    risk_adjusted: float = 0.0
    probability: float = 0.0
    volatility: float = 0.0
    time_decay: float = 0.0
    market_regime: float = 0.0
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall score."""
        return (
            self.technical * 0.25 +
            self.liquidity * 0.20 +
            self.risk_adjusted * 0.20 +
            self.probability * 0.15 +
            self.volatility * 0.10 +
            self.time_decay * 0.05 +
            self.market_regime * 0.05
        )


@dataclass  
class ScoringResult:
    """Complete scoring result with explanation."""
    overall_score: float
    confidence_percentage: float
    quality_tier: str  # HIGH, MEDIUM, LOW
    score_breakdown: ScoreBreakdown
    profit_explanation: Optional[str] = None
    reasoning: Optional[str] = None


class OpportunityScoringService:
    """
    Comprehensive opportunity scoring service.
    
    Provides multi-dimensional scoring across technical, fundamental, and risk factors
    to help traders make informed decisions with transparent reasoning.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
    def score_opportunity(
        self, 
        opportunity: StrategyOpportunity,
        technical_data: Optional[Dict] = None
    ) -> ScoringResult:
        """
        Comprehensive opportunity scoring with transparent methodology.
        
        Args:
            opportunity: The trading opportunity to score
            technical_data: Optional technical indicator data
            
        Returns:
            Complete scoring result with breakdown and explanation
        """
        try:
            # Get or calculate technical indicators
            tech_indicators = technical_data or self._get_technical_indicators(opportunity.symbol)
            
            # Calculate individual score components
            breakdown = ScoreBreakdown()
            breakdown.technical = self._score_technical_analysis(opportunity, tech_indicators)
            breakdown.liquidity = self._score_liquidity(opportunity)
            breakdown.risk_adjusted = self._score_risk_adjusted_return(opportunity)
            breakdown.probability = self._score_probability_metrics(opportunity)
            breakdown.volatility = self._score_volatility_edge(opportunity, tech_indicators)
            breakdown.time_decay = self._score_time_decay(opportunity)
            breakdown.market_regime = self._score_market_regime(opportunity, tech_indicators)
            
            # Calculate overall score and confidence
            overall_score = breakdown.overall_score
            confidence = self._calculate_confidence_percentage(opportunity, breakdown, tech_indicators)
            quality_tier = self._determine_quality_tier(overall_score, confidence)
            
            # Generate profit explanation
            profit_explanation = self._generate_profit_explanation(opportunity, breakdown, tech_indicators)
            
            # Store in database for performance tracking
            self._store_score_result(opportunity, breakdown, overall_score, confidence, quality_tier)
            
            return ScoringResult(
                overall_score=overall_score,
                confidence_percentage=confidence,
                quality_tier=quality_tier,
                score_breakdown=breakdown,
                profit_explanation=profit_explanation,
                reasoning=f"Score based on {len([x for x in [breakdown.technical, breakdown.liquidity, breakdown.risk_adjusted] if x > 0])} validated factors"
            )
            
        except Exception as e:
            self.logger.error(f"Error scoring opportunity {opportunity.id}: {str(e)}")
            # Return fallback scoring
            return self._fallback_scoring(opportunity)
    
    def _score_technical_analysis(self, opportunity: StrategyOpportunity, tech_data: Dict) -> float:
        """Score based on technical indicator strength (25% weight)."""
        try:
            score = 0.0
            factors = 0
            
            # RSI Analysis (0-25 points)
            rsi = tech_data.get('rsi', 50)
            if rsi is not None:
                if opportunity.strategy_type in ['PUT', 'PROTECTIVE_PUT', 'COLLAR']:
                    # Bullish strategies favor oversold conditions
                    rsi_score = max(0, (30 - rsi) * 2.5) if rsi < 50 else 0
                elif opportunity.strategy_type in ['CALL', 'COVERED_CALL']:
                    # Bearish strategies favor overbought conditions  
                    rsi_score = max(0, (rsi - 70) * 2.5) if rsi > 50 else 0
                else:
                    # Neutral strategies favor extreme conditions
                    rsi_score = max(0, min(25, abs(rsi - 50) * 0.5))
                score += min(25, rsi_score)
                factors += 1
            
            # MACD Signal Strength (0-25 points)
            macd = tech_data.get('macd', 0)
            macd_signal = tech_data.get('macd_signal', 0)
            if macd is not None and macd_signal is not None:
                macd_divergence = abs(macd - macd_signal)
                macd_score = min(25, macd_divergence * 100)  # Normalize divergence
                score += macd_score
                factors += 1
            
            # Trend Strength (0-25 points) 
            trend_strength = tech_data.get('trend_strength', 0)
            if trend_strength is not None:
                trend_score = min(25, abs(trend_strength) * 25)
                score += trend_score
                factors += 1
                
            # Bollinger Band Position (0-25 points)
            bb_position = tech_data.get('bollinger_position', 0.5)
            if bb_position is not None:
                # Extreme positions indicate potential reversals
                bb_score = min(25, abs(bb_position - 0.5) * 50)
                score += bb_score
                factors += 1
            
            # Average the score if we have indicators
            final_score = score / max(1, factors) if factors > 0 else 0
            return min(100, final_score)
            
        except Exception as e:
            self.logger.warning(f"Technical analysis scoring error: {e}")
            return 0.0
    
    def _score_liquidity(self, opportunity: StrategyOpportunity) -> float:
        """Score based on market liquidity and execution quality (20% weight)."""
        try:
            score = 0.0
            
            # Use existing liquidity_score if available (0-40 points)
            if hasattr(opportunity, 'liquidity_score') and opportunity.liquidity_score:
                liquidity_raw = opportunity.liquidity_score
                # Normalize from 0-10 scale to 0-40
                score += (liquidity_raw / 10) * 40
            else:
                # Fallback based on symbol popularity
                popular_symbols = ['SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']
                if opportunity.symbol in popular_symbols:
                    score += 35  # High liquidity
                else:
                    score += 20  # Medium liquidity assumed
            
            # Bid-Ask Spread Factor (0-30 points)
            # TODO: Implement when market data includes spread information
            score += 25  # Assume reasonable spread for now
            
            # Volume Analysis (0-30 points)
            # TODO: Implement when volume data is available
            score += 20  # Assume reasonable volume
            
            return min(100, score)
            
        except Exception as e:
            self.logger.warning(f"Liquidity scoring error: {e}")
            return 50.0  # Conservative fallback
    
    def _score_risk_adjusted_return(self, opportunity: StrategyOpportunity) -> float:
        """Score based on risk-adjusted return potential (20% weight)."""
        try:
            score = 0.0
            
            # Profit to Risk Ratio (0-50 points)
            max_profit = getattr(opportunity, 'max_profit', 0)
            max_loss = abs(getattr(opportunity, 'max_loss', 0))
            
            if max_loss > 0:
                risk_reward_ratio = max_profit / max_loss
                # Score increases with better risk/reward, cap at 3:1 ratio
                ratio_score = min(50, (risk_reward_ratio / 3.0) * 50)
                score += ratio_score
            else:
                score += 25  # Moderate score if risk data unavailable
            
            # Expected Value Analysis (0-30 points)
            expected_value = getattr(opportunity, 'expected_value', 0)
            if expected_value > 0:
                # Normalize expected value (assuming $0-500 range)
                ev_score = min(30, (expected_value / 500) * 30)
                score += ev_score
            
            # Downside Protection (0-20 points)
            if opportunity.strategy_type in ['PROTECTIVE_PUT', 'COLLAR', 'IRON_CONDOR']:
                score += 15  # Defensive strategies get bonus points
            elif opportunity.strategy_type in ['COVERED_CALL', 'CREDIT_SPREAD']:
                score += 10  # Income strategies get moderate bonus
            elif opportunity.strategy_type in ['NAKED_CALL', 'NAKED_PUT']:
                score -= 5   # Naked options penalized for unlimited risk
            
            return max(0, min(100, score))
            
        except Exception as e:
            self.logger.warning(f"Risk-adjusted return scoring error: {e}")
            return 40.0  # Conservative fallback
    
    def _score_probability_metrics(self, opportunity: StrategyOpportunity) -> float:
        """Score based on probability of profit and statistical edge (15% weight)."""
        try:
            score = 0.0
            
            # Probability of Profit (0-60 points)
            prob_profit = getattr(opportunity, 'probability_profit', 0)
            if prob_profit > 0:
                # Linear scoring: 50% = 30 points, 75% = 45 points, 90% = 54 points
                prob_score = min(60, prob_profit * 60)
                score += prob_score
            
            # Delta Exposure Analysis (0-25 points)
            delta = getattr(opportunity, 'delta', 0)
            if delta is not None:
                # Prefer neutral to slightly negative delta for most strategies
                optimal_delta = -0.1  # Slightly bearish bias
                delta_deviation = abs(delta - optimal_delta)
                # Score decreases as we move away from optimal
                delta_score = max(0, 25 - (delta_deviation * 100))
                score += delta_score
            
            # Historical Win Rate (0-15 points)
            # TODO: Implement when historical performance tracking is available
            score += 10  # Assume moderate historical performance
            
            return min(100, score)
            
        except Exception as e:
            self.logger.warning(f"Probability metrics scoring error: {e}")
            return 45.0  # Conservative fallback
    
    def _score_volatility_edge(self, opportunity: StrategyOpportunity, tech_data: Dict) -> float:
        """Score based on volatility advantage and timing (10% weight)."""
        try:
            score = 0.0
            
            # Implied vs Realized Volatility (0-50 points)
            implied_vol = getattr(opportunity, 'implied_volatility', 0)
            realized_vol = tech_data.get('realized_volatility_20d', implied_vol)
            
            if implied_vol > 0 and realized_vol > 0:
                vol_ratio = implied_vol / realized_vol
                if opportunity.strategy_type in ['IRON_CONDOR', 'STRANGLE', 'STRADDLE']:
                    # Vol selling strategies benefit from high implied vol
                    vol_score = min(50, max(0, (vol_ratio - 1.0) * 50))
                else:
                    # Vol buying strategies benefit from low implied vol
                    vol_score = min(50, max(0, (2.0 - vol_ratio) * 25))
                score += vol_score
            else:
                score += 25  # Neutral if vol data unavailable
            
            # Volatility Rank (0-30 points)
            vol_rank = tech_data.get('volatility_rank', 50)
            if vol_rank is not None:
                if opportunity.strategy_type in ['IRON_CONDOR', 'CREDIT_SPREAD', 'COVERED_CALL']:
                    # High vol rank benefits premium selling
                    rank_score = min(30, (vol_rank / 100) * 30)
                else:
                    # Low vol rank benefits premium buying
                    rank_score = min(30, ((100 - vol_rank) / 100) * 30)
                score += rank_score
            
            # VIX Environment (0-20 points) 
            # TODO: Incorporate VIX analysis when available
            score += 15  # Assume moderate VIX environment
            
            return min(100, score)
            
        except Exception as e:
            self.logger.warning(f"Volatility edge scoring error: {e}")
            return 35.0  # Conservative fallback
    
    def _score_time_decay(self, opportunity: StrategyOpportunity) -> float:
        """Score based on time decay advantage (5% weight)."""
        try:
            score = 0.0
            
            # Days to Expiration Optimization (0-60 points)
            dte = getattr(opportunity, 'days_to_expiration', 30)
            if dte:
                if opportunity.strategy_type in ['IRON_CONDOR', 'CREDIT_SPREAD', 'COVERED_CALL']:
                    # Premium selling benefits from 15-45 DTE range
                    optimal_range = range(15, 46)
                    if dte in optimal_range:
                        score += 60
                    else:
                        # Linear decay from optimal
                        distance = min(abs(dte - 15), abs(dte - 45))
                        score += max(20, 60 - (distance * 2))
                else:
                    # Premium buying prefers longer timeframes
                    if dte >= 30:
                        score += min(60, 30 + dte)
                    else:
                        score += dte  # Linear scoring for shorter timeframes
            
            # Theta Value Analysis (0-40 points) 
            theta = getattr(opportunity, 'theta', 0)
            if theta:
                if opportunity.strategy_type in ['IRON_CONDOR', 'CREDIT_SPREAD']:
                    # Positive theta is good for premium sellers
                    theta_score = min(40, max(0, theta * 40))
                else:
                    # Negative theta acceptable for long strategies with longer timeframes
                    theta_score = min(40, max(0, 40 + theta * 20))
                score += theta_score
            
            return min(100, score)
            
        except Exception as e:
            self.logger.warning(f"Time decay scoring error: {e}")
            return 40.0  # Conservative fallback
    
    def _score_market_regime(self, opportunity: StrategyOpportunity, tech_data: Dict) -> float:
        """Score based on current market regime alignment (5% weight)."""
        try:
            score = 0.0
            
            # Trend Alignment (0-50 points)
            trend_strength = tech_data.get('trend_strength', 0)
            if trend_strength is not None:
                if opportunity.strategy_type in ['CALL', 'COVERED_CALL'] and trend_strength > 0.3:
                    score += 45  # Bullish strategy in bull market
                elif opportunity.strategy_type in ['PUT', 'PROTECTIVE_PUT'] and trend_strength < -0.3:
                    score += 45  # Bearish strategy in bear market  
                elif opportunity.strategy_type in ['IRON_CONDOR', 'STRANGLE'] and abs(trend_strength) < 0.2:
                    score += 50  # Neutral strategy in sideways market
                else:
                    score += 25  # Moderate alignment
            
            # Market Bias Confirmation (0-30 points)
            market_bias = getattr(opportunity, 'market_bias', 'NEUTRAL')
            if market_bias == 'BULLISH' and trend_strength > 0:
                score += 25
            elif market_bias == 'BEARISH' and trend_strength < 0:
                score += 25  
            elif market_bias == 'NEUTRAL' and abs(trend_strength) < 0.3:
                score += 30
            else:
                score += 15  # Partial alignment
            
            # Support/Resistance Levels (0-20 points)
            support = tech_data.get('support_level', 0)
            resistance = tech_data.get('resistance_level', 0)
            current_price = getattr(opportunity, 'underlying_price', 0)
            
            if support and resistance and current_price:
                # Score based on position within range
                range_position = (current_price - support) / (resistance - support)
                if 0.3 <= range_position <= 0.7:
                    score += 20  # Good position within range
                else:
                    score += 10  # Near boundaries
            
            return min(100, score)
            
        except Exception as e:
            self.logger.warning(f"Market regime scoring error: {e}")
            return 35.0  # Conservative fallback
    
    def _calculate_confidence_percentage(
        self, 
        opportunity: StrategyOpportunity, 
        breakdown: ScoreBreakdown,
        tech_data: Dict
    ) -> float:
        """Calculate statistical confidence in the scoring."""
        try:
            confidence_factors = []
            
            # Data Quality Factor (0-30%)
            data_quality = tech_data.get('data_quality', 'MEDIUM')
            if data_quality == 'HIGH':
                confidence_factors.append(25)
            elif data_quality == 'MEDIUM':
                confidence_factors.append(15)
            else:
                confidence_factors.append(5)
            
            # Score Consistency (0-25%)
            scores = [breakdown.technical, breakdown.liquidity, breakdown.risk_adjusted, 
                     breakdown.probability, breakdown.volatility, breakdown.time_decay, breakdown.market_regime]
            non_zero_scores = [s for s in scores if s > 0]
            if len(non_zero_scores) >= 4:
                score_std = statistics.stdev(non_zero_scores) if len(non_zero_scores) > 1 else 0
                consistency = max(0, 25 - (score_std / 10))  # Lower std dev = higher consistency
                confidence_factors.append(consistency)
            else:
                confidence_factors.append(10)  # Low confidence with few factors
            
            # Strategy Type Certainty (0-20%)
            strategy_certainty_map = {
                'IRON_CONDOR': 20, 'COVERED_CALL': 18, 'PROTECTIVE_PUT': 18,
                'CREDIT_SPREAD': 16, 'VERTICAL_SPREAD': 16, 'CALENDAR_SPREAD': 14,
                'STRADDLE': 12, 'STRANGLE': 12, 'COLLAR': 15,
                'NAKED_CALL': 8, 'NAKED_PUT': 8, 'BUTTERFLY': 10
            }
            strategy_confidence = strategy_certainty_map.get(opportunity.strategy_type, 10)
            confidence_factors.append(strategy_confidence)
            
            # Market Conditions Factor (0-15%)
            if hasattr(opportunity, 'liquidity_score') and opportunity.liquidity_score > 7:
                confidence_factors.append(15)  # High liquidity increases confidence
            else:
                confidence_factors.append(8)
            
            # Historical Performance Factor (0-10%)
            # TODO: Implement when historical tracking is available
            confidence_factors.append(8)  # Assume moderate historical validation
            
            total_confidence = sum(confidence_factors)
            return min(95, max(15, total_confidence))  # Cap between 15% and 95%
            
        except Exception as e:
            self.logger.warning(f"Confidence calculation error: {e}")
            return 60.0  # Conservative fallback
    
    def _determine_quality_tier(self, overall_score: float, confidence: float) -> str:
        """Determine quality tier based on score and confidence."""
        # Weighted scoring considering both score and confidence
        weighted_score = (overall_score * 0.7) + (confidence * 0.3)
        
        if weighted_score >= 75:
            return "HIGH"
        elif weighted_score >= 50:
            return "MEDIUM" 
        else:
            return "LOW"
    
    def _generate_profit_explanation(
        self, 
        opportunity: StrategyOpportunity, 
        breakdown: ScoreBreakdown,
        tech_data: Dict
    ) -> str:
        """Generate single-line profit explanation."""
        try:
            # Identify the strongest scoring factors
            factor_scores = {
                'technical': breakdown.technical,
                'liquidity': breakdown.liquidity, 
                'risk_adjusted': breakdown.risk_adjusted,
                'probability': breakdown.probability,
                'volatility': breakdown.volatility
            }
            
            # Find top 2 factors
            sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
            top_factors = [f[0] for f in sorted_factors[:2] if f[1] > 40]
            
            # Build explanation based on top factors
            prob_profit = getattr(opportunity, 'probability_profit', 0)
            prob_text = f"{prob_profit:.0%}" if prob_profit > 0 else "High"
            
            strategy_name = opportunity.strategy_type.replace('_', ' ').title()
            
            # Technical factor explanations
            explanations = []
            if 'technical' in top_factors:
                rsi = tech_data.get('rsi', 50)
                if rsi < 35:
                    explanations.append("RSI oversold signal")
                elif rsi > 65:
                    explanations.append("RSI overbought signal")
                else:
                    explanations.append("strong technical setup")
            
            if 'liquidity' in top_factors and hasattr(opportunity, 'liquidity_score'):
                if opportunity.liquidity_score > 8:
                    explanations.append("excellent liquidity")
                else:
                    explanations.append("good execution quality")
            
            if 'risk_adjusted' in top_factors:
                max_profit = getattr(opportunity, 'max_profit', 0)
                max_loss = abs(getattr(opportunity, 'max_loss', 0))
                if max_loss > 0:
                    ratio = max_profit / max_loss
                    if ratio > 2:
                        explanations.append("favorable risk-reward")
                    else:
                        explanations.append("balanced risk profile")
            
            if 'volatility' in top_factors:
                explanations.append("volatility advantage")
                
            if 'probability' in top_factors:
                explanations.append("high-probability setup")
            
            # Construct final explanation
            explanation_text = " with ".join(explanations[:2]) if explanations else "solid fundamentals"
            
            return f"{prob_text} win rate {strategy_name.lower()} with {explanation_text}"
            
        except Exception as e:
            self.logger.warning(f"Profit explanation generation error: {e}")
            return f"Profitable {opportunity.strategy_type.replace('_', ' ').lower()} opportunity"
    
    def _get_technical_indicators(self, symbol: str) -> Dict:
        """Get or calculate technical indicators for symbol."""
        try:
            # Check database for recent indicators (within 1 hour)
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            
            indicator = self.db.query(TechnicalIndicator).filter(
                and_(
                    TechnicalIndicator.symbol == symbol,
                    TechnicalIndicator.calculated_at >= recent_cutoff
                )
            ).order_by(desc(TechnicalIndicator.calculated_at)).first()
            
            if indicator:
                return {
                    'rsi': indicator.rsi,
                    'macd': indicator.macd,
                    'macd_signal': indicator.macd_signal,
                    'trend_strength': indicator.trend_strength,
                    'bollinger_position': indicator.bollinger_position,
                    'realized_volatility_20d': indicator.realized_volatility_20d,
                    'volatility_rank': indicator.volatility_rank,
                    'support_level': indicator.support_level,
                    'resistance_level': indicator.resistance_level,
                    'data_quality': indicator.data_quality or 'MEDIUM'
                }
            else:
                # Return default values if no technical data available
                return {
                    'rsi': 50, 'macd': 0, 'macd_signal': 0, 'trend_strength': 0,
                    'bollinger_position': 0.5, 'realized_volatility_20d': 0.2,
                    'volatility_rank': 50, 'support_level': 0, 'resistance_level': 0,
                    'data_quality': 'LOW'
                }
                
        except Exception as e:
            self.logger.error(f"Error fetching technical indicators for {symbol}: {e}")
            return {
                'rsi': 50, 'macd': 0, 'macd_signal': 0, 'trend_strength': 0,
                'bollinger_position': 0.5, 'realized_volatility_20d': 0.2,
                'volatility_rank': 50, 'support_level': 0, 'resistance_level': 0,
                'data_quality': 'ERROR'
            }
    
    def _store_score_result(
        self, 
        opportunity: StrategyOpportunity, 
        breakdown: ScoreBreakdown,
        overall_score: float, 
        confidence: float, 
        quality_tier: str
    ) -> None:
        """Store scoring result in database for performance tracking."""
        try:
            score_record = OpportunityScore(
                opportunity_id=opportunity.id,
                technical_score=breakdown.technical,
                liquidity_score=breakdown.liquidity,
                risk_adjusted_score=breakdown.risk_adjusted,
                probability_score=breakdown.probability,
                volatility_score=breakdown.volatility,
                time_decay_score=breakdown.time_decay,
                market_regime_score=breakdown.market_regime,
                overall_score=overall_score,
                confidence_percentage=confidence,
                quality_tier=quality_tier,
                calculated_at=datetime.utcnow(),
                score_version="v1.0"
            )
            
            self.db.add(score_record)
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Error storing score result: {e}")
            self.db.rollback()
    
    def _fallback_scoring(self, opportunity: StrategyOpportunity) -> ScoringResult:
        """Provide fallback scoring when main scoring fails."""
        breakdown = ScoreBreakdown()
        
        # Basic scoring based on available opportunity data
        if hasattr(opportunity, 'probability_profit') and opportunity.probability_profit:
            breakdown.probability = opportunity.probability_profit * 60
        else:
            breakdown.probability = 35
            
        if hasattr(opportunity, 'liquidity_score') and opportunity.liquidity_score:
            breakdown.liquidity = (opportunity.liquidity_score / 10) * 80
        else:
            breakdown.liquidity = 40
            
        # Conservative scoring for other factors
        breakdown.technical = 30
        breakdown.risk_adjusted = 35
        breakdown.volatility = 25
        breakdown.time_decay = 30
        breakdown.market_regime = 25
        
        overall_score = breakdown.overall_score
        confidence = 45.0  # Low confidence due to limited data
        quality_tier = "MEDIUM" if overall_score > 40 else "LOW"
        
        return ScoringResult(
            overall_score=overall_score,
            confidence_percentage=confidence,
            quality_tier=quality_tier,
            score_breakdown=breakdown,
            profit_explanation=f"Moderate {opportunity.strategy_type.replace('_', ' ').lower()} opportunity",
            reasoning="Limited data available for comprehensive analysis"
        )
    
    def get_cached_score(self, opportunity_id: str) -> Optional[ScoringResult]:
        """Get cached scoring result if available and fresh."""
        try:
            # Look for recent score (within 1 hour)
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            
            score_record = self.db.query(OpportunityScore).filter(
                and_(
                    OpportunityScore.opportunity_id == opportunity_id,
                    OpportunityScore.calculated_at >= recent_cutoff
                )
            ).order_by(desc(OpportunityScore.calculated_at)).first()
            
            if score_record:
                breakdown = ScoreBreakdown(
                    technical=score_record.technical_score or 0,
                    liquidity=score_record.liquidity_score or 0,
                    risk_adjusted=score_record.risk_adjusted_score or 0,
                    probability=score_record.probability_score or 0,
                    volatility=score_record.volatility_score or 0,
                    time_decay=score_record.time_decay_score or 0,
                    market_regime=score_record.market_regime_score or 0
                )
                
                return ScoringResult(
                    overall_score=score_record.overall_score or 0,
                    confidence_percentage=score_record.confidence_percentage or 0,
                    quality_tier=score_record.quality_tier or "LOW",
                    score_breakdown=breakdown,
                    reasoning="Cached result"
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving cached score: {e}")
            return None

    async def score_opportunities_batch(self, opportunities: List[Dict[str, Any]], max_concurrent: int = 5) -> List[ScoringResult]:
        """
        Score multiple opportunities using thread pool for better performance.
        
        Args:
            opportunities: List of opportunity dictionaries from API
            max_concurrent: Maximum concurrent scoring operations (ignored for now)
            
        Returns:
            List of ScoringResult objects corresponding to input opportunities
        """
        try:
            # Convert dictionaries to StrategyOpportunity objects
            from plugins.trading.base_strategy import StrategyOpportunity
            strategy_opportunities = []
            
            for opp_dict in opportunities:
                try:
                    # Create StrategyOpportunity from dict manually
                    strategy_opp = StrategyOpportunity(
                        id=opp_dict.get('id', ''),
                        symbol=opp_dict.get('symbol', ''),
                        strategy_type=opp_dict.get('strategy_type', ''),
                        strategy_id=opp_dict.get('strategy', ''),
                        universe=opp_dict.get('universe', 'default'),
                        strike=opp_dict.get('strike'),
                        short_strike=opp_dict.get('short_strike'),
                        long_strike=opp_dict.get('long_strike'),
                        expiration=opp_dict.get('expiration'),
                        days_to_expiration=opp_dict.get('days_to_expiration', 0),
                        premium=opp_dict.get('premium', 0.0),
                        max_loss=opp_dict.get('max_loss', 0.0),
                        max_profit=opp_dict.get('max_profit', 0.0),
                        probability_profit=opp_dict.get('probability_profit', 0.0),
                        expected_value=opp_dict.get('expected_value', 0.0),
                        delta=opp_dict.get('delta', 0.0),
                        gamma=opp_dict.get('gamma'),
                        theta=opp_dict.get('theta'),
                        vega=opp_dict.get('vega'),
                        implied_volatility=opp_dict.get('implied_volatility'),
                        volume=opp_dict.get('volume'),
                        open_interest=opp_dict.get('open_interest'),
                        liquidity_score=opp_dict.get('liquidity_score', 0.0),
                        underlying_price=opp_dict.get('underlying_price', 0.0),
                        bias=opp_dict.get('bias', 'NEUTRAL'),
                        rsi=opp_dict.get('rsi'),
                        trade_setup=opp_dict.get('trade_setup', ''),
                        risk_level=opp_dict.get('risk_level', 'MEDIUM')
                    )
                    strategy_opportunities.append(strategy_opp)
                except Exception as e:
                    self.logger.warning(f"Failed to convert opportunity dict to StrategyOpportunity: {e}")
                    continue
            
            # Score all opportunities in executor to avoid blocking
            import asyncio
            import concurrent.futures
            
            def score_single(opportunity):
                try:
                    return self.score_opportunity(opportunity)
                except Exception as e:
                    self.logger.error(f"Failed to score opportunity {opportunity.id}: {e}")
                    # Return a default low-quality score for failed opportunities
                    return ScoringResult(
                        overall_score=15.0,
                        confidence_percentage=10.0,
                        quality_tier=QualityTier.LOW,
                        score_breakdown=ScoreBreakdown(),
                        profit_explanation="Analysis partially available - limited scoring",
                        reasoning=f"Scoring error: {str(e)[:100]}"
                    )
            
            # Use thread pool executor for CPU-bound scoring work
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(executor, score_single, opportunity)
                    for opportunity in strategy_opportunities
                ]
                results = await asyncio.gather(*tasks)
            
            self.logger.info(f"Batch scored {len(results)} opportunities")
            return results
            
        except Exception as e:
            self.logger.error(f"Batch scoring failed: {e}")
            # Return default results for all opportunities to prevent API failure
            return [
                ScoringResult(
                    overall_score=15.0,
                    confidence_percentage=10.0,
                    quality_tier=QualityTier.LOW,
                    score_breakdown=ScoreBreakdown(),
                    profit_explanation="Scoring service temporarily unavailable - basic analysis only",
                    reasoning="Batch scoring service error"
                ) for _ in opportunities
            ]


def get_scoring_service() -> OpportunityScoringService:
    """Get scoring service instance with database connection."""
    db = next(get_db())
    return OpportunityScoringService(db)