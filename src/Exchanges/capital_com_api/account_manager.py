# account_manager.py
import logging
import json
import os
from typing import Dict, Any, List, Optional, Union, Tuple

# Import SessionManager from session_manager module
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException
from src.Exchanges.capital_com_api.account_config import AccountConfig

logger = logging.getLogger(__name__)

class AccountManager:
    """Manages Capital.com trading accounts and provides account operations"""
    
    def __init__(self, session_manager: SessionManager, account_config=None):
        """
        Initialize AccountManager with a SessionManager instance.
        
        Args:
            session_manager: Authenticated SessionManager instance
            account_config: Optional AccountConfig instance
        """
        self.session_manager = session_manager
        self.account_config = account_config
        self.active_account_id = None
        self.accounts = []
        
    def load_accounts(self) -> List[Dict[str, Any]]:
        """
        Load all available trading accounts.
        
        Returns:
            List of account dictionaries
        """
        try:
            if not self.session_manager.is_authenticated:
                self.session_manager.create_session()
                
            accounts_response = self.session_manager._make_request("GET", "/api/v1/accounts")
            self.accounts = accounts_response.get('accounts', [])
            logger.info(f"Loaded {len(self.accounts)} accounts")
            return self.accounts
        except Exception as e:
            logger.error(f"Failed to load accounts: {str(e)}")
            raise CapitalAPIException(f"Failed to load accounts: {str(e)}")
    
    def set_active_account(self, account_id: str) -> Dict[str, Any]:
        """
        Set active trading account by ID.
        
        Args:
            account_id: Account ID to set as active
            
        Returns:
            Account info dictionary
        """
        try:
            if not self.session_manager.is_authenticated:
                self.session_manager.create_session()
                
            # Find account in loaded accounts
            if not self.accounts:
                self.load_accounts()
                
            account = next((acc for acc in self.accounts if acc.get('accountId') == account_id), None)
            if not account:
                raise ValueError(f"Account ID {account_id} not found")
                
            # Set active account in API
            response = self.session_manager._make_request(
                "PUT", 
                f"/api/v1/session",
                {"accountId": account_id}
            )
            
            self.active_account_id = account_id
            logger.info(f"Set active account: {account_id}")
            
            # Save to config file
            self._save_active_account(account)
            
            return account
        except Exception as e:
            logger.error(f"Failed to set active account: {str(e)}")
            raise CapitalAPIException(f"Failed to set active account: {str(e)}")
    
    def get_active_account(self) -> Dict[str, Any]:
        """
        Get currently active trading account.
        
        Returns:
            Active account info dictionary
        """
        try:
            if not self.session_manager.is_authenticated:
                self.session_manager.create_session()
                
            response = self.session_manager._make_request("GET", "/api/v1/session")
            
            if 'currentAccountId' in response:
                self.active_account_id = response['currentAccountId']
                
                # Find full account info
                if not self.accounts:
                    self.load_accounts()
                    
                account = next((acc for acc in self.accounts if acc.get('accountId') == self.active_account_id), None)
                if account:
                    return account
            
            return response
        except Exception as e:
            logger.error(f"Failed to get active account: {str(e)}")
            raise CapitalAPIException(f"Failed to get active account: {str(e)}")
    
    def _save_active_account(self, account: Dict[str, Any]) -> None:
        """
        Save active account info to configuration file.
        
        Args:
            account: Account information to save
        """
        try:
            config_dir = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Credentials'
            os.makedirs(config_dir, exist_ok=True)
            
            save_data = {
                "accountId": account.get('accountId'),
                "accountType": account.get('accountType'),
                "preferred": account.get('preferred', False),
                "server": self.session_manager.server,
                "timestamp": account.get('timestamp', None)
            }
            
            with open(f"{config_dir}/active_account.json", 'w') as f:
                json.dump(save_data, f, indent=2)
                
            logger.debug(f"Saved active account configuration")
        except Exception as e:
            logger.error(f"Failed to save active account config: {str(e)}")