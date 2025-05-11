from flask import Flask, request, jsonify, current_app, g, redirect, send_from_directory, url_for, session, flash
from functools import wraps
import logging
import json
from datetime import datetime
import os
import threading
import time
import signal
import sys
import subprocess

# Import utilities directly from the package
from src.Webhook import (
    get_client,
    get_position_details,
    execute_trade,
    save_signal,
    save_trade_result,
    get_db,
    WEBHOOK_TOKEN
)

# Import error handling utilities
from src.Webhook.utils import create_error_response, handle_request_error, jsonify_error

# Import rate limiting utility
from src.Optional.rate_limiter import rate_limit

logger = logging.getLogger('webhook')

def init_server_control_watcher(app: Flask):
    """Initialize a background thread to watch for server control files"""
    # Flag to indicate if trading should be paused
    app.config['TRADING_PAUSED'] = False
    
    # Set up the file paths
    restart_file = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'tmp', 'restart.txt')
    stop_trading_file = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'tmp', 'stop_trading.txt')
    restart_script = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'tmp', 'restart_server.sh')
    
    def check_control_files():
        """Background thread function to check for control files"""
        logger.info("Server control file watcher started")
        while True:
            try:
                # Check for stop trading file
                if os.path.exists(stop_trading_file):
                    logger.warning("Stop trading file detected, setting trading_paused flag to True")
                    app.config['TRADING_PAUSED'] = True
                    # Rename the file to avoid processing it multiple times
                    os.rename(stop_trading_file, stop_trading_file + ".processed")
                    logger.info(f"Renamed {stop_trading_file} to {stop_trading_file}.processed")
                
                # Check for restart file
                if os.path.exists(restart_file):
                    logger.warning("Restart file detected, server will restart")
                    # Rename the file to avoid processing it multiple times
                    os.rename(restart_file, restart_file + ".processed")
                    logger.info(f"Renamed {restart_file} to {restart_file}.processed")
                    
                    # Different restart methods depending on environment
                    if app.debug:
                        # In debug mode, start the independent restart script
                        logger.info("Debug mode detected, using independent restart script")
                        # Launch the restart script in a completely separate process
                        # Using nohup to ensure it runs even if parent process terminates
                        subprocess.Popen(
                            ["nohup", restart_script, "&"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL, 
                            stdin=subprocess.DEVNULL,
                            start_new_session=True,  # Creates a new process group
                            shell=False  # More reliable as separate args
                        )
                        # Exit with a short delay to allow restart script to launch
                        logger.info("Exiting current process for restart...")
                        time.sleep(0.5)  # Brief delay
                        os._exit(0)  # Clean exit
                    else:
                        # Production mode - touch restart.txt for passenger
                        logger.info("Production mode detected, using passenger restart mechanism")
                        passenger_restart = os.path.join('/home/jamso-ai-server/Jamso-Ai-Engine', 'tmp', 'restart.txt')
                        with open(passenger_restart, 'w') as f:
                            f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                        logger.info(f"Created Passenger restart file: {passenger_restart}")
                        # No need to exit in production as Passenger handles the restart
            
            except Exception as e:
                logger.error(f"Error in server control file watcher: {str(e)}")
            
            # Sleep for a short time before next check
            time.sleep(5)
    
    # Start the watcher thread
    watcher_thread = threading.Thread(target=check_control_files, daemon=True)
    watcher_thread.start()
    logger.info("Server control file watcher thread started")

def init_routes(app: Flask):
    """Initialize routes for the Flask app"""
    
    # Initialize file watcher for server control
    init_server_control_watcher(app)
    
    # Add a root route to serve as a health check and tunnel test
    @app.route('/')
    def index():
        """Root endpoint that serves as a health check and tunnel test"""
        logger.info("Root endpoint called - server is healthy")
        # Redirect to dashboard instead of just returning JSON
        return redirect('/dashboard/')

    # Add a static file handler for dashboard static files
    @app.route('/dashboard/static/<path:filename>')
    def dashboard_static(filename):
        """Serve dashboard static files directly"""
        dashboard_static_folder = os.path.join(os.path.dirname(__file__), 'dashboard', 'static')
        return send_from_directory(dashboard_static_folder, filename)
    
    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_token = request.headers.get('X-Trading-Token')
            
            # Direct token comparison
            if not auth_token or auth_token != WEBHOOK_TOKEN:
                return jsonify_error(create_error_response(
                    message="Authentication required",
                    error_code="UNAUTHORIZED",
                    status_code=401
                ))
            return f(*args, **kwargs)
        return decorated

    @app.route('/webhook', methods=['POST'])
    @require_auth
    @rate_limit(limit=20, window=60)  # 20 requests per minute
    def webhook():
        """Handles incoming webhook requests from TradingView"""
        logger.info("Webhook endpoint called")
        
        try:
            # Log raw request data for debugging
            logger.debug(f"Request headers: {dict(request.headers)}")
            logger.debug(f"Request data: {request.get_data(as_text=True)}")
            
            # Try multiple ways to get the data
            data = None
            if request.is_json:
                data = request.get_json(silent=True)
                logger.debug("Parsed JSON data from request.is_json")
            
            if not data and request.data:
                try:
                    data = json.loads(request.data.decode('utf-8'))
                    logger.debug("Parsed JSON data from request.data")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    return jsonify_error(create_error_response(
                        message="Invalid JSON format", 
                        error_code="JSON_PARSE_ERROR"
                    ))
            
            if not data and request.form:
                data = dict(request.form)
                logger.debug("Got data from request.form")
            
            if not data:
                logger.error('No data received in any format')
                return jsonify_error(create_error_response(
                    message="No data received", 
                    error_code="NO_DATA"
                ))
            
            logger.info(f"Received webhook data: {data}")
            
            # Check if trading is paused
            if app.config.get('TRADING_PAUSED', False):
                logger.warning("Trade rejected: Trading is currently paused by admin")
                return jsonify_error(create_error_response(
                    message="Trading is currently paused by administrator",
                    error_code="TRADING_PAUSED",
                    details={"order_id": data.get('order_id', 'unknown')}
                ))
            
            # Use our enhanced validation system
            from src.Webhook.validators import validate_webhook_data
            validation_errors = validate_webhook_data(data)
            
            if validation_errors:
                logger.error(f"Validation errors: {validation_errors}")
                return jsonify_error(create_error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    details={"errors": validation_errors}
                ))

            # Remove webhook token if present
            data.pop('X-Webhook-Token', None)
            
            # Initialize client and execute trade
            client = get_client()
            
            # Map webhook fields to database fields
            order_id = data.get('order_id')
            symbol = data.get('ticker')
            direction = data.get('order_action')
            quantity = float(data.get('position_size', 0))
            price = float(data.get('price', 0))
            
            # Save signal to database BEFORE executing trade
            with app.app_context():
                db = get_db()
                # Store trade information in signals table with both original and mapped fields
                cursor = db.execute(
                    'INSERT INTO signals (order_id, symbol, direction, quantity, price, signal_data, trade_action, trade_direction, position_size) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                        order_id,
                        symbol,
                        direction,
                        quantity,
                        price,
                        json.dumps(data),
                        order_id,
                        direction,
                        quantity
                    )
                )
                signal_id = cursor.lastrowid
                db.commit()
                logger.info(f"Signal saved with ID: {signal_id}")
            
            # Execute the trade
            result = execute_trade(client, data)
            
            # Check if result contains error status
            if isinstance(result, dict) and result.get('status') == 'error':
                error_msg = result.get('message', 'Unknown error during trade execution')
                error_code = result.get('code', 'EXECUTION_ERROR')
                logger.error(f"Trade execution failed: {error_msg}")
                
                # Update signal with error
                with app.app_context():
                    db = get_db()
                    db.execute(
                        'UPDATE signals SET status = ?, error = ? WHERE id = ?',
                        ('failed', error_msg, signal_id)
                    )
                    db.commit()
                    
                return jsonify_error(create_error_response(
                    message=error_msg,
                    error_code=error_code,
                    details={"order_id": data['order_id']}
                ))
            
            # Update signal with deal ID from successful trade
            deal_reference = result.get('dealReference') if isinstance(result, dict) else None
            
            with app.app_context():
                db = get_db()
                db.execute(
                    'UPDATE signals SET status = ?, deal_id = ? WHERE id = ?',
                    ('success', deal_reference, signal_id)
                )
                db.commit()
            
            # Prepare response
            response_data = {
                'status': 'success',
                'order_id': data['order_id'],
                'deal_reference': deal_reference,
                'trade_details': {
                    'action': data['order_action'],
                    'size': data['position_size'],
                    'ticker': data['ticker']
                }
            }
            
            logger.info(f"Trade executed successfully: {response_data}")
            return jsonify(response_data), 200
            
        except ValueError as ve:
            return jsonify_error(handle_request_error(ve, 400))
        except Exception as e:
            return jsonify_error(handle_request_error(e))

    @app.route('/webhook/tradingview', methods=['POST'])
    @require_auth
    @rate_limit(limit=20, window=60)  # 20 requests per minute
    def tradingview_webhook():
        """Specific endpoint for TradingView signals"""
        try:
            if not request.is_json:
                return jsonify_error(create_error_response(
                    message="Content-Type must be application/json",
                    error_code="INVALID_CONTENT_TYPE",
                    status_code=415
                ))

            data = request.get_json()
            logger.info(f"TradingView signal received: {data}")

            # Use our enhanced validation system
            from src.Webhook.validators import validate_webhook_data
            validation_errors = validate_webhook_data(data)
            
            if validation_errors:
                logger.error(f"Validation errors: {validation_errors}")
                return jsonify_error(create_error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    details={"errors": validation_errors}
                ))

            # Initialize client before database operations
            client = get_client()
            
            # Database operations within app context
            with app.app_context():
                db = get_db()
                signal_id = save_signal(db, data)
                result = execute_trade(client, data)
                
                # Check if result contains error status
                if isinstance(result, dict) and result.get('status') == 'error':
                    error_msg = result.get('message', 'Unknown error during trade execution')
                    error_code = result.get('code', 'EXECUTION_ERROR')
                    logger.error(f"Trade execution failed: {error_msg}")
                    return jsonify_error(create_error_response(
                        message=error_msg,
                        error_code=error_code,
                        details={"signal_id": signal_id}
                    ))
                
                position_id = save_trade_result(db, signal_id, result)

                return jsonify({
                    "status": "success",
                    "signal_id": signal_id,
                    "position_id": position_id,
                    "deal_reference": result.get('dealReference'),
                    "timestamp": datetime.utcnow().isoformat()
                }), 200

        except Exception as e:
            return jsonify_error(handle_request_error(e))

    @app.route('/close_position', methods=['POST'])
    @rate_limit(limit=10, window=60)  # 10 requests per minute (more restrictive for trade closing)
    def close_position():
        """Handles requests to close positions on Capital.com."""
        logger.info("Close position endpoint called")
        
        try:
            # Parse the JSON data
            try:
                data = request.get_json(force=True)
            except json.JSONDecodeError as e:
                return jsonify_error(create_error_response(
                    message="Invalid JSON format", 
                    error_code="JSON_PARSE_ERROR"
                ))
                
            if not data:
                return jsonify_error(create_error_response(
                    message="No data received", 
                    error_code="NO_DATA"
                ))
                
            logger.info(f"Received close position data: {data}")
            
            # Use our enhanced validation for close position data
            from src.Webhook.validators import validate_close_position_data
            validation_errors = validate_close_position_data(data)
            
            if validation_errors:
                logger.error(f"Validation errors: {validation_errors}")
                return jsonify_error(create_error_response(
                    message="Validation failed",
                    error_code="VALIDATION_ERROR",
                    details={"errors": validation_errors}
                ))

            # Get the validated fields
            order_id = data.get('order_id')
            size = float(data.get('size', 1))  # Default to closing the entire position

            # Retrieve the deal ID using the order ID
            with app.app_context():
                db = get_db()
                cursor = db.execute('SELECT deal_id FROM signals WHERE order_id = ?', (order_id,))
                row = cursor.fetchone()
                if not row:
                    return jsonify_error(create_error_response(
                        message="No deal ID found for the given order ID",
                        error_code="DEAL_ID_NOT_FOUND",
                        details={"order_id": order_id}
                    ))
                deal_id = row[0]

            logger.debug(f"Retrieved deal ID: {deal_id}")

            # Ensure the session token is valid
            client = get_client()
            client.session_manager.create_session()

            # Retrieve position details to get the direction and epic
            position_details = get_position_details(client, deal_id)
            position = position_details.get('position')
            if not position:
                return jsonify_error(create_error_response(
                    message="No position details found for the given deal ID",
                    error_code="POSITION_NOT_FOUND",
                    details={"deal_id": deal_id}
                ))

            direction = position['direction']
            epic = position['market']['epic']

            # Determine the opposite direction
            opposite_direction = 'SELL' if direction == 'BUY' else 'BUY'

            # Close the position by placing an opposite trade with force_open=False
            close_position_response = client.create_position(
                epic=epic,
                direction=opposite_direction,
                size=size,
                order_type='MARKET',
                force_open=False  # Closing the existing position
            )

            logger.debug(f"Close position response: {close_position_response}")

            # Validate the response
            if isinstance(close_position_response, dict) and close_position_response.get('status') == 'error':
                error_msg = close_position_response.get('message', 'Unknown error during position closure')
                error_code = close_position_response.get('code', 'CLOSE_POSITION_FAILED')
                return jsonify_error(create_error_response(
                    message=error_msg,
                    error_code=error_code,
                    details={"deal_id": deal_id}
                ))

            close_deal_reference = close_position_response.get('dealReference', '')
            if not close_deal_reference:
                return jsonify_error(create_error_response(
                    message="No deal reference received when closing the position",
                    error_code="MISSING_DEAL_REFERENCE"
                ))

            logger.info(f"Position closed successfully for deal ID: {deal_id}")
            return jsonify({
                'status': 'success',
                'deal_id': deal_id,
                'close_deal_reference': close_deal_reference,
                'response': close_position_response
            }), 200
            
        except Exception as e:
            return jsonify_error(handle_request_error(e))

    # Add stylesheets route
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        """Serve CSS files from the static/css folder"""
        static_folder = os.path.join(os.path.dirname(__file__), 'static', 'css')
        return send_from_directory(static_folder, filename)
    
    # Add JavaScript route
    @app.route('/js/<path:filename>')
    def serve_js(filename):
        """Serve JavaScript files from the static/js folder"""
        static_folder = os.path.join(os.path.dirname(__file__), 'static', 'js')
        return send_from_directory(static_folder, filename)
    
    # Add a max stop loss value endpoint
    @app.route('/api/max_stop_loss_value')
    def max_stop_loss_value():
        """Get the maximum stop loss value"""
        return jsonify({
            "max_stop_loss_value": 178.01
        })
    
    # Add accounts endpoint 
    @app.route('/api/accounts')
    def accounts():
        """Get available trading accounts"""
        mode = request.args.get('mode', 'live')
        return jsonify([
            {
                "id": "123456",
                "name": "Demo Account",
                "balance": 10000,
                "currency": "USD" 
            }
        ])
