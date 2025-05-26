import logging
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from contextvars import ContextVar

# Context variables for request context
request_id: ContextVar[str] = ContextVar('request_id', default='')
user_id: ContextVar[str] = ContextVar('user_id', default='')
endpoint: ContextVar[str] = ContextVar('endpoint', default='')
ip_address: ContextVar[str] = ContextVar('ip_address', default='')

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create JSON formatter
        self.formatter = logging.Formatter('%(message)s')
        
        # Add console handler
        handler = logging.StreamHandler()
        handler.setFormatter(self.formatter)
        self.logger.addHandler(handler)

    def _get_context(self) -> Dict[str, Any]:
        """Get current request context"""
        return {
            'request_id': request_id.get(),
            'user_id': user_id.get(),
            'endpoint': endpoint.get(),
            'ip_address': ip_address.get(),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured format"""
        log_data = {
            'level': logging.getLevelName(level),
            'message': message,
            **self._get_context(),
            **kwargs
        }
        self.logger.log(level, json.dumps(log_data))

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)

class Logger:
    """Wrapper for backward compatibility"""
    def __init__(self, name: str):
        self.logger = StructuredLogger(name)

    def info(self, message: str, **kwargs):
        self.logger.info(message, **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **kwargs)

    def critical(self, message: str, **kwargs):
        self.logger.critical(message, **kwargs) 