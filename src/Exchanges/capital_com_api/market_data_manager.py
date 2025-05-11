import logging
import json
import os
import requests
from pathlib import Path
from typing import Dict, Any
from .session_manager import SessionManager
from .request_handler import RequestHandler

logger = logging.getLogger(__name__)

class MarketDataManager:
    def __init__(self, session_manager: SessionManager, request_handler: RequestHandler):
        self.session_manager = session_manager
        self.request_handler = request_handler
        
        try:
            # First try to get from database
            try:
                # Import here to avoid circular imports
                from src.Exchanges.capital_com_api.account_db import get_active_account_from_db
                
                # Get account from database
                account_data = get_active_account_from_db()
                
                if account_data:
                    logger.info(f"Loaded account from database: {account_data['account'].get('accountName')} on {account_data['server']}")
                    self.account_config = account_data
                    return
            except Exception as db_err:
                logger.warning(f"Failed to load account from database: {db_err}, trying fallback")
            
            # Fallback to new file path
            base_dir = self._get_base_dir()
            active_account_path = os.path.join(base_dir, 'src', 'Credentials', 'active_account.json')
            
            if os.path.exists(active_account_path):
                logger.debug(f"Using active account path: {active_account_path}")
                with open(active_account_path, 'r') as f:
                    self.account_config = json.load(f)
                    logger.info(f"Loaded account configuration from file: {active_account_path}")
            else:
                # Last resort, try the old path for compatibility
                old_path = os.path.join(base_dir, 'Backend', 'Utils', 'Config', 'active_account.json')
                if os.path.exists(old_path):
                    logger.warning(f"Using deprecated path: {old_path}")
                    with open(old_path, 'r') as f:
                        self.account_config = json.load(f)
                else:
                    logger.warning("No active account configuration found, using defaults")
                    self.account_config = {
                        "server": "https://demo-api-capital.backend-capital.com",
                        "account": {"accountId": None}
                    }
        except Exception as e:
            logger.error(f"Error loading account configuration: {e}")
            # Use defaults as fallback
            self.account_config = {
                "server": "https://demo-api-capital.backend-capital.com",
                "account": {"accountId": None}
            }
    
    def _get_base_dir(self):
        """Get the base directory dynamically."""
        # First check from environment variable
        if "ROOT_DIR" in os.environ:
            return os.environ["ROOT_DIR"]
        
        # Next try to determine from script location
        script_path = Path(__file__).resolve()
        # Go up three levels from src/Exchanges/capital_com_api/market_data_manager.py
        return str(script_path.parent.parent.parent.parent)

    def all_top(self) -> Dict[str, Any]:
        """Fetch all top-level nodes."""
        logger.info("Fetching all top-level nodes")
        try:
            self.session_manager.create_session()
            url = f"{self.session_manager.server}/api/v1/marketnavigation"
            logger.debug(f"Request URL: {url}")
            try:
                data, _ = self.request_handler.make_request(
                    method="get",
                    url=url,
                    data="",
                    headers={
                        "CST": str(self.session_manager.CST or ""),
                        "X-SECURITY-TOKEN": str(self.session_manager.X_TOKEN or "")
                    }
                )
                logger.info("Fetched all top-level nodes successfully")
                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching all top-level nodes: {e}")
                if e.response is not None:
                    logger.error(f"Response Status Code: {e.response.status_code}")
                    logger.error(f"Response Text: {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"Error fetching all top-level nodes: {e}")
            raise
        finally:
            self.session_manager.end_session()  # Changed from close_session

    def all_top_sub(self, node_id: str) -> Dict[str, Any]:
        """Fetch all sub-nodes for node ID."""
        logger.info("Fetching all sub-nodes for node ID: %s", node_id)
        self.session_manager.create_session()
        url = f"{self.session_manager.server}/api/v1/marketnavigation/{node_id}?limit=500"
        logger.debug(f"Request URL: {url}")
        try:
            headers = {}
            if self.session_manager.CST:
                headers["CST"] = str(self.session_manager.CST)
            if self.session_manager.X_TOKEN:
                headers["X-SECURITY-TOKEN"] = str(self.session_manager.X_TOKEN)
                
            data, _ = self.request_handler.make_request(
                method="get",
                url=url,
                data="",
                headers=headers
            )
            logger.info("Fetched all sub-nodes successfully")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching all sub-nodes for node ID {node_id}: {e}")
            if e.response is not None:
                logger.error(f"Response Status Code: {e.response.status_code}")
                logger.error(f"Response Text: {e.response.text}")
            raise
        finally:
            self.session_manager.end_session()  # Changed from destroy_session

    def market_details(self, market: str) -> Dict[str, Any]:
        """Fetch market details."""
        logger.info("Fetching market details for market: %s", market)
        self.session_manager.create_session()
        url = f"{self.session_manager.server}/api/v1/markets?searchTerm={market}"
        logger.debug(f"Request URL: {url}")
        try:
            headers = {}
            if self.session_manager.CST:
                headers["CST"] = str(self.session_manager.CST)
            if self.session_manager.X_TOKEN:
                headers["X-SECURITY-TOKEN"] = str(self.session_manager.X_TOKEN)

            data, _ = self.request_handler.make_request(
                method="get",
                url=url,
                data="",
                headers=headers
            )
            logger.info("Fetched market details successfully")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching market details for market {market}: {e}")
            if e.response is not None:
                logger.error(f"Response Status Code: {e.response.status_code}")
                logger.error(f"Response Text: {e.response.text}")
            raise
        finally:
            self.session_manager.end_session()  # Changed from destroy_session

    def single_market_details(self, epic: str) -> Dict[str, Any]:
        """Fetch single market details."""
        logger.info("Fetching single market details for epic: %s", epic)
        self.session_manager.create_session()
        url = f"{self.session_manager.server}/api/v1/markets/{epic}"
        logger.debug(f"Request URL: {url}")
        try:
            headers = {}
            if self.session_manager.CST:
                headers["CST"] = str(self.session_manager.CST)
            if self.session_manager.X_TOKEN:
                headers["X-SECURITY-TOKEN"] = str(self.session_manager.X_TOKEN)

            data, _ = self.request_handler.make_request(
                method="get",
                url=url,
                data="",
                headers=headers
            )
            logger.info("Fetched single market details successfully")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching single market details for epic {epic}: {e}")
            if e.response is not None:
                logger.error(f"Response Status Code: {e.response.status_code}")
                logger.error(f"Response Text: {e.response.text}")
            raise
        finally:
            self.session_manager.end_session()  # Changed from close_session/destroy_session

    def prices(self, epic: str, resolution: str = "MINUTE", max: int = 10) -> Dict[str, Any]:
        """Fetch historical prices."""
        logger.info("Fetching historical prices for epic: %s", epic)
        try:
            self.session_manager.create_session()
            url = f"{self.session_manager.server}/api/v1/prices/{epic}?resolution={resolution}&max={max}"
            logger.debug(f"Request URL: {url}")
            try:
                headers = {}
                if self.session_manager.CST:
                    headers["CST"] = str(self.session_manager.CST)
                if self.session_manager.X_TOKEN:
                    headers["X-SECURITY-TOKEN"] = str(self.session_manager.X_TOKEN)

                data, _ = self.request_handler.make_request(
                    method="get",
                    url=url,
                    data="",
                    headers=headers
                )
                logger.info("Fetched historical prices successfully")
                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching historical prices for epic {epic}: {e}")
                if e.response is not None:
                    logger.error(f"Response Status Code: {e.response.status_code}")
                    logger.error(f"Response Text: {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            raise
        finally:
            self.session_manager.end_session()  # Add session cleanup

    def client_sentiment(self, market_id: str) -> Dict[str, Any]:
        """Fetch client sentiment for market ID."""
        logger.info("Fetching client sentiment for market ID: %s", market_id)
        try:
            self.session_manager.create_session()
            url = f"{self.session_manager.server}/api/v1/clientsentiment/{market_id}"
            logger.debug(f"Request URL: {url}")
            try:
                headers = {}
                if self.session_manager.CST:
                    headers["CST"] = str(self.session_manager.CST)
                if self.session_manager.X_TOKEN:
                    headers["X-SECURITY-TOKEN"] = str(self.session_manager.X_TOKEN)

                data, _ = self.request_handler.make_request(
                    method="get",
                    url=url,
                    data="",
                    headers=headers
                )
                logger.info("Fetched client sentiment successfully")
                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching client sentiment for market ID {market_id}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response Status Code: {e.response.status_code}")
                    logger.error(f"Response Text: {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"Error fetching client sentiment: {e}")
            raise
        finally:
            self.session_manager.end_session()  # Changed from close_session