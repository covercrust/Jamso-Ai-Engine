#!/usr/bin/env python3
"""
Account selection module for Capital.com API.
Handles environment switching between demo and live trading accounts.
Provides interactive CLI for selecting trading environment and account.
"""

import json
import logging
from logging.handlers import RotatingFileHandler
import os
import subprocess
import sys
import time
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Union, Type

try:
    import requests
    from requests.exceptions import RequestException
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests
    from requests.exceptions import RequestException

# Replace env.sh usage with database-based credential management
from src.Credentials.credentials.credential_manager import CredentialManager

# Initialize CredentialManager
credential_manager = CredentialManager()

# Fetch credentials dynamically using get_credential method
CAPITAL_API_KEY = credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY')
CAPITAL_API_LOGIN = credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN')
CAPITAL_API_PASSWORD = credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')

# Define base style and color classes
class StyleBase:
    RESET_ALL = ''
    NORMAL = ''
    BRIGHT = ''
    DIM = ''
    BOLD = ''

class ForeBase:
    RESET = ''
    RED = ''
    GREEN = ''
    YELLOW = ''
    BLUE = ''
    MAGENTA = ''
    CYAN = ''
    WHITE = ''

# Initialize Style and Fore variables
Style: StyleBase
Fore: ForeBase

# Add color support
try:
    import colorama
    from colorama import Fore as ColoramaFore, Back, Style as ColoramaStyle
    colorama.init(autoreset=True)
    HAS_COLORAMA = True
    
    class ColoramaStyleAdapter(StyleBase):
        def __init__(self):
            self.RESET_ALL = ColoramaStyle.RESET_ALL
            self.NORMAL = ColoramaStyle.NORMAL
            self.BRIGHT = ColoramaStyle.BRIGHT
            self.DIM = ColoramaStyle.DIM
            self.BOLD = ColoramaStyle.BRIGHT  # Map BOLD to BRIGHT
    
    class ColoramaForeAdapter(ForeBase):
        def __init__(self):
            self.RESET = ColoramaFore.RESET
            self.RED = ColoramaFore.RED  # Fixed typo here
            self.GREEN = ColoramaFore.GREEN
            self.YELLOW = ColoramaFore.YELLOW
            self.BLUE = ColoramaFore.BLUE
            self.MAGENTA = ColoramaFore.MAGENTA
            self.CYAN = ColoramaFore.CYAN
            self.WHITE = ColoramaFore.WHITE
    
    # Instantiate our adapter classes with proper type annotations
    Style = ColoramaStyleAdapter()
    Fore = ColoramaForeAdapter()
    
except ImportError:
    # Fallback to ANSI escape codes if colorama is not available
    HAS_COLORAMA = False
    
    class ANSIStyleAdapter(StyleBase):
        def __init__(self):
            self.RESET_ALL = '\033[0m'
            self.NORMAL = '\033[0m'
            self.BRIGHT = '\033[1m'
            self.DIM = '\033[2m'
            self.BOLD = '\033[1m'
    
    class ANSIForeAdapter(ForeBase):
        def __init__(self):
            self.RESET = '\033[0m'
            self.RED = '\033[91m'
            self.GREEN = '\033[92m'
            self.YELLOW = '\033[93m'
            self.BLUE = '\033[94m'
            self.MAGENTA = '\033[95m'
            self.CYAN = '\033[96m'
            self.WHITE = '\033[97m'
    
    # Instantiate our adapter classes with proper type annotations
    Style = ANSIStyleAdapter()
    Fore = ANSIForeAdapter()

# Constants
DEMO_SERVER: str = "https://demo-api-capital.backend-capital.com"
LIVE_SERVER: str = "https://api-capital.backend-capital.com"

# Get the base directory dynamically
def get_base_dir() -> Path:
    """Get the base directory dynamically."""
    # First check from environment variable
    if "ROOT_DIR" in os.environ:
        return Path(os.environ["ROOT_DIR"])
    
    # Next try to determine from script location
    script_path = Path(__file__).resolve()
    # Go up three levels from src/Exchanges/capital_com_api/select_account.py
    return script_path.parent.parent.parent.parent

BASE_PATH = get_base_dir()
ACTIVE_ACCOUNT_PATH = BASE_PATH / 'Backend' / 'Utils' / 'Config' / 'active_account.json'
LOG_FILE = BASE_PATH / 'Logs' / 'select_account.log'

# Database path for storing selected accounts
DB_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Credentials/credentials.db'

