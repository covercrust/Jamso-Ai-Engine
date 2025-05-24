#!/usr/bin/env python3
"""
Test script for verifying environment variable loading
This script tests whether python-dotenv is correctly loading
environment variables from the .env file.
"""

import os
import sys

print("Testing environment variable loading")
print("===================================")

# Try to load environment variables using dotenv
print("1. Testing dotenv import...")
try:
    from dotenv import load_dotenv
    print("✅ dotenv module imported successfully")
    
    # Test loading environment variables
    print("\n2. Loading environment variables...")
    load_dotenv()
    print("✅ load_dotenv() called without errors")
    
    # Check for Capital.com API credentials
    print("\n3. Checking for Capital.com API credentials...")
    api_key = os.environ.get('CAPITAL_API_KEY')
    api_login = os.environ.get('CAPITAL_API_LOGIN')
    api_password = os.environ.get('CAPITAL_API_PASSWORD')
    
    if api_key:
        print("✅ CAPITAL_API_KEY found")
    else:
        print("❌ CAPITAL_API_KEY not found")
    
    if api_login:
        print("✅ CAPITAL_API_LOGIN found")
    else:
        print("❌ CAPITAL_API_LOGIN not found")
    
    if api_password:
        print("✅ CAPITAL_API_PASSWORD found")
    else:
        print("❌ CAPITAL_API_PASSWORD not found")
    
    # Check .env file location
    print("\n4. Checking .env file location...")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(BASE_DIR, '.env')
    
    if os.path.exists(env_path):
        print(f"✅ .env file found at: {env_path}")
        
        # Check file permissions
        try:
            from stat import S_IRUSR, S_IWUSR
            mode = os.stat(env_path).st_mode
            if mode & S_IRUSR and mode & S_IWUSR:
                print("✅ .env file has correct read/write permissions")
            else:
                print("❌ .env file may have incorrect permissions")
        except:
            print("⚠️ Could not check file permissions")
    else:
        print(f"❌ .env file NOT found at: {env_path}")
        
        # Try to find any .env file
        print("\n5. Looking for .env file in other locations...")
        from subprocess import Popen, PIPE
        try:
            process = Popen(f'find {BASE_DIR} -name ".env"', shell=True, stdout=PIPE)
            output, _ = process.communicate()
            results = output.decode('utf-8').strip().split('\n')
            if any(results):
                print(f"✅ Found .env files at:")
                for path in results:
                    if path:
                        print(f"   - {path}")
            else:
                print("❌ No .env files found in project directory")
        except:
            print("⚠️ Could not search for .env files")

except ImportError:
    print("❌ Failed to import dotenv module")
    print("\nRecommendation: Run 'pip install python-dotenv' to install the module")

print("\n===================================")
print("Environment test completed")
