"""
Error Sanitization Utilities
Provides secure error handling for production APIs
"""

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Patterns that should be removed from error messages
SENSITIVE_PATTERNS = [
    r"password[=:]\s*[^\s]+",
    r"api[_-]?key[=:]\s*[^\s]+",
    r"token[=:]\s*[^\s]+",
    r"secret[=:]\s*[^\s]+",
    r"auth[=:]\s*[^\s]+",
    r"/home/[^/]+/",  # User home directories
    r'File ".*?backend.*?"',  # Internal file paths
    r"line \d+",  # Line numbers
    r"0x[0-9a-fA-F]+",  # Memory addresses
]

# Safe error messages for different error types
SAFE_ERROR_MESSAGES = {
    "connection": "Data source temporarily unavailable",
    "authentication": "Authentication failed",
    "authorization": "Access denied",
    "validation": "Invalid input parameters",
    "not_found": "Requested resource not found",
    "rate_limit": "Rate limit exceeded - please try again later",
    "internal": "Internal system error - support has been notified",
    "timeout": "Request timed out - please try again",
    "unavailable": "Service temporarily unavailable",
}


def sanitize_error_message(error_message: str, error_type: Optional[str] = None) -> str:
    """
    Sanitize error message for safe public consumption

    Args:
        error_message: Raw error message
        error_type: Type of error (optional) for targeted sanitization

    Returns:
        Sanitized error message safe for API responses
    """
    if not error_message:
        return "An unknown error occurred"

    # Convert to string if not already
    message = str(error_message)

    # Remove sensitive information using patterns
    for pattern in SENSITIVE_PATTERNS:
        message = re.sub(pattern, "[REDACTED]", message, flags=re.IGNORECASE)

    # Use safe message for known error types
    if error_type and error_type in SAFE_ERROR_MESSAGES:
        return SAFE_ERROR_MESSAGES[error_type]

    # For specific error conditions, use safe alternatives
    message_lower = message.lower()

    if any(
        keyword in message_lower for keyword in ["connection", "timeout", "network"]
    ):
        return SAFE_ERROR_MESSAGES["connection"]

    if any(keyword in message_lower for keyword in ["auth", "permission", "forbidden"]):
        return SAFE_ERROR_MESSAGES["authorization"]

    if any(keyword in message_lower for keyword in ["not found", "404"]):
        return SAFE_ERROR_MESSAGES["not_found"]

    if any(keyword in message_lower for keyword in ["rate limit", "too many"]):
        return SAFE_ERROR_MESSAGES["rate_limit"]

    if any(
        keyword in message_lower for keyword in ["validation", "invalid", "required"]
    ):
        return SAFE_ERROR_MESSAGES["validation"]

    # For unknown errors, provide generic message
    return SAFE_ERROR_MESSAGES["internal"]


def create_error_response(
    error: Exception, error_type: Optional[str] = None, include_details: bool = False
) -> Dict[str, Any]:
    """
    Create a sanitized error response for API endpoints

    Args:
        error: The exception that occurred
        error_type: Optional error type for categorization
        include_details: Whether to include additional details (for development)

    Returns:
        Dict containing sanitized error information
    """
    # Log the full error internally
    logger.error(f"API Error [{error_type or 'unknown'}]: {str(error)}", exc_info=True)

    # Create sanitized response
    response = {
        "error": True,
        "message": sanitize_error_message(str(error), error_type),
        "error_type": error_type or "internal",
        "timestamp": (
            logger._formatTime(logger.created) if hasattr(logger, "created") else None
        ),
    }

    # Add details only in development mode
    if include_details:
        response["details"] = {
            "raw_error": str(error)[:200],  # Truncate for safety
            "error_class": error.__class__.__name__,
        }

    return response


def classify_error_type(error: Exception) -> str:
    """
    Classify error into a safe category

    Args:
        error: The exception to classify

    Returns:
        Error type string for categorization
    """
    error_class = error.__class__.__name__.lower()
    error_message = str(error).lower()

    # Classification based on exception type
    if "connection" in error_class or "timeout" in error_class:
        return "connection"

    if "validation" in error_class or "value" in error_class:
        return "validation"

    if "permission" in error_class or "auth" in error_class:
        return "authorization"

    if "notfound" in error_class or "404" in error_message:
        return "not_found"

    if "ratelimit" in error_class or "rate limit" in error_message:
        return "rate_limit"

    # Default to internal error
    return "internal"


class SafeHTTPException:
    """
    Factory for creating sanitized HTTP exceptions
    """

    @staticmethod
    def internal_error(error: Exception) -> Dict[str, Any]:
        """Create sanitized 500 error response"""
        error_type = classify_error_type(error)
        return create_error_response(error, error_type)

    @staticmethod
    def validation_error(message: str = None) -> Dict[str, Any]:
        """Create sanitized 400 validation error"""
        safe_message = message or "Invalid input parameters"
        return {
            "error": True,
            "message": sanitize_error_message(safe_message, "validation"),
            "error_type": "validation",
        }

    @staticmethod
    def not_found_error(resource: str = "resource") -> Dict[str, Any]:
        """Create sanitized 404 error"""
        return {
            "error": True,
            "message": f"Requested {resource} not found",
            "error_type": "not_found",
        }

    @staticmethod
    def service_unavailable(service: str = "service") -> Dict[str, Any]:
        """Create sanitized 503 error"""
        return {
            "error": True,
            "message": f"{service.title()} temporarily unavailable",
            "error_type": "unavailable",
        }


# Development vs Production mode detection
def is_development_mode() -> bool:
    """Check if running in development mode"""
    import os

    return os.getenv("ENVIRONMENT", "production").lower() in [
        "development",
        "dev",
        "local",
    ]
