from pathlib import Path
# integration_test_account_manager.py
import logging
import os
import sys
import json
import time  # Add time module import
import subprocess
from typing import Dict, Any

# Configure paths
ROOT_DIR = '/home/jamso-ai-server/Jamso-Ai-Engine'
# Fix import issue by adding the project root to the Python path
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now imports should work correctly

from src.Exchanges.capital_com_api.account_manager import AccountManager
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.FileHandler(f'{ROOT_DIR}/Logs/integration_test_account_manager.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def source_env_file(env_file: str) -> None:
    """Source environment variables"""
    try:
        command = f"source {env_file} && env"
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        
        # Handle potential None output from subprocess
        if proc.stdout is None:
            logger.error("Failed to get output from subprocess")
            return

        # Safely iterate over subprocess output
        for line in iter(proc.stdout.readline, b''):
            try:
                decoded_line = line.decode('utf-8')
                if '=' in decoded_line:
                    key, value = decoded_line.strip().split('=', 1)
                    os.environ[key] = value
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode line from environment: {line}")
                continue

        # Ensure process completes
        proc.stdout.close()
        proc.wait()

        if proc.returncode != 0:
            logger.error(f"Environment sourcing failed with return code {proc.returncode}")
            
    except Exception as e:
        logger.error(f"Error sourcing environment file: {str(e)}")

def load_active_account(active_account_path: str) -> Dict[str, str]:
    """Load active account from database or fallback to JSON file."""
    try:
        # First try to get from database
        try:
            # Import here to avoid circular imports
            from src.Exchanges.capital_com_api.account_db import get_active_account_from_db
            
            # Get account from database
            account_data = get_active_account_from_db()
            
            # Validate account data
            if account_data and account_data.get('server') and account_data.get('account', {}).get('accountId'):
                logger.info(f"Loaded active account from database: {json.dumps(account_data, indent=2)}")
                return account_data
            else:
                logger.warning("Invalid or incomplete account data from database, trying fallback")
        except Exception as e:
            logger.error(f"Failed to load account from database: {e}, trying fallback")
        
        # Fallback to JSON file
        if not os.path.exists(active_account_path):
            raise FileNotFoundError(f"Active account file {active_account_path} not found.")
        
        with open(active_account_path, 'r') as file:
            account_details = json.load(file)
            logger.info(f"Loaded active account details from file: {json.dumps(account_details, indent=2)}")
            return account_details
    except Exception as e:
        logger.error(f"Failed to load active account: {e}")
        raise

def load_configuration() -> Dict[str, Any]:
    """Load configuration from database or env.sh and active_account.json."""
    try:
        # Use our utility functions for fetching credentials
        from src.Credentials.credentials import get_api_credentials
        
        # Try to get API credentials from database first
        try:
            credentials = get_api_credentials()
            logger.info(f"Loaded API credentials from database: {list(credentials.keys())}")
            
            # Map the credential names to what the test expects
            os.environ['CAPITAL_API_KEY'] = credentials['api_key']
            os.environ['CAPITAL_API_LOGIN'] = credentials['username']
            os.environ['CAPITAL_API_PASSWORD'] = credentials['password']
            
            # Debug output
            logger.info(f"API Key (first 4 chars): {credentials['api_key'][:4]}...")
            logger.info(f"Username: {credentials['username']}")
            logger.info(f"Environment variables set: {[key for key in os.environ.keys() if 'CAPITAL' in key]}")
        except Exception as db_err:
            logger.error(f"Failed to load credentials from database: {db_err}, falling back to environment")
            # Source environment variables as fallback
            source_env_file(f'{ROOT_DIR}/src/Credentials/env.sh')
            
            # Create credentials dict from environment variables
            credentials = {
                'api_key': os.getenv('CAPITAL_API_KEY'),
                'username': os.getenv('CAPITAL_API_LOGIN'),
                'password': os.getenv('CAPITAL_API_PASSWORD')
            }
        
        # Load active account from database, with file fallback
        try:
            # Import here to avoid circular imports
            from src.Exchanges.capital_com_api.account_db import get_active_account_from_db
            
            # Get account from database
            active_account = get_active_account_from_db()
            if active_account:
                logger.info(f"Retrieved active account from database: {active_account['account'].get('accountName')} on {active_account['server']}")
            else:
                # Fallback to file
                active_account_path = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Credentials/active_account.json'
                active_account = load_active_account(active_account_path)
                logger.info(f"Retrieved active account from file")
        except Exception as e:
            logger.warning(f"Failed to get active account from database: {e}")
            # Final fallback
            active_account_path = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Credentials/active_account.json'
            active_account = load_active_account(active_account_path)
        
        # Return both credentials and active account
        return {
            'credentials': credentials,
            'active_account': active_account
        }
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise
    
    # Combine data
    config = {
        'CAPITAL_API_KEY': os.environ.get('CAPITAL_API_KEY'),
        'CAPITAL_API_LOGIN': os.environ.get('CAPITAL_API_LOGIN'),
        'CAPITAL_API_PASSWORD': os.environ.get('CAPITAL_API_PASSWORD'),
        'server': active_account.get('server', 'default_server'),  # Provide a default value or handle appropriately
        'active_account': active_account
    }
    
    # Validate required environment variables
    for key in ['CAPITAL_API_KEY', 'CAPITAL_API_LOGIN', 'CAPITAL_API_PASSWORD']:
        if not config.get(key):
            logger.error(f"Required environment variable {key} is not available in config")
            raise ValueError(f"Required environment variable {key} is not set")
        logger.debug(f"Loaded env var: {key}={config[key][:4]}...")
    
    return config

def cleanup_resources(session_manager, request_handler):
    """Cleanup resources properly."""
    if session_manager is not None:
        try:
            session_manager.end_session()  # Use end_session() instead of log_out()
            logger.info("Session ended successfully")
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            
    if request_handler is not None:
        try:
            request_handler.close_session()
            logger.info("Request handler session closed")
        except Exception as e:
            logger.error(f"Error closing request handler session: {e}")

def main():
    """Main execution function."""
    session_manager = None
    request_handler = None
    account_manager = None
    
    try:
        # Load configuration
        config_data = load_configuration()
        logger.debug("Configuration loaded successfully")
        
        # Extract credentials and active account from config data
        credentials = config_data['credentials']
        active_account = config_data['active_account']
        
        # Build the final config
        config = {
            'CAPITAL_API_KEY': credentials['api_key'],
            'CAPITAL_API_LOGIN': credentials['username'],
            'CAPITAL_API_PASSWORD': credentials['password'],
            'server': active_account.get('server', 'default_server'),
            'active_account': active_account
        }
        
        # Debug output to verify config values
        logger.info(f"Using API Key (first 4 chars): {config['CAPITAL_API_KEY'][:4]}...")
        logger.info(f"Using username: {config['CAPITAL_API_LOGIN']}")
        logger.info(f"Server URL: {config['server']}")
        
        # Initialize request handler with retry mechanism
        request_handler = RequestHandler()
        request_handler.update_headers({
            "X-CAP-API-KEY": config['CAPITAL_API_KEY'],
            "Content-Type": "application/json"
        })
        
        # Initialize SessionManager
        session_manager = SessionManager(
            server=config['server'],
            api_key=config['CAPITAL_API_KEY'],
            username=config['CAPITAL_API_LOGIN'],
            password=config['CAPITAL_API_PASSWORD']
        )
        
        # Create initial session with retry
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                session_manager.create_session()
                logger.info("Session created successfully")
                break
            except CapitalAPIException as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.warning(f"Rate limit hit, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise
        
        # Initialize AccountManager
        account_manager = AccountManager(
            session_manager=session_manager
        )
        
        # Test account operations
        try:
            logger.info("Testing account operations...")
            
            # Test account manager functions with delays between calls
            logger.info("Testing load_accounts...")
            time.sleep(1)  # Rate limiting protection
            account_list = account_manager.load_accounts()
            if not account_list:
                raise Exception("No accounts returned")
            logger.info("Fetched account list successfully")
            
            account_manager.get_active_account()
            logger.info("Active account retrieved")
            
            _ = account_manager.load_accounts()
            logger.info("All accounts retrieved")
        except Exception as e:
            logger.error(f"Error during account operations: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)
    finally:
        cleanup_resources(session_manager, request_handler)

if __name__ == "__main__":
    main()