# Configure logging
logger = logging.getLogger(__name__)
os.makedirs(Path(LOG_FILE).parent, exist_ok=True)
handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=1024*1024,
    backupCount=5,
    encoding='utf-8'
)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def login_to_capital(server: str) -> Dict[str, str]:
    """Login to Capital.com API and get session tokens"""
    if not all([CAPITAL_API_KEY, CAPITAL_API_LOGIN, CAPITAL_API_PASSWORD]):
        raise ValueError("Missing required credentials")
    
    headers = {
        "X-CAP-API-KEY": CAPITAL_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "identifier": CAPITAL_API_LOGIN,
        "password": CAPITAL_API_PASSWORD
    }
    
    logger.debug(f"Attempting login to {server}")
    
    try:
        response = requests.post(
            f"{server}/api/v1/session",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return {
            "CST": response.headers["CST"],
            "X-SECURITY-TOKEN": response.headers["X-SECURITY-TOKEN"]
        }
    except requests.RequestException as e:
        logger.error(f"Login failed: {e}")
        raise

def fetch_accounts(server: str, session_tokens: Dict[str, str]) -> List[Dict[str, Any]]:
    """Fetch accounts from Capital.com API"""
    headers = {
        "X-CAP-API-KEY": CAPITAL_API_KEY,
        "CST": session_tokens["CST"],
        "X-SECURITY-TOKEN": session_tokens["X-SECURITY-TOKEN"]
    }
    
    try:
        response = requests.get(f"{server}/api/v1/accounts", headers=headers)
        response.raise_for_status()
        accounts_data = response.json()
        if "accounts" not in accounts_data:
            logger.warning("API response did not contain expected 'accounts' field")
            return []
        return accounts_data["accounts"]
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching accounts: {e} (Status code: {e.response.status_code})")
        # Log the error response for debugging
        try:
            error_data = e.response.json()
            logger.error(f"API error response: {error_data}")
        except:
            logger.error(f"API error response could not be parsed: {e.response.text[:500]}")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching accounts: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in API response: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching accounts: {e}")
        return []

def flash_warning(text: str, times: int = 3) -> None:
    """Flash warning text in red"""
    # Initial save of cursor position
    print("\033[s", end='', flush=True)
    
    for _ in range(times):
        # Print warning in red
        print(f"\033[91m{text}\033[0m", end='', flush=True)
        time.sleep(0.5)
        # Return to saved position and clear
        print("\033[u\033[K", end='', flush=True)
        time.sleep(0.5)
        
    # Final warning display
    print(f"\033[91m{text}\033[0m", end='', flush=True)

def display_menu() -> str:
    """
    Display and handle main menu selection.
    
    Returns:
        str: Selected menu option
    """
    print("\nSelect Environment:")
    print("1. Demo Environment")
    print(f"2. Live Environment(Caution: {Fore.RED}{Style.BOLD}Real Money{Style.RESET_ALL})")
    print("3. Exit")
    return input("Choice: ")

def display_accounts(accounts: List[Dict[str, Any]]) -> int:
    """
    Display and handle account selection.
    
    Args:
        accounts: List of available trading accounts
    
    Returns:
        int: Selected account index
    """
    print("\nSelect Account:")
    for idx, acc in enumerate(accounts, 1):
        # Format account ID in green
        account_id = f"{Fore.GREEN}{acc['accountId']}{Style.RESET_ALL}"
        print(f"{idx}. {acc['accountName']} ({account_id})")
    while True:
        try:
            choice = int(input("Choice: ")) - 1
            if 0 <= choice < len(accounts):
                return choice
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def save_account_to_db(account: Dict[str, Any], server: str) -> None:
    """Save selected account configuration to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selected_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                account_name TEXT NOT NULL,
                server TEXT NOT NULL,
                balance REAL,
                currency TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert the selected account
        cursor.execute('''
            INSERT INTO selected_accounts (account_id, account_name, server, balance, currency)
            VALUES (?, ?, ?, ?, ?)
        ''', (account['accountId'], account['accountName'], server, account['balance']['balance'], account['currency']))

        conn.commit()
        conn.close()
        logger.info("Account configuration saved to the database.")
    except sqlite3.Error as e:
        logger.error(f"Failed to save account to database: {e}")
        raise

def clear_screen():
    """Clear the terminal screen for better UI."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print a stylish header for the application."""
    banner = f"""
{Style.BOLD}{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                 {Fore.YELLOW}CAPITAL.COM ACCOUNT SELECTOR{Fore.CYAN}                 ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

def print_section(title):
    """Print a section title with formatting."""
    print(f"\n{Style.BOLD}{Fore.BLUE}▶ {title}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'─' * 50}{Style.RESET_ALL}")

def print_option(index, text, highlight=False, warning=False):
    """Print a menu option with optional highlighting."""
    prefix = f"{Style.BOLD}{Fore.GREEN}[{index}]{Style.RESET_ALL}"
    
    if warning:
        text_formatted = f"{Fore.RED}{Style.BOLD}{text}{Style.RESET_ALL}"
    elif highlight:
        text_formatted = f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    else:
        text_formatted = text  # Fixed: was incorrectly reassigning to text variable
        
    print(f"  {prefix} {text_formatted}")

def print_success(message):
    """Print a success message."""
    print(f"\n{Style.BOLD}{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_warning(message):
    """Print a warning message."""
    print(f"\n{Style.BOLD}{Fore.RED}⚠ {message}{Style.RESET_ALL}")

def print_info(message):
    """Print an informational message."""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")

def get_user_choice(max_choice, prompt="Choice"):
    """Get user input with validation and pretty formatting."""
    while True:
        try:
            choice = input(f"{Fore.YELLOW}{Style.BOLD}► {prompt}: {Style.RESET_ALL}")
            choice = int(choice)
            if 1 <= choice <= max_choice:
                return choice
            print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and {max_choice}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")

def main() -> None:
    """Main function to handle account selection."""
    try:
        clear_screen()
        print_header()
        
        # Introduction
        print_info("This utility helps you select a Capital.com trading account.")
        print_info("Your selection will be saved to the configuration file.")
        
        choice = display_menu()
        if choice == '3':
            return

        server = DEMO_SERVER if choice == '1' else LIVE_SERVER
        session_tokens = login_to_capital(server)
        accounts = fetch_accounts(server, session_tokens)

        if not accounts:
            logger.warning("No accounts found")
            print("No accounts found")
            return

        acc_idx = display_accounts(accounts)
        selected_account = accounts[acc_idx]
        save_account_to_db(selected_account, server)
        
        logger.info(
            "Selected %s on %s",
            selected_account['accountName'],
            server
        )
        print(
            f"Selected {selected_account['accountName']} "
            f"on {server}"
        )

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("File operation error: %s", str(e))
        print(f"Error: {str(e)}")
    except RequestException as e:
        logger.error("API request error: %s", str(e))
        print(f"Error: {str(e)}")
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled")
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()