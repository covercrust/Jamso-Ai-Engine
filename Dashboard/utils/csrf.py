"""
CSRF Protection Utility

This module provides CSRF protection for dashboard forms using Flask-WTF.
"""
from flask import Blueprint, request, session, abort, current_app
from flask_wtf.csrf import CSRFProtect, generate_csrf
import logging

logger = logging.getLogger(__name__)

# Create a CSRF protection instance
csrf = CSRFProtect()

def init_csrf(app):
    """
    Initialize CSRF protection for the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Initialize CSRF protection
    csrf.init_app(app)
    
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