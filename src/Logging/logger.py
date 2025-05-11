#!/usr/bin/env python3
"""
Logging utilities for Jamso AI Server.
This module provides logging configuration and utilities.
"""

import os
import logging
import time
import functools
import json
from typing import Any, Callable, Dict, Optional, TypeVar, cast
from logging.handlers import RotatingFileHandler

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])

# Add a ContextAdapter to add context to logs
class ContextAdapter(logging.LoggerAdapter):
    """
    Adapter to add context information to log records.
    """
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})
        self._context = {}
        
    def process(self, msg, kwargs):
        kwargs.setdefault('extra', {}).update(self._context)
        return msg, kwargs
        
    def with_context(self, **context):
        """Context manager to add temporary context to logs"""
        class ContextManager:
            def __init__(self, adapter, context):
                self.adapter = adapter
                self.context = context
                self.old_context = {}
                
            def __enter__(self):
                # Save old context values that would be overwritten
                for key, value in self.context.items():
                    if key in self.adapter._context:
                        self.old_context[key] = self.adapter._context[key]
                
                # Update context with new values
                self.adapter._context.update(self.context)
                return self.adapter
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Restore old context values
                for key in self.context:
                    if key in self.old_context:
                        self.adapter._context[key] = self.old_context[key]
                    else:
                        del self.adapter._context[key]
                
        return ContextManager(self, context)
        
    def add_context(self, **context):
        """Add persistent context to logs"""
        self._context.update(context)
        
    def clear_context(self):
        """Clear all context data"""
        self._context.clear()

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    """
    def format(self, record):
        logobj = {
            'timestamp': self.formatTime(record, '%Y-%m-%dT%H:%M:%S'),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if hasattr(record, 'exc_info') and record.exc_info:
            logobj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(logobj)

def configure_root_logger(level: str = "INFO", log_dir: Optional[str] = None, 
                         console: bool = True, json_format: bool = False) -> None:
    """
    Configure the root logger for the application.
    
    Args:
        level: The logging level to use
        log_dir: Optional custom log directory path
        console: Whether to output logs to console
        json_format: Whether to format logs as JSON
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Create logs directory if it doesn't exist
    if log_dir is None:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                            "Logs")
    else:
        logs_dir = log_dir
        
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set up formatters based on json_format flag
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Set up handlers
    handlers = []
    
    # Always add file handler
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
    
    # Conditionally add console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    
    # Configure the root logger
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers
    )

def get_logger(name: str) -> ContextAdapter:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logger instance with context capabilities
    """
    return ContextAdapter(logging.getLogger(name))

def timing_decorator(func: F) -> F:
    """
    Decorator to log execution time of functions.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {elapsed_time:.3f} seconds")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed_time:.3f} seconds: {str(e)}")
            raise
            
    return cast(F, wrapper)
