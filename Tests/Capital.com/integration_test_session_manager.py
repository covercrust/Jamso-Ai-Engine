# integration_test_session_manager.py

import os
import sys
import json
import logging
import unittest
import sqlite3
import subprocess
from typing import Dict, Any, Tuple, Optional

# Add project root to Python path
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.insert(0, PROJECT_ROOT)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(f'{PROJECT_ROOT}/Logs/integration_test_session_manager.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Check dependencies
def check_dependencies():
    """Check and install required dependencies"""
    try:
        import Crypto
    except ImportError:
        logger.info("Installing pycryptodome package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome"])
        logger.info("pycryptodome installed successfully")

# Check dependencies before imports
check_dependencies()

from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException
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

class TestSessionManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment"""
        cls.api_credentials, cls.active_account = load_configuration()
        logger.debug("Test environment initialized")

    def setUp(self):
        """Initialize test environment"""
        # Get the server URL from the active_account or use default
        server_url = self.active_account.get('server', 'https://demo-api-capital.backend-capital.com')
        
        # Debug info
        logger.debug(f"Initializing session manager with server: {server_url}")
        
        self.session_manager = SessionManager(
            server=server_url.rstrip('/'),
            api_key=self.api_credentials['api_key'],
            username=self.api_credentials['username'],
            password=self.api_credentials['password']
        )

    def test_session_creation(self):
        """Test session creation"""
        self.session_manager.create_session()
        logger.debug(f"Session token: {getattr(self.session_manager, 'session_token', None)}")
        logger.debug(f"Is authenticated: {self.session_manager.is_authenticated}")
        self.assertTrue(self.session_manager.is_authenticated)
        logger.info("Session created successfully")

    def test_account_fetching(self):
        """Test account list fetching"""
        self.session_manager.create_session()
        accounts = self.session_manager.fetch_account_list()
        self.assertTrue(len(accounts) > 0)
        logger.info(f"Retrieved {len(accounts)} accounts")

    def test_session_logout(self):
        """Test session logout"""
        self.session_manager.create_session()
        self.session_manager.end_session()  # Changed from log_out to end_session
        self.assertFalse(self.session_manager.is_authenticated)
        logger.info("Logged out successfully")

    def tearDown(self):
        """Cleanup after each test"""
        if self.session_manager.is_authenticated:
            self.session_manager.end_session()  # Changed from log_out to end_session

def main():
    """Main execution function."""
    session_manager = None
    try:
        # Load configuration from database
        api_credentials, active_account = load_configuration()
        logger.info("Configuration loaded successfully from database.")

        # Get the server URL
        server_url = active_account.get('server', 'https://demo-api-capital.backend-capital.com')
        logger.debug(f"Using server URL: {server_url}")

        # Initialize session manager
        session_manager = SessionManager(
            server=server_url.rstrip('/'),
            api_key=api_credentials['api_key'],
            username=api_credentials['username'],
            password=api_credentials['password']
        )

        # Quick test: create session and check authentication
        result = session_manager.create_session()
        logger.debug(f"Authentication result: {result}")
        
        if session_manager.is_authenticated:
            logger.info("Authentication successful")
            
            # Test account fetching
            accounts = session_manager.fetch_account_list()
            logger.info(f"Retrieved {len(accounts)} accounts")
            
            # End the session
            session_manager.end_session()
            logger.info("Session ended successfully")
        else:
            logger.error("Authentication failed")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    finally:
        if session_manager is not None and session_manager.is_authenticated:
            try:
                session_manager.end_session()
                logger.info("Session ended")
            except Exception as e:
                logger.error(f"Error ending session: {e}")

if __name__ == '__main__':
    try:
        # Manual test
        logger.info("Running manual test...")
        
        # Load configuration
        api_credentials, active_account = load_configuration()
        
        # Print loaded credentials and account info
        logger.info(f"API Credentials: {', '.join(api_credentials.keys())}")
        logger.info(f"Active Account: {active_account}")
        
        # Run main test
        main()
        
        # Run unittest
        unittest.main(verbosity=2)
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        sys.exit(1)