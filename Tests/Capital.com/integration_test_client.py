import logging
import os
import sys
import json

# Fix import issue by adding the project root to the Python path
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now imports should work correctly
from src.Exchanges.capital_com_api.client import Client
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Credentials.credentials import get_api_credentials

# Configure logging
log_file_path = f'{PROJECT_ROOT}/Logs/integration_test_client.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(log_file_path)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def load_active_account(file_path: str) -> dict:
    """Load the active account details from database or fallback to JSON file."""
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
        if not os.path.exists(file_path):
            logger.error(f"Active account file {file_path} does not exist.")
            raise FileNotFoundError(f"Active account file {file_path} not found.")
        
        with open(file_path, 'r') as file:
            account_details = json.load(file)
            logger.info(f"Loaded active account details from file: {json.dumps(account_details, indent=2)}")
            return account_details
    except Exception as e:
        logger.error(f"Failed to load active account: {e}")
        raise

def load_configuration():
    """Load environment variables and active account configuration from database."""
    try:
        # Use our utility functions for fetching credentials
        from src.Credentials.credentials import get_api_credentials
        
        # Get API credentials from database
        credentials = get_api_credentials()
        
        # Validate API key
        if not credentials.get('api_key'):
            raise ValueError("API key not found in credentials")
        
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
        
        logger.info("Configuration loaded successfully")
        return credentials, active_account
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

def main():
    """Main execution function."""
    session_manager = None
    request_handler = None
    
    try:
        # Load configuration
        env_vars, active_account = load_configuration()
        logger.info("Environment variables sourced successfully.")

        # Initialize components
        request_handler = RequestHandler()
        
        session_manager = SessionManager(
            server=active_account['server'].rstrip('/'),
            api_key=env_vars['api_key'],
            username=env_vars['username'],
            password=env_vars['password']
        )

        # Test API operations
        try:
            # Your test code here
            logger.info("Starting API tests...")
            # ...test operations...
            
        except Exception as e:
            logger.error(f"Error during API testing: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)
        
    finally:
        # Proper cleanup using the correct method names
        if session_manager is not None:
            try:
                # Use end_session instead of logout/log_out
                session_manager.end_session()
                logger.info("Session ended successfully")
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")
                
        if request_handler is not None:
            try:
                request_handler.close_session()
                logger.info("Request handler session closed")
            except Exception as e:
                logger.error(f"Error closing request handler session: {e}")

if __name__ == "__main__":
    main()