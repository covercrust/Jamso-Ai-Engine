import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple, cast
from datetime import datetime

from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException

logger = logging.getLogger(__name__)

class OrderManager:
    """Manages trading orders for Capital.com API"""
    
    def __init__(self, session_manager: SessionManager, request_handler: RequestHandler):
        """
        Initialize OrderManager with session manager and request handler.
        
        Args:
            session_manager: Authenticated SessionManager instance
            request_handler: RequestHandler instance for API calls
        """
        self.session_manager = session_manager
        self.request_handler = request_handler
        
    def _sanitize_headers(self, headers: Dict[str, Optional[str]]) -> Dict[str, str]:
        """
        Sanitize headers by removing None values.
        
        Args:
            headers: Dictionary of headers that might contain None values
            
        Returns:
            Dictionary with only string values
        """
        # Filter out None values and ensure all values are strings
        return {k: str(v) for k, v in headers.items() if v is not None}
        
    def create_order(self, 
                    epic: str, 
                    direction: str, 
                    size: float, 
                    order_type: str = "MARKET",
                    limit_distance: Optional[float] = None, 
                    stop_distance: Optional[float] = None,
                    guaranteed_stop: bool = False,
                    trailing_stop: bool = False) -> Dict[str, Any]:
        """
        Create a new trading order.
        
        Args:
            epic: Market identifier
            direction: BUY or SELL
            size: Trade size
            order_type: Type of order (MARKET, LIMIT, etc.)
            limit_distance: Distance for limit orders
            stop_distance: Distance for stop orders
            guaranteed_stop: Whether to use guaranteed stop
            trailing_stop: Whether to use trailing stop
            
        Returns:
            Order creation response
        """
        try:
            if not self.session_manager.is_authenticated:
                self.session_manager.create_session()
                
            order_data = {
                "epic": epic,
                "direction": direction.upper(),
                "size": str(size),
                "orderType": order_type
            }
            
            # Add optional parameters if provided
            if limit_distance:
                order_data["limitDistance"] = str(limit_distance)
                
            if stop_distance:
                order_data["stopDistance"] = str(stop_distance)
                
            if guaranteed_stop:
                order_data["guaranteedStop"] = "true"
                
            if trailing_stop:
                order_data["trailingStop"] = "true"
                
            # Get headers and sanitize them by removing any None values
            headers = self._sanitize_headers({
                "Content-Type": "application/json",
                "X-CAP-API-KEY": self.session_manager.api_key,
                "CST": self.session_manager.CST,
                "X-SECURITY-TOKEN": self.session_manager.X_TOKEN
            })
            
            # Make API request with sanitized headers
            response, resp_headers = self.request_handler.make_request(
                "POST", 
                f"{self.session_manager.server}/api/v1/positions", 
                json.dumps(order_data), 
                headers
            )
            
            logger.info(f"Created order: {epic}, {direction}, {size}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            raise CapitalAPIException(f"Failed to create order: {str(e)}")
            
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Returns:
            List of position dictionaries
        """
        try:
            if not self.session_manager.is_authenticated:
                self.session_manager.create_session()
                
            # Get headers and sanitize them
            headers = self._sanitize_headers({
                "Content-Type": "application/json",
                "X-CAP-API-KEY": self.session_manager.api_key,
                "CST": self.session_manager.CST,
                "X-SECURITY-TOKEN": self.session_manager.X_TOKEN
            })
                
            response, _ = self.request_handler.make_request(
                "GET",
                f"{self.session_manager.server}/api/v1/positions",
                None,
                headers
            )
            
            positions = response.get('positions', [])
            logger.info(f"Retrieved {len(positions)} open positions")
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {str(e)}")
            raise CapitalAPIException(f"Failed to get positions: {str(e)}")
            
    def close_position(self, deal_id: str) -> Dict[str, Any]:
        """
        Close a position by deal ID.
        
        Args:
            deal_id: Deal identifier
            
        Returns:
            Position closure response
        """
        try:
            if not self.session_manager.is_authenticated:
                self.session_manager.create_session()
                
            # First get position details to determine direction and size
            position = self._get_position_details(deal_id)
            
            if not position:
                raise CapitalAPIException(f"Position not found: {deal_id}")
                
            # Determine close direction (opposite of position direction)
            direction = "BUY" if position.get('direction') == "SELL" else "SELL"
            size = position.get('size')
            
            # Prepare close position request
            close_data = {
                "dealId": deal_id,
                "direction": direction,
                "size": str(size),
                "orderType": "MARKET"
            }
            
            # Get headers and sanitize them
            headers = self._sanitize_headers({
                "Content-Type": "application/json", 
                "X-CAP-API-KEY": self.session_manager.api_key,
                "CST": self.session_manager.CST, 
                "X-SECURITY-TOKEN": self.session_manager.X_TOKEN
            })
                
            response, _ = self.request_handler.make_request(
                "POST",
                f"{self.session_manager.server}/api/v1/positions/otc",
                json.dumps(close_data),
                headers
            )
            
            logger.info(f"Closed position: {deal_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to close position: {str(e)}")
            raise CapitalAPIException(f"Failed to close position: {str(e)}")
            
    def _get_position_details(self, deal_id: str) -> Dict[str, Any]:
        """
        Get details of a specific position.
        
        Args:
            deal_id: Deal identifier
            
        Returns:
            Position details
        """
        try:
            if not self.session_manager.is_authenticated:
                self.session_manager.create_session()
                
            # Get headers and sanitize them
            headers = self._sanitize_headers({
                "Content-Type": "application/json",
                "X-CAP-API-KEY": self.session_manager.api_key,
                "CST": self.session_manager.CST,
                "X-SECURITY-TOKEN": self.session_manager.X_TOKEN
            })
                
            response, _ = self.request_handler.make_request(
                "GET",
                f"{self.session_manager.server}/api/v1/positions/{deal_id}",
                None,
                headers
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get position details: {str(e)}")
            raise CapitalAPIException(f"Failed to get position details: {str(e)}")