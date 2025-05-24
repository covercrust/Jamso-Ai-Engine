"""
CSRF Protection Utility

Enhancements:
- Added detailed comments for better understanding.
- Improved logging configuration.
- Enhanced error handling.
"""

from flask import Blueprint, request, session, abort, current_app
# NOTE: If your IDE shows an error on the following import but the code runs,
# see /home/jamso-ai-server/Jamso-Ai-Engine/Docs/IDE_Import_Resolution.md
from flask_wtf.csrf import CSRFProtect, generate_csrf
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File-level comment: This module provides CSRF protection for dashboard forms using Flask-WTF.

# Create a CSRF protection instance
csrf = CSRFProtect()

def init_csrf(app):
    """
    Initialize CSRF protection for the Flask application.

    Args:
        app: Flask application instance

    Returns:
        None
    """
    try:
        logger.info("Initializing CSRF protection.")
        csrf.init_app(app)
        logger.info("CSRF protection initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing CSRF protection: {e}")
        raise

    # Create a function to inject CSRF token into all templates
    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token into all templates."""
        return {
            'csrf_token': generate_csrf()
        }
    
    # Add CSRF token to AJAX responses if needed
    @app.after_request
    def add_csrf_header(response):
        """Add CSRF token to response headers for AJAX requests."""
        if request.endpoint and not request.endpoint.startswith('static'):
            response.headers.set('X-CSRF-Token', generate_csrf())
        return response
    
    logger.info("CSRF protection initialized for dashboard")
    
    return csrf

def csrf_blueprint():
    """Create a blueprint with CSRF protection routes."""
    bp = Blueprint('csrf', __name__)
    
    @bp.route('/csrf-token')
    def get_csrf_token():
        """Endpoint to get a new CSRF token."""
        token = generate_csrf()
        return {'csrf_token': token}
    
    return bp