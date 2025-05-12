"""
Authentication utilities for dashboard API endpoints.

Enhancements:
- Added detailed comments for better understanding.
- Improved error handling and logging.
"""

import logging
import functools
from flask import request, g, jsonify, current_app, session
from Webhook.utils import create_error_response, jsonify_error

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File-level comment: This module provides authentication utilities for securing API endpoints.

def api_auth_required(f):
    """
    Decorator for API endpoints that require authentication.

    Authentication Methods:
    1. Session-based authentication (for browser access).
    2. API key authentication (for programmatic access via X-API-Key header).

    Args:
        f (function): The API endpoint function to secure.

    Returns:
        function: The decorated function with authentication checks.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Check for API key in header first (for programmatic access)
            api_key = request.headers.get('X-API-Key')
            if api_key:
                # Validate API key (placeholder for actual validation logic)
                if api_key != current_app.config.get('VALID_API_KEY'):
                    logger.warning("Invalid API key provided.")
                    return create_error_response("Invalid API key.", 401)

            # Check for session-based authentication (for browser access)
            elif 'user_id' not in session:
                logger.warning("User not authenticated via session.")
                return create_error_response("Authentication required.", 401)

            # Proceed with the original function if authenticated
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in api_auth_required: {e}")
            return jsonify_error("Internal server error.", 500)

    return decorated