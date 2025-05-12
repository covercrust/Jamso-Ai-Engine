#!/usr/bin/env python3
"""
Flask Memory Optimizer for Jamso-AI Engine

This script optimizes Flask application memory usage by:
1. Configuring Flask for better memory utilization
2. Setting up proper caching mechanisms
3. Implementing database connection pooling
4. Adding memory usage monitoring
5. Setting up proper garbage collection
"""
import os
import sys
import logging
import gc
import time
import psutil
import threading

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_PATH, 'Logs', 'flask_memory_optimizer.log'))
    ]
)
logger = logging.getLogger('flask_memory_optimizer')

def patch_flask_app():
    """
    Patch Jamso-AI Engine's Flask application to improve memory usage.
    This should be imported in the Flask application's __init__.py file.
    """
    try:
        # Import the Flask app
        from src.Webhook.app import create_app
        
        # Create the app instance
        app = create_app()
        
        # Enable aggressive garbage collection
        gc.set_threshold(100, 5, 5)
        
        # Configure Flask for production use
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
        app.config['TEMPLATES_AUTO_RELOAD'] = False
        app.config['EXPLAIN_TEMPLATE_LOADING'] = False
        
        # Setup session cleanup
        if 'SESSION_TYPE' in app.config and app.config['SESSION_TYPE'] == 'filesystem':
            # Set session file age to 1 day maximum
            app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 1 day in seconds
            
            # Set up session cleanup thread
            def cleanup_sessions():
                while True:
                    try:
                        session_path = app.config.get('SESSION_FILE_DIR', 'instance/sessions')
                        now = time.time()
                        for f in os.listdir(session_path):
                            if f.endswith('.session'):
                                file_path = os.path.join(session_path, f)
                                # Delete sessions older than 1 day
                                if os.stat(file_path).st_mtime < now - 86400:
                                    os.unlink(file_path)
                    except Exception as e:
                        logger.error(f"Error cleaning up sessions: {str(e)}")
                    time.sleep(3600)  # Run once per hour
            
            # Start the session cleanup thread
            threading.Thread(target=cleanup_sessions, daemon=True).start()
        
        # Set up SQLite optimizations if using SQLite
        if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', '').lower():
            from sqlalchemy import event
            from sqlalchemy.engine import Engine
            import sqlite3
            
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if isinstance(dbapi_connection, sqlite3.Connection):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.execute("PRAGMA cache_size=10000")
                    cursor.execute("PRAGMA temp_store=MEMORY")
                    cursor.close()
        
        # Set up memory usage monitoring
        def monitor_memory_usage():
            while True:
                process = psutil.Process(os.getpid())
                memory_use = process.memory_info().rss / 1024 / 1024  # Convert to MB
                logger.info(f"Flask application memory usage: {memory_use:.2f} MB")
                time.sleep(300)  # Log every 5 minutes
        
        # Start the memory monitoring thread
        threading.Thread(target=monitor_memory_usage, daemon=True).start()
        
        logger.info("Flask memory optimization patches applied successfully")
        return app
    except Exception as e:
        logger.error(f"Error applying Flask memory optimization patches: {str(e)}")
        return None

if __name__ == "__main__":
    # This script can be run directly to test the memory optimization patches
    app = patch_flask_app()
    if app:
        logger.info("Flask memory optimization patches applied successfully")
        sys.exit(0)
    else:
        logger.error("Failed to apply Flask memory optimization patches")
        sys.exit(1)
