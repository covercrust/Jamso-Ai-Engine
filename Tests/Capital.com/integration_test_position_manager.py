"""
Integration test for PositionManager.
"""

import logging
import os
import sys
import json
import subprocess
from typing import Dict, Any, Tuple, Mapping

# Configure paths using relative paths for better portability
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, ROOT_DIR)  # Add project root to path before imports

# Now we can import modules from the project based on the current structure
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException
from src.Credentials.credentials_manager import CredentialManager

# Configure constants
ACTIVE_ACCOUNT_PATH = f'{ROOT_DIR}/src/Credentials/active_account.json'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{ROOT_DIR}/Logs/integration_test_position_manager.log'),
        logging.StreamHandler(sys.stdout)  # Add stdout handler to ensure we see logs
    ]
)
logger = logging.getLogger(__name__)

# Check if PositionManager exists, if not we'll need to import from order_manager
try:
    from src.Exchanges.capital_com_api.position_manager import PositionManager
    POSITION_MANAGER_EXISTS = True
except ImportError:
    from src.Exchanges.capital_com_api.order_manager import OrderManager
    POSITION_MANAGER_EXISTS = False
    logger.info("Using OrderManager as PositionManager is not available")

def source_env_file(env_file: str) -> None:
    """Source environment variables"""
    try:
        command = f"source {env_file} && env"
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        
        # Handle potential None output from subprocess
        if proc.stdout is None:
            logger.error("Failed to get output from subprocess")
            return

        # Safely iterate over subprocess output
        for line in iter(proc.stdout.readline, b''):
            try:
                decoded_line = line.decode('utf-8')
                if '=' in decoded_line:
                    key, value = decoded_line.strip().split('=', 1)
                    os.environ[key] = value
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode line from environment: {line}")
                continue

        # Ensure process completes
        proc.stdout.close()
        proc.wait()

        if proc.returncode != 0:
            logger.error(f"Environment sourcing failed with return code {proc.returncode}")
            
    except Exception as e:
        logger.error(f"Error sourcing environment file: {str(e)}")
        raise

def load_active_account(active_account_path: str) -> dict:
    """Load active account details from database or fallback to active_account.json."""
    try:
        # First try to get from database
        try:
            # Import here to avoid circular imports
            from src.Exchanges.capital_com_api.account_db import get_active_account_from_db
            
            # Get account from database
            account_data = get_active_account_from_db()
            
            # Validate account data
            if account_data and account_data.get('server') and account_data.get('account', {}).get('accountId'):
                account_id = account_data["account"]["accountId"]
                server = account_data["server"]
                logger.debug(f"Loaded active account from database: account_id={account_id}, server={server}")
                return {
                    "server": server,
                    "accountId": account_id
                }
            else:
                logger.warning("Invalid or incomplete account data from database, trying fallback")
        except Exception as e:
            logger.error(f"Failed to load account from database: {e}, trying fallback")
    
        # Fallback to JSON file if database retrieval failed
        if not os.path.exists(active_account_path):
            raise FileNotFoundError(f"Active account file not found: {active_account_path}")
            
        with open(active_account_path, 'r') as f:
            data = json.load(f)
            logger.debug(f"Loaded active account data from file: {json.dumps(data, indent=2)}")
            
            # Validate required fields (use flexible format handling)
            server = data.get("server")
            account_id = data.get("accountId") or data.get("account", {}).get("accountId")
                
            if not server:
                raise ValueError("Server URL missing in active_account.json")
            if not account_id:
                raise ValueError("Account ID missing in active_account.json")
                
            return {
                "server": server,
                "accountId": account_id
            }
    except Exception as e:
        logger.error(f"Failed to load active account: {e}")
        raise
            
    except Exception as e:
        logger.error(f"Failed to read {active_account_path}: {e}")
        raise

