# request_handler.py
from typing import Dict, Any, Tuple, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict
from urllib3.util.retry import Retry
import logging
import os
import json
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException

logger = logging.getLogger(__name__)

class RequestHandler:
    """
    A class to handle HTTP requests with retry mechanism and exponential backoff.
    """
    def __init__(self):
        """Initialize RequestHandler."""
        self._default_headers = {"Content-Type": "application/json"}
        self._auth_headers = {}
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        self.session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
        
        # Initialize credentials
        self.credentials = self.fetch_credentials()

    @property
    def headers(self):
        """Get combined headers."""
        return {**self._default_headers, **self._auth_headers}

    def update_headers(self, new_headers: Dict[str, str]):
        """Update headers safely."""
        if not isinstance(new_headers, dict):
            raise ValueError("Headers must be a dictionary")
        self._auth_headers.update(new_headers)
        logger.debug("Headers updated successfully")

    def update_auth_headers(self, headers: Dict[str, str]) -> None:
        """Update authentication headers safely."""
        if not isinstance(headers, dict):
            raise ValueError("Headers must be a dictionary")
        if "CST" not in headers or "X-SECURITY-TOKEN" not in headers:
            raise ValueError("Missing required authentication headers: CST or X-SECURITY-TOKEN")
        self._auth_headers.update(headers)

    def clear_auth_headers(self) -> None:
        """Clear authentication headers safely."""
        self._auth_headers.clear()
        logger.debug("Authentication headers cleared")

    def fetch_credentials(self) -> Dict[str, str]:
        """Fetch credentials from database or active_account.json"""
        # First try to get from database
        try:
            # Import here to avoid circular imports
            from src.Exchanges.capital_com_api.account_db import get_active_account_from_db
            
            # Get account from database
            account_data = get_active_account_from_db()
            
            if account_data and account_data.get('server') and account_data.get('account', {}).get('accountId'):
                logger.info(f"Loaded active account from database: {account_data['account'].get('accountName')} on {account_data['server']}")
                return {
                    'server': account_data.get('server', ''),
                    'account_id': account_data['account'].get('accountId', ''),
                    'api_key': os.getenv('CAPITAL_API_KEY', '')
                }
                
        except Exception as db_err:
            logger.warning(f"Failed to load account from database: {db_err}, falling back to file")
        
        # Then try the new location
        active_account_path = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Credentials/active_account.json'
        try:
            with open(active_account_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded active account from file: {active_account_path}")
                return {
                    'server': data.get('server', ''),
                    'account_id': data.get('account', {}).get('accountId', ''),
                    'api_key': os.getenv('CAPITAL_API_KEY', '')
                }
        except FileNotFoundError:
            logger.warning(f"Active account file not found at {active_account_path}. Using defaults.")
            return {
                'server': 'https://demo-api-capital.backend-capital.com',  # Default to demo server
                'account_id': '',
                'api_key': os.getenv('CAPITAL_API_KEY', '')
            }

    def make_request(self, method: str, url: str, data: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Make HTTP request with automatic retries and error handling."""
        try:
            method = method.lower()
            if method not in ['get', 'post', 'put', 'delete']:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response = requests.request(
                method=method,
                url=url,
                data=data,
                headers=headers or {},
                verify=True
            )

            # Handle 204 No Content for DELETE requests
            if response.status_code == 204:
                # Convert CaseInsensitiveDict to regular dict
                headers_dict = dict(response.headers)
                return {}, headers_dict

            # Handle other responses
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('errorCode', str(response.text))
                except json.JSONDecodeError:
                    error_msg = response.text
                raise CapitalAPIException(error_msg)

            try:
                # Convert CaseInsensitiveDict to regular dict
                headers_dict = dict(response.headers)
                return response.json(), headers_dict
            except json.JSONDecodeError:
                # Convert CaseInsensitiveDict to regular dict
                headers_dict = dict(response.headers)
                return {}, headers_dict

        except requests.exceptions.RequestException as e:
            raise CapitalAPIException(f"Request failed: {str(e)}")
        except Exception as e:
            raise CapitalAPIException(f"Unexpected error: {str(e)}")

    def clear_auth_tokens(self) -> None:
        """Clear authentication tokens."""
        self.auth_tokens = {}

    def close_session(self):
        """Close the session explicitly."""
        self.session.close()

    def setup_retry(self, session: requests.Session, retries: int = 3, backoff_factor: float = 0.3) -> None:
        """Setup retry strategy for requests."""
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)