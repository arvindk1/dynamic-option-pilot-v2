"""
Sandbox Database Models
Self-contained models for strategy testing and development
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import json

from models.database import Base

class SandboxStrategyConfig(Base):
    """
    Sandbox strategy configurations for testing
    Completely isolated from live strategy system
    """
    __tablename__ = "sandbox_strategy_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, default='default_user')
    strategy_id = Column(String(100), nullable=False)  # e.g., 'thetacrop_weekly'
    name = Column(String(200), nullable=False)  # User-friendly name
    config_data = Column(JSON, nullable=False)  # Strategy parameters
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=False)  # Is this deployed live?
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deployed_at = Column(DateTime, nullable=True)
    
    # Relationships
    test_runs = relationship("SandboxTestRun", back_populates="config")
    ai_conversations = relationship("SandboxAIConversation", back_populates="config")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_strategy', 'user_id', 'strategy_id'),
        Index('idx_active', 'is_active'),
    )
    
    def to_dict(self, test_run_count: int = 0) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'strategy_id': self.strategy_id,
            'name': self.name,
            'config_data': self.config_data,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'test_run_count': test_run_count
        }
    
    @classmethod
    def from_strategy_config(cls, strategy_id: str, name: str, config_data: Dict[str, Any], 
                           user_id: str = 'default_user') -> 'SandboxStrategyConfig':
        """Create from strategy configuration data"""
        return cls(
            strategy_id=strategy_id,
            name=name,
            config_data=config_data,
            user_id=user_id
        )


class SandboxTestRun(Base):
    """
    Records of strategy test executions in sandbox
    """
    __tablename__ = "sandbox_test_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String, ForeignKey('sandbox_strategy_configs.id'), nullable=False)
    test_parameters = Column(JSON, nullable=False)  # Test-specific params
    execution_time_ms = Column(Integer, nullable=True)
    opportunities_found = Column(Integer, default=0)
    test_results = Column(JSON, nullable=False)  # Detailed results
    cached_data_used = Column(JSON, nullable=True)  # What cached data was used
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    config = relationship("SandboxStrategyConfig", back_populates="test_runs")
    
    # Indexes
    __table_args__ = (
        Index('idx_config_id', 'config_id'),
        Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'config_id': self.config_id,
            'test_parameters': self.test_parameters,
            'execution_time_ms': self.execution_time_ms,
            'opportunities_found': self.opportunities_found,
            'test_results': self.test_results,
            'cached_data_used': self.cached_data_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_test_run(cls, config_id: str, test_params: Dict[str, Any], 
                       results: Dict[str, Any], execution_time: int = None) -> 'SandboxTestRun':
        """Create a new test run record"""
        opportunities_count = len(results.get('opportunities', []))
        
        return cls(
            config_id=config_id,
            test_parameters=test_params,
            execution_time_ms=execution_time,
            opportunities_found=opportunities_count,
            test_results=results
        )


class SandboxAIConversation(Base):
    """
    AI assistant conversations tied to specific strategy configurations
    """
    __tablename__ = "sandbox_ai_conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String, ForeignKey('sandbox_strategy_configs.id'), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    context_data = Column(JSON, nullable=True)  # Strategy context used
    model_used = Column(String(50), default='gpt-4o-mini')
    tokens_used = Column(Integer, default=0)
    estimated_cost = Column(String(20), default='$0.00')  # Store as string for precision
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    config = relationship("SandboxStrategyConfig", back_populates="ai_conversations")
    
    # Indexes
    __table_args__ = (
        Index('idx_config_id_ai', 'config_id'),
        Index('idx_created_at_ai', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'config_id': self.config_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'context_data': self.context_data,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'estimated_cost': self.estimated_cost,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_conversation(cls, config_id: str, user_msg: str, ai_response: str,
                          model: str = 'gpt-4o-mini', tokens: int = 0, 
                          cost: str = '$0.00', context: Dict = None) -> 'SandboxAIConversation':
        """Create a new AI conversation record"""
        return cls(
            config_id=config_id,
            user_message=user_msg,
            ai_response=ai_response,
            model_used=model,
            tokens_used=tokens,
            estimated_cost=cost,
            context_data=context
        )


class SandboxHistoricalCache(Base):
    """
    Cached historical data for sandbox testing
    Avoids hitting live APIs during strategy testing
    """
    __tablename__ = "sandbox_historical_cache"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key = Column(String(200), unique=True, nullable=False)
    symbol = Column(String(10), nullable=False)
    data_type = Column(String(50), nullable=False)  # 'market_data', 'options_chain', 'historical_prices'
    data = Column(JSON, nullable=False)
    cached_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_symbol_type', 'symbol', 'data_type'),
        Index('idx_expires_at', 'expires_at'),
        Index('idx_cache_key', 'cache_key'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'symbol': self.symbol,
            'data_type': self.data_type,
            'data': self.data,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': datetime.utcnow() > self.expires_at if self.expires_at else True
        }
    
    @classmethod
    def create_cache_entry(cls, symbol: str, data_type: str, data: Dict[str, Any], 
                          ttl_hours: int = 24) -> 'SandboxHistoricalCache':
        """Create a new cache entry"""
        cache_key = f"{symbol}_{data_type}_{datetime.utcnow().strftime('%Y%m%d')}"
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        return cls(
            cache_key=cache_key,
            symbol=symbol,
            data_type=data_type,
            data=data,
            expires_at=expires_at
        )
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.utcnow() > self.expires_at if self.expires_at else True
    
    def refresh_expiry(self, ttl_hours: int = 24):
        """Extend cache expiry"""
        self.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)


class SandboxStats(Base):
    """
    Aggregate statistics for sandbox usage
    """
    __tablename__ = "sandbox_stats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, default='default_user')
    date = Column(DateTime, default=func.now())
    strategies_created = Column(Integer, default=0)
    test_runs_executed = Column(Integer, default=0)
    ai_conversations = Column(Integer, default=0)
    total_ai_cost = Column(String(20), default='$0.00')
    opportunities_generated = Column(Integer, default=0)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'date'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'strategies_created': self.strategies_created,
            'test_runs_executed': self.test_runs_executed,
            'ai_conversations': self.ai_conversations,
            'total_ai_cost': self.total_ai_cost,
            'opportunities_generated': self.opportunities_generated
        }


# Helper functions for sandbox operations
def get_user_sandbox_stats(db, user_id: str = 'default_user') -> Dict[str, Any]:
    """Get aggregate sandbox statistics for a user"""
    configs = db.query(SandboxStrategyConfig).filter(
        SandboxStrategyConfig.user_id == user_id
    ).all()
    
    test_runs = db.query(SandboxTestRun).join(SandboxStrategyConfig).filter(
        SandboxStrategyConfig.user_id == user_id
    ).all()
    
    ai_conversations = db.query(SandboxAIConversation).join(SandboxStrategyConfig).filter(
        SandboxStrategyConfig.user_id == user_id
    ).all()
    
    return {
        'total_strategies': len(configs),
        'active_strategies': len([c for c in configs if c.is_active]),
        'total_test_runs': len(test_runs),
        'total_ai_conversations': len(ai_conversations),
        'total_opportunities_found': sum(tr.opportunities_found for tr in test_runs),
        'last_activity': max([c.updated_at for c in configs] + [tr.created_at for tr in test_runs]) if configs or test_runs else None
    }


def cleanup_expired_cache(db) -> int:
    """Clean up expired cache entries"""
    expired_entries = db.query(SandboxHistoricalCache).filter(
        SandboxHistoricalCache.expires_at < datetime.utcnow()
    ).all()
    
    count = len(expired_entries)
    for entry in expired_entries:
        db.delete(entry)
    
    db.commit()
    return count