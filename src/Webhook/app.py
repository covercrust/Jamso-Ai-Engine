#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_login import LoginManager
from flask_cors import CORS
import os
from functools import wraps
import time

from src.Logging.logger import get_logger, timing_decorator, configure_root_logger
from src.Webhook.database import init_db
from src.Webhook.routes import init_routes
from src.Webhook.config import Config

# Initialize the root logger before anything else
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Logs')
configure_root_logger(
    level="INFO",  # You can change this to "DEBUG" for more detailed logs
    log_dir=log_dir,
    console=True,
    json_format=False
)

# Get a logger for this module
logger = get_logger(__name__)

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_object(Config)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize database
    with app.app_context():
        init_db(app)
    
    # Register blueprints and routes
    init_routes(app)
    
    # Initialize CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    # Define a user loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        # Since we don't need authentication for the dashboard yet,
        # return None to allow anonymous access
        return None
        
    # Optional: Set login view if you implement authentication later
    login_manager.login_view = None
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({
            "status": "error",
            "code": "NOT_FOUND", 
            "message": str(e)
        }), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": str(e)
        }), 500
        
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "status": "error",
            "code": "BAD_REQUEST",
            "message": str(e)
        }), 400
        
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({
            "status": "error",
            "code": "UNAUTHORIZED",
            "message": "Authentication required"
        }), 401
        
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({
            "status": "error",
            "code": "FORBIDDEN",
            "message": "You don't have permission to access this resource"
        }), 403
        
    @app.before_request
    def log_request():
        # Add request ID and start time to request context
        request.request_id = os.urandom(16).hex()
        request.start_time = time.time()
        
        # Add request info to log context
        if hasattr(logger, 'add_context'):
            logger.add_context(
                request_id=request.request_id,
                method=request.method,
                path=request.path,
                remote_addr=request.remote_addr
            )
        
        logger.info(f"Request started: {request.method} {request.path}")
        
    @app.after_request
    def log_response(response):
        # Calculate request duration
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        logger.info(
            f"Request completed: {request.method} {request.path} "
            f"Status: {response.status_code} Duration: {duration:.3f}s"
        )
        
        # Clear the context after the request is complete
        if hasattr(logger, 'clear_context'):
            logger.clear_context()
        
        return response

    # Log application startup
    try:
        if hasattr(logger, 'with_context'):
            with logger.with_context(action="app_startup"):
                logger.info(f"Application started in {app.config['ENV']} mode")
        else:
            logger.info(f"Application started in {app.config['ENV']} mode")
    except Exception as e:
        logger.error(f"Error during startup logging: {e}")
        
    return app

# Create Flask application instance
flask_app = create_app()

if __name__ == "__main__":
    flask_app.run(debug=True, host='0.0.0.0', port=5000)