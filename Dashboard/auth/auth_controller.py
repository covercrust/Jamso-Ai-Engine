"""
Jamso AI Trading Bot - Auth Controller

Enhancements:
- Added detailed comments for better understanding.
- Improved logging configuration.
- Enhanced error handling.
"""

import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, current_app
from Dashboard.models.user import User

# Configure detailed logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Configure a file handler for detailed auth logs
auth_log_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/Logs', 'auth_debug.log')
file_handler = logging.FileHandler(auth_log_path)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# File-level comment: This module handles user authentication for the Jamso AI Trading Bot.

# Create blueprint - note: url_prefix will be prepended in main app.py
auth_bp = Blueprint('auth', __name__, template_folder='templates')

def render_auth_template(template_name, **context):
    """Helper function to render templates from the correct folder"""
    dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(dashboard_dir, 'templates', template_name)
    
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template_content = f.read()
        return current_app.jinja_env.from_string(template_content).render(**context)
    else:
        logger.error(f"Template not found: {template_path}")
        return f"Template {template_name} not found."

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.

    Returns:
        str: Redirects to the dashboard or renders the login page.
    """
    logger.debug(f"Login route accessed with method: {request.method}")
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.debug(f"Login attempt for username: {username}")
        
        try:
            user = User.authenticate(username, password)
            if user:
                session.clear()
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                
                logger.info(f"User {username} logged in successfully.")
                
                next_page = request.args.get('next', url_for('dashboard.index'))
                return redirect(next_page)
            else:
                flash("Invalid credentials.", "error")
                logger.warning(f"Failed login attempt for username: {username}")
        except Exception as e:
            logger.error(f"Error during login: {e}")
            flash("An error occurred during login.", "error")
    
    return render_auth_template('auth/login.html', page_title='Login - Jamso AI Trading Bot')

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=('GET', 'POST'))
def reset_password():
    """Handle password reset"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        error = None
        
        if not email:
            error = 'Email is required.'
        
        if error is None:
            flash('If an account with that email exists, a password reset link has been sent.')
            return redirect(url_for('auth.login'))
        
        flash(error)
    
    return render_auth_template('auth/reset_password.html', page_title='Reset Password - Jamso AI Trading Bot')

# Load user into g for each request
@auth_bp.before_app_request
def load_logged_in_user():
    """Load user info into Flask's g object"""
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = User.find_by_id(user_id)