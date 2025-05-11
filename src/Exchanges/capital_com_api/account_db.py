"""Module for accessing selected account from the database."""

import os
import json
import sqlite3
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Database path for selected accounts
DB_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Credentials/credentials.db'
# Fallback paths for legacy compatibility
LEGACY_CONFIG_DIR = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Credentials'
LEGACY_ACCOUNT_FILE = os.path.join(LEGACY_CONFIG_DIR, 'active_account.json')

def get_active_account_from_db() -> Optional[Dict[str, Any]]:
    """Retrieve the most recently selected account from the database.
    
    Returns:
        A dictionary containing the account information with the structure:
        {
            'account': {
                'accountId': str,
                'accountName': str,
                'balance': {'balance': float},
                'currency': str
            },
            'server': str
        }
        
    Note:
        Returns None if no account is found in the database.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='selected_accounts'")
        if not cursor.fetchone():
            logger.warning("selected_accounts table doesn't exist in the database yet")
            return _load_legacy_account()
            
        # Get the most recent account entry
        cursor.execute('''
            SELECT account_id, account_name, server, balance, currency 
            FROM selected_accounts 
            ORDER BY created_at DESC LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            logger.warning("No active account found in database")
            return _load_legacy_account()
            
        # Format the account data to match expected structure
        account_data = {
            'account': {
                'accountId': row[0],
                'accountName': row[1],
                'balance': {'balance': row[3]},
                'currency': row[4]
            },
            'server': row[2]
        }
        
        logger.info(f"Retrieved active account from database: {account_data['account']['accountName']} on {account_data['server']}")
        return account_data
        
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving active account: {e}")
        return _load_legacy_account()
    except Exception as e:
        logger.error(f"Error retrieving active account from database: {e}")
        return _load_legacy_account()

def _load_legacy_account() -> Optional[Dict[str, Any]]:
    """Load account from legacy JSON file as fallback."""
    try:
        # Use the legacy JSON file if available
        if os.path.exists(LEGACY_ACCOUNT_FILE):
            logger.warning(f"Falling back to legacy account file: {LEGACY_ACCOUNT_FILE}")
            with open(LEGACY_ACCOUNT_FILE, 'r') as f:
                data = json.load(f)
                if not data.get('server'):
                    logger.error("Server URL missing in legacy account configuration")
                    return None
                return data
        return None
    except Exception as e:
        logger.error(f"Error loading legacy account file: {e}")
        return None

def get_server_url() -> str:
    """Get the server URL for the Capital.com API.
    
    Returns:
        The server URL from the active account, or the demo server URL as fallback.
    """
    # Default to demo server if we can't get the account
    DEFAULT_DEMO_SERVER = "https://demo-api-capital.backend-capital.com"
    
    active_account = get_active_account_from_db()
    if active_account and active_account.get('server'):
        return active_account['server']
    
    logger.warning(f"No active account server found, using default demo server: {DEFAULT_DEMO_SERVER}")
    return DEFAULT_DEMO_SERVER
