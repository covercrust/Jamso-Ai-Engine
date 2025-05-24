#!/usr/bin/env python3
"""
Test script for verifying Telegram and OpenAI credential integration.
This script tests how the secure credential system provides these credentials
to application components with proper fallback mechanisms.
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
    # Go up one level from Tools/test_telegram_openai_integration.py
    return script_path.parent.parent

# Set up base directory and add to path
BASE_DIR = get_base_dir()
sys.path.append(str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TelegramOpenAIIntegrationTest")

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
    print("\n" + "=" * 70)
    print(f"{Colors.BLUE}{title}{Colors.ENDC}")
    print("=" * 70)

def mask_credential(value, show_chars=4):
    """Mask a credential value for display, showing only the last few characters."""
    if not value:
        return "Not set"
    if len(value) <= show_chars:
        return "*" * len(value)
    return "*" * (len(value) - show_chars) + value[-show_chars:]

def test_telegram_credentials():
    """Test that the Telegram credentials are properly loaded."""
    print_header("Testing Telegram Credentials")
    
    try:
        # Access secure database directly
        from src.Credentials.credentials_manager import CredentialManager
        manager = CredentialManager()
        
        # Get credentials from database
        db_bot_token = manager.get_credential('telegram', 'TELEGRAM_BOT_TOKEN')
        db_chat_id = manager.get_credential('telegram', 'TELEGRAM_CHAT_ID')
        
        # Check environment variables
        env_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        env_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # Report findings
        print("Telegram Bot Token:")
        if db_bot_token:
            print(f"  Database: {mask_credential(db_bot_token, 6)} {Colors.GREEN}[✓]{Colors.ENDC}")
        else:
            print(f"  Database: {Colors.RED}Not set [✗]{Colors.ENDC}")
            
        if env_bot_token:
            print(f"  Environment: {mask_credential(env_bot_token, 6)} {Colors.GREEN}[✓]{Colors.ENDC}")
        else:
            print(f"  Environment: {Colors.RED}Not set [✗]{Colors.ENDC}")
        
        print("\nTelegram Chat ID:")
        if db_chat_id:
            print(f"  Database: {db_chat_id} {Colors.GREEN}[✓]{Colors.ENDC}")
        else:
            print(f"  Database: {Colors.RED}Not set [✗]{Colors.ENDC}")
            
        if env_chat_id:
            print(f"  Environment: {env_chat_id} {Colors.GREEN}[✓]{Colors.ENDC}")
        else:
            print(f"  Environment: {Colors.RED}Not set [✗]{Colors.ENDC}")
        
        # Try importing the Telegram notification module (if it exists)
        try:
            from src.Notifications.telegram_alerts import TelegramAlerts
            print(f"\n{Colors.BLUE}Testing Telegram module import:{Colors.ENDC}")
            print(f"{Colors.GREEN}✓ Successfully imported TelegramAlerts module{Colors.ENDC}")
            
            # Try to initialize the alerts object (without sending)
            alerts = TelegramAlerts()
            
            # Check which credentials were used
            used_bot_token = alerts.bot_token if hasattr(alerts, 'bot_token') else None
            used_chat_id = alerts.chat_id if hasattr(alerts, 'chat_id') else None
            
            if used_bot_token and used_bot_token == db_bot_token and db_bot_token:
                print(f"{Colors.GREEN}✓ Using bot token from secure database{Colors.ENDC}")
            elif used_bot_token and used_bot_token == env_bot_token and env_bot_token:
                print(f"{Colors.YELLOW}! Using bot token from environment variables{Colors.ENDC}")
            else:
                print(f"{Colors.RED}? Could not determine bot token source{Colors.ENDC}")
                
            if used_chat_id and used_chat_id == db_chat_id and db_chat_id:
                print(f"{Colors.GREEN}✓ Using chat ID from secure database{Colors.ENDC}")
            elif used_chat_id and used_chat_id == env_chat_id and env_chat_id:
                print(f"{Colors.YELLOW}! Using chat ID from environment variables{Colors.ENDC}")
            else:
                print(f"{Colors.RED}? Could not determine chat ID source{Colors.ENDC}")
                
        except ImportError:
            print(f"{Colors.YELLOW}! Could not import TelegramAlerts module (module may not exist){Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}✗ Error testing Telegram module: {e}{Colors.ENDC}")
            
        # Overall verdict
        if db_bot_token and db_chat_id:
            print(f"\n{Colors.GREEN}✓ Telegram credentials properly set in secure database{Colors.ENDC}")
            return True
        elif env_bot_token and env_chat_id:
            print(f"\n{Colors.YELLOW}! Telegram credentials available in environment variables but not in database{Colors.ENDC}")
            return False
        else:
            print(f"\n{Colors.RED}✗ Missing some or all Telegram credentials{Colors.ENDC}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error testing Telegram credentials: {e}{Colors.ENDC}")
        return False

def test_openai_credentials():
    """Test that OpenAI API credentials are properly loaded."""
    print_header("Testing OpenAI Credentials")
    
    try:
        # Access secure database directly
        from src.Credentials.credentials_manager import CredentialManager
        manager = CredentialManager()
        
        # Get credentials from database
        db_api_key = manager.get_credential('openai', 'OPENAI_API_KEY')
        
        # Check environment variables
        env_api_key = os.environ.get('OPENAI_API_KEY')
        
        # Report findings
        print("OpenAI API Key:")
        if db_api_key:
            print(f"  Database: {mask_credential(db_api_key, 6)} {Colors.GREEN}[✓]{Colors.ENDC}")
        else:
            print(f"  Database: {Colors.RED}Not set [✗]{Colors.ENDC}")
            
        if env_api_key:
            print(f"  Environment: {mask_credential(env_api_key, 6)} {Colors.GREEN}[✓]{Colors.ENDC}")
        else:
            print(f"  Environment: {Colors.RED}Not set [✗]{Colors.ENDC}")
        
        # Try importing the OpenAI module (if it exists)
        try:
            from src.AI.openai_client import OpenAIClient
            print(f"\n{Colors.BLUE}Testing OpenAI module import:{Colors.ENDC}")
            print(f"{Colors.GREEN}✓ Successfully imported OpenAIClient module{Colors.ENDC}")
            
            # Try to initialize the client (without making API calls)
            client = OpenAIClient()
            
            # Check which credentials were used
            used_api_key = client.api_key if hasattr(client, 'api_key') else None
            
            if used_api_key and used_api_key == db_api_key and db_api_key:
                print(f"{Colors.GREEN}✓ Using API key from secure database{Colors.ENDC}")
            elif used_api_key and used_api_key == env_api_key and env_api_key:
                print(f"{Colors.YELLOW}! Using API key from environment variables{Colors.ENDC}")
            else:
                print(f"{Colors.RED}? Could not determine API key source{Colors.ENDC}")
                
        except ImportError:
            print(f"{Colors.YELLOW}! Could not import OpenAIClient module (module may not exist){Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}✗ Error testing OpenAI module: {e}{Colors.ENDC}")
            
        # Alternative: test openai module integration if it exists
        try:
            import openai
            print(f"\n{Colors.BLUE}Testing direct OpenAI module integration:{Colors.ENDC}")
            
            # Check if API key is set in the openai module
            current_key = openai.api_key if hasattr(openai, 'api_key') else None
            
            if current_key:
                if current_key == db_api_key and db_api_key:
                    print(f"{Colors.GREEN}✓ OpenAI module using API key from secure database{Colors.ENDC}")
                elif current_key == env_api_key and env_api_key:
                    print(f"{Colors.YELLOW}! OpenAI module using API key from environment variables{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}? OpenAI module using API key from unknown source{Colors.ENDC}")
            else:
                print(f"{Colors.YELLOW}! OpenAI module imported but API key not set{Colors.ENDC}")
                
        except ImportError:
            print(f"{Colors.YELLOW}! OpenAI module not installed{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}✗ Error testing direct OpenAI integration: {e}{Colors.ENDC}")
            
        # Overall verdict
        if db_api_key:
            print(f"\n{Colors.GREEN}✓ OpenAI credentials properly set in secure database{Colors.ENDC}")
            return True
        elif env_api_key:
            print(f"\n{Colors.YELLOW}! OpenAI credentials available in environment variables but not in database{Colors.ENDC}")
            return False
        else:
            print(f"\n{Colors.RED}✗ Missing OpenAI API key{Colors.ENDC}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error testing OpenAI credentials: {e}{Colors.ENDC}")
        return False

def test_credential_syncing():
    """Test if database and environment credentials are in sync."""
    print_header("Testing Credential Synchronization")
    
    try:
        # Access secure database directly
        from src.Credentials.credentials_manager import CredentialManager
        manager = CredentialManager()
        
        # Get credentials from database
        db_telegram_token = manager.get_credential('telegram', 'TELEGRAM_BOT_TOKEN')
        db_telegram_chat_id = manager.get_credential('telegram', 'TELEGRAM_CHAT_ID')
        db_openai_key = manager.get_credential('openai', 'OPENAI_API_KEY')
        
        # Check environment variables
        env_telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        env_telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        env_openai_key = os.environ.get('OPENAI_API_KEY')
        
        # Check synchronization for each credential
        sync_status = []
        
        # Telegram Bot Token
        if db_telegram_token and env_telegram_token:
            if db_telegram_token == env_telegram_token:
                sync_status.append((f"Telegram Bot Token", True))
            else:
                sync_status.append((f"Telegram Bot Token", False))
        elif not db_telegram_token and not env_telegram_token:
            sync_status.append((f"Telegram Bot Token", None))
        else:
            sync_status.append((f"Telegram Bot Token", False))
            
        # Telegram Chat ID
        if db_telegram_chat_id and env_telegram_chat_id:
            if db_telegram_chat_id == env_telegram_chat_id:
                sync_status.append((f"Telegram Chat ID", True))
            else:
                sync_status.append((f"Telegram Chat ID", False))
        elif not db_telegram_chat_id and not env_telegram_chat_id:
            sync_status.append((f"Telegram Chat ID", None))
        else:
            sync_status.append((f"Telegram Chat ID", False))
            
        # OpenAI API Key
        if db_openai_key and env_openai_key:
            if db_openai_key == env_openai_key:
                sync_status.append((f"OpenAI API Key", True))
            else:
                sync_status.append((f"OpenAI API Key", False))
        elif not db_openai_key and not env_openai_key:
            sync_status.append((f"OpenAI API Key", None))
        else:
            sync_status.append((f"OpenAI API Key", False))
            
        # Display results
        print("Credential Synchronization Status:")
        for cred, status in sync_status:
            if status is True:
                print(f"  {cred}: {Colors.GREEN}Synchronized [✓]{Colors.ENDC}")
            elif status is False:
                print(f"  {cred}: {Colors.RED}Different values [✗]{Colors.ENDC}")
            else:
                print(f"  {cred}: {Colors.YELLOW}Not set in both locations [!]{Colors.ENDC}")
                
        # Overall verdict
        all_synced = all(status is True for _, status in sync_status)
        all_present = all(status is True for _, status in sync_status if status is not None)
        
        if all_synced:
            print(f"\n{Colors.GREEN}✓ All credentials are properly synchronized{Colors.ENDC}")
            return True
        elif all_present:
            print(f"\n{Colors.YELLOW}! Some credentials differ between database and environment{Colors.ENDC}")
            print(f"{Colors.YELLOW}! Run Tools/sync_credentials.py to synchronize them{Colors.ENDC}")
            return False
        else:
            print(f"\n{Colors.RED}✗ Some credentials are not set in both locations{Colors.ENDC}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error testing credential synchronization: {e}{Colors.ENDC}")
        return False

def main():
    """Run all tests for Telegram and OpenAI credential integration."""
    print("\nJamso-AI-Engine Telegram & OpenAI Credential Integration Test")
    print("===========================================================")
    
    # Run tests
    tests = [
        ("Telegram Credentials", test_telegram_credentials),
        ("OpenAI Credentials", test_openai_credentials),
        ("Credential Synchronization", test_credential_syncing),
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
        print(f"\n{Colors.GREEN}All tests passed! Telegram & OpenAI credential integration is working correctly.{Colors.ENDC}")
        return 0
    else:
        print(f"\n{Colors.RED}Some tests failed. Please check the logs above.{Colors.ENDC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
