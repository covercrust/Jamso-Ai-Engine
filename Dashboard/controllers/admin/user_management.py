"""
Admin User Management Controller

Enhancements:
- Added detailed comments for better understanding.
- Improved logging configuration.
- Enhanced error handling.
"""

import logging
import uuid
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort, current_app
from ...models.user import User
from functools import wraps

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File-level comment: This module allows administrators to manage users (create, view, update, delete).

# Create blueprint
admin_users_bp = Blueprint('admin_users', __name__, url_prefix='/admin/users')

def render_admin_template(template_name, **context):
    """
    Helper function to render templates from the correct folder.

    Args:
        template_name (str): Name of the template file.
        **context: Additional context variables for rendering.

    Returns:
        str: Rendered HTML template.
    """
    try:
        dashboard_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_path = os.path.join(dashboard_dir, 'templates', template_name)
        logger.info(f"Rendering template: {template_name}")
        return render_template(template_path, **context)
    except Exception as e:
        logger.error(f"Error rendering template {template_name}: {e}")
        abort(500)

def admin_required(f):
    """Decorator to restrict access to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or g.user.role != User.ROLE_ADMIN:
            logger.warning(f"Unauthorized access attempt to admin area by user: {g.user.username if g.user else 'anonymous'}")
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@admin_users_bp.route('/')
@admin_required
def index():
    """List all users"""
    try:
        conn = User.get_db_connection()
        conn.row_factory = User.dict_factory
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, email, role, created_at, last_login FROM users ORDER BY username")
        users = cursor.fetchall()
        conn.close()
        
        return render_admin_template('admin/users/index.html', users=users, page_title='User Management')
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        flash('Failed to retrieve user list.', 'danger')
        return redirect(url_for('dashboard.index'))

@admin_users_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    """Create a new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role', User.ROLE_USER)
        
        # Validate input
        error = None
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'
