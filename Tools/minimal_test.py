#!/usr/bin/env python3
"""
Extremely simple test script to load modules.
"""

import os
import sys

# Add the project root to the path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

# Import the modules one by one with try/except to see which one fails
try:
    print("Importing src.Credentials.credentials_manager")
    from src.Credentials.credentials_manager import CredentialManager
    print("Successfully imported CredentialManager")
except Exception as e:
    print(f"Failed to import CredentialManager: {e}")

try:
    print("Importing src.Exchanges.capital_com_api.session_manager")
    from src.Exchanges.capital_com_api.session_manager import SessionManager
    print("Successfully imported SessionManager")
except Exception as e:
    print(f"Failed to import SessionManager: {e}")

try:
    print("Importing src.Exchanges.capital_com_api.request_handler")
    from src.Exchanges.capital_com_api.request_handler import RequestHandler
    print("Successfully imported RequestHandler")
except Exception as e:
    print(f"Failed to import RequestHandler: {e}")

try:
    print("Creating CredentialManager instance")
    cm = CredentialManager()
    print("Successfully created CredentialManager instance")
except Exception as e:
    print(f"Failed to create CredentialManager instance: {e}")

try:
    print("Getting a credential")
    api_key = cm.get_credential('capital_com', 'CAPITAL_API_KEY')
    print(f"Successfully got a credential: {'*' * (len(api_key) if api_key else 0)}")
except Exception as e:
    print(f"Failed to get a credential: {e}")

print("Test completed")