def load_configuration() -> Tuple[Mapping[str, str], Dict[str, Any]]:
    """Load environment variables and active account configuration."""
    try:
        # Initialize CredentialManager
        credential_manager = CredentialManager()

        # Load credentials from the database
        credentials = {
            'CAPITAL_API_KEY': credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY') or '',
            'CAPITAL_API_LOGIN': credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN') or '',
            'CAPITAL_API_PASSWORD': credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD') or ''
        }
        os.environ.update(credentials)
        logger.info("Loaded credentials from the database.")

        # Validate environment variables
        missing_vars = [key for key, value in credentials.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required credentials: {', '.join(missing_vars)}\n"
                           f"Please ensure these are set in the database")

        logger.debug("Credentials loaded successfully")
        for key in credentials:
            logger.debug(f"Loaded {key}=***")  # Don't log actual values

        # Load active account configuration
        if not os.path.exists(ACTIVE_ACCOUNT_PATH):
            logger.warning(f"Active account configuration not found: {ACTIVE_ACCOUNT_PATH}")
            # Return default values
            return credentials, {
                "server": "https://demo-api-capital.backend-capital.com",
                "accountId": "demo"
            }
            
        active_account = load_active_account(ACTIVE_ACCOUNT_PATH)
        logger.debug(f"Loaded active account configuration")

        return credentials, active_account

    except Exception as e:
        logger.error(f"Configuration loading failed: {str(e)}")
        raise

def main():
    """Main execution function."""
    try:
        # Load configuration
        env_vars, active_account = load_configuration()
        logger.info("Environment variables sourced successfully.")

        # Initialize components
        request_handler = RequestHandler()
        
        session_manager = SessionManager(
            server=active_account['server'].rstrip('/'),
            api_key=env_vars['CAPITAL_API_KEY'],
            username=env_vars['CAPITAL_API_LOGIN'],
            password=env_vars['CAPITAL_API_PASSWORD']
        )

        # Log credentials being used (do not log password for security)
        logger.debug(f"API_KEY={env_vars['CAPITAL_API_KEY']}")
        logger.debug(f"LOGIN={env_vars['CAPITAL_API_LOGIN']}")
        # logger.debug(f"PASSWORD={env_vars['CAPITAL_API_PASSWORD']}")  # Avoid logging sensitive info

        # Create session and log details
        session_result = session_manager.create_session()
        logger.debug(f"Session creation result: {session_result}")
        logger.debug(f"CST token after creation: {getattr(session_manager, 'CST', None)}")
        logger.debug(f"X-SECURITY-TOKEN after creation: {getattr(session_manager, 'X_TOKEN', None)}")
        logger.debug(f"Is authenticated after creation: {session_manager.is_authenticated}")
        
        # Log any error messages
        if not session_result.get('success', False):
            error_code = session_result.get('error_code', 'UNKNOWN')
            error_message = session_result.get('error_message', 'No error message')
            logger.error(f"Session creation failed with code: {error_code}, message: {error_message}")
            
        if hasattr(session_manager, 'last_error'):
            logger.error(f"SessionManager last_error: {getattr(session_manager, 'last_error', None)}")
            
        if not session_manager.is_authenticated:
            logger.error("Session authentication failed. Aborting position creation.")
            return

        # Initialize position manager based on availability
        if POSITION_MANAGER_EXISTS:
            position_manager = PositionManager(
                session_manager=session_manager,
                request_handler=request_handler
            )
            logger.info("Using PositionManager")
        else:
            position_manager = OrderManager(
                session_manager=session_manager,
                request_handler=request_handler
            )
            logger.info("Using OrderManager as fallback")

        try:
            # Test position creation
            ticker = "BTCUSD"
            direction = "BUY"
            size = 1.0
            
            logger.info(f"Creating position: ticker={ticker}, direction={direction}, size={size}")
            
            logger.debug(f"Session token before position creation: {getattr(session_manager, 'session_token', None)}")
            logger.debug(f"Is authenticated before position creation: {session_manager.is_authenticated}")
            
            # Use appropriate method name based on what's available
            if POSITION_MANAGER_EXISTS:
                create_position_response = position_manager.create_position(ticker, direction, size)
            else:
                create_position_response = position_manager.create_order(ticker, direction, size)
                
            logger.info(f"Position created successfully: {create_position_response}")
            
        except Exception as e:
            logger.error(f"Error during position management: {e}")
        finally:
            # Use correct method name for session cleanup
            session_manager.end_session()
            request_handler.close_session()

    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()