"""
Jamso AI Trading Bot - Dashboard Controller

Enhancements:
- Added detailed comments for better understanding.
- Improved logging configuration.
- Enhanced error handling.
- Fixed type safety issues with request.json handling.
"""

import logging
import time
import sqlite3
import os
import subprocess
import signal
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify, current_app
from functools import wraps
from ..models.user import User
from src.AI import PerformanceMonitor
from src.AI.example_strategies import jamso_ai_bot_strategy  # Direct import of strategy function

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File-level comment: This module handles dashboard routes and functionality for the Jamso AI Trading Bot.

# Create blueprint - url_prefix will be added in main app.py
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard', template_folder='templates')

# Server control process IDs
SERVER_PID_FILE = '/home/jamso-ai-server/Jamso-Ai-Engine/tmp/server.pid'

# Ensure g.user is always set to avoid AttributeError
@dashboard_bp.before_app_request
def load_user_to_g():
    if not hasattr(g, 'user'):
        g.user = None

def render_dashboard_template(template_name, **context):
    """Helper function to render templates from the correct folder"""
    dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(dashboard_dir, 'templates', template_name)
    
    # Add user permissions to context
    if g.user:
        context['user_permissions'] = g.user.get_permissions() if hasattr(g.user, 'get_permissions') else []
    
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template_content = f.read()
        return current_app.jinja_env.from_string(template_content).render(**context)
    else:
        logger.error(f"Template not found: {template_path}")
        return f"Template {template_name} not found."

# Authentication decorator
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view

# Admin role decorator
def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user.role != 'admin':
            flash('You do not have permission to access this page.')
            return redirect(url_for('dashboard.index'))
        return view(**kwargs)
    return wrapped_view

# Permission-based decorator
def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for('auth.login', next=request.url))
            if not g.user.has_permission(permission):
                flash('You do not have permission to access this feature.')
                return redirect(url_for('dashboard.index'))
            return view(**kwargs)
        return wrapped_view
    return decorator

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard index page"""
    # Get current system uptime (placeholder)
    uptime = int(time.time()) - 1713897600  # Example start time
    
    # Get real webhook stats
    trade_stats = get_trade_stats()
    
    return render_dashboard_template('Public_html/index.html', 
                         page_title="Dashboard - Jamso AI Trading Bot",
                         username=session.get('username', 'User'),
                         uptime=uptime,
                         trade_stats=trade_stats)

@dashboard_bp.route('/trades')
@permission_required('view_trades')
def trades():
    """Render trades page with real trade data"""
    # Get actual trades from the database
    trades_data = get_recent_trades(10)  # Get 10 most recent trades
    
    return render_dashboard_template('Public_html/trades.html', 
                         page_title="Trades - Jamso AI Trading Bot",
                         username=session.get('username', 'User'),
                         trades=trades_data)

@dashboard_bp.route('/signals')
@permission_required('view_signals')
def signals():
    """Render signals page with real signal data"""
    # Get actual signals from the database
    signals_data = get_recent_signals(10)  # Get 10 most recent signals
    
    return render_dashboard_template('Public_html/signals.html', 
                         page_title="Signals - Jamso AI Trading Bot",
                         username=session.get('username', 'User'),
                         signals=signals_data)

@dashboard_bp.route('/analytics')
@permission_required('view_analytics')
def analytics():
    """Render analytics page"""
    # Get actual performance metrics
    performance_data = get_performance_data()
    
    return render_dashboard_template('Public_html/analytics.html', 
                         page_title="Analytics - Jamso AI Trading Bot",
                         username=session.get('username', 'User'),
                         performance=performance_data)

@dashboard_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    # Get API keys for the current user
    api_keys = get_user_api_keys(g.user.id)
    
    return render_dashboard_template('Public_html/settings.html', 
                         page_title="Settings - Jamso AI Trading Bot",
                         username=session.get('username', 'User'),
                         user=g.user,
                         api_keys=api_keys)

@dashboard_bp.route('/admin')
@login_required
@admin_required
def admin():
    """Admin panel page"""
    return render_dashboard_template('dashboard/admin.html', 
                         page_title="Admin Panel - Jamso AI Trading Bot",
                         username=session.get('username', 'Admin'))

@dashboard_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Render admin users page (admin only)"""
    users = User.get_all_users()
    
    return render_dashboard_template('dashboard/admin_users.html', 
                         page_title="User Management - Jamso AI Trading Bot",
                         username=session.get('username', 'Admin'),
                         users=users)

