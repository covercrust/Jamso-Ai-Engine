#!/usr/bin/env python3
"""
Jamso AI Trading Bot - Dashboard Application
Main entry point for the dashboard web application
"""
import os
import sys
import logging
from datetime import timedelta
from flask import Flask, redirect, url_for, render_template, Blueprint
from flask_session import Session  # type: ignore

# Setup base path and ensure it's in Python path
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_PATH)

# Configure proper logging using the centralized logger
from src.Logging.logger import configure_root_logger, get_logger

# Ensure logs go to the correct directory
log_dir = os.path.join(BASE_PATH, 'Logs')
configure_root_logger(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    log_dir=log_dir,
    console=True,
    json_format=False
)

logger = get_logger(__name__)

# Import resource management utilities
try:
    from src.Exchanges.capital_com_api.session_manager import SessionManager
    from src.Optional.process_monitor import ProcessMonitor, is_psutil_available
    resource_monitoring_available = True
except ImportError as e:
    logger.warning(f"Resource monitoring modules not fully available: {e}")
    resource_monitoring_available = False

# Import controllers after path setup
from Dashboard.auth.auth_controller import auth_bp
from Dashboard.controllers.dashboard_controller import dashboard_bp
from Dashboard.controllers.admin.user_management import admin_users_bp
from Dashboard.models.user import User

# Import CSRF protection
from Dashboard.utils.csrf import init_csrf, csrf_blueprint

def create_app():
    """Create and configure the Flask application"""
    # Create Flask app with standardized template and static folders
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Load configuration with standardized paths
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production'),
        SESSION_TYPE='filesystem',
        SESSION_FILE_DIR=os.path.join(BASE_PATH, 'instance', 'sessions'),
        SESSION_PERMANENT=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=1),  # Reduced from 30 days to 1 day
        SESSION_USE_SIGNER=True,
        SESSION_COOKIE_SECURE=False,  # Set to False for development
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        # Database path updated to standardized location
        DATABASE_PATH=os.path.join(BASE_PATH, 'src', 'Database', 'Users', 'users.db'),
        # Dashboard API authentication key
        DASHBOARD_API_KEY=os.environ.get('DASHBOARD_API_KEY', 'default_dashboard_api_key_change_in_production'),
        # CSRF protection settings
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_SECRET_KEY=os.environ.get('CSRF_SECRET_KEY', 'csrf_secret_key_change_in_production'),
        WTF_CSRF_TIME_LIMIT=3600  # 1 hour token expiration
    )
    
    # Ensure session folder exists
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Initialize Flask-Session
    Session(app)
    
    # Initialize CSRF protection
    init_csrf(app)
    # Call the function to get the blueprint, then register it
    app.register_blueprint(csrf_blueprint())
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_users_bp)
    
    # Main route redirects to dashboard
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))
    
    # Add system status check route
    @app.route('/status')
    def status():
        system_info = {
            'status': 'ok',
            'timestamp': os.environ.get('SERVER_START_TIME', 'unknown'),
            'version': os.environ.get('APP_VERSION', '1.0.0'),
        }
        
        # Add resource monitoring if available
        if resource_monitoring_available and is_psutil_available:
            try:
                monitor = ProcessMonitor()
                system_resources = monitor.get_system_resources()
                system_info.update({
                    'cpu_usage': system_resources['cpu_usage'],
                    'memory_percent': system_resources['memory']['percent'],
                    'disk_usage': system_resources['disk']['percent'],
                })
            except Exception as e:
                logger.error(f"Error getting system metrics: {e}")
                system_info['status'] = 'degraded'
                system_info['error'] = str(e)
        
        return system_info
    
    # Log that we've created the app
    logger.info("Dashboard application created")
    return app