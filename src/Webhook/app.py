#!/usr/bin/env python3
from flask import Flask, jsonify, request, Blueprint
from flask_login import LoginManager
from flask_cors import CORS
import os
import psutil
import sys
from functools import wraps
import time
import termios
import subprocess
import threading
import requests
import logging

from src.Logging.logger import get_logger, timing_decorator, configure_root_logger
from src.Webhook.database import init_db
from src.Webhook.routes import init_routes
from src.Webhook.config import Config
# Import dashboard blueprint
from Dashboard.controllers.dashboard_controller import dashboard_bp
from Dashboard.auth.auth_controller import auth_bp
# Import dashboard integration
from Dashboard.dashboard_integration import setup_dashboard

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

def kill_process_on_port(port):
    """Kill any process using the specified port, excluding the current process."""
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port and proc.info['pid'] != current_pid:
                    os.kill(proc.info['pid'], 9)
                    print(f"Killed process {proc.info['name']} (PID: {proc.info['pid']}) using port {port}.")
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

def is_interactive():
    """Check if the environment is interactive."""
    try:
        termios.tcgetattr(sys.stdin)
        return True
    except termios.error:
        return False

def create_app(test_config=None):
    # Create and configure the app
    # Set dashboard's static folder as the app's static folder for direct static file access
    dashboard_static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Dashboard', 'static')
    app = Flask(__name__, 
                instance_relative_config=True,
                static_folder=dashboard_static_folder,
                static_url_path='/static')
    
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_object(Config)
        # SECRET_KEY is now always a string (see config.py)
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
    
    # Properly setup dashboard and its static files
    # This handles blueprints registration, so we don't need to register them again
    if setup_dashboard(app):
        logger.info("Dashboard integration successful")
    else:
        logger.warning("Dashboard integration failed, some features may not work correctly")
    
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
    
    # Define routes to handle direct static file requests (for compatibility)
    # Remove these specific routes as they're now handled in dashboard_integration.py
    
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

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"}), 200

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

# Delay before starting health monitoring to allow Flask app initialization
INITIAL_DELAY = 30  # Increased from 10 to 30 seconds
HEALTH_CHECK_INTERVAL = 20  # Increased from 10 to 20 seconds
MAX_RESTART_ATTEMPTS = 3
RESTART_COOLDOWN = 60  # seconds

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("health_monitor")

def monitor_health():
    """Monitor the health of the Flask app and restart if unresponsive."""
    logger.info(f"Health monitoring will start in {INITIAL_DELAY} seconds to allow app initialization")
    time.sleep(INITIAL_DELAY)  # Wait before starting health checks
    
    restart_attempts = 0
    last_restart_time = 0
    
    while True:
        current_time = time.time()
        
        # Check if we need to reset the restart counter (after cooldown period)
        if (current_time - last_restart_time) > RESTART_COOLDOWN and restart_attempts > 0:
            logger.info(f"Cooldown period passed. Resetting restart attempts counter from {restart_attempts} to 0")
            restart_attempts = 0
        
        try:
            logger.info("Performing health check...")
            response = requests.get("http://127.0.0.1:5000/health", timeout=15)  # Increased timeout
            if response.status_code == 200:
                logger.info("Health check passed.")
                # Reset restart counter after successful health check
                if restart_attempts > 0:
                    restart_attempts = 0
                    logger.info("Reset restart attempts to 0 after successful health check.")
            else:
                logger.warning(f"Health check failed with status code {response.status_code}.")
                if restart_attempts < MAX_RESTART_ATTEMPTS:
                    restart_attempts += 1
                    last_restart_time = current_time
                    logger.warning(f"Restarting Flask app (attempt {restart_attempts}/{MAX_RESTART_ATTEMPTS})...")
                    restart_flask_app()
                else:
                    logger.error(f"Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached. Waiting for manual intervention.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check request failed: {e}.")
            if restart_attempts < MAX_RESTART_ATTEMPTS:
                restart_attempts += 1
                last_restart_time = current_time
                logger.warning(f"Restarting Flask app (attempt {restart_attempts}/{MAX_RESTART_ATTEMPTS})...")
                restart_flask_app()
            else:
                logger.error(f"Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached. Waiting for manual intervention.")
        
        # Sleep before next check
        logger.debug(f"Sleeping for {HEALTH_CHECK_INTERVAL} seconds before next health check")
        time.sleep(HEALTH_CHECK_INTERVAL)

def restart_flask_app():
    """Restart the Flask app by killing the process on port 5000."""
    port = 5000
    current_pid = os.getpid()
    found_process = False
    
    logger.info(f"Attempting to restart Flask app (port {port})...")
    
    # Find and kill the process on the specified port
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port and proc.info['pid'] != current_pid:
                    found_process = True
                    proc_name = proc.info['name']
                    proc_pid = proc.info['pid']
                    proc_cmdline = ' '.join(proc.info['cmdline'] if proc.info['cmdline'] else [])
                    
                    logger.info(f"Found process using port {port}: {proc_name} (PID: {proc_pid}, CMD: {proc_cmdline})")
                    
                    try:
                        os.kill(proc_pid, 9)
                        logger.info(f"Successfully killed process (PID: {proc_pid}) using port {port}")
                    except Exception as e:
                        logger.error(f"Failed to kill process: {e}")
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess) as e:
            logger.warning(f"Error accessing process information: {e}")
            continue
    
    if not found_process:
        logger.warning(f"No process found using port {port}")
        
    # Give port time to be released
    logger.info("Waiting for port to be released...")
    time.sleep(5)

def monitor_and_restart():
    """Monitor the Flask app and restart it if it crashes."""
    logger.info("Starting Flask app monitoring...")
    while True:
        try:
            # Start Flask app as a subprocess
            logger.info("Starting Flask app as a subprocess...")
            process = subprocess.Popen(
                ['python', '-m', 'src.Webhook.app'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Log the PID for debugging
            logger.info(f"Flask app started with PID: {process.pid}")
            
            # Wait for the process to complete (should only happen if it crashes)
            stdout, stderr = process.communicate()
            
            # Log process exit
            if process.returncode != 0:
                logger.error(f"Flask app crashed with return code {process.returncode}")
                if stderr:
                    logger.error(f"Error output: {stderr.decode()}")
                logger.info("Waiting 10 seconds before restarting...")
                time.sleep(10)  # Wait before restarting
            else:
                logger.info(f"Flask app exited normally with return code {process.returncode}")
                logger.info("Waiting 5 seconds before restarting...")
                time.sleep(5)  # Shorter wait for normal exit
                
        except Exception as e:
            logger.error(f"Error monitoring Flask app: {e}")
            logger.info("Waiting 10 seconds before retrying...")
            time.sleep(10)

if __name__ == "__main__":
    # Only start the health monitoring thread if we're directly running the script
    # and not when it's imported as a module
    app = create_app()
    
    # Configure logging for the main process
    logger.info("Starting Jamso AI Webhook server...")
    
    # Start health monitoring in a daemon thread
    health_monitor_thread = threading.Thread(target=monitor_health, daemon=True)
    health_monitor_thread.start()
    logger.info("Health monitoring thread started")
    
    # If running in direct/interactive mode, start the Flask app directly
    if is_interactive():
        logger.info("Running in interactive mode. Starting Flask app directly.")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        # Otherwise, use the monitor_and_restart function to keep the app running
        logger.info("Running in non-interactive mode. Using monitor_and_restart.")
        monitor_and_restart()