# API endpoints for dashboard functionality

@dashboard_bp.route('/api/status')
@login_required
def api_status():
    """Get system status for dashboard"""
    # Check actual system statuses
    statuses = check_system_status()
    
    last_update = int(time.time())
    
    return jsonify({
        'statuses': statuses,
        'last_update': last_update
    })

@dashboard_bp.route('/api/performance/<int:days>')
@login_required
def api_performance(days):
    """Get trading performance data for chart display"""
    # Get actual performance data from database
    performance_data = get_historical_performance(days)
    
    return jsonify(performance_data)

@dashboard_bp.route('/api/trades/recent')
@login_required
def api_recent_trades():
    """Get recent trades data"""
    # Get actual trades data from database
    trades = get_recent_trades(5)  # Get 5 most recent trades
    
    return jsonify({
        'trades': trades
    })

@dashboard_bp.route('/api/server/restart', methods=['POST'])
@login_required
@admin_required
def restart_server():
    """API endpoint to restart the webhook server"""
    try:
        # Create the restart trigger file for Passenger in production
        restart_file = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'tmp', 'restart.txt')
        with open(restart_file, 'w') as f:
            f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info(f"Server restart triggered by user {g.user.username}")
        
        # For development mode, we'll return instructions instead of trying to restart
        if current_app.debug:
            return jsonify({
                'success': True,
                'message': 'Server restart file created. In development mode, please restart the server manually: Press Ctrl+C in the terminal and run ./run_local.sh',
                'dev_mode': True
            })
        # In production, Passenger will handle the restart
        else:
            return jsonify({
                'success': True,
                'message': 'Server restart triggered successfully',
                'dev_mode': False
            })
    except Exception as e:
        logger.error(f"Error restarting server: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error restarting server: {str(e)}'
        }), 500

@dashboard_bp.route('/api/server/stop', methods=['POST'])
@login_required
@admin_required
def stop_server():
    """API endpoint to stop all trading activities"""
    try:
        # Create a stop trading flag file
        stop_file = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'tmp', 'stop_trading.txt')
        with open(stop_file, 'w') as f:
            f.write(f"Trading stopped at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info(f"Trading stopped by user {g.user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Trading stopped successfully'
        })
    except Exception as e:
        logger.error(f"Error stopping trading: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error stopping trading: {str(e)}'
        }), 500

