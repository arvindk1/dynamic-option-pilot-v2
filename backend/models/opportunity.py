"""Opportunity snapshot and scan session models."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
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
    status = Column(
        String, default="RUNNING", index=True
    )  # RUNNING, COMPLETED, FAILED, CANCELLED
    error_message = Column(Text)
    scan_parameters = Column(JSON)  # Store scan configuration used

    # Relationship to opportunities
    opportunities = relationship(
        "OpportunitySnapshot",
        back_populates="scan_session",
        cascade="all, delete-orphan",
    )

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
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "opportunities_found": self.opportunities_found,
            "status": self.status,
            "error_message": self.error_message,
            "scan_parameters": self.scan_parameters,
            "duration_seconds": self.duration_seconds,
        }


class OpportunitySnapshot(Base):
    """Store opportunity snapshots with expiration and caching support."""

    __tablename__ = "opportunity_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(
        String, unique=True, index=True, nullable=False
    )  # Unique identifier for the opportunity
    symbol = Column(String, index=True, nullable=False)
    strategy_type = Column(
        String, index=True, nullable=False
    )  # iron_condor, put_spread, etc.

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
        if "expires_at" not in kwargs:
            # Default expiration: 5 minutes for high-frequency strategies, 15 minutes for others
            strategy = kwargs.get("strategy_type", "")
            if strategy in ["quick_scalp", "volatility_play"]:
                expiration_delta = timedelta(minutes=5)
            elif strategy in ["high_probability"]:
                expiration_delta = timedelta(minutes=3)
            else:
                expiration_delta = timedelta(minutes=15)

            kwargs["expires_at"] = datetime.utcnow() + expiration_delta

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
            "scan_session_id": self.scan_session_id,
        }

        # Merge with the stored data
        if self.data:
            result.update(self.data)

        return result

    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API response format (without internal metadata)."""
        result = self.data.copy() if self.data else {}
        result.update(
            {
                "id": self.opportunity_id,
                "symbol": self.symbol,
                "strategy_type": self.strategy_type,
            }
        )
        return result

    @classmethod
    def from_opportunity_data(
        cls,
        opportunity_data: Dict[str, Any],
        strategy_type: str,
        scan_session_id: Optional[str] = None,
    ) -> "OpportunitySnapshot":
        """Create OpportunitySnapshot from opportunity data dict."""
        # Generate unique ID if not provided
        opportunity_id = (
            opportunity_data.get("id")
            or f"{opportunity_data.get('symbol', 'UNK')}_{strategy_type}_{int(datetime.utcnow().timestamp())}"
        )

        # Extract key metrics for denormalized fields
        premium = opportunity_data.get("premium", 0.0)
        max_loss = opportunity_data.get("max_loss", 0.0)
        probability_profit = opportunity_data.get("probability_profit", 0.0)
        expected_value = opportunity_data.get("expected_value", 0.0)
        days_to_expiration = opportunity_data.get("days_to_expiration", 0)
        underlying_price = opportunity_data.get("underlying_price", 0.0)
        liquidity_score = opportunity_data.get("liquidity_score", 0.0)

        return cls(
            opportunity_id=opportunity_id,
            symbol=opportunity_data.get("symbol", ""),
            strategy_type=strategy_type,
            data=opportunity_data,
            scan_session_id=scan_session_id,
            premium=premium,
            max_loss=max_loss,
            probability_profit=probability_profit,
            expected_value=expected_value,
            days_to_expiration=days_to_expiration,
            underlying_price=underlying_price,
            liquidity_score=liquidity_score,
        )
