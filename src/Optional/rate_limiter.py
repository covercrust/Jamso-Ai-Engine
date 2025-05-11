#!/usr/bin/env python3
"""
Rate limiting utilities for Jamso AI Server.
This module provides rate limiting functionality for API endpoints.
"""

import time
import logging
from typing import Dict, Any, Callable, Optional, TypeVar, cast
from functools import wraps
from flask import request, jsonify, Response

logger = logging.getLogger(__name__)

# Create type variables for function typing
F = TypeVar('F', bound=Callable[..., Any])

# In-memory rate limit store (IP -> last request timestamp)
_rate_limit_store: Dict[str, Dict[str, Any]] = {}

def _get_client_ip() -> str:
    """
    Get the client IP address from the request
    """
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    return request.remote_addr or "unknown"

def rate_limit(limit: int = 60, window: int = 60) -> Callable[[F], F]:
    """
    Rate limiting decorator for Flask routes.
    
    Args:
        limit: Maximum number of requests allowed in the time window
        window: Time window in seconds (default is 60 seconds/1 minute)
        
    Returns:
        Decorated function with rate limiting
    """
    min_interval = float(window) / float(limit)
    
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            client_ip = _get_client_ip()
            
            # Initialize client in store if not exists
            if client_ip not in _rate_limit_store:
                _rate_limit_store[client_ip] = {
                    'last_request_time': 0,
                    'count': 0
                }
            
            # Check timing
            client_data = _rate_limit_store[client_ip]
            current_time = time.time()
            time_passed = current_time - client_data['last_request_time']
            
            # If within the time window, increment counter
            if time_passed < window:
                client_data['count'] += 1
            else:
                # Reset counter for a new time window
                client_data['count'] = 1
            
            # Store last request time
            client_data['last_request_time'] = current_time
            
            # Check if we're over the limit
            if client_data['count'] > limit:
                logger.warning(f"Rate limit exceeded for {client_ip}: {client_data['count']} requests/{window}s")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {limit} requests per {window} seconds allowed'
                }), 429
            
            # Allow the request and call the original function
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator
