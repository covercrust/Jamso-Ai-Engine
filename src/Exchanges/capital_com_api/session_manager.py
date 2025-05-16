# session_manager.py
import requests
import time
import os
import json
import http.client
from typing import Dict, Any, Tuple, Optional, List, Union
from requests.structures import CaseInsensitiveDict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from base64 import b64decode, b64encode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException
from src.Exchanges.capital_com_api.account_config import AccountConfig
from src.Credentials.credentials_manager import CredentialManager

class SessionManager:
    MAX_SESSIONS = 10
    active_sessions = 0

    def __init__(self, server: str, api_key: Optional[str] = None, 
                 username: Optional[str] = None, password: Optional[str] = None,
                 auth_tokens: Optional[Dict[str, str]] = None):
        """Initialize session manager with credentials from params or environment."""        
        self.server = server.rstrip('/')
        
        # Ensure all credentials are fetched dynamically from the database
        credential_manager = CredentialManager()
        credentials = {
            'CAPITAL_API_KEY': credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY'),
            'CAPITAL_API_LOGIN': credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN'),
            'CAPITAL_API_PASSWORD': credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')
        }

        self.api_key = api_key or credentials.get('CAPITAL_API_KEY', '')
        self.username = username or credentials.get('CAPITAL_API_LOGIN', '')
        self.password = password or credentials.get('CAPITAL_API_PASSWORD', '')
        
        # Initialize auth tokens and session state
        self.CST = auth_tokens.get('CST', '') if auth_tokens else ''
        self.X_TOKEN = auth_tokens.get('X-SECURITY-TOKEN', '') if auth_tokens else ''
        self.is_authenticated = bool(self.CST and self.X_TOKEN)
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Seconds between requests
        self.last_auth_time = time.time()  # Initialize last auth time
        
        # Track authentication attempts
        self.auth_attempts = 0
        self.last_auth_attempt = 0
        
        # Set up session with retry
        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json", "X-CAP-API-KEY": self.api_key}
        if self.CST and self.X_TOKEN:
            self.headers.update({"CST": self.CST, "X-SECURITY-TOKEN": self.X_TOKEN})

    def _update_auth_headers(self):
        """Update headers with authentication tokens"""
        if self.CST and self.X_TOKEN:
            self.headers.update({
                "CST": self.CST,
                "X-SECURITY-TOKEN": self.X_TOKEN
            })

    def _wait_for_rate_limit(self):
        """Implement smarter rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed + 0.1)  # Small buffer
        self.last_request_time = time.time()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication tokens if available."""
        headers = {
            "Content-Type": "application/json",
            "X-CAP-API-KEY": self.api_key
        }
        if self.CST and self.X_TOKEN:
            headers.update({
                "CST": self.CST,
                "X-SECURITY-TOKEN": self.X_TOKEN
            })
        return headers

    def create_session(self, attempt: int = 1, max_attempts: int = 3) -> Dict[str, Any]:
        """
        Create a new session or refresh existing session.
        
        Returns:
            Dict containing status and error information if applicable
        """
        if SessionManager.active_sessions >= SessionManager.MAX_SESSIONS:
            return {"success": False, "error_code": "SESSION_LIMIT", "error_message": "Maximum session limit reached.", "attempt": attempt}
        
        SessionManager.active_sessions += 1
        try:
            # Return detailed status information for better error handling
            result = {
                "success": False,
                "error_code": None,
                "error_message": None,
                "attempt": attempt
            }
            
            # Skip if already authenticated (first attempt)
            if self.is_authenticated and attempt == 1:
                if self._is_token_valid():
                    result["success"] = True
                    return result
            
            if attempt > max_attempts:
                result["error_code"] = "MAX_ATTEMPTS_EXCEEDED"
                result["error_message"] = f"Failed to create session after {max_attempts} attempts"
                return result
            
            headers = {
                "X-CAP-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "identifier": self.username,
                "password": self.password
            }
            
            try:
                response = requests.post(
                    f"{self.server}/api/v1/session",
                    headers=headers,
                    json=data,
                    timeout=10  # Add timeout for better resilience
                )
                
                if response.status_code == 200:
                    self.CST = response.headers.get('CST')
                    self.X_TOKEN = response.headers.get('X-SECURITY-TOKEN')
                    self.is_authenticated = True
                    self.last_auth_time = time.time()
                    result["success"] = True
                    return result
                
                # Add detailed error information
                result["error_code"] = f"HTTP_{response.status_code}"
                
                # Try to parse error message from response
                try:
                    error_data = response.json()
                    result["error_message"] = error_data.get("errorCode", "") + ": " + error_data.get("errorMessage", "")
                except:
                    result["error_message"] = f"HTTP error {response.status_code}: {response.reason}"
                
                # Rate limiting specific handling
                if response.status_code == 429:
                    result["error_code"] = "RATE_LIMITED"
                    wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30 seconds
                    time.sleep(wait_time)
                    return self.create_session(attempt + 1, max_attempts)
                    
                # Session expired specific handling
                if response.status_code == 401:
                    result["error_code"] = "SESSION_EXPIRED"
                    self.CST = None
                    self.X_TOKEN = None
                    self.is_authenticated = False
                    if attempt < max_attempts:
                        return self.create_session(attempt + 1, max_attempts)
                
                return result
                
            except requests.exceptions.ConnectionError as e:
                result["error_code"] = "CONNECTION_ERROR"
                result["error_message"] = str(e)
                
            except requests.exceptions.Timeout as e:
                result["error_code"] = "TIMEOUT_ERROR"
                result["error_message"] = str(e)
                
            except Exception as e:
                result["error_code"] = "UNEXPECTED_ERROR"
                result["error_message"] = str(e)
            
            # Retry logic
            if attempt < max_attempts:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                return self.create_session(attempt + 1, max_attempts)
            
            return result
        finally:
            if not self.is_authenticated:
                SessionManager.active_sessions -= 1

    def _is_token_valid(self) -> bool:
        """Check if the current authentication token is still valid."""
        if not self.CST or not self.X_TOKEN:
            return False
            
        # Token age check - refresh if older than 15 minutes
        if time.time() - self.last_auth_time > 900:  # 15 minutes in seconds
            return False
            
        # Verify token with a lightweight API call
        try:
            conn = http.client.HTTPSConnection(self.server.replace('https://', ''))
            headers = {
                "X-CAP-API-KEY": self.api_key,
                "CST": self.CST,
                "X-SECURITY-TOKEN": self.X_TOKEN
            }
            conn.request("GET", "/api/v1/session", headers=headers)
            res = conn.getresponse()
            
            # Read and discard the response data
            res.read()
            
            # Check if we got a successful response
            if res.status == 200:
                return True
                
            # If we got a 401 or other error, token is invalid
            return False
        except Exception as e:
            return False
        finally:
            conn.close()

    def _handle_session_response(self, response: requests.Response) -> None:
        """Handle the session response and update tokens."""
        try:
            self.CST = response.headers.get('CST')
            self.X_TOKEN = response.headers.get('X-SECURITY-TOKEN')
            if not (self.CST and self.X_TOKEN):
                raise CapitalAPIException("Missing authentication tokens in response")
            self._update_auth_headers()
        except Exception as e:
            raise CapitalAPIException(f"Failed to handle session response: {e}")

    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to the API."""
        headers = {
            "Content-Type": "application/json",
            "X-CAP-API-KEY": self.api_key
        }
        if self.CST and self.X_TOKEN:
            headers.update({
                "CST": self.CST,
                "X-SECURITY-TOKEN": self.X_TOKEN
            })
        try:
            self._wait_for_rate_limit()
            response = requests.request(
                method=method,
                url=f"{self.server}{endpoint}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {}

    def _get_encryption_key(self) -> None:
        """Fetch the encryption key for password encryption"""
        url = f"{self.server}/api/v1/session/encryptionKey"
        data = self._make_request("GET", url, None)
        self.enc_key = data.get("encryptionKey")  # Use dict get method

    def _encrypt(self, password: str, key_str: str) -> str:
        """Encrypt the password using the retrieved RSA key"""
        key_bytes = b64decode(key_str)
        rsa_key = RSA.importKey(key_bytes)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = cipher.encrypt(password.encode())
        return b64encode(encrypted).decode()

    def fetch_account_details(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Fetch account details."""
        try:
            if not self.is_authenticated:
                self.create_session()

            account_info = self._make_request("GET", "/api/v1/session", None)
            if not account_info:
                raise ValueError("Failed to fetch account information")

            account_list = self._make_request("GET", "/api/v1/accounts", None)
            if not account_list:
                raise ValueError("Failed to fetch account list")

            return account_info, account_list
            
        except Exception as e:
            return {}, {}

    def fetch_account_list(self) -> List[Dict[str, Any]]:
        """Fetch list of accounts."""
        try:
            if not self.is_authenticated:
                self.create_session()

            account_list = self._make_request("GET", "/api/v1/accounts", None)
            if not account_list:
                return []  # Return empty list instead of None

            return account_list.get('accounts', [])

        except Exception as e:
            return []  # Return empty list on error

    def end_session(self) -> None:
        """End the current session and clear authentication tokens."""
        try:
            if self.is_authenticated:
                # Try to logout from the API
                try:
                    self._make_request("DELETE", "/api/v1/session")
                except Exception as e:
                    pass

                # Clear authentication tokens
                self.CST = None
                self.X_TOKEN = None
                self.is_authenticated = False
        except Exception as e:
            raise