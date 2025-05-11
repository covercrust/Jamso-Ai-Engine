"""
Authentication utilities for dashboard API endpoints.
"""
import logging
import functools
from flask import request, g, jsonify, current_app, session
from Webhook.utils import create_error_response, jsonify_error

logger = logging.getLogger(__name__)

def api_auth_required(f):
    """
    Decorator for API endpoints that require authentication.
    Uses either:
    1. Session-based authentication (for browser access)
    2. API key authentication (for programmatic access via X-API-Key header)
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Check for API key in header first (for programmatic access)
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Validate API key
            if current_app.config.get('DASHBOARD_API_KEY') and api_key == current_app.config['DASHBOARD_API_KEY']:
                logger.debug("API authentication successful via API key")
                return f(*args, **kwargs)
            else:
                logger.warning(f"Invalid API key attempt: {api_key[:5]}...")
                return jsonify_error(create_error_response(
                    message="Invalid API key",
                    error_code="INVALID_API_KEY",
                    status_code=401
                ))
                
        # Check for session-based authentication (for browser access)
        if session.get('user_id'):
            # User is authenticated via session
            logger.debug(f"API authentication successful via session for user_id: {session.get('user_id')}")
            return f(*args, **kwargs)
            
        # No valid authentication method found
        logger.warning("API authentication failed: No valid authentication method")
        return jsonify_error(create_error_response(
            message="Authentication required",
            error_code="UNAUTHORIZED",
            status_code=401
        ))
        
    return decorated