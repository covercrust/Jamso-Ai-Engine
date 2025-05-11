#!/usr/bin/env python3
"""
Environment Variables Checker for Capital.com API

This utility script checks if the required environment variables are set.
Run this script to diagnose missing environment variables.
"""

import os
import sys
import json
from pathlib import Path

# Get the base directory dynamically
def get_base_dir():
    """Get the base directory dynamically."""
    # First check from environment variable
    if "ROOT_DIR" in os.environ:
        return Path(os.environ["ROOT_DIR"])
    
    # Next try to determine from script location
    script_path = Path(__file__).resolve()
    # Go up three levels from src/Credentials/
    return script_path.parent.parent.parent.parent

# Base directory
BASE_DIR = get_base_dir()

# Required environment variables
REQUIRED_ENV_VARS = [
    'CAPITAL_API_KEY',
    'CAPITAL_API_LOGIN',
    'CAPITAL_API_PASSWORD'
]

def check_env_vars():
    """Check for required environment variables"""
    missing = []
    present = []
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            present.append(var)
    
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("\nPlease set these variables in your environment or in your env.sh file.")
        print("Example env.sh content:")
        print("------------------------")
        print('export CAPITAL_API_KEY="your_api_key"')
        print('export CAPITAL_API_LOGIN="your_username"')
        print('export CAPITAL_API_PASSWORD="your_password"')
        print("------------------------")
        print("\nYou can create or edit the env.sh file at:")
        env_path = os.path.join(BASE_DIR, 'Backend', 'Utils', 'Config', 'env.sh')
        print(f"{env_path}")
        print("\nFor a guided setup, run:")
        setup_path = os.path.join(BASE_DIR, 'Backend', 'Utils', 'setup_env.py')
        print(f"python {setup_path}")
        print("\nThen source it with: source env.sh")
        return False
    else:
        print("✅ All required environment variables are set.")
        # Show masked values
        for var in REQUIRED_ENV_VARS:
            value = os.getenv(var)
            # Add null check before using len()
            if value and len(value) > 8:
                masked = value[0:4] + '*' * (len(value) - 8) + value[-4:]
            else:
                masked = '****'
            print(f"{var}: {masked}")
        return True

def load_env_file():
    """Load environment variables from env.sh"""
    env_file = os.path.join(BASE_DIR, 'Backend', 'Utils', 'Config', 'env.sh')
    
    if not os.path.exists(env_file):
        print(f"WARNING: Environment file not found: {env_file}")
        print("Run the setup utility to create it:")
        setup_path = os.path.join(BASE_DIR, 'Backend', 'Utils', 'setup_env.py')
        print(f"python {setup_path}")
        return False
    
    print(f"Loading environment variables from {env_file}")
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if 'export' in line:
                    line = line.replace('export', '').strip()
                    
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    # Remove quotes if present
                    value = value.strip().strip('"\'')
                    os.environ[key] = value
                    
        print(f"Successfully loaded variables from {env_file}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to load environment file: {e}")
        return False

def check_active_account():
    """Check if active account configuration exists and is valid"""
    account_file = os.path.join(BASE_DIR, 'Backend', 'Utils', 'Config', 'active_account.json')
    
    if not os.path.exists(account_file):
        print(f"WARNING: Active account file not found: {account_file}")
        return False
    
    try:
        with open(account_file) as f:
            config = json.load(f)
            
        # Verify required fields
        if 'server' not in config:
            print("ERROR: Missing 'server' in active account configuration")
            return False
            
        if 'account' not in config:
            print("ERROR: Missing 'account' in active account configuration")
            return False
            
        account = config['account']
        if 'accountId' not in account:
            print("ERROR: Missing 'accountId' in active account configuration")
            return False
            
        print("✅ Active account configuration is valid:")
        print(f"  Server: {config['server']}")
        print(f"  Account ID: {account['accountId']}")
        return True
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in active account file: {account_file}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to check active account: {e}")
        return False

if __name__ == "__main__":
    print("Capital.com API Environment Checker")
    print("--------------------------------------------")
    
    # First check if active account config exists
    print("\nChecking active account configuration...")
    account_valid = check_active_account()
    
    # Then check current environment
    print("\nChecking current environment variables...")
    env_valid = check_env_vars()
    
    # If missing, try to load from env file
    if not env_valid:
        print("\nAttempting to load variables from env.sh file...")
        if load_env_file() and check_env_vars():
            print("\nSuccessfully loaded missing variables from env.sh")
            env_valid = True
    
    # Summary and recommendations
    print("\n--------------------------------------------")
    print("Summary:")
    print(f"- Active account configuration: {'Valid' if account_valid else 'Invalid'}")
    print(f"- Environment variables: {'Valid' if env_valid else 'Missing'}")
    print("--------------------------------------------")
    
    if not account_valid or not env_valid:
        print("\nRecommendations:")
        if not account_valid:
            print("- Configure your active account in active_account.json")
        if not env_valid:
            print("- Run the setup utility to create your env.sh file:")
            setup_path = os.path.join(BASE_DIR, 'Backend', 'Utils', 'setup_env.py')
            print(f"  python {setup_path}")
        sys.exit(1)
    else:
        print("\nAll configuration is valid! You're ready to go.")
        sys.exit(0)
