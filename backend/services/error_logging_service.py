"""
Error Logging Service for Critical System Issues
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.database import get_db
from models.error_log import CriticalErrorLog, SystemHealthStatus

logger = logging.getLogger(__name__)


async def log_critical_error(
    error_type: str, 
    message: str, 
    details: Dict[str, Any] = None,
    service: str = None,
    user_id: str = None,
    severity: str = "HIGH"
) -> str:
    """
    Log a critical error to the database
    
    Args:
        error_type: Type of error (universe_loading_failed, ai_service_error, etc.)
        message: Human-readable error message
        details: Additional error details as dictionary
        service: Service/module where error occurred
        user_id: User affected (if applicable)
        severity: Error severity (HIGH, MEDIUM, LOW)
        
    Returns:
        Error log ID
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            error_log = CriticalErrorLog.create_error_log(
                error_type=error_type,
                message=message,
                details=details or {},
                service=service,
                user_id=user_id,
                severity=severity
            )
            
            db.add(error_log)
            db.commit()
            db.refresh(error_log)
            
            logger.error(f"CRITICAL ERROR LOGGED: {error_type} - {message[:100]}... [ID: {error_log.id}]")
            
            return error_log.id
            
        finally:
            db.close()
            
    except Exception as e:
        # Fallback to file logging if database fails
        logger.critical(f"FAILED TO LOG ERROR TO DATABASE: {e}")
        logger.critical(f"ORIGINAL ERROR: {error_type} - {message}")
        return None


async def get_critical_errors(
    limit: int = 50,
    error_type: str = None,
    service: str = None,
    unresolved_only: bool = False,
    since_hours: int = None
) -> List[Dict[str, Any]]:
    """
    Retrieve critical errors from database
    
    Args:
        limit: Maximum number of errors to return
        error_type: Filter by error type
        service: Filter by service
        unresolved_only: Only return unresolved errors
        since_hours: Only return errors from last N hours
        
    Returns:
        List of error dictionaries
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            query = db.query(CriticalErrorLog)
            
            if error_type:
                query = query.filter(CriticalErrorLog.error_type == error_type)
            
            if service:
                query = query.filter(CriticalErrorLog.service == service)
            
            if unresolved_only:
                query = query.filter(CriticalErrorLog.resolved_at.is_(None))
            
            if since_hours:
                since_time = datetime.utcnow() - timedelta(hours=since_hours)
                query = query.filter(CriticalErrorLog.created_at >= since_time)
            
            errors = query.order_by(CriticalErrorLog.created_at.desc()).limit(limit).all()
            
            return [error.to_dict() for error in errors]
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to retrieve critical errors: {e}")
        return []


async def mark_error_resolved(error_id: str, resolution_notes: str = None) -> bool:
    """
    Mark a critical error as resolved
    
    Args:
        error_id: Error log ID
        resolution_notes: Notes about how it was resolved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            error_log = db.query(CriticalErrorLog).filter(CriticalErrorLog.id == error_id).first()
            
            if not error_log:
                logger.warning(f"Error log not found: {error_id}")
                return False
            
            error_log.mark_resolved(resolution_notes)
            db.commit()
            
            logger.info(f"Marked error as resolved: {error_id}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to mark error as resolved: {e}")
        return False


async def record_system_health(
    service_name: str,
    status: str,
    response_time_ms: int = None,
    error_count_24h: int = None,
    details: Dict[str, Any] = None
) -> str:
    """
    Record system health status
    
    Args:
        service_name: Name of the service being checked
        status: HEALTHY, DEGRADED, or DOWN
        response_time_ms: Service response time in milliseconds
        error_count_24h: Number of errors in last 24 hours
        details: Additional health check details
        
    Returns:
        Health record ID
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            health_record = SystemHealthStatus.record_health_check(
                service_name=service_name,
                status=status,
                response_time_ms=response_time_ms,
                error_count_24h=error_count_24h,
                details=details or {}
            )
            
            db.add(health_record)
            db.commit()
            db.refresh(health_record)
            
            logger.info(f"Health check recorded: {service_name} - {status}")
            
            return health_record.id
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to record system health: {e}")
        return None


async def get_system_health_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive system health dashboard data
    
    Returns:
        Dictionary with system health overview
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Get recent critical errors (last 24 hours)
            recent_errors = await get_critical_errors(
                limit=10,
                unresolved_only=True,
                since_hours=24
            )
            
            # Get latest health status for each service
            latest_health = db.query(SystemHealthStatus).order_by(
                SystemHealthStatus.service_name,
                SystemHealthStatus.check_timestamp.desc()
            ).all()
            
            # Group by service (get most recent for each)
            service_health = {}
            for health in latest_health:
                if health.service_name not in service_health:
                    service_health[health.service_name] = health.to_dict()
            
            # Count errors by type (last 24 hours)
            since_24h = datetime.utcnow() - timedelta(hours=24)
            error_counts = db.query(CriticalErrorLog).filter(
                CriticalErrorLog.created_at >= since_24h
            ).all()
            
            error_summary = {}
            for error in error_counts:
                error_type = error.error_type
                if error_type not in error_summary:
                    error_summary[error_type] = {'count': 0, 'unresolved': 0}
                error_summary[error_type]['count'] += 1
                if not error.resolved_at:
                    error_summary[error_type]['unresolved'] += 1
            
            return {
                'overall_status': 'HEALTHY' if len(recent_errors) == 0 else 'DEGRADED',
                'critical_errors_24h': len(recent_errors),
                'unresolved_errors': len(recent_errors),
                'recent_errors': recent_errors,
                'service_health': service_health,
                'error_summary': error_summary,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to get system health dashboard: {e}")
        return {
            'overall_status': 'UNKNOWN',
            'critical_errors_24h': 0,
            'unresolved_errors': 0,
            'recent_errors': [],
            'service_health': {},
            'error_summary': {},
            'last_updated': datetime.utcnow().isoformat(),
            'error': str(e)
        }