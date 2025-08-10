"""
LLM-powered opportunity validation service with intelligent cost control.

This service provides AI-powered analysis and explanations for trading opportunities
while maintaining strict cost controls through intelligent caching and rate limiting.
"""

import os
import logging
import hashlib
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import openai
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from models.database import get_db
from models.opportunity import LLMAnalysis
from plugins.trading.base_strategy import StrategyOpportunity
from services.opportunity_scoring import ScoringResult


logger = logging.getLogger(__name__)


@dataclass
class LLMValidationResult:
    """Result from LLM validation with cost tracking."""
    profit_explanation: str
    technical_analysis: str
    risk_assessment: str
    market_context: str
    confidence_rating: float  # 0.0 to 1.0
    model_used: str
    tokens_consumed: int
    processing_time_ms: int
    cached: bool = False
    

class LLMValidatorService:
    """
    Cost-controlled LLM validation service for trading opportunities.
    
    Features intelligent caching, rate limiting, and fallback mechanisms
    to provide AI-powered insights while maintaining strict cost controls.
    """
    
    # Cost control parameters
    MAX_TOKENS_PER_REQUEST = 500
    MAX_REQUESTS_PER_HOUR = 100
    CACHE_DURATION_HOURS = 24
    RATE_LIMIT_DELAY_SECONDS = 1.0
    
    # Model preferences (ordered by cost-effectiveness)
    MODEL_PREFERENCES = [
        "gpt-3.5-turbo",  # Most cost-effective
        "gpt-4",          # Higher quality but more expensive
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client if API key available
        self.openai_client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                openai.api_key = api_key
                self.openai_client = openai
                self.logger.info("✅ OpenAI client initialized successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ OpenAI initialization failed: {e}")
                self.openai_client = None
        else:
            self.logger.info("ℹ️ No OpenAI API key found - LLM validation will use fallback analysis")
    
    async def validate_opportunity(
        self,
        opportunity: StrategyOpportunity,
        scoring_result: ScoringResult,
        force_refresh: bool = False
    ) -> LLMValidationResult:
        """
        Validate opportunity with LLM analysis and intelligent caching.
        
        Args:
            opportunity: Trading opportunity to validate
            scoring_result: Current scoring analysis
            force_refresh: Force new LLM call (bypasses cache)
            
        Returns:
            LLM validation result with cost tracking
        """
        try:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_result = self._get_cached_analysis(opportunity, scoring_result)
                if cached_result:
                    self.logger.info(f"📦 Using cached LLM analysis for {opportunity.symbol}")
                    return cached_result
            
            # Rate limiting check
            if not self._check_rate_limits():
                self.logger.warning("⏰ Rate limit exceeded - using fallback analysis")
                return self._fallback_analysis(opportunity, scoring_result)
            
            # Generate new LLM analysis if client available
            if self.openai_client:
                result = await self._generate_llm_analysis(opportunity, scoring_result)
            else:
                result = self._fallback_analysis(opportunity, scoring_result)
            
            # Store in cache for future use
            self._cache_analysis_result(opportunity, scoring_result, result)
            
            # Apply rate limiting delay
            await asyncio.sleep(self.RATE_LIMIT_DELAY_SECONDS)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in LLM validation: {str(e)}")
            return self._fallback_analysis(opportunity, scoring_result)
    
    async def _generate_llm_analysis(
        self,
        opportunity: StrategyOpportunity,
        scoring_result: ScoringResult
    ) -> LLMValidationResult:
        """Generate new LLM analysis with cost controls."""
        start_time = time.time()
        
        try:
            # Prepare prompt with opportunity and scoring data
            prompt = self._build_analysis_prompt(opportunity, scoring_result)
            
            # Try models in order of cost-effectiveness
            for model in self.MODEL_PREFERENCES:
                try:
                    response = await self._call_openai_api(prompt, model)
                    if response:
                        processing_time = int((time.time() - start_time) * 1000)
                        return self._parse_llm_response(response, model, processing_time)
                except Exception as e:
                    self.logger.warning(f"Model {model} failed: {e}")
                    continue
            
            # If all models fail, use fallback
            self.logger.warning("All LLM models failed - using fallback analysis")
            return self._fallback_analysis(opportunity, scoring_result)
            
        except Exception as e:
            self.logger.error(f"LLM analysis generation error: {e}")
            return self._fallback_analysis(opportunity, scoring_result)
    
    async def _call_openai_api(self, prompt: str, model: str) -> Optional[Dict]:
        """Make API call to OpenAI with error handling."""
        try:
            response = await asyncio.to_thread(
                self.openai_client.ChatCompletion.create,
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional options trading analyst providing concise, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.MAX_TOKENS_PER_REQUEST,
                temperature=0.3,  # Lower temperature for more consistent analysis
                timeout=30
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}")
            return None
    
    def _build_analysis_prompt(
        self,
        opportunity: StrategyOpportunity,
        scoring_result: ScoringResult
    ) -> str:
        """Build structured prompt for LLM analysis."""
        
        # Extract key metrics
        prob_profit = getattr(opportunity, 'probability_profit', 0) * 100
        max_profit = getattr(opportunity, 'max_profit', 0)
        max_loss = abs(getattr(opportunity, 'max_loss', 0))
        dte = getattr(opportunity, 'days_to_expiration', 0)
        
        prompt = f"""
Analyze this options trading opportunity and provide a structured assessment:

OPPORTUNITY DETAILS:
- Symbol: {opportunity.symbol}
- Strategy: {opportunity.strategy_type.replace('_', ' ').title()}
- Probability of Profit: {prob_profit:.1f}%
- Max Profit: ${max_profit:.2f}
- Max Loss: ${max_loss:.2f}
- Days to Expiration: {dte}
- Current Score: {scoring_result.overall_score:.1f}/100
- Quality Tier: {scoring_result.quality_tier}
- Confidence: {scoring_result.confidence_percentage:.1f}%

SCORING BREAKDOWN:
- Technical: {scoring_result.score_breakdown.technical:.1f}/100
- Liquidity: {scoring_result.score_breakdown.liquidity:.1f}/100  
- Risk-Adjusted: {scoring_result.score_breakdown.risk_adjusted:.1f}/100
- Probability: {scoring_result.score_breakdown.probability:.1f}/100

Please provide your analysis in this exact JSON format:

{{
  "profit_explanation": "Single line explaining why this trade could be profitable",
  "technical_analysis": "Brief technical assessment focusing on key indicators",
  "risk_assessment": "Concise risk evaluation with specific concerns", 
  "market_context": "Current market conditions relevance to this trade",
  "confidence_rating": 0.85
}}

Keep responses concise and actionable. Focus on the most important factors for trading decisions.
"""
        
        return prompt.strip()
    
    def _parse_llm_response(
        self,
        response: Dict,
        model: str,
        processing_time: int
    ) -> LLMValidationResult:
        """Parse and validate LLM response."""
        try:
            # Extract response content
            content = response['choices'][0]['message']['content'].strip()
            tokens_used = response.get('usage', {}).get('total_tokens', 0)
            
            # Try to parse as JSON
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured fallback
                analysis = self._extract_fallback_analysis(content)
            
            # Validate and sanitize fields
            profit_explanation = str(analysis.get('profit_explanation', 'Profitable opportunity'))[:200]
            technical_analysis = str(analysis.get('technical_analysis', 'Technical analysis unavailable'))[:300]
            risk_assessment = str(analysis.get('risk_assessment', 'Risk assessment unavailable'))[:300]
            market_context = str(analysis.get('market_context', 'Market context unavailable'))[:300]
            
            # Validate confidence rating
            confidence = analysis.get('confidence_rating', 0.75)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                confidence = 0.75
            
            return LLMValidationResult(
                profit_explanation=profit_explanation,
                technical_analysis=technical_analysis,
                risk_assessment=risk_assessment,
                market_context=market_context,
                confidence_rating=confidence,
                model_used=model,
                tokens_consumed=tokens_used,
                processing_time_ms=processing_time,
                cached=False
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            # Return minimal valid response
            return LLMValidationResult(
                profit_explanation="LLM analysis processing error",
                technical_analysis="Analysis unavailable due to processing error",
                risk_assessment="Risk assessment unavailable",
                market_context="Market context unavailable",
                confidence_rating=0.5,
                model_used=model,
                tokens_consumed=0,
                processing_time_ms=processing_time,
                cached=False
            )
    
    def _extract_fallback_analysis(self, content: str) -> Dict:
        """Extract analysis from non-JSON LLM response."""
        # Simple text extraction for common patterns
        lines = content.split('\n')
        analysis = {}
        
        for line in lines:
            line = line.strip()
            if 'profit' in line.lower() and not analysis.get('profit_explanation'):
                analysis['profit_explanation'] = line
            elif 'technical' in line.lower() and not analysis.get('technical_analysis'):
                analysis['technical_analysis'] = line
            elif 'risk' in line.lower() and not analysis.get('risk_assessment'):
                analysis['risk_assessment'] = line
            elif 'market' in line.lower() and not analysis.get('market_context'):
                analysis['market_context'] = line
        
        return analysis
    
    def _fallback_analysis(
        self,
        opportunity: StrategyOpportunity,
        scoring_result: ScoringResult
    ) -> LLMValidationResult:
        """Generate rule-based analysis when LLM is unavailable."""
        
        # Use existing profit explanation if available
        profit_explanation = scoring_result.profit_explanation or f"Moderate {opportunity.strategy_type.replace('_', ' ').lower()} opportunity"
        
        # Generate basic technical analysis based on scores
        tech_score = scoring_result.score_breakdown.technical
        if tech_score > 70:
            technical_analysis = "Strong technical indicators support this trade setup"
        elif tech_score > 40:
            technical_analysis = "Moderate technical support with some positive indicators"
        else:
            technical_analysis = "Limited technical evidence - consider additional analysis"
        
        # Risk assessment based on strategy type and scores
        risk_score = scoring_result.score_breakdown.risk_adjusted
        if opportunity.strategy_type in ['IRON_CONDOR', 'CREDIT_SPREAD', 'COVERED_CALL']:
            if risk_score > 60:
                risk_assessment = "Well-defined risk with favorable risk-reward profile"
            else:
                risk_assessment = "Moderate risk - monitor position sizing and exit rules"
        else:
            risk_assessment = "Standard risk profile for this strategy type"
        
        # Market context based on overall quality
        if scoring_result.quality_tier == 'HIGH':
            market_context = "Current market conditions appear favorable for this strategy"
        elif scoring_result.quality_tier == 'MEDIUM':
            market_context = "Neutral market environment with selective opportunities"
        else:
            market_context = "Challenging market conditions - exercise additional caution"
        
        return LLMValidationResult(
            profit_explanation=profit_explanation,
            technical_analysis=technical_analysis,
            risk_assessment=risk_assessment,
            market_context=market_context,
            confidence_rating=scoring_result.confidence_percentage / 100,
            model_used="rule_based",
            tokens_consumed=0,
            processing_time_ms=10,
            cached=False
        )
    
    def _get_cached_analysis(
        self,
        opportunity: StrategyOpportunity,
        scoring_result: ScoringResult
    ) -> Optional[LLMValidationResult]:
        """Check for cached LLM analysis that's still valid."""
        try:
            # Generate input hash for cache lookup
            input_hash = self._generate_input_hash(opportunity, scoring_result)
            
            # Look for valid cached analysis
            cutoff_time = datetime.utcnow() - timedelta(hours=self.CACHE_DURATION_HOURS)
            
            cached_analysis = self.db.query(LLMAnalysis).filter(
                and_(
                    LLMAnalysis.input_data_hash == input_hash,
                    LLMAnalysis.expires_at > datetime.utcnow(),
                    LLMAnalysis.created_at >= cutoff_time,
                    LLMAnalysis.is_valid == True
                )
            ).order_by(desc(LLMAnalysis.created_at)).first()
            
            if cached_analysis:
                return LLMValidationResult(
                    profit_explanation=cached_analysis.profit_explanation,
                    technical_analysis=cached_analysis.technical_analysis or "Technical analysis not available",
                    risk_assessment=cached_analysis.risk_assessment or "Risk assessment not available",
                    market_context=cached_analysis.market_context or "Market context not available",
                    confidence_rating=cached_analysis.confidence_rating or 0.75,
                    model_used=cached_analysis.model_used or "cached",
                    tokens_consumed=0,  # No tokens used for cached result
                    processing_time_ms=5,  # Minimal processing time for cache hit
                    cached=True
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking cached analysis: {e}")
            return None
    
    def _cache_analysis_result(
        self,
        opportunity: StrategyOpportunity,
        scoring_result: ScoringResult,
        llm_result: LLMValidationResult
    ) -> None:
        """Store LLM analysis result in cache."""
        try:
            input_hash = self._generate_input_hash(opportunity, scoring_result)
            expires_at = datetime.utcnow() + timedelta(hours=self.CACHE_DURATION_HOURS)
            
            analysis_record = LLMAnalysis(
                opportunity_id=opportunity.id,
                symbol=opportunity.symbol,
                strategy_type=opportunity.strategy_type,
                profit_explanation=llm_result.profit_explanation,
                technical_analysis=llm_result.technical_analysis,
                risk_assessment=llm_result.risk_assessment,
                market_context=llm_result.market_context,
                model_used=llm_result.model_used,
                tokens_consumed=llm_result.tokens_consumed,
                processing_time_ms=llm_result.processing_time_ms,
                input_data_hash=input_hash,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                is_valid=True,
                confidence_rating=llm_result.confidence_rating
            )
            
            self.db.add(analysis_record)
            self.db.commit()
            
            self.logger.info(f"💾 Cached LLM analysis for {opportunity.symbol} (expires: {expires_at})")
            
        except Exception as e:
            self.logger.error(f"Error caching analysis result: {e}")
            self.db.rollback()
    
    def _generate_input_hash(
        self,
        opportunity: StrategyOpportunity,
        scoring_result: ScoringResult
    ) -> str:
        """Generate hash of input data to detect when re-analysis is needed."""
        # Include key opportunity and scoring data that would affect analysis
        hash_data = {
            'symbol': opportunity.symbol,
            'strategy_type': opportunity.strategy_type,
            'probability_profit': getattr(opportunity, 'probability_profit', 0),
            'max_profit': getattr(opportunity, 'max_profit', 0),
            'max_loss': getattr(opportunity, 'max_loss', 0),
            'days_to_expiration': getattr(opportunity, 'days_to_expiration', 0),
            'overall_score': round(scoring_result.overall_score, 1),
            'quality_tier': scoring_result.quality_tier,
            'technical_score': round(scoring_result.score_breakdown.technical, 1),
            'liquidity_score': round(scoring_result.score_breakdown.liquidity, 1),
            'risk_adjusted_score': round(scoring_result.score_breakdown.risk_adjusted, 1)
        }
        
        # Create hash from serialized data
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _check_rate_limits(self) -> bool:
        """Check if we're within rate limits for LLM calls."""
        try:
            # Count requests in the last hour
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            request_count = self.db.query(func.count(LLMAnalysis.id)).filter(
                and_(
                    LLMAnalysis.created_at >= cutoff_time,
                    LLMAnalysis.model_used != 'rule_based',  # Don't count fallback analyses
                    LLMAnalysis.tokens_consumed > 0  # Only count actual API calls
                )
            ).scalar()
            
            if request_count >= self.MAX_REQUESTS_PER_HOUR:
                self.logger.warning(f"⚠️ Rate limit exceeded: {request_count}/{self.MAX_REQUESTS_PER_HOUR} requests in last hour")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking rate limits: {e}")
            return False  # Conservative approach - deny if check fails
    
    def get_cost_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get LLM usage and cost statistics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Query usage statistics
            stats_query = self.db.query(
                func.count(LLMAnalysis.id).label('total_requests'),
                func.sum(LLMAnalysis.tokens_consumed).label('total_tokens'),
                func.avg(LLMAnalysis.processing_time_ms).label('avg_processing_time'),
                func.count(func.distinct(LLMAnalysis.symbol)).label('unique_symbols')
            ).filter(
                and_(
                    LLMAnalysis.created_at >= cutoff_date,
                    LLMAnalysis.model_used != 'rule_based'
                )
            ).first()
            
            # Model usage breakdown
            model_stats = self.db.query(
                LLMAnalysis.model_used,
                func.count(LLMAnalysis.id).label('requests'),
                func.sum(LLMAnalysis.tokens_consumed).label('tokens')
            ).filter(
                LLMAnalysis.created_at >= cutoff_date
            ).group_by(LLMAnalysis.model_used).all()
            
            # Calculate estimated costs (rough estimates based on OpenAI pricing)
            cost_per_token = {
                'gpt-3.5-turbo': 0.002 / 1000,  # $0.002 per 1K tokens
                'gpt-4': 0.03 / 1000,           # $0.03 per 1K tokens  
                'rule_based': 0                 # No cost for fallback
            }
            
            total_cost = 0
            model_breakdown = {}
            
            for model_stat in model_stats:
                model = model_stat.model_used
                tokens = model_stat.tokens or 0
                requests = model_stat.requests
                cost = tokens * cost_per_token.get(model, 0)
                total_cost += cost
                
                model_breakdown[model] = {
                    'requests': requests,
                    'tokens': tokens,
                    'estimated_cost': round(cost, 4)
                }
            
            return {
                'period_days': days,
                'total_requests': stats_query.total_requests or 0,
                'total_tokens': stats_query.total_tokens or 0,
                'unique_symbols_analyzed': stats_query.unique_symbols or 0,
                'avg_processing_time_ms': round(stats_query.avg_processing_time or 0, 1),
                'estimated_total_cost': round(total_cost, 4),
                'model_breakdown': model_breakdown,
                'cache_hit_rate': self._calculate_cache_hit_rate(days)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cost statistics: {e}")
            return {'error': 'Unable to calculate cost statistics'}
    
    def _calculate_cache_hit_rate(self, days: int) -> float:
        """Calculate cache hit rate for the given period."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Count total analyses requested (including cached)
            total_requests = self.db.query(func.count(LLMAnalysis.id)).filter(
                LLMAnalysis.created_at >= cutoff_date
            ).scalar() or 0
            
            # Count actual API calls (non-cached)
            api_calls = self.db.query(func.count(LLMAnalysis.id)).filter(
                and_(
                    LLMAnalysis.created_at >= cutoff_date,
                    LLMAnalysis.tokens_consumed > 0  # Only actual API calls consume tokens
                )
            ).scalar() or 0
            
            if total_requests > 0:
                cache_hits = total_requests - api_calls
                return round((cache_hits / total_requests) * 100, 1)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating cache hit rate: {e}")
            return 0.0
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries and return count of removed items."""
        try:
            # Delete expired entries
            deleted_count = self.db.query(LLMAnalysis).filter(
                LLMAnalysis.expires_at <= datetime.utcnow()
            ).count()
            
            self.db.query(LLMAnalysis).filter(
                LLMAnalysis.expires_at <= datetime.utcnow()
            ).delete()
            
            self.db.commit()
            
            if deleted_count > 0:
                self.logger.info(f"🧹 Cleaned up {deleted_count} expired LLM cache entries")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired cache: {e}")
            self.db.rollback()
            return 0


def get_llm_validator() -> LLMValidatorService:
    """Get LLM validator service instance with database connection."""
    db = next(get_db())
    return LLMValidatorService(db)