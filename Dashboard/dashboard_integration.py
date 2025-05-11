"""
Dashboard Integration Module

This file provides simplified functions to integrate the dashboard with the main webhook app.
"""

import os
import logging
from flask import Flask, Blueprint, redirect, url_for, send_from_directory
from flask_session import Session
from Dashboard.app import create_app as create_dashboard_app
from Dashboard.auth.auth_controller import auth_bp 
from Dashboard.controllers.dashboard_controller import dashboard_bp
from Dashboard.controllers.admin.user_management import admin_users_bp
from Dashboard.models.user import User

# Configure logger
logger = logging.getLogger(__name__)

def setup_dashboard(app):
    """
    Integrate dashboard with the main Flask application
    
    Args:
        app: The main Flask application object
    """
    try:
        logger.info("Initializing dashboard integration...")
        
        # Set up template and static folders for the dashboard
        dashboard_folder = os.path.dirname(os.path.abspath(__file__))
        template_folder = os.path.join(dashboard_folder, 'templates')
        static_folder = os.path.join(dashboard_folder, 'static')
        
        logger.info(f"Dashboard template folder: {template_folder}")
        
        # Create a special blueprint just for handling templates and static files
        dashboard_assets = Blueprint(
            'dashboard_assets', 
            __name__,
            template_folder=template_folder,
            static_folder=static_folder,
            static_url_path='/dashboard/static'
        )
        
        # Configure session with more reliable settings
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'instance', 'dashboard_sessions')
        app.config['SESSION_PERMANENT'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['SESSION_COOKIE_NAME'] = 'dashboard_session'
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
        
        # Initialize Flask-Session
        Session(app)
        
        # Initialize the database for the User model with absolute path
        User.DB_PATH = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'src', 'Database', 'Users', 'users.db')
        os.makedirs(os.path.dirname(User.DB_PATH), exist_ok=True)
        
        # Create a new admin user with a simple password to ensure login works
        try:
            import sqlite3
            import hashlib
            
            conn = sqlite3.connect(User.DB_PATH)
            cursor = conn.cursor()
            
            # Make sure the users table exists
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                api_key TEXT UNIQUE,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
            ''')
            
            # Check if admin exists
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            admin = cursor.fetchone()
            
            admin_password = 'admin'
            password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
            
            if admin:
                # Update admin password
                cursor.execute(
                    "UPDATE users SET password_hash = ? WHERE username = 'admin'",
                    (password_hash,)
                )
                logger.info(f"Updated admin password to: {admin_password}")
            else:
                # Insert new admin
                cursor.execute(
                    "INSERT INTO users (username, password_hash, email, role, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                    ('admin', password_hash, 'admin@example.com', 'admin')
                )
                logger.info(f"Created new admin user with password: {admin_password}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error setting up admin user: {str(e)}")
        
        # Register the dashboard assets blueprint first
        app.register_blueprint(dashboard_assets)
        
        # Register all blueprint routes
        app.register_blueprint(auth_bp, url_prefix='/dashboard/auth')
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        app.register_blueprint(admin_users_bp, url_prefix='/dashboard/admin')
        
        # Helper function to render templates from the dashboard template folder
        def render_dashboard_template(template_name, **context):
            template_path = os.path.join(template_folder, template_name)
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    template_content = f.read()
                return app.jinja_env.from_string(template_content).render(**context)
            else:
                raise FileNotFoundError(f"Template not found: {template_path}")
        
        # Add this function to the app context
        app.jinja_env.globals['render_dashboard_template'] = render_dashboard_template
        
        # Add root dashboard route
        @app.route('/dashboard')
        def dashboard_root():
            return redirect(url_for('dashboard.index'))
        
        logger.info("Dashboard integration complete")
        return True
    except Exception as e:
        logger.error(f"Failed to setup dashboard: {str(e)}")
        return False

