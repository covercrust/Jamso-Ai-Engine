import os
import logging
import json
import requests
from typing import Optional, Dict
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64encode, b64decode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccountConfig:
    def __init__(self):
        # Set up necessary paths with updated directory structure
        self.base_path = '/home/jamso-ai-server/Jamso-Ai-Engine'
        self.active_account_file = f"{self.base_path}/src/Credentials/active_account.json"
        self.config_path = f"{self.base_path}/src/Credentials"
        self.credentials_file = f"{self.config_path}/credentials.json"
        
        # Ensure directory exists with correct permissions
        os.makedirs(self.config_path, exist_ok=True)
        os.chmod(self.config_path, 0o700)
        
        # Initialize credentials as None
        self.api_key = None
        self.username = None
        self.password = None
        self._cst = None
        self._security_token = None
        self.enc_key = None
        self.time_stamp = None
        self.server = None
        self.account_id = None
        
        # Load configurations
        self._load_credentials()
        self.load_active_account()

    def _load_credentials(self):
        """Load API credentials from the secure credentials file or environment variables."""
        try:
            # First try to load from credentials file
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    self.api_key = creds.get('api_key')
                    self.username = creds.get('username')
                    self.password = creds.get('password')
                    logger.info("Loaded credentials from file")
            
            # If credentials file doesn't exist or some credentials are missing, try environment variables
            if not all([self.api_key, self.username, self.password]):
                self.api_key = os.getenv('CAPITAL_API_KEY')
                self.username = os.getenv('CAPITAL_API_LOGIN')
                self.password = os.getenv('CAPITAL_API_PASSWORD')
                logger.info("Using credentials from environment variables")
            
            # If still missing credentials, try the database
            if not all([self.api_key, self.username, self.password]):
                try:
                    # Import here to avoid circular imports
                    from src.Credentials.credentials import get_api_credentials
                    
                    # Get credentials from database
                    api_credentials = get_api_credentials()
                    if api_credentials:
                        self.api_key = api_credentials.get('api_key')
                        self.username = api_credentials.get('username')
                        self.password = api_credentials.get('password')
                        logger.info("Loaded credentials from database")
                except Exception as db_err:
                    logger.warning(f"Failed to load credentials from database: {db_err}")
            
            # Check if we have valid credentials
            if not all([self.api_key, self.username, self.password]):
                raise ValueError("Missing required credentials in file, environment variables, and database")
                
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            raise

    def load_active_account(self):
        """Load server and account_id from the database or active account configuration file."""
        try:
            # First try to get from database
            try:
                # Import here to avoid circular imports
                from src.Exchanges.capital_com_api.account_db import get_active_account_from_db
                
                # Get account from database
                account_data = get_active_account_from_db()
                
                if account_data and account_data.get('server') and account_data.get('account', {}).get('accountId'):
                    self.server = account_data.get("server", "").rstrip('/')
                    self.account_id = account_data["account"].get("accountId")
                    logger.info(f"Loaded active account configuration from database: {account_data['account'].get('accountName')} on {self.server}")
                    return
                    
            except Exception as db_err:
                logger.warning(f"Failed to load account from database: {db_err}, falling back to file")
            
            # Fallback to file if database retrieval failed
            if os.path.exists(self.active_account_file):
                with open(self.active_account_file, 'r') as f:
                    data = json.load(f)
                    self.server = data.get("server", "").rstrip('/')
                    if "account" in data:
                        self.account_id = data["account"].get("accountId")
                    logger.info("Loaded active account configuration from file")
            else:
                logger.warning(f"Active account file not found at {self.active_account_file}. Using default values.")
                # Set default values for demo environment
                self.server = "https://demo-api-capital.backend-capital.com"
                logger.info(f"Using default demo server: {self.server}")
                
        except Exception as e:
            logger.error(f"Error loading active account: {e}")
            # Instead of raising, use default values
            self.server = "https://demo-api-capital.backend-capital.com"
            logger.info(f"Falling back to default demo server: {self.server}")

    def set_server(self, server: str):
        """Set the server URL."""
        if not server:
            raise ValueError("Server URL cannot be None.")
        self.server = server.rstrip('/')
        logger.info(f"Server set to: {self.server}")

    def get_server(self) -> str:
        """Get the server URL."""
        if not self.server:
            raise ValueError("Server URL not set.")
        return self.server

    def set_account_id(self, account_id: str):
        """Set the account ID."""
        self.account_id = account_id

    def get_account_id(self) -> Optional[str]:
        """Get the account ID."""
        return self.account_id

    def validate_env_vars(self):
        """Validate required environment variables."""
        required_vars = ['CAPITAL_API_KEY', 'CAPITAL_API_LOGIN', 'CAPITAL_API_PASSWORD']
        for var in required_vars:
            if not os.getenv(var):
                raise ValueError(f"Environment variable {var} is not set.")

    def get_api_key(self) -> Optional[str]:
        """Get the API key."""
        return self.api_key

    def get_username(self) -> Optional[str]:
        """Get the username."""
        return self.username

    def get_password(self) -> Optional[str]:
        """Get the password."""
        return self.password

    def get_cst(self) -> str:
        """Get the CST token."""
        if not self._cst:
            raise ValueError("CST token not set.")
        return self._cst

    def set_cst(self, cst: str):
        """Set the CST token."""
        self._cst = cst

    def get_security_token(self) -> str:
        """Get the security token."""
        if not self._security_token:
            raise ValueError("Security token not set.")
        return self._security_token

    def set_security_token(self, token: str):
        """Set the security token."""
        self._security_token = token

    def authenticate(self):
        """Authenticate with Capital.com and return authentication tokens."""
        try:
            logger.info("Authenticating with Capital.com...")
            response = requests.post(
                f"{self.server}/api/v1/session",
                json={
                    "identifier": self.username,
                    "password": self.password
                },
                headers={
                    "X-CAP-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()
            self.enc_key = data.get('encryptionKey')
            self.account_id = data.get('accountId')
            logger.info("Authentication successful.")
            return {
                "CST": response.headers.get('CST'),
                "X-SECURITY-TOKEN": response.headers.get('X-SECURITY-TOKEN')
            }
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return None

    def _get_encryption_key(self):
        """Get the encryption key from the server."""
        url = f"{self.get_server()}/api/v1/session/encryptionKey"
        headers = {"X-CAP-API-KEY": self.api_key}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.enc_key = data.get("encryptionKey")
            self.time_stamp = data.get("timeStamp")
            if not self.enc_key or not self.time_stamp:
                raise ValueError("Invalid encryption key response.")
            logger.info("Encryption key and timestamp obtained successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get encryption key: {e}")
            raise

    def _encrypt_password(self) -> str:
        """Encrypt the password using RSA."""
        if not self.enc_key or not self.time_stamp:
            raise ValueError("Encryption key or timestamp not set.")
        public_key = RSA.importKey(b64decode(self.enc_key))
        cipher = PKCS1_v1_5.new(public_key)
        password_with_timestamp = f"{self.password}|{self.time_stamp}"
        encrypted_password = cipher.encrypt(password_with_timestamp.encode())
        return b64encode(encrypted_password).decode()

    def test_connection(self) -> bool:
        """Test connection to the API server by making a lightweight request."""
        url = f"{self.server}/api/v1/accounts"  # Using the accounts endpoint
        headers = {"X-CAP-API-KEY": self.api_key}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            logger.info("Connection to server successful.")
            return True
        except requests.exceptions.HTTPError as e:
            logger.error(f"Connection test failed: {e}")
            # Gracefully handle the 400 error
            if response.status_code == 400:
                logger.warning("Connection requires authentication. Proceeding with tests...")
                return False
            raise