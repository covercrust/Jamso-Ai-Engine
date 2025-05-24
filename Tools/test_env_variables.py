#!/usr/bin/env python3
"""
Test script for checking Capital.com API credentials from both
secure database and environment variables.
"""

import os
import sys
import logging
from pathlib import Path

# Get the base directory dynamically
def get_base_dir():
    """Get the base directory dynamically."""
    # First check from environment variable
    if "ROOT_DIR" in os.environ:
        return Path(os.environ["ROOT_DIR"])
    
    # Next try to determine from script location
    script_path = Path(__file__).resolve()
    # Go up one level from Tools/test_env_variables.py
    return script_path.parent.parent

# Set up base directory and add to path
BASE_DIR = get_base_dir()
sys.path.append(str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EnvTester")

print("Testing environment variable loading")
print("===================================")

print("1. Testing dotenv import...")
try:
    from dotenv import load_dotenv
    print("✅ dotenv module imported successfully")
except ImportError:
    print("❌ dotenv module not found")
    sys.exit(1)

print("\n2. Loading environment variables...")
try:
    load_dotenv()  # Load environment variables from .env file if it exists
    print("✅ load_dotenv() called without errors")
except Exception as e:
    print(f"❌ Error loading environment variables: {e}")

print("\n3. Checking for Capital.com API credentials...")
# Check environment variables
env_key = os.environ.get('CAPITAL_API_KEY')
env_login = os.environ.get('CAPITAL_API_LOGIN')
env_password = os.environ.get('CAPITAL_API_PASSWORD')

if env_key:
    print("✅ CAPITAL_API_KEY found in environment")
else:
    print("❌ CAPITAL_API_KEY not found in environment")

if env_login:
    print("✅ CAPITAL_API_LOGIN found in environment")
else:
    print("❌ CAPITAL_API_LOGIN not found in environment")

if env_password:
    print("✅ CAPITAL_API_PASSWORD found in environment")
else:
    print("❌ CAPITAL_API_PASSWORD not found in environment")

print("\n4. Checking secure credential database...")
try:
    from src.Credentials.credentials_manager import CredentialManager
    credential_manager = CredentialManager()
    
    db_key = credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY')
    db_login = credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN')
    db_password = credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')
    
    if db_key:
        print("✅ CAPITAL_API_KEY found in credential database")
    else:
        print("❌ CAPITAL_API_KEY not found in credential database")
    
    if db_login:
        print("✅ CAPITAL_API_LOGIN found in credential database")
    else:
        print("❌ CAPITAL_API_LOGIN not found in credential database")
    
    if db_password:
        print("✅ CAPITAL_API_PASSWORD found in credential database")
    else:
        print("❌ CAPITAL_API_PASSWORD not found in credential database")
    
    print("\nCredential Database Status: " + ("✅ OPERATIONAL" if (db_key or db_login or db_password) else "❌ NOT ACCESSIBLE OR EMPTY"))
    
except Exception as e:
    print(f"❌ Error accessing credential database: {e}")
    print("\nCredential Database Status: ❌ ERROR")

print("\n5. Checking .env file location...")
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    print(f"✅ .env file found at: {env_file}")
    if os.access(env_file, os.R_OK | os.W_OK):
        print("✅ .env file has correct read/write permissions")
    else:
        print("❌ .env file permissions issue")
else:
    print(f"❌ .env file not found at: {env_file}")

print("\n===================================")
print("Environment test completed")

sys.exit(0)
