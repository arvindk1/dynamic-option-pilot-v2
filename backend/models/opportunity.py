"""Opportunity snapshot and scan session models."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Boolean, Text, Index
from sqlalchemy.orm import relationship
from .database import Base


class ScanSession(Base):
    """Track scanning sessions and their results."""
    __tablename__ = "scan_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy = Column(String, index=True, nullable=False)
    symbols_scanned = Column(JSON)  # List of symbols that were scanned
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    opportunities_found = Column(Integer, default=0)
    status = Column(String, default="RUNNING", index=True)  # RUNNING, COMPLETED, FAILED, CANCELLED
    error_message = Column(Text)
    scan_parameters = Column(JSON)  # Store scan configuration used
    
    # Relationship to opportunities
    opportunities = relationship("OpportunitySnapshot", back_populates="scan_session", cascade="all, delete-orphan")
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get scan duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if scan session is still active."""
        return self.status == "RUNNING"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "strategy": self.strategy,
            "symbols_scanned": self.symbols_scanned,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "opportunities_found": self.opportunities_found,
            "status": self.status,
            "error_message": self.error_message,
            "scan_parameters": self.scan_parameters,
            "duration_seconds": self.duration_seconds
        }


class OpportunitySnapshot(Base):
    """Store opportunity snapshots with expiration and caching support."""
    __tablename__ = "opportunity_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(String, unique=True, index=True, nullable=False)  # Unique identifier for the opportunity
    symbol = Column(String, index=True, nullable=False)
    strategy_type = Column(String, index=True, nullable=False)  # iron_condor, put_spread, etc.
    
    # Core opportunity data
    data = Column(JSON, nullable=False)  # Store full opportunity data as JSON
    
    # Metadata for caching and lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, index=True, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Scan session reference
    scan_session_id = Column(String, ForeignKey("scan_sessions.id"), index=True)
    scan_session = relationship("ScanSession", back_populates="opportunities")
    
    # Cache optimization fields
    is_active = Column(Boolean, default=True, index=True)
    cache_hits = Column(Integer, default=0)
    
    # Key metrics for fast filtering (denormalized for performance)
    premium = Column(Float, index=True)
    max_loss = Column(Float, index=True)
    probability_profit = Column(Float, index=True)
    expected_value = Column(Float, index=True)
    days_to_expiration = Column(Integer, index=True)
    underlying_price = Column(Float, index=True)
    liquidity_score = Column(Float, index=True)
    
    def __init__(self, **kwargs):
        """Initialize with default expiration if not provided."""
        if 'expires_at' not in kwargs:
            # Default expiration: 5 minutes for high-frequency strategies, 15 minutes for others
            strategy = kwargs.get('strategy_type', '')
            if strategy in ['quick_scalp', 'volatility_play']:
                expiration_delta = timedelta(minutes=5)
            elif strategy in ['high_probability']:
                expiration_delta = timedelta(minutes=3)
            else:
                expiration_delta = timedelta(minutes=15)
            
            kwargs['expires_at'] = datetime.utcnow() + expiration_delta
        
        super().__init__(**kwargs)
    
    @property
    def is_expired(self) -> bool:
        """Check if opportunity has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def time_to_expiry_seconds(self) -> float:
        """Get seconds until expiration."""
        return max(0, (self.expires_at - datetime.utcnow()).total_seconds())
    
    @property
    def age_seconds(self) -> float:
        """Get age of opportunity in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    def extend_expiration(self, minutes: int = 5):
        """Extend expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.last_updated = datetime.utcnow()
    
    def increment_cache_hit(self):
        """Increment cache hit counter."""
        self.cache_hits += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including metadata."""
        result = {
            "id": self.opportunity_id,
            "symbol": self.symbol,
            "strategy_type": self.strategy_type,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "is_expired": self.is_expired,
            "time_to_expiry_seconds": self.time_to_expiry_seconds,
            "age_seconds": self.age_seconds,
            "cache_hits": self.cache_hits,
            "scan_session_id": self.scan_session_id
        }
        
        # Merge with the stored data
        if self.data:
            result.update(self.data)
        
        return result
    
    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API response format (without internal metadata)."""
        result = self.data.copy() if self.data else {}
        result.update({
            "id": self.opportunity_id,
            "symbol": self.symbol,
            "strategy_type": self.strategy_type,
        })
        return result
    
    @classmethod
    def from_opportunity_data(
        cls, 
        opportunity_data: Dict[str, Any], 
        strategy_type: str, 
        scan_session_id: Optional[str] = None
    ) -> 'OpportunitySnapshot':
        """Create OpportunitySnapshot from opportunity data dict."""
        # Generate unique ID if not provided
        opportunity_id = opportunity_data.get('id') or f"{opportunity_data.get('symbol', 'UNK')}_{strategy_type}_{int(datetime.utcnow().timestamp())}"
        
        # Extract key metrics for denormalized fields
        premium = opportunity_data.get('premium', 0.0)
        max_loss = opportunity_data.get('max_loss', 0.0)
        probability_profit = opportunity_data.get('probability_profit', 0.0)
        expected_value = opportunity_data.get('expected_value', 0.0)
        days_to_expiration = opportunity_data.get('days_to_expiration', 0)
        underlying_price = opportunity_data.get('underlying_price', 0.0)
        liquidity_score = opportunity_data.get('liquidity_score', 0.0)
        
        return cls(
            opportunity_id=opportunity_id,
            symbol=opportunity_data.get('symbol', ''),
            strategy_type=strategy_type,
            data=opportunity_data,
            scan_session_id=scan_session_id,
            premium=premium,
            max_loss=max_loss,
            probability_profit=probability_profit,
            expected_value=expected_value,
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            liquidity_score=liquidity_score
        )


class OpportunityScore(Base):
    """Advanced scoring metrics for opportunities with LLM integration."""
    __tablename__ = "opportunity_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(String, ForeignKey("opportunity_snapshots.opportunity_id"), index=True, nullable=False)
    
    # Multi-dimensional scores (0-100 scale)
    technical_score = Column(Float, default=0.0)  # RSI, MACD, trend strength
    liquidity_score = Column(Float, default=0.0)  # Volume, spreads, depth
    risk_adjusted_score = Column(Float, default=0.0)  # Risk-reward ratio
    probability_score = Column(Float, default=0.0)  # Win rate based
    volatility_score = Column(Float, default=0.0)  # Implied vol vs realized
    time_decay_score = Column(Float, default=0.0)  # Theta efficiency
    market_regime_score = Column(Float, default=0.0)  # Current market conditions fit
    
    # Composite scores
    overall_score = Column(Float, index=True, default=0.0)  # Weighted composite (0-100)
    confidence_percentage = Column(Float, default=0.0)  # How confident we are (0-100)
    quality_tier = Column(String, index=True, default="MEDIUM")  # HIGH, MEDIUM, LOW
    
    # Scoring metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    score_version = Column(String, default="1.0")  # For A/B testing different algorithms
    
    # Performance tracking
    actual_outcome = Column(Float)  # Actual P&L if trade was taken
    outcome_recorded_at = Column(DateTime)
    
    __table_args__ = (
        Index('ix_scores_composite', 'overall_score', 'confidence_percentage', 'quality_tier'),
        Index('ix_scores_performance', 'calculated_at', 'overall_score'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "technical_score": self.technical_score,
            "liquidity_score": self.liquidity_score,
            "risk_adjusted_score": self.risk_adjusted_score,
            "probability_score": self.probability_score,
            "volatility_score": self.volatility_score,
            "time_decay_score": self.time_decay_score,
            "market_regime_score": self.market_regime_score,
            "overall_score": self.overall_score,
            "confidence_percentage": self.confidence_percentage,
            "quality_tier": self.quality_tier,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
            "score_version": self.score_version
        }


class LLMAnalysis(Base):
    """LLM-generated analyses for opportunities with cost optimization."""
    __tablename__ = "llm_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    strategy_type = Column(String, index=True, nullable=False)
    
    # Analysis content
    profit_explanation = Column(Text, nullable=False)  # Single-line explanation
    technical_analysis = Column(Text)  # Detailed technical breakdown
    risk_assessment = Column(Text)  # Risk factors and mitigation
    market_context = Column(Text)  # How current market conditions affect this trade
    
    # LLM metadata
    model_used = Column(String, default="gpt-4-turbo")  # Track which model
    tokens_consumed = Column(Integer, default=0)  # Cost tracking
    processing_time_ms = Column(Integer, default=0)  # Performance tracking
    
    # Input hash for deduplication (avoid repeat LLM calls for same data)
    input_data_hash = Column(String, index=True, nullable=False)  # MD5 of input data
    
    # Validity and caching
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # Cache expiration
    is_valid = Column(Boolean, default=True, index=True)  # Can be invalidated if market changes
    confidence_rating = Column(Float, default=0.0)  # LLM's confidence in its analysis
    
    # Performance tracking
    user_rating = Column(Integer)  # 1-5 star rating from users
    actual_accuracy = Column(Float)  # How accurate the prediction was
    
    __table_args__ = (
        Index('ix_llm_cache_lookup', 'input_data_hash', 'expires_at', 'is_valid'),
        Index('ix_llm_performance', 'created_at', 'model_used', 'tokens_consumed'),
        Index('ix_llm_validity', 'symbol', 'strategy_type', 'is_valid', 'expires_at'),
    )
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "symbol": self.symbol,
            "strategy_type": self.strategy_type,
            "profit_explanation": self.profit_explanation,
            "technical_analysis": self.technical_analysis,
            "risk_assessment": self.risk_assessment,
            "market_context": self.market_context,
            "model_used": self.model_used,
            "confidence_rating": self.confidence_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_valid": self.is_valid and not self.is_expired
        }


class TechnicalIndicator(Base):
    """Store calculated technical indicators for symbols with caching."""
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    
    # Core indicators
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    bollinger_upper = Column(Float)
    bollinger_lower = Column(Float)
    bollinger_position = Column(Float)  # Where price sits in BB bands (0-1)
    
    # Trend indicators
    sma_20 = Column(Float)
    sma_50 = Column(Float) 
    sma_200 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    trend_strength = Column(Float)  # 0-100 based on moving average alignment
    
    # Volume indicators
    volume_sma_20 = Column(Float)
    volume_ratio = Column(Float)  # Current volume / 20-day average
    
    # Volatility indicators
    atr = Column(Float)  # Average True Range
    realized_volatility_20d = Column(Float)
    volatility_rank = Column(Float)  # 0-100 percentile rank
    
    # Support/resistance levels
    support_level = Column(Float)
    resistance_level = Column(Float)
    level_confidence = Column(Float)  # How strong these levels are
    
    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    market_price = Column(Float, nullable=False)  # Price when indicators were calculated
    data_quality = Column(String, default="GOOD")  # GOOD, STALE, INSUFFICIENT
    
    __table_args__ = (
        Index('ix_technical_fresh', 'symbol', 'calculated_at', 'data_quality'),
        Index('ix_technical_signals', 'rsi', 'trend_strength', 'volatility_rank'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "rsi": self.rsi,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "bollinger_position": self.bollinger_position,
            "sma_20": self.sma_20,
            "sma_50": self.sma_50,
            "sma_200": self.sma_200,
            "trend_strength": self.trend_strength,
            "volume_ratio": self.volume_ratio,
            "atr": self.atr,
            "realized_volatility_20d": self.realized_volatility_20d,
            "volatility_rank": self.volatility_rank,
            "support_level": self.support_level,
            "resistance_level": self.resistance_level,
            "level_confidence": self.level_confidence,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
            "market_price": self.market_price,
            "data_quality": self.data_quality
        }