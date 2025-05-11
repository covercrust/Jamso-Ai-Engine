"""
Jamso AI Trading Bot - Auth Controller
Handles user authentication
"""
import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, current_app
from Dashboard.models.user import User

# Configure detailed logger
logger = logging.getLogger(__name__)
# Configure a file handler for detailed auth logs
auth_log_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/Logs', 'auth_debug.log')
file_handler = logging.FileHandler(auth_log_path)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

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

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    """Handle user login"""
    logger.debug(f"Login route accessed with method: {request.method}")
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.debug(f"Login attempt for username: {username}")
        
        error = None
        
        if not username:
            error = 'Username is required.'
            logger.warning("Login attempt with empty username")
        elif not password:
            error = 'Password is required.'
            logger.warning("Login attempt with empty password")
        else:
            # Log the database path being used
            logger.debug(f"Using database path: {User.DB_PATH}")
            
            # Check if database file exists
            if os.path.exists(User.DB_PATH):
                logger.debug(f"Database file exists: {User.DB_PATH}")
            else:
                logger.error(f"Database file does not exist: {User.DB_PATH}")
            
            user = User.find_by_username(username)
            
            if user is None:
                error = 'Invalid username or password.'
                logger.warning(f"No user found with username: {username}")
            else:
                logger.debug(f"User found: {username}, Verifying password...")
                
                # Debug: Log password hash comparison
                submitted_hash = User.hash_password(password)
                logger.debug(f"Stored hash: {user.password_hash}")
                logger.debug(f"Submitted password hash: {submitted_hash}")
                
                if not User.verify_password(password, user.password_hash):
                    error = 'Invalid username or password.'
                    logger.warning(f"Invalid password for user: {username}")
                else:
                    logger.debug(f"Password verification successful for user: {username}")
        
        if error is None:
            # Store user info in session
            session.clear()
            # Ensure user is not None before accessing attributes
            if user is not None:
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                
                logger.info(f"User {username} logged in successfully")
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next', url_for('dashboard.index'))
                return redirect(next_page)
            else:
                # This should not happen as we check for user existence earlier,
                # but adding it for robustness
                error = "User authentication failed."
                logger.error(f"User object is None after successful password verification")
                flash(error)
                return render_auth_template('auth/login.html', page_title='Login - Jamso AI Trading Bot')
        
        flash(error)
        logger.warning(f"Login error: {error}")
    
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