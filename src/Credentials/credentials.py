#!/usr/bin/env python3
"""
Credentials management for the Jamso AI Server
This module handles loading and retrieving API credentials for exchange connections.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from src.Credentials.credentials_manager import CredentialManager

logger = logging.getLogger(__name__)

# Ensure all credentials are fetched dynamically from the database
credential_manager = CredentialManager()

def load_credentials_from_db() -> bool:
    """Load credentials dynamically from the database."""
    try:
        credentials = {
            'CAPITAL_API_KEY': credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY'),
            'CAPITAL_API_LOGIN': credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN'),
            'CAPITAL_API_PASSWORD': credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD'),
            'username': credential_manager.get_credential('capital_com', 'username')  # Add username field
        }
        os.environ.update(credentials)
        logger.info("Loaded credentials from the database.")
        return True
    except Exception as e:
        logger.error(f"Error loading credentials from the database: {e}")
        return False

def load_credentials() -> bool:
    """
    Load credentials from environment variables or configuration files.
    Returns True if credentials were successfully loaded.
    """
    # Check if credentials are already loaded
    if os.environ.get('CAPITAL_COM_API_KEY') and os.environ.get('CAPITAL_COM_API_PASSWORD'):
        logger.info("Credentials already loaded in environment")
        return True
    
    # Try to load from the database
    if load_credentials_from_db():
        return True
    
    logger.error("Failed to load credentials")
    return False

# Ensure the `username` field is properly fetched and validated
def get_api_credentials() -> Dict[str, str]:
    try:
        credentials = {
            'CAPITAL_API_KEY': credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY'),
            'CAPITAL_API_LOGIN': credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN'),
            'CAPITAL_API_PASSWORD': credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD'),
            'username': credential_manager.get_credential('capital_com', 'username')  # Add username field
        }

        # Map credential keys to the ones expected by the API client
        api_credentials = {
            'api_key': credentials['CAPITAL_API_KEY'],
            'username': credentials['username'] or credentials['CAPITAL_API_LOGIN'],  # Fallback to login if username is not set
            'password': credentials['CAPITAL_API_PASSWORD']
        }
        
        # Debug log for credential values
        logger.debug(f"Retrieved and mapped API credentials successfully")

        # Validate credentials
        missing_fields = [key for key, value in api_credentials.items() if not value]
        if missing_fields:
            logger.error(f"Missing or invalid credentials for fields: {', '.join(missing_fields)}")
            raise ValueError(f"Missing or invalid credentials for fields: {', '.join(missing_fields)}")

        return api_credentials
    except Exception as e:
        logger.error(f"Error loading credentials from the database: {e}")
        raise

def get_server_url() -> str:
    """
    Get the server URL for the Capital.com API from the active account in the database.
    """
    try:
        # Import here to avoid circular imports
        from src.Exchanges.capital_com_api.account_db import get_server_url as get_capital_server_url
        return get_capital_server_url()
    except Exception as e:
        logger.error(f"Error getting server URL from database: {e}")
        # Fallback to a default value if database access fails
        return os.environ.get('DEMO_API_BASE_URL', 'https://demo-api-capital.backend-capital.com')
