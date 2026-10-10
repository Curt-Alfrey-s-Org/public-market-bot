"""
Logging utilities for secret redaction and secure logging.
Automatically redacts sensitive values from logs.
"""

import logging
import re
from typing import List, Dict, Any

# List of sensitive environment variable names to redact
SENSITIVE_KEYS = {
    "BOT_API_KEY",
    "VITE_API_KEY",
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
    "SCHWAB_CLIENT_ID",
    "SCHWAB_CLIENT_SECRET",
    "ADMIN_PASSWORD",
    "DIRECTOR_PASSWORD",
    "USER_PASSWORD",
    "api_key",
    "password",
    "secret",
    "token",
    "credentials",
}

# Patterns to match sensitive values
REDACT_PATTERNS = [
    (r'(database_?url|postgresql)=([^\s&:]+:[^\s&]+@[^\s&]+)', r'postgresql://***REDACTED***'),  # PostgreSQL URLs
    (r'(api[_-]?key|vite[_-]?api[_-]?key)=([^\s&]*)', r'\1=***REDACTED***'),  # API keys
    (r'(password|passwd)=([^\s&]*)', r'\1=***REDACTED***'),  # Passwords
    (r'(secret|token)=([^\s&]*)', r'\1=***REDACTED***'),  # Secrets and tokens
    (r'Bearer\s+([^\s]*)', r'Bearer ***REDACTED***'),  # Bearer tokens
    (r'Authorization:\s*([^\s]*)', r'Authorization: ***REDACTED***'),  # Authorization headers
]


class SecretRedactionFilter(logging.Filter):
    """Logging filter that redacts sensitive information from log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record and redact sensitive information.
        
        Args:
            record: LogRecord to filter
            
        Returns:
            bool: Always True to allow the log record through
        """
        try:
            # Redact the main message
            if record.msg:
                record.msg = self._redact_value(str(record.msg))
            
            # Redact message arguments
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: self._redact_value(v) for k, v in record.args.items()}
                elif isinstance(record.args, tuple):
                    record.args = tuple(self._redact_value(arg) for arg in record.args)
        except Exception as e:
            # Don't let redaction errors break logging
            pass
        
        return True
    
    @staticmethod
    def _redact_value(value: Any) -> Any:
        """
        Redact sensitive values from a string.
        
        Args:
            value: Value to redact (can be any type)
            
        Returns:
            Redacted value
        """
        if not isinstance(value, str):
            return value
        
        # Apply regex patterns
        for pattern, replacement in REDACT_PATTERNS:
            value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        
        return value


def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact sensitive keys from a dictionary.
    
    Args:
        data: Dictionary that may contain sensitive values
        
    Returns:
        Dictionary with sensitive values redacted
    """
    redacted = {}
    for key, value in data.items():
        if any(sensitive in key.upper() for sensitive in SENSITIVE_KEYS):
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value)
        elif isinstance(value, list):
            redacted[key] = [redact_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            redacted[key] = value
    
    return redacted


def setup_secret_logging():
    """
    Setup logging with secret redaction filter.
    Should be called early in application startup.
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Add redaction filter to all handlers
    redaction_filter = SecretRedactionFilter()
    for handler in root_logger.handlers:
        handler.addFilter(redaction_filter)
    
    return redaction_filter
