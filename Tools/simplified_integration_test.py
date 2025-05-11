#!/usr/bin/env python3
"""
Simplified version of the integration test.
"""

import logging
import os
import sys
import json

# Configure paths using relative paths for better portability
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)  # Add project root to path before imports

# Import the modules
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException
from src.Credentials.credentials_manager import CredentialManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Just log to stdout for now
    ]
)
logger = logging.getLogger(__name__)

# Path to active account JSON file
ACTIVE_ACCOUNT_PATH = f'{ROOT_DIR}/src/Credentials/active_account.json'

def load_active_account(active_account_path: str) -> dict:
    """Load active account details from file."""
    try:
        if not os.path.exists(active_account_path):
            raise FileNotFoundError(f"Active account file not found: {active_account_path}")
        
        with open(active_account_path, 'r') as f:
            data = json.load(f)
            logger.debug(f"Loaded active account data from file: {json.dumps(data, indent=2)}")
            
            # Get server and account ID
            server = data.get("server")
            account_id = data.get("accountId") or data.get("account", {}).get("accountId")
            
            if not server:
                raise ValueError("Server URL missing in active_account.json")
            if not account_id:
                raise ValueError("Account ID missing in active_account.json")
            
            return {
                "server": server,
                "accountId": account_id
            }
    except Exception as e:
        logger.error(f"Failed to load active account: {e}")
        raise

def main():
    """Main test function."""
    try:
        # Initialize CredentialManager
        logger.info("Creating CredentialManager instance")
        credential_manager = CredentialManager()
        
        # Load credentials from the database
        logger.info("Loading credentials")
        credentials = {
            'CAPITAL_API_KEY': credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY') or '',
            'CAPITAL_API_LOGIN': credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN') or '',
            'CAPITAL_API_PASSWORD': credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD') or ''
        }
        
        # Update environment variables
        os.environ.update(credentials)
        logger.info("Loaded credentials from the database.")
        
        # Validate environment variables
        missing_vars = [key for key, value in credentials.items() if not value]
        if missing_vars:
            logger.warning(f"Missing credentials: {', '.join(missing_vars)}")
        
        # Load active account configuration
        logger.info("Loading active account configuration")
        try:
            active_account = load_active_account(ACTIVE_ACCOUNT_PATH)
            logger.info(f"Loaded active account configuration: {active_account}")
        except Exception as e:
            logger.warning(f"Failed to load active account, using default: {e}")
            active_account = {
                "server": "https://demo-api-capital.backend-capital.com",
                "accountId": "demo"
            }
        
        # Initialize components
        logger.info("Initializing RequestHandler")
        request_handler = RequestHandler()
        
        logger.info("Initializing SessionManager")
        session_manager = SessionManager(
            server=active_account['server'].rstrip('/'),
            api_key=credentials['CAPITAL_API_KEY'],
            username=credentials['CAPITAL_API_LOGIN'],
            password=credentials['CAPITAL_API_PASSWORD']
        )
        
        # Log authentication info (mask sensitive data)
        logger.info(f"Using server: {active_account['server']}")
        logger.info(f"Using account ID: {active_account['accountId']}")
        logger.info(f"API key length: {len(credentials['CAPITAL_API_KEY']) if credentials['CAPITAL_API_KEY'] else 0}")
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
