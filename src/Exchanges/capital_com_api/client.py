# client.py

import logging
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.account_manager import AccountManager
from src.Exchanges.capital_com_api.position_manager import PositionManager
from src.Exchanges.capital_com_api.order_manager import OrderManager
from src.Exchanges.capital_com_api.market_data_manager import MarketDataManager
from src.Exchanges.capital_com_api.account_config import AccountConfig
from src.Credentials.credentials_manager import CredentialManager

# Get the base directory dynamically
def get_base_dir():
    """Get the base directory dynamically."""
    # First check from environment variable
    if "ROOT_DIR" in os.environ:
        return Path(os.environ["ROOT_DIR"])
    
    # Next try to determine from script location
    script_path = Path(__file__).resolve()
    # Go up three levels from src/Exchanges/capital_com_api/client.py
    return script_path.parent.parent.parent.parent

BASE_DIR = get_base_dir()

# Configure logging with dynamic path
log_file_path = os.path.join(BASE_DIR, 'src', 'Logs', 'client.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize CredentialManager
credential_manager = CredentialManager()

# Fetch credentials dynamically
credentials = {
    'CAPITAL_API_KEY': credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY'),
    'CAPITAL_API_LOGIN': credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN'),
    'CAPITAL_API_PASSWORD': credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')
}

CAPITAL_API_KEY = credentials.get('CAPITAL_API_KEY', '')
CAPITAL_API_LOGIN = credentials.get('CAPITAL_API_LOGIN', '')
CAPITAL_API_PASSWORD = credentials.get('CAPITAL_API_PASSWORD', '')

def load_active_account() -> dict:
    """Load active account configuration from database."""
    active_account_path = os.path.join(BASE_DIR, 'src', 'Credentials', 'active_account.json')
    
    # Try to load from database first
    try:
        # Import here to avoid circular imports
        from src.Exchanges.capital_com_api.account_db import get_active_account_from_db
        
        # Get account from database
        account_data = get_active_account_from_db()
        
        # Validate account data
        if account_data and account_data.get('account', {}).get('accountId') and account_data.get('server'):
            logger.info(f"Loaded account configuration from database: {account_data['account']['accountName']} on {account_data['server']}")
            return account_data
        else:
            logger.warning("Invalid or incomplete account data from database, trying fallback")
    except Exception as e:
        logger.error(f"Failed to load account from database: {e}, trying fallback")
    
    # Fallback to JSON file if database retrieval failed
    try:
        with open(active_account_path, 'r') as f:
            data = json.load(f)
            if not data.get('account', {}).get('accountId'):
                raise ValueError("Account ID missing in account configuration")
            if not data.get('server'):
                raise ValueError("Server URL missing in account configuration")
            logger.debug(f"Loaded account configuration from file: {json.dumps(data, indent=2)}")
            return data
    except Exception as e:
        logger.error(f"Failed to load active account from {active_account_path}: {e}")
        raise

# Load the active account information
active_account = load_active_account()

# Use the account information from active_account.json
CAPITAL_API_SERVER = active_account["server"]
CAPITAL_ACCOUNT_ID = active_account["account"]["accountId"]  # Fixed nested access

class Client:
    """A client for interacting with the Capital.com API."""

    def __init__(self, session_manager: Optional[SessionManager] = None, request_handler: Optional[RequestHandler] = None):
        """Initialize client with all required managers."""
        # Use loaded credentials if not provided through parameters
        if session_manager is None:
            logger.info("Creating new session manager with loaded credentials")
            session_manager = SessionManager(
                server=CAPITAL_API_SERVER,
                api_key=CAPITAL_API_KEY,
                username=CAPITAL_API_LOGIN,
                password=CAPITAL_API_PASSWORD
            )
        
        self.session_manager = session_manager
        self.server = self.session_manager.server
        
        # Create request handler if not provided
        if request_handler is None:
            self.request_handler = RequestHandler()
        else:
            self.request_handler = request_handler
        
        # Initialize account configuration
        self.account_config = AccountConfig()
        self.account_config.set_server(self.server)
        
        # Add flag for authentication checking
        self._ensure_authenticated = True
        
        # Set up authentication headers
        self._setup_auth_headers()
        
        # Initialize managers
        self._init_managers()
        
        # Authenticate immediately
        try:
            logger.info("Attempting initial authentication")
            self.session_manager.create_session()
            if self.session_manager.is_authenticated:
                logger.info("Initial authentication successful")
            else:
                logger.warning("Initial authentication failed")
        except Exception as e:
            logger.error(f"Error during initial authentication: {str(e)}")

    def _setup_auth_headers(self):
        """Set up authentication headers after initialization."""
        self.request_handler.update_headers({
            "X-CAP-API-KEY": self.account_config.api_key or '',
            "CST": self.session_manager.CST or '',
            "X-SECURITY-TOKEN": self.session_manager.X_TOKEN or ''
        })

    def _init_managers(self):
        """Initialize the various API managers."""
        try:
            # Initialize the account manager
            self.account_manager = AccountManager(
                session_manager=self.session_manager,
                # Remove the request_handler parameter as AccountManager doesn't accept it
                account_config=self.account_config
            )
            
            # Initialize position manager
            self.position_manager = PositionManager(
                session_manager=self.session_manager,
                request_handler=self.request_handler
            )
            
            # Initialize order manager
            self.order_manager = OrderManager(
                session_manager=self.session_manager,
                request_handler=self.request_handler
            )
            
            # Initialize market data manager
            self.market_data_manager = MarketDataManager(
                session_manager=self.session_manager,
                request_handler=self.request_handler
            )
        except Exception as e:
            logger.error(f"Failed to initialize managers: {str(e)}")
            raise

    def _ensure_session_valid(self):
        """Ensure session is valid before making requests."""
        if self._ensure_authenticated:
            logger.debug("Ensuring session validity.")
            self.session_manager.create_session()
            cst = self.session_manager.CST or ''
            token = self.session_manager.X_TOKEN or ''
            self.request_handler.update_auth_headers({
                "CST": cst,
                "X-SECURITY-TOKEN": token
            })

    def all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts for the client."""
        self._ensure_session_valid()
        # Fixed: AccountManager doesn't have all_accounts method, use load_accounts instead
        return self.account_manager.load_accounts()

    def change_active_account(self, account_id: str) -> None:
        """Changes the active account used by the client."""
        logger.info(f"Changing active account to: {account_id}")
        self.account_config.set_account_id(account_id)

    def create_position(self, **kwargs) -> dict:
        """Create a new position."""
        logger.info(f"Creating position with args: {kwargs}")
        try:
            # Rename fields to match API requirements
            if 'stopLevel' in kwargs:
                kwargs['stopLevel'] = float(kwargs['stopLevel'])
            if 'limitLevel' in kwargs:
                kwargs['limitLevel'] = float(kwargs['limitLevel'])
            if 'profitLevel' in kwargs:
                kwargs['profitLevel'] = float(kwargs['profitLevel'])
            if 'orderType' in kwargs:
                kwargs['type'] = kwargs.pop('orderType')  # API expects 'type' not 'orderType'
            if 'forceOpen' in kwargs:
                kwargs['timeInForce'] = 'FILL_OR_KILL' if kwargs.pop('forceOpen') else 'EXECUTE_AND_ELIMINATE'

            # Ensure required fields
            required_fields = ['epic', 'direction', 'size', 'type']
            missing_fields = [field for field in required_fields if field not in kwargs]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Ensure all specified parameters are passed to the position manager
            self.session_manager.create_session()  # Ensure fresh session
            response = self.position_manager.create_position(**kwargs)
            logger.info(f"Position created successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to create position: {e}")
            raise

    def close_position(self, deal_id: str, size: float = 1) -> dict:
        """Closes an existing position."""
        payload = {
            "dealId": deal_id,
            "size": size
        }
        url = f"{self.server}/api/v1/positions/otc"
        headers = {
            "CST": self.session_manager.CST,
            "X-SECURITY-TOKEN": self.session_manager.X_TOKEN,
            "Content-Type": "application/json"
        }
        response, _ = self.request_handler.make_request("DELETE", url, json.dumps(payload), headers=headers)
        return response

    def get_position(self, deal_id: str) -> dict:
        """Retrieve details of a specific position."""
        self._ensure_session_valid()
        url = f"{self.server}/api/v1/positions/{deal_id}"
        response, _ = self.request_handler.make_request(
            "GET", 
            url, 
            headers=self.request_handler.headers
        )
        return response

    def get_client_sentiment(self, market_id: str) -> dict:
        """Retrieves client sentiment data for a specific market."""
        return self.market_data_manager.client_sentiment(market_id)

    def test_fetch_account_details(self) -> None:
        """Tests fetching account details."""
        try:
            self._ensure_session_valid()
            logger.info("Fetching account details...")
            accounts = self.all_accounts()
            logger.info(f"Accounts: {accounts}")
        except Exception as e:
            logger.error(f"Error fetching account details: {e}")

def main():
    """Main test function."""
    try:
        # Load active account configuration
        active_account = load_active_account()
        server = active_account['server']

        # Initialize dependencies
        session_manager = SessionManager(
            server=server,
            api_key=CAPITAL_API_KEY,
            username=CAPITAL_API_LOGIN,
            password=CAPITAL_API_PASSWORD
        )

        request_handler = RequestHandler()

        # Initialize client with required dependencies
        client = Client(
            session_manager=session_manager,
            request_handler=request_handler
        )
        
        logger.info("Client initialized successfully")

        # Test client operations
        try:
            # Test fetching account details
            account_details = client.all_accounts()
            logger.info(f"Account details: {account_details}")

        except Exception as e:
            logger.error(f"Error during client operations: {e}")
        finally:
            # session_manager.log_out()  # Remove or implement log_out method in SessionManager
            request_handler.close_session()

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()