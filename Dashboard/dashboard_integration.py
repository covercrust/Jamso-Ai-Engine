"""
Dashboard Integration Module

This file provides simplified functions to integrate the dashboard with the main webhook app.

Enhancements:
- Added detailed comments for better understanding.
- Improved logging for better traceability.
"""

import os
import logging
from flask import Flask, Blueprint, redirect, url_for, send_from_directory
from flask_session import Session
from Dashboard.auth.auth_controller import auth_bp 
from Dashboard.controllers.dashboard_controller import dashboard_bp
from Dashboard.controllers.admin.user_management import admin_users_bp
from Dashboard.models.user import User

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File-level comment: This module integrates the dashboard with the main Flask app.

def setup_dashboard(app):
    """
    Integrate dashboard with the main Flask application.

    Args:
        app (Flask): The main Flask application instance.

    Returns:
        None
    """
    logger.info("Setting up the dashboard integration.")
    try:
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/dashboard/auth')
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        app.register_blueprint(admin_users_bp, url_prefix='/dashboard/admin')
        logger.info("Blueprints registered successfully.")

        # Add root dashboard route
        @app.route('/dashboard')
        def dashboard_root():
            return redirect(url_for('dashboard.index'))

        # Set up template and static folders for the dashboard
        dashboard_folder = os.path.dirname(os.path.abspath(__file__))
        template_folder = os.path.join(dashboard_folder, 'templates')
        static_folder = os.path.join(dashboard_folder, 'static')
        
        logger.info(f"Dashboard template folder: {template_folder}")
        
        # Create a special blueprint for dashboard static files
        dashboard_assets = Blueprint(
            'dashboard_assets_' + str(id(app)), # Use a unique name based on the app instance
            __name__,
            template_folder=template_folder,
            static_folder=static_folder,
            static_url_path='/dashboard/static'
        )
        
        # Define multiple routes for directly accessing dashboard static files 
        # This handles both /static/js/settings.js and /js/settings.js paths
        @app.route('/static/<path:filename>')
        def dashboard_static_files(filename):
            logger.info(f"Serving static file from Dashboard: /static/{filename}")
            return send_from_directory(static_folder, filename)
            
        @app.route('/js/<path:filename>')
        def js_files_shortcut(filename):
            logger.info(f"Serving JS file from shortcut path: /js/{filename}")
            return send_from_directory(os.path.join(static_folder, 'js'), filename)
            
        @app.route('/css/<path:filename>')
        def css_files_shortcut(filename):
            logger.info(f"Serving CSS file from shortcut path: /css/{filename}")
            return send_from_directory(os.path.join(static_folder, 'css'), filename)
            
        @app.route('/img/<path:filename>')
        def img_files_shortcut(filename):
            logger.info(f"Serving image file from shortcut path: /img/{filename}")
            return send_from_directory(os.path.join(static_folder, 'img'), filename)
        
        # Register the dashboard assets blueprint 
        app.register_blueprint(dashboard_assets)

        # Configure session with more reliable settings
        # --- SECURITY/CONFIG UPDATE: Now loads all session config from environment variables or .env ---
        app.config['SESSION_TYPE'] = os.environ.get('SESSION_TYPE', 'filesystem')
        app.config['SESSION_FILE_DIR'] = os.environ.get('SESSION_FILE_DIR', os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'instance', 'dashboard_sessions'))
        app.config['SESSION_PERMANENT'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = int(os.environ.get('PERMANENT_SESSION_LIFETIME', '86400'))  # 24 hours in seconds
        app.config['SESSION_USE_SIGNER'] = os.environ.get('SESSION_USE_SIGNER', 'False') == 'True'
        app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
        app.config['SESSION_COOKIE_HTTPONLY'] = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
        app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
        app.config['SESSION_COOKIE_NAME'] = os.environ.get('SESSION_COOKIE_NAME', 'dashboard_session')
        # Redis support for production
        redis_url = os.environ.get('REDIS_URL')
        if app.config['SESSION_TYPE'] == 'redis' and redis_url:
            app.config['SESSION_REDIS'] = redis_url
        
        # Ensure session folder exists
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
        
        # We're using string for secret key to avoid bytes conversion issues in Python 3.12
        if 'SECRET_KEY' in app.config and isinstance(app.config['SECRET_KEY'], bytes):
            app.config['SECRET_KEY'] = app.config['SECRET_KEY'].decode('utf-8')
            
        # Initialize Flask-Session with modified interface to fix Python 3.12 compatibility
        from flask.sessions import SecureCookieSessionInterface
        from flask_session import Session as FlaskSession
        
        # Create a patched session interface
        class PatchedSessionInterface(SecureCookieSessionInterface):
            def save_session(self, app, session, response):
                # Call parent method but catch the specific error
                try:
                    return super().save_session(app, session, response)
                except TypeError as e:
                    # If it's the specific error we're patching
                    if "cannot use a string pattern on a bytes-like object" in str(e):
                        # Convert session_id to string if it's bytes
                        domain = self.get_cookie_domain(app)
                        path = self.get_cookie_path(app)
                        if not session:
                            if session.modified:
                                response.delete_cookie(app.config['SESSION_COOKIE_NAME'],
                                                      domain=domain, path=path)
                            return
                        
                        httponly = self.get_cookie_httponly(app)
                        secure = self.get_cookie_secure(app)
                        samesite = self.get_cookie_samesite(app)
                        expires = self.get_expiration_time(app, session)
                        
                        # Get session ID and ensure it's a string
                        session_id = self.get_signing_serializer(app).dumps(dict(session))
                        if isinstance(session_id, bytes):
                            session_id = session_id.decode('utf-8')
                            
                        response.set_cookie(app.config['SESSION_COOKIE_NAME'], session_id,
                                          expires=expires, httponly=httponly,
                                          domain=domain, path=path, secure=secure,
                                          samesite=samesite)
                    else:
                        # Re-raise if it's a different error
                        raise
                        
        # Use our custom session interface
        session = FlaskSession()
        session.session_interface = PatchedSessionInterface()
        session.init_app(app)
        
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
        
        logger.info("Dashboard integration complete")
        return True
    except Exception as e:
        logger.error(f"Failed to setup dashboard: {str(e)}")
        return False

