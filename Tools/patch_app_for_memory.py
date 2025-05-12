#!/usr/bin/env python3
"""
Patch Script for Memory Optimization

This script patches the Webhook app.py file to include memory optimizations.
"""
import os
import sys
import fileinput
import re
import logging
from pathlib import Path

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_PATH, 'Logs', 'patch_script.log'))
    ]
)
logger = logging.getLogger('patch_script')

def patch_app_py():
    """Patch the app.py file to include memory optimizations"""
    app_py_path = os.path.join(BASE_PATH, 'src', 'Webhook', 'app.py')
    
    if not os.path.exists(app_py_path):
        logger.error(f"File not found: {app_py_path}")
        return False
    
    # Backup the original file
    backup_path = f"{app_py_path}.bak"
    try:
        with open(app_py_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Backup created at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return False
    
    # Add memory optimization imports
    try:
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Add import for gc (garbage collection)
        import_pattern = r'import threading\nimport requests\nimport logging'
        if import_pattern in content:
            replacement = 'import threading\nimport requests\nimport logging\nimport gc'
            content = content.replace(import_pattern, replacement)
            
            # Add memory optimization in create_app function
            app_config_pattern = r'    # Ensure the instance folder exists\n    os.makedirs\(app.instance_path, exist_ok=True\)'
            if app_config_pattern in content:
                optimization_code = """    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Optimize memory usage
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    app.config['EXPLAIN_TEMPLATE_LOADING'] = False
    
    # Set up more aggressive garbage collection
    gc.set_threshold(100, 5, 5)"""
                
                content = content.replace(app_config_pattern, optimization_code)
            
            # Add database connection pooling setting
            db_init_pattern = r'    # Initialize database\n    with app.app_context\(\):\n        init_db\(app\)'
            if db_init_pattern in content:
                db_optimization_code = """    # Initialize database
    # Configure database for connection pooling
    app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
    
    with app.app_context():
        init_db(app)"""
                
                content = content.replace(db_init_pattern, db_optimization_code)
            
            # Write the modified content back to the file
            with open(app_py_path, 'w') as f:
                f.write(content)
            
            logger.info("Successfully patched app.py with memory optimizations")
            return True
        else:
            logger.error("Could not find the import pattern in app.py")
            return False
    except Exception as e:
        logger.error(f"Error patching app.py: {str(e)}")
        # Restore the backup
        try:
            with open(backup_path, 'r') as src, open(app_py_path, 'w') as dst:
                dst.write(src.read())
            logger.info("Restored original file from backup")
        except Exception as restore_error:
            logger.error(f"Failed to restore backup: {str(restore_error)}")
        return False

if __name__ == "__main__":
    logger.info("Starting app.py patching for memory optimization")
    if patch_app_py():
        print("Successfully patched app.py with memory optimizations")
        sys.exit(0)
    else:
        print("Failed to patch app.py. Check log for details.")
        sys.exit(1)