@dashboard_bp.route('/api/credentials', methods=['GET'])
@login_required
@admin_required
def get_credentials():
    """Fetch all credentials"""
    try:
        conn = sqlite3.connect('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Credentials/credentials.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, service_name, created_at, updated_at FROM credentials")
        credentials = cursor.fetchall()
        conn.close()
        return jsonify(credentials)
    except Exception as e:
        logger.error(f"Error fetching credentials: {str(e)}")
        return jsonify({'error': 'Failed to fetch credentials'}), 500

@dashboard_bp.route('/api/credentials', methods=['POST'])
@login_required
@admin_required
def create_credential():
    """Create a new credential"""
    data = request.json or {}  # Use empty dict as fallback if request.json is None
    service_name = data.get('service_name')
    api_key = data.get('api_key')
    encrypted_secret = data.get('encrypted_secret')

    if not service_name or not api_key or not encrypted_secret:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = sqlite3.connect('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Credentials/credentials.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO credentials (service_name, api_key, encrypted_secret) VALUES (?, ?, ?)",
            (service_name, api_key, encrypted_secret)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Credential created successfully'}), 201
    except Exception as e:
        logger.error(f"Error creating credential: {str(e)}")
        return jsonify({'error': 'Failed to create credential'}), 500

@dashboard_bp.route('/api/credentials/<int:credential_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_credential(credential_id):
    """Delete a credential"""
    try:
        conn = sqlite3.connect('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Credentials/credentials.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM credentials WHERE id = ?", (credential_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Credential deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting credential: {str(e)}")
        return jsonify({'error': 'Failed to delete credential'}), 500

@dashboard_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """API endpoint to update user profile settings"""
    try:
        data = request.json or {}  # Use empty dict as fallback if request.json is None
        user = g.user
        
        # Update email if provided
        if data.get('email') and data['email'] != user.email:
            user.email = data['email']
        
        # Update names if provided
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        # Handle password change if requested
        if data.get('new_password') and data.get('current_password'):
            import hashlib
            # Verify current password
            current_hash = hashlib.sha256(data['current_password'].encode()).hexdigest()
            if current_hash != user.password_hash:
                return jsonify({
                    'success': False,
                    'message': 'Current password is incorrect'
                }), 400
                
            # Update to new password
            if data.get('new_password') == data.get('confirm_password'):
                user.password_hash = hashlib.sha256(data['new_password'].encode()).hexdigest()
            else:
                return jsonify({
                    'success': False,
                    'message': 'New passwords do not match'
                }), 400
        
        # Save user to database
        user.save()
        
        logger.info(f"User {user.username} updated their profile")
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error updating profile: {str(e)}'
        }), 500

# Functions to interact with the WebHook database

def get_trade_stats():
    """Get trade statistics from signals database"""
    try:
        db_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook', 'trading_signals.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_signals': 0,
            'total_trades': 0,
            'successful_trades': 0,
            'pending_signals': 0,
            'failed_signals': 0
        }
        
        # Get total signals
        cursor.execute("SELECT COUNT(*) FROM signals")
        stats['total_signals'] = cursor.fetchone()[0] or 0
        
        # Get successful trades
        cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'completed'")
        stats['successful_trades'] = cursor.fetchone()[0] or 0
        
        # Get pending signals
        cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'pending'")
        stats['pending_signals'] = cursor.fetchone()[0] or 0
        
        # Get failed signals
        cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'failed'")
        stats['failed_signals'] = cursor.fetchone()[0] or 0
        
        # Calculate total trades
        stats['total_trades'] = stats['successful_trades'] + stats['failed_signals']
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Error getting trade stats: {str(e)}")
        return {
            'total_signals': 0,
            'total_trades': 0,
            'successful_trades': 0,
            'pending_signals': 0,
            'failed_signals': 0
        }

def get_recent_trades(limit=10):
    """Get recent trades from database"""
    try:
        db_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook', 'trading_signals.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, order_id, deal_id, position_status, trade_direction as action, position_size as size
            FROM signals 
            WHERE deal_id IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        trades = []
        for row in cursor.fetchall():
            trades.append(dict(row))
        
        conn.close()
        return trades
    except Exception as e:
        logger.error(f"Error getting recent trades: {str(e)}")
        return []

def get_recent_signals(limit=10):
    """Get recent signals from database"""
    try:
        db_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook', 'trading_signals.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, order_id, status, trade_action, trade_direction, position_size
            FROM signals
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        signals = []
        for row in cursor.fetchall():
            signals.append(dict(row))
        
        conn.close()
        return signals
    except Exception as e:
        logger.error(f"Error getting recent signals: {str(e)}")
        return []

def get_performance_data():
    """Get trade performance data"""
    try:
        db_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook', 'trading_signals.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Initialize performance metrics
        performance = {
            'win_rate': 0.0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'net_pnl': 0.0,
            'average_win': 0.0,
            'average_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0
        }
        
        # Get total completed trades with profit/loss data
        cursor.execute("""
            SELECT COUNT(*) FROM positions p
            JOIN signals s ON p.signal_id = s.id
            WHERE p.status = 'closed' AND p.profit_loss IS NOT NULL
        """)
        total_trades = cursor.fetchone()[0] or 0
        
        if total_trades > 0:
            # Calculate winning trades
            cursor.execute("""
                SELECT COUNT(*) FROM positions p
                JOIN signals s ON p.signal_id = s.id
                WHERE p.status = 'closed' AND p.profit_loss > 0
            """)
            winning_trades = cursor.fetchone()[0] or 0
            
            # Calculate win rate
            performance['win_rate'] = round((winning_trades / total_trades) * 100, 2) if total_trades > 0 else 0.0
            
            # Get total profit from winning trades
            cursor.execute("""
                SELECT SUM(profit_loss) FROM positions p
                JOIN signals s ON p.signal_id = s.id
                WHERE p.status = 'closed' AND p.profit_loss > 0
            """)
            total_profit = cursor.fetchone()[0] or 0
            performance['total_profit'] = round(total_profit, 2)
            
            # Get total loss from losing trades
            cursor.execute("""
                SELECT SUM(profit_loss) FROM positions p
                JOIN signals s ON p.signal_id = s.id
                WHERE p.status = 'closed' AND p.profit_loss < 0
            """)
            total_loss = cursor.fetchone()[0] or 0
            performance['total_loss'] = round(abs(total_loss), 2)
            
            # Calculate net P&L
            performance['net_pnl'] = round(total_profit + total_loss, 2)
            
            # Calculate average win
            if winning_trades > 0:
                cursor.execute("""
                    SELECT AVG(profit_loss) FROM positions p
                    JOIN signals s ON p.signal_id = s.id
                    WHERE p.status = 'closed' AND p.profit_loss > 0
                """)
                performance['average_win'] = round(cursor.fetchone()[0] or 0, 2)
            
            # Calculate average loss
            cursor.execute("""
                SELECT COUNT(*) FROM positions p
                JOIN signals s ON p.signal_id = s.id
                WHERE p.status = 'closed' AND p.profit_loss < 0
            """)
            losing_trades = cursor.fetchone()[0] or 0
            if losing_trades > 0:
                cursor.execute("""
                    SELECT AVG(profit_loss) FROM positions p
                    JOIN signals s ON p.signal_id = s.id
                    WHERE p.status = 'closed' AND p.profit_loss < 0
                """)
                performance['average_loss'] = round(abs(cursor.fetchone()[0] or 0), 2)
            
            # Get largest win
            cursor.execute("""
                SELECT MAX(profit_loss) FROM positions p
                JOIN signals s ON p.signal_id = s.id
                WHERE p.status = 'closed'
            """)
            performance['largest_win'] = round(cursor.fetchone()[0] or 0, 2)
            
            # Get largest loss
            cursor.execute("""
                SELECT MIN(profit_loss) FROM positions p
                JOIN signals s ON p.signal_id = s.id
                WHERE p.status = 'closed'
            """)
            largest_loss = cursor.fetchone()[0]
            if largest_loss is not None and largest_loss < 0:
                performance['largest_loss'] = round(abs(largest_loss), 2)
        
        conn.close()
        return performance
    except Exception as e:
        logger.error(f"Error getting performance data: {str(e)}")
        return {
            'win_rate': 0.0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'net_pnl': 0.0,
            'average_win': 0.0,
            'average_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0
        }

def get_historical_performance(days=30):
    """Get historical performance data for charting"""
    try:
        db_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook', 'trading_signals.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        # Initialize the data structure needed by the frontend
        performance_data = {
            'daily_performance': [],
            'win_loss': {
                'win': 0,
                'loss': 0
            },
            'instrument_breakdown': [],
            'weekday_performance': [
                {'name': 'Monday', 'trades': 0, 'pnl': 0},
                {'name': 'Tuesday', 'trades': 0, 'pnl': 0},
                {'name': 'Wednesday', 'trades': 0, 'pnl': 0},
                {'name': 'Thursday', 'trades': 0, 'pnl': 0},
                {'name': 'Friday', 'trades': 0, 'pnl': 0}
            ],
            'summary': {
                'total_trades': 0,
                'win_rate': 0,
                'net_pnl': 0,
                'largest_win': 0,
                'largest_loss': 0
            }
        }
        
        # 1. Get daily performance data
        cursor.execute("""
            SELECT date(p.close_time) as trade_date, 
                   SUM(p.profit_loss) as daily_pnl,
                   COUNT(*) as trade_count
            FROM positions p
            JOIN signals s ON p.signal_id = s.id
            WHERE p.status = 'closed' 
            AND p.close_time >= ?
            GROUP BY trade_date
            ORDER BY trade_date
        """, (start_date_str,))
        
        # Build daily performance array
        daily_data = cursor.fetchall()
        dates = []
        values = []
        base_value = 10000  # Starting account value
        current_value = base_value
        
        for day in daily_data:
            dates.append(day['trade_date'])
            daily_pnl = day['daily_pnl'] or 0
            current_value += daily_pnl
            values.append(round(current_value, 2))
            
            # Add to daily performance array
            performance_data['daily_performance'].append({
                'date': day['trade_date'],
                'value': round(current_value, 2),
                'trades': day['trade_count']
            })
        
        # Fill in missing dates if necessary
        if not dates:
            # If no data, generate empty dataset with just dates
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                dates.append(date_str)
                performance_data['daily_performance'].append({
                    'date': date_str,
                    'value': base_value,
                    'trades': 0
                })
                current_date += timedelta(days=1)
            values = [base_value] * len(dates)
        
        # 2. Get win/loss ratio
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN p.profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN p.profit_loss < 0 THEN 1 ELSE 0 END) as losses
            FROM positions p
            JOIN signals s ON p.signal_id = s.id
            WHERE p.status = 'closed' AND p.close_time >= ?
        """, (start_date_str,))
        
        win_loss = cursor.fetchone()
        if win_loss:
            performance_data['win_loss']['win'] = win_loss['wins'] or 0
            performance_data['win_loss']['loss'] = win_loss['losses'] or 0
        
        # 3. Get instrument breakdown
        cursor.execute("""
            SELECT 
                s.instrument as name,
                COUNT(*) as trades,
                SUM(p.profit_loss) as pnl
            FROM positions p
            JOIN signals s ON p.signal_id = s.id
            WHERE p.status = 'closed' AND p.close_time >= ?
            GROUP BY s.instrument
            ORDER BY pnl DESC
            LIMIT 5
        """, (start_date_str,))
        
        for instrument in cursor.fetchall():
            performance_data['instrument_breakdown'].append({
                'name': instrument['name'],
                'trades': instrument['trades'],
                'pnl': round(instrument['pnl'] or 0, 2)
            })
        
        # 4. Get weekday performance
        cursor.execute("""
            SELECT 
                strftime('%w', p.close_time) as weekday,
                COUNT(*) as trades,
                SUM(p.profit_loss) as pnl
            FROM positions p
            JOIN signals s ON p.signal_id = s.id
            WHERE p.status = 'closed' AND p.close_time >= ?
            GROUP BY weekday
        """, (start_date_str,))
        
        weekday_map = {
            '1': 0,  # Monday (index in our array)
            '2': 1,  # Tuesday
            '3': 2,  # Wednesday
            '4': 3,  # Thursday
            '5': 4,  # Friday
        }
        
        for day in cursor.fetchall():
            weekday_idx = weekday_map.get(day['weekday'])
            if weekday_idx is not None:
                performance_data['weekday_performance'][weekday_idx]['trades'] = day['trades']
                performance_data['weekday_performance'][weekday_idx]['pnl'] = round(day['pnl'] or 0, 2)
        
        # 5. Get summary statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN p.profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                SUM(p.profit_loss) as net_pnl,
                MAX(p.profit_loss) as largest_win,
                MIN(p.profit_loss) as largest_loss
            FROM positions p
            JOIN signals s ON p.signal_id = s.id
            WHERE p.status = 'closed' AND p.close_time >= ?
        """, (start_date_str,))
        
        summary = cursor.fetchone()
        if summary and summary['total_trades'] > 0:
            performance_data['summary']['total_trades'] = summary['total_trades']
            performance_data['summary']['win_rate'] = round((summary['wins'] / summary['total_trades']) * 100, 1) if summary['wins'] else 0
            performance_data['summary']['net_pnl'] = round(summary['net_pnl'] or 0, 2)
            performance_data['summary']['largest_win'] = round(summary['largest_win'] or 0, 2)
            performance_data['summary']['largest_loss'] = abs(round(summary['largest_loss'] or 0, 2))
        
        # Add basic data for backward compatibility
        performance_data['dates'] = dates
        performance_data['values'] = values
        
        conn.close()
        return performance_data
        
    except Exception as e:
        logger.error(f"Error getting historical performance: {str(e)}")
        
        # Return a minimal dataset with empty/default values
        from datetime import datetime, timedelta
        
        # Generate empty date range for the chart
        dates = []
        values = []
        daily_performance = []
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        current_date = start_date
        base_value = 10000
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            values.append(base_value)
            
            daily_performance.append({
                'date': date_str,
                'value': base_value,
                'trades': 0
            })
            
            current_date += timedelta(days=1)
        
        return {
            'dates': dates,
            'values': values,
            'daily_performance': daily_performance,
            'win_loss': {'win': 0, 'loss': 0},
            'instrument_breakdown': [],
            'weekday_performance': [
                {'name': 'Monday', 'trades': 0, 'pnl': 0},
                {'name': 'Tuesday', 'trades': 0, 'pnl': 0},
                {'name': 'Wednesday', 'trades': 0, 'pnl': 0},
                {'name': 'Thursday', 'trades': 0, 'pnl': 0},
                {'name': 'Friday', 'trades': 0, 'pnl': 0}
            ],
            'summary': {
                'total_trades': 0,
                'win_rate': 0,
                'net_pnl': 0,
                'largest_win': 0,
                'largest_loss': 0
            }
        }

