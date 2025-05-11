"""
Integration test for MarketDataManager.
"""

import logging
import os
import sys
import json
from typing import Dict, Any, Tuple

# Fix import issue by adding the project root to the Python path
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now imports should work correctly
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.market_data_manager import MarketDataManager
from src.Credentials.credentials import get_api_credentials
from src.Credentials.credentials_manager import CredentialManager
from src.Exchanges.capital_com_api.account_db import get_active_account_from_db

# Configure paths
ROOT_DIR = PROJECT_ROOT

# Configure logging
log_file_path = f'{ROOT_DIR}/Logs/integration_test_market_data_manager.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(log_file_path)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Database path for selected accounts
DB_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Credentials/credentials.db'

def get_account_from_db() -> Dict[str, Any]:
    """Retrieve the most recently selected account from the database."""
    try:
        # Use the shared implementation
        account_data = get_active_account_from_db()
        if account_data:
            logger.info(f"Retrieved active account from database: {account_data['account']['accountName']} on {account_data['server']}")
        else:
            logger.warning("No active account found in database")
        
        return account_data
        
    except Exception as e:
        logger.error(f"Error retrieving active account from database: {e}")
        return {
            'server': 'https://demo-api-capital.backend-capital.com',
            'account': {'accountName': 'Demo Account'}
        }

def load_configuration() -> Tuple[Dict[str, str], Dict[str, Any]]:
    """Load credentials and account configuration from database."""
    try:
        # Get API credentials from the database
        api_credentials = get_api_credentials()
        logger.info("Loaded credentials from the database.")
        
        # Get active account from database
        active_account = get_account_from_db()
        
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
    """Main execution function."""
    session_manager = None
    request_handler = None
    market_data_manager = None
    
    try:
        # Load configuration from database
        api_credentials, active_account = load_configuration()
        logger.info("Configuration loaded successfully from database.")

        # Initialize components
        try:
            request_handler = RequestHandler()
            
            session_manager = SessionManager(
                server=active_account.get('server', 'https://demo-api-capital.backend-capital.com').rstrip('/'),
                api_key=api_credentials['api_key'],
                username=api_credentials['username'],
                password=api_credentials['password']
            )

            market_data_manager = MarketDataManager(
                session_manager=session_manager,
                request_handler=request_handler
            )
            
            # Test market data operations
            logger.info("Testing market data operations...")
            # Add your test operations here
            try:
                # Test fetching market data for AAPL
                epic = "AAPL"
                
                # Get market details using the correct method name
                session_manager.create_session()
                market_details = market_data_manager.market_details(epic)
                logger.info(f"Market details fetched for {epic}: {market_details}")
                
                # Test fetching market details again
                session_manager.create_session()
                market_details = market_data_manager.market_details(epic)
                logger.info(f"Market details fetched for {epic}: {market_details}")
                
                # Test single market details
                session_manager.create_session()
                single_market = market_data_manager.single_market_details(epic)
                logger.info(f"Single market details fetched for {epic}: {single_market}")
                
                # Test price history
                session_manager.create_session()
                price_history = market_data_manager.prices(epic)
                logger.info(f"Price history fetched for {epic}: {price_history}")
                
                # Test client sentiment
                session_manager.create_session()
                sentiment = market_data_manager.client_sentiment(epic)
                logger.info(f"Client sentiment fetched for {epic}: {sentiment}")
            except Exception as e:
                logger.error(f"Error during market data operations: {e}")
                raise
            
        except Exception as e:
            logger.error(f"Error during market data operations: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)
        
    finally:
        # Cleanup
        if session_manager is not None:
            try:
                session_manager.end_session()
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