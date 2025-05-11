#!/usr/bin/env python3
"""
Simple test script to load modules and check for errors.
"""

import logging
import os
import sys
import json

# Configure paths using relative paths for better portability
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)  # Add project root to path before imports

from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException
from src.Credentials.credentials_manager import CredentialManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{ROOT_DIR}/Logs/simple_test.log'),
        logging.StreamHandler(sys.stdout)  # Add stdout handler to ensure we see logs
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Simple test function."""
    try:
        # Initialize CredentialManager
        logger.info("Creating CredentialManager instance")
        credential_manager = CredentialManager()
        
        # Try to get a credential
        logger.info("Trying to get a credential")
        api_key = credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY')
        logger.info(f"Got API key: {'*' * (len(api_key) if api_key else 0)}")
        
        # Initialize RequestHandler
        logger.info("Creating RequestHandler instance")
        request_handler = RequestHandler()
        
        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
