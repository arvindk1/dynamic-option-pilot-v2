"""
Error Logging Models for Critical System Issues
"""

from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import json

from models.database import Base


class CriticalErrorLog(Base):
    """Log critical system errors to database for monitoring"""
    __tablename__ = "critical_error_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    error_type = Column(String, nullable=False, index=True)  # universe_loading_failed, ai_service_error, etc.
    message = Column(Text, nullable=False)  # Human-readable error message
    details = Column(JSON, nullable=True)  # Additional error details as JSON
    service = Column(String, nullable=True)  # Service/module where error occurred
    user_id = Column(String, nullable=True)  # User affected (if applicable)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)  # When error was resolved
    resolution_notes = Column(Text, nullable=True)  # How it was resolved
    severity = Column(String, default="HIGH", nullable=False)  # HIGH, MEDIUM, LOW
    
    @classmethod
    def create_error_log(cls, error_type: str, message: str, details: dict = None, 
                        service: str = None, user_id: str = None, severity: str = "HIGH"):
        """Create a new critical error log entry"""
        return cls(
            error_type=error_type,
            message=message,
            details=details or {},
            service=service,
            user_id=user_id,
            severity=severity
        )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'error_type': self.error_type,
            'message': self.message,
            'details': self.details,
            'service': self.service,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'severity': self.severity,
            'is_resolved': self.resolved_at is not None
        }
    
    def mark_resolved(self, resolution_notes: str = None):
        """Mark error as resolved"""
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = resolution_notes


class SystemHealthStatus(Base):
    """Track overall system health metrics"""
    __tablename__ = "system_health_status"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    check_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    service_name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)  # HEALTHY, DEGRADED, DOWN
    response_time_ms = Column(String, nullable=True)  # Service response time
    error_count_24h = Column(String, nullable=True)  # Error count in last 24h
    details = Column(JSON, nullable=True)  # Health check details
    
    @classmethod
    def record_health_check(cls, service_name: str, status: str, response_time_ms: int = None, 
                          error_count_24h: int = None, details: dict = None):
        """Record a health check result"""
        return cls(
            service_name=service_name,
            status=status,
            response_time_ms=str(response_time_ms) if response_time_ms else None,
            error_count_24h=str(error_count_24h) if error_count_24h else None,
            details=details or {}
        )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'check_timestamp': self.check_timestamp.isoformat() if self.check_timestamp else None,
            'service_name': self.service_name,
            'status': self.status,
            'response_time_ms': int(self.response_time_ms) if self.response_time_ms else None,
            'error_count_24h': int(self.error_count_24h) if self.error_count_24h else None,
            'details': self.details
        }