def check_system_status():
    """Check various system components status"""
    statuses = {
        'webhook': True,
        'api': True,
        'database': True,
        'authentication': True,
        'market_data': True,
        'order_execution': True
    }
    
    # Check database connection
    try:
        db_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook', 'trading_signals.db')
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        statuses['database'] = False
    
    # For a real implementation, you would check other services as well
    
    return statuses

def get_user_api_keys(user_id):
    """Get API keys for a user from the database"""
    try:
        db_path = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Users', 'users.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT capital_key, capital_secret, capital_demo, webhook_key
            FROM user_api_keys
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            api_keys = dict(row)
        else:
            # Return empty keys if none found
            api_keys = {
                'capital_key': '',
                'capital_secret': '',
                'capital_demo': True,
                'webhook_key': ''
            }
        
        conn.close()
        return api_keys
    except Exception as e:
        logger.error(f"Error getting API keys: {str(e)}")
        # Return empty keys on error
        return {
            'capital_key': '',
            'capital_secret': '',
            'capital_demo': True,
            'webhook_key': ''
        }

def get_instruments_db_path():
    return os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook', 'trading_signals.db')

def init_instruments_table():
    db_path = get_instruments_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instruments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            risk_percent REAL NOT NULL,
            stop_loss TEXT NOT NULL,
            take_profit TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_instruments_table()

@dashboard_bp.route('/api/instruments', methods=['GET'])
def api_list_instruments():
    db_path = get_instruments_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM instruments ORDER BY name')
    instruments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'data': instruments})

@dashboard_bp.route('/api/instruments', methods=['POST'])
def api_add_instrument():
    data = request.json or {}  # Use empty dict as fallback if request.json is None
    db_path = get_instruments_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO instruments (name, risk_percent, stop_loss, take_profit, enabled)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data.get('name'),
        float(data.get('risk_percent', 0)),
        data.get('stop_loss'),
        data.get('take_profit'),
        1 if data.get('enabled', True) else 0
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@dashboard_bp.route('/api/instruments/<int:instrument_id>', methods=['PUT'])
def api_update_instrument(instrument_id):
    data = request.json or {}  # Use empty dict as fallback if request.json is None
    db_path = get_instruments_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE instruments SET name=?, risk_percent=?, stop_loss=?, take_profit=?, enabled=? WHERE id=?
    ''', (
        data.get('name'),
        float(data.get('risk_percent', 0)),
        data.get('stop_loss'),
        data.get('take_profit'),
        1 if data.get('enabled', True) else 0,
        instrument_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@dashboard_bp.route('/api/instruments/<int:instrument_id>', methods=['DELETE'])
def api_delete_instrument(instrument_id):
    db_path = get_instruments_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM instruments WHERE id=?', (instrument_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Example route
@dashboard_bp.route('/overview')
def overview():
    """
    Render the dashboard overview page.

    Returns:
        str: Rendered HTML template for the overview page.
    """
    try:
        logger.info("Rendering dashboard overview page.")
        return render_template('overview.html')
    except Exception as e:
        logger.error(f"Error rendering overview page: {e}")
        flash("An error occurred while loading the overview page.", "error")
        return redirect(url_for('dashboard.index'))

# Example: Advanced backtest endpoint for dashboard analytics
@dashboard_bp.route('/api/advanced_backtest', methods=['POST'])
@permission_required('view_analytics')
def advanced_backtest():
    """
    Run an advanced backtest using PerformanceMonitor and return results for analytics.
    Expects JSON: {"strategy": "example_strategy", "params": {...}, "data": ...}
    """
    import pandas as pd
    try:
        req = request.get_json() or {}  # Use empty dict as fallback if request.json is None
        strategy_name = req.get('strategy')
        params = req.get('params', {})
        data = req.get('data')
        
        # Use direct import instead of dynamic function import
        # from src.AI.example_strategies import get_strategy_fn
        # strategy_fn = get_strategy_fn(strategy_name)
        
        # Use the imported strategy directly
        df = pd.DataFrame(data) if data else pd.DataFrame()
        monitor = PerformanceMonitor(jamso_ai_bot_strategy, df, params)
        result = monitor.run_backtest()
        payload = monitor.to_dashboard_payload()
        return jsonify({'success': True, 'result': payload})
    except Exception as e:
        logger.error(f"Advanced backtest error: {e}")
        return jsonify({'success': False, 'error': str(e)})
