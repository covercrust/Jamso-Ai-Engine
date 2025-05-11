import os
import sys

# Fix import issue by adding the project root to the Python path
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.Exchanges.capital_com_api.account_config import AccountConfig

def integration_test_account_config():
    """Integration test for AccountConfig functionality."""
    print("Starting integration test for AccountConfig...")

    # Initialize AccountConfig
    try:
        account_config = AccountConfig()
        print("AccountConfig initialized successfully.")
    except ValueError as e:
        print(f"Environment validation failed: {e}")
        return

    # Test server and account ID
    try:
        server = account_config.get_server()
        account_id = account_config.get_account_id()
        print(f"Server: {server}")
        print(f"Account ID: {account_id}")
    except ValueError as e:
        print(f"Error retrieving server or account ID: {e}")
        return

    # Test connection to API server
    print("Testing connection to the API server...")
    connection_result = account_config.test_connection()
    if connection_result:
        print("Connection test passed.")
    else:
        print("Connection test failed.")

    # Authenticate
    print("Authenticating...")
    try:
        account_config.authenticate()
        print("Authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    print("Integration test for AccountConfig completed.")

if __name__ == "__main__":
    integration_test_account_config()