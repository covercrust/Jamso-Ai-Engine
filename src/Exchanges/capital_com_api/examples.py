"""
Example usage of the Capital API Client.
"""

import os
import logging
from typing import Dict, Any, List

# Import required modules
from src.Exchanges.capital_com_api.client import Client
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.account_config import AccountConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_credentials() -> Dict[str, str]:
    """Load credentials from the database or fallback to environment variables"""
    try:
        # Import database utilities
        from src.Credentials.credentials import get_api_credentials
        from src.Exchanges.capital_com_api.account_db import get_server_url
        
        # Get API credentials
        credentials = get_api_credentials()
        
        # Get server URL from database
        server = get_server_url()
        
        logger.info("Loaded credentials and server URL from database")
        return {
            "api_key": credentials["api_key"],
            "username": credentials["username"],
            "password": credentials["password"],
            "server": server
        }
    except Exception as e:
        logger.warning(f"Failed to load credentials from database: {e}")
        
        # Fallback to environment variables
        api_key = os.getenv("CAPITAL_API_KEY", "")
        username = os.getenv("CAPITAL_USERNAME", "")
        password = os.getenv("CAPITAL_PASSWORD", "")
        server = os.getenv("CAPITAL_SERVER", "https://demo-api-capital.backend-capital.com")
        
        # Try account config as last resort
        if not all([api_key, username, password]):
            try:
                account_config = AccountConfig()
                if not api_key:
                    api_key = account_config.api_key
                if not username:
                    username = account_config.username
                if not password:
                    password = account_config.password
                if not server:
                    server = account_config.server
            except Exception as e2:
                logger.warning(f"Failed to load credentials from account config: {e2}")
        
        return {
            "api_key": api_key,
            "username": username,
            "password": password,
            "server": server
        }

def main():
    try:
        # Load credentials
        creds = load_credentials()
        
        # Initialize the SessionManager with credentials
        session_manager = SessionManager(
            server=creds["server"],
            api_key=creds["api_key"],
            username=creds["username"],
            password=creds["password"]
        )
        
        # Initialize the RequestHandler
        request_handler = RequestHandler()
        
        # Initialize the client with required arguments
        client = Client(session_manager, request_handler)
        
        # Ensure we're authenticated
        if not session_manager.is_authenticated:
            session_manager.create_session()
            
        logger.info("Client initialized successfully")
        
        # Fetch all accounts using the account_manager
        accounts_response = client.account_manager.load_accounts()
        accounts = accounts_response
        
        if not accounts:
            logger.warning("No accounts found")
            return
            
        logger.info(f"Found {len(accounts)} accounts")
        
        # Change active account to the first one
        account_id = accounts[0].get("accountId")
        if account_id:  # Check if account_id is not None before passing to set_active_account
            client.account_manager.set_active_account(account_id)
            logger.info(f"Changed active account to: {account_id}")
        else:
            logger.error("Failed to get account ID from the first account")
            return
        
        # Create a new position for TSLA using position_manager
        epic = "TSLA"
        direction = "BUY"
        size = 1.0  # Smaller position size for safety
        
        logger.info(f"Creating {direction} position for {epic}, size: {size}")
        position_response = client.position_manager.create_position(epic, direction, size)
        
        deal_reference = position_response.get("dealReference")
        if not deal_reference:
            logger.error("Failed to get deal reference")
            return
            
        logger.info(f"Position created with deal reference: {deal_reference}")
        
        # Wait for confirmation - using the position_manager to get deal status
        confirmation = client.position_manager.position_details(deal_reference)
        deal_id = confirmation.get("dealId")
        if not deal_id:
            logger.error("Failed to get deal ID")
            return
            
        logger.info(f"Position confirmed with deal ID: {deal_id}")
        
        # Fetch all positions
        positions = client.position_manager.all_positions()
        logger.info(f"Current positions: {positions}")
        
        # Update the position (add stop loss)
        logger.info(f"Updating position: {deal_id}")
        update_response = client.position_manager.update_position(deal_id=deal_id, stopLevel=90.0)
        logger.info(f"Position updated: {update_response}")
        
        # Close the position
        logger.info(f"Closing position: {deal_id}")
        close_response = client.position_manager.close_position(deal_id=deal_id)
        profit = close_response.get("profit", 0)
        logger.info(f"Position closed with profit: ${profit}")
        
    except Exception as e:
        logger.error(f"Error in example: {e}", exc_info=True)

if __name__ == "__main__":
    main()