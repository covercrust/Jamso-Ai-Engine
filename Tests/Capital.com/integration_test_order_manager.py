# integration_test_order_manager.py
import logging
import os
import sys
import json
import subprocess
from typing import Dict, Any, Tuple, Optional, Mapping

# Fix import issue by adding the project root to the Python path
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now imports should work correctly
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.order_manager import OrderManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException

# Configure logging
log_file_path = f'{PROJECT_ROOT}/Logs/integration_test_order_manager.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure paths
ROOT_DIR = PROJECT_ROOT

# Import credentials utils
from src.Credentials.credentials import get_api_credentials
from src.Credentials.credentials_manager import CredentialManager

# Database path for selected accounts
DB_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Credentials/credentials.db'

def get_account_from_db() -> Optional[Dict[str, Any]]:
    """Retrieve the most recently selected account from the database."""
    try:
        # Import from our shared utility
        from src.Exchanges.capital_com_api.account_db import get_active_account_from_db
        
        # Use the shared implementation
        account_data = get_active_account_from_db()
        if account_data:
            logger.info(f"Retrieved active account from database: {account_data['account']['accountName']} on {account_data['server']}")
        else:
            logger.warning("No active account found in database")
        
        return account_data
        
    except Exception as e:
        logger.error(f"Error retrieving active account from database: {e}")
        return None

def load_configuration() -> Tuple[Dict[str, str], Dict[str, Any]]:
    """Load and validate all required configuration from database"""
    try:
        # Get API credentials from the database
        api_credentials = get_api_credentials()
        logger.info("Loaded credentials from the database.")
        
        # Get active account from database
        active_account = get_account_from_db()
        
        # If no active account in database, use default demo server
        if not active_account:
            logger.warning("No active account found in database, using default demo server")
            active_account = {
                'server': 'https://demo-api-capital.backend-capital.com'
            }
        
        # Log credential status (without exposing sensitive information)
        for key in api_credentials:
            value = api_credentials[key]
            if value:
                masked_value = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '****'
                logger.debug(f"Loaded credential: {key}={masked_value}")
        
        return api_credentials, active_account
    except Exception as e:
        logger.error(f"Error loading configuration from the database: {e}")
        raise

def main():
    """Main function to test order management."""
    session_manager = None
    request_handler = None
    order_manager = None
    
    try:
        api_credentials, active_account = load_configuration()
        logger.info("Configuration loaded successfully from database.")

        # Check if account data is available
        account_id = active_account.get('account', {}).get('accountId')
        if not active_account.get('server') or not account_id:
            logger.warning("Server URL or Account ID is missing in active account data. Will use demo account.")
            active_account['server'] = 'https://demo-api-capital.backend-capital.com'
            # Continue without account ID, will use default account

        # Initialize components
        request_handler = RequestHandler()
        
        session_manager = SessionManager(
            server=active_account['server'].rstrip('/'),
            api_key=api_credentials['api_key'],
            username=api_credentials['username'],
            password=api_credentials['password']
        )

        order_manager = OrderManager(
            session_manager=session_manager,
            request_handler=request_handler
        )

        # Test fetching all positions (instead of working orders)
        try:
            positions = order_manager.get_positions()
            print("All positions fetched successfully:", positions)
            logger.info("All positions fetched successfully")
        except CapitalAPIException as e:
            logger.error("Error fetching positions: %s", e)
            print(f"Error fetching positions: {e}")

        # Test creating a new order (instead of working order)
        try:
            epic = "AAPL"  # Replace with a valid epic
            direction = "BUY"
            size = 1.0
            logger.info(f"Creating order: epic={epic}, direction={direction}, size={size}")
            # Use create_order instead of create_working_order
            create_order_response = order_manager.create_order(
                epic=epic, 
                direction=direction, 
                size=size, 
                order_type="MARKET"
            )
            print("Order created successfully:", create_order_response)
            logger.info("Order created successfully")
        except Exception as e:
            logger.error("Error creating order: %s", e)
            print(f"Error creating order: {e}")

    except CapitalAPIException as e:
        logger.error(f"API Exception occurred: {e}")
    except Exception as e:
        logger.error(f"Error during session management: {e}")
    finally:
        # Proper cleanup using correct method names
        if session_manager is not None:
            try:
                session_manager.end_session()  # Use end_session instead of log_out
                logger.info("Session ended successfully")
            except Exception as e:
                logger.error(f"Error ending session: {e}")
                
        if request_handler is not None:
            try:
                request_handler.close_session()
                logger.info("Request handler session closed")
            except Exception as e:
                logger.error(f"Error closing request handler session: {e}")

if __name__ == "__main__":
    main()