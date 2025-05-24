#!/usr/bin/env python3
"""
Test script for the fallback Capital.com API client and its credential handling.
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
    # Go up one level from Tools/test_fallback_api.py
    return script_path.parent.parent

# Set up base directory and add to path
BASE_DIR = get_base_dir()
sys.path.append(str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FallbackAPITest")

# ANSI color codes for prettier output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"{Colors.BLUE}{title}{Colors.ENDC}")
    print("=" * 60)

def mask_credential(value, show_chars=4):
    """Mask a credential value for display, showing only the last few characters."""
    if not value:
        return "Not set"
    if len(value) <= show_chars:
        return "*" * len(value)
    return "*" * (len(value) - show_chars) + value[-show_chars:]

def test_credential_loading():
    """Test that the FallbackApiClient loads credentials properly."""
    print_header("Testing FallbackApiClient Credential Loading")
    
    try:
        from src.AI.fallback_capital_api import FallbackApiClient
        
        # Create an instance of the client which should automatically load credentials
        client = FallbackApiClient()
        
        # Check if credentials were loaded
        has_api_key = bool(client.api_key)
        has_username = bool(client.username)
        has_password = bool(client.password)
        
        print(f"API Key: {mask_credential(client.api_key)}")
        print(f"Username: {client.username[:3]}...{client.username[-3:] if len(client.username) > 6 else ''}" if has_username else "Username: Not set")
        print(f"Password: {mask_credential(client.password)}")
        
        # Check if all credentials were loaded
        if has_api_key and has_username and has_password:
            print(f"{Colors.GREEN}✓ All credentials were loaded successfully{Colors.ENDC}")
            return True
        else:
            missing = []
            if not has_api_key: missing.append("API Key")
            if not has_username: missing.append("Username")
            if not has_password: missing.append("Password")
            
            print(f"{Colors.RED}✗ Missing credentials: {', '.join(missing)}{Colors.ENDC}")
            return False
            
    except ImportError:
        print(f"{Colors.RED}✗ Could not import FallbackApiClient{Colors.ENDC}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error testing FallbackApiClient: {e}{Colors.ENDC}")
        return False

def test_credential_source():
    """Test whether credentials are coming from the secure database or environment variables."""
    print_header("Testing Credential Source")
    
    try:
        # Access secure database directly first
        from src.Credentials.credentials_manager import CredentialManager
        manager = CredentialManager()
        
        db_api_key = manager.get_credential('capital_com', 'CAPITAL_API_KEY')
        db_api_login = manager.get_credential('capital_com', 'CAPITAL_API_LOGIN')
        db_api_password = manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')
        
        # Check environment variables
        env_api_key = os.environ.get('CAPITAL_API_KEY')
        env_api_login = os.environ.get('CAPITAL_API_LOGIN')
        env_api_password = os.environ.get('CAPITAL_API_PASSWORD')
        
        # Instantiate the client
        from src.AI.fallback_capital_api import FallbackApiClient
        client = FallbackApiClient()
        
        # Compare client credentials with source
        if client.api_key == db_api_key and db_api_key:
            print(f"{Colors.GREEN}✓ Client is using API key from secure database{Colors.ENDC}")
            db_source = True
        elif client.api_key == env_api_key and env_api_key:
            print(f"{Colors.YELLOW}! Client is using API key from environment variables{Colors.ENDC}")
            db_source = False
        else:
            print(f"{Colors.RED}? Client API key doesn't match any known source{Colors.ENDC}")
            db_source = None
            
        if client.username == db_api_login and db_api_login:
            print(f"{Colors.GREEN}✓ Client is using username from secure database{Colors.ENDC}")
            db_source = db_source and True
        elif client.username == env_api_login and env_api_login:
            print(f"{Colors.YELLOW}! Client is using username from environment variables{Colors.ENDC}")
            db_source = False
        else:
            print(f"{Colors.RED}? Client username doesn't match any known source{Colors.ENDC}")
            db_source = None
            
        if client.password == db_api_password and db_api_password:
            print(f"{Colors.GREEN}✓ Client is using password from secure database{Colors.ENDC}")
            db_source = db_source and True
        elif client.password == env_api_password and env_api_password:
            print(f"{Colors.YELLOW}! Client is using password from environment variables{Colors.ENDC}")
            db_source = False
        else:
            print(f"{Colors.RED}? Client password doesn't match any known source{Colors.ENDC}")
            db_source = None
            
        # Final verdict
        if db_source is True:
            print(f"{Colors.GREEN}✓ FallbackApiClient is correctly prioritizing secure database credentials{Colors.ENDC}")
            return True
        elif db_source is False:
            print(f"{Colors.YELLOW}! FallbackApiClient is using environment variables instead of secure database{Colors.ENDC}")
            if all([db_api_key, db_api_login, db_api_password]):
                print(f"{Colors.RED}✗ This is NOT expected since database credentials exist!{Colors.ENDC}")
            else:
                print(f"{Colors.GREEN}✓ This is expected since database credentials are incomplete{Colors.ENDC}")
            return False
        else:
            print(f"{Colors.RED}? Could not determine credential source{Colors.ENDC}")
            return None
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error testing credential source: {e}{Colors.ENDC}")
        return False

def test_fallback_behavior():
    """Test that the client correctly falls back to environment variables if database access fails."""
    print_header("Testing Fallback Behavior")
    
    try:
        # We'll simulate database access failing by monkeypatching the import
        import sys
        import types
        
        # Store reference to original import
        original_import = __import__
        
        # Define our patched import
        def patched_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'src.Credentials.credentials_manager' or name.endswith('credentials_manager'):
                raise ImportError("Simulated database access failure")
            return original_import(name, globals, locals, fromlist, level)
        
        # Apply monkey patch
        sys.meta_path.insert(0, types.ModuleType('mocked_credentials'))
        sys.__import__ = patched_import
        
        # Now try to instantiate the client with the patched import
        from src.AI.fallback_capital_api import FallbackApiClient
        client = FallbackApiClient()
        
        # Check if it fell back to environment variables
        env_api_key = os.environ.get('CAPITAL_API_KEY')
        env_api_login = os.environ.get('CAPITAL_API_LOGIN')
        env_api_password = os.environ.get('CAPITAL_API_PASSWORD')
        
        using_env = (
            client.api_key == env_api_key and 
            client.username == env_api_login and 
            client.password == env_api_password and
            all([env_api_key, env_api_login, env_api_password])
        )
        
        if using_env:
            print(f"{Colors.GREEN}✓ Client correctly fell back to environment variables when database access failed{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.RED}✗ Client did not correctly fall back to environment variables{Colors.ENDC}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error testing fallback behavior: {e}{Colors.ENDC}")
        return False
    finally:
        # Restore original import
        if 'sys' in locals() and hasattr(sys, '__import__'):
            sys.__import__ = original_import
            if hasattr(sys, 'meta_path') and len(sys.meta_path) > 0:
                sys.meta_path.pop(0)

def main():
    """Run all tests for the fallback API client."""
    print("\nJamso-AI-Engine Fallback API Client Test")
    print("=======================================")
    
    # Run tests
    tests = [
        ("Credential Loading", test_credential_loading),
        ("Credential Source", test_credential_source),
        # Uncomment to test fallback behavior - but note this modifies system behavior
        # ("Fallback Behavior", test_fallback_behavior),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nRunning test: {name}")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"Uncaught error in test {name}: {e}")
            results.append((name, False))
    
    # Print summary
    print_header("Test Summary")
    
    all_passed = True
    for name, result in results:
        if result is True:
            print(f"{Colors.GREEN}✓ {name}: Passed{Colors.ENDC}")
        elif result is False:
            print(f"{Colors.RED}✗ {name}: Failed{Colors.ENDC}")
            all_passed = False
        else:
            print(f"{Colors.YELLOW}? {name}: Inconclusive{Colors.ENDC}")
            all_passed = False
    
    if all_passed:
        print(f"\n{Colors.GREEN}All tests passed! The fallback Capital.com API client is working correctly.{Colors.ENDC}")
        return 0
    else:
        print(f"\n{Colors.RED}Some tests failed. Please check the logs above.{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
