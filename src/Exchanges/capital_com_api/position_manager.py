import logging
import json
from typing import Dict, Any, Optional, List
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
import time

# Create a module-level logger
logger = logging.getLogger(__name__)

class PositionManager:
    def __init__(self, session_manager: SessionManager, request_handler: RequestHandler):
        """
        Initialize the PositionManager.
        
        Args:
            session_manager: The SessionManager to handle authentication
            request_handler: The RequestHandler to send requests to the API
        """
        self.session_manager = session_manager
        self.request_handler = request_handler
        # Add this line to fix the 'PositionManager' object has no attribute 'logger' error
        self.logger = logger
        
    def all_positions(self) -> Dict[str, Any]:
        logger.info("Fetching all open positions")
        self.session_manager.create_session()
        url = f"{self.session_manager.server}/api/v1/positions"
        headers: Dict[str, str] = {
            "CST": str(self.session_manager.CST) if self.session_manager.CST else "",
            "X-SECURITY-TOKEN": str(self.session_manager.X_TOKEN) if self.session_manager.X_TOKEN else ""
        }
        data = self.request_handler.make_request("get", url, headers=headers)[0]
        logger.info("Fetched all open positions successfully")
        return data

    def position_details(self, deal_id: str) -> Dict[str, Any]:
        logger.info("Fetching position details for deal ID: %s", deal_id)
        self.session_manager.create_session()
        url = f"{self.session_manager.server}/api/v1/positions/{deal_id}"
        headers = {
            "CST": str(self.session_manager.CST) if self.session_manager.CST else "",
            "X-SECURITY-TOKEN": str(self.session_manager.X_TOKEN) if self.session_manager.X_TOKEN else ""
        }
        data = self.request_handler.make_request("get", url, headers=headers)[0]
        logger.info("Fetched position details successfully")
        return data

    def create_position(self, epic: str, direction: str, size: float, 
                       type: str = "MARKET", timeInForce: str = "FILL_OR_KILL", 
                       stopLevel: Optional[float] = None, 
                       profitLevel: Optional[float] = None,
                       limitLevel: Optional[float] = None, 
                       **kwargs) -> Dict[str, Any]:
        """
        Create a new position (open a trade).
        """
        self.logger.info(f"Creating position with args: {locals()}")
        
        # Format the position request payload
        payload = {
            'epic': epic,
            'direction': direction,
            'size': str(size),
            'orderType': type,
            'timeInForce': timeInForce
        }
        
        # Add optional parameters if they're provided
        if stopLevel:
            payload['stopLevel'] = str(stopLevel)
            
        if profitLevel:
            self.logger.info(f"Setting profit level to {profitLevel}")
            payload['profitLevel'] = str(profitLevel)
            
        if limitLevel:
            payload['limitLevel'] = str(limitLevel)
            
        # Add any additional parameters
        for key, value in kwargs.items():
            payload[key] = value
            
        # Send the request to create the position
        self.logger.debug(f"Sending position request with method=post, url={self.session_manager.server}/api/v1/positions, payload={payload}")
        # Fix: Changed send_request to make_request
        headers = {
            "CST": str(self.session_manager.CST) if self.session_manager.CST else "",
            "X-SECURITY-TOKEN": str(self.session_manager.X_TOKEN) if self.session_manager.X_TOKEN else "",
            "Content-Type": "application/json"
        }
        response = self.request_handler.make_request(
            method="post",
            url=f"{self.session_manager.server}/api/v1/positions",
            data=json.dumps(payload),
            headers=headers
        )[0]
        
        return response

    def update_position(self, deal_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing position with new parameters.
        
        Args:
            deal_id: The deal ID of the position to update
            **kwargs: Parameters to update
        
        Returns:
            API response
        """
        logger.info(f"Updating position {deal_id} with args: {kwargs}")
        
        # Create the payload
        payload = {}
        
        # Handle trailing stop vs guaranteed stop - critical for hedging accounts
        if kwargs.get('trailingStop', False):
            # IMPORTANT: For hedging accounts, must be string "true" not boolean
            payload['trailingStop'] = "true"  # API expects string "true" not boolean
            
            # stopDistance is required when trailingStop is true
            if 'stopDistance' in kwargs:
                payload['stopDistance'] = str(kwargs['stopDistance'])
                logger.info(f"Using provided stop distance: {payload['stopDistance']}")
            elif 'trailingStopDistance' in kwargs:
                payload['stopDistance'] = str(kwargs['trailingStopDistance'])
                logger.info(f"Using trailing stop distance: {payload['stopDistance']}")
            else:
                logger.warning("Trailing stop enabled but no distance specified - attempting to get position details")
                try:
                    # Try to get position details to calculate a reasonable stop distance
                    pos_details = self.position_details(deal_id)
                    position_data = pos_details.get('position', {})
                    
                    if position_data:
                        # Get market price from position data
                        level = float(position_data.get('level', 0))
                        if level > 0:
                            # For crypto like BTC/USD, use 1% as default
                            epic = position_data.get('epic', '').upper()
                            default_percent = 1.0 if 'BTC' in epic or 'USD' in epic else 0.5
                            stop_distance = level * default_percent / 100
                            payload['stopDistance'] = str(stop_distance)
                            logger.info(f"Calculated default trailing stop distance: {stop_distance} ({default_percent}%)")
                except Exception as e:
                    logger.error(f"Failed to calculate default trailing stop: {str(e)}")
                    logger.warning("No stopDistance provided - trailing stop may fail without it")
        elif kwargs.get('guaranteedStop', False):
            payload['guaranteedStop'] = "true"  # API expects string "true" not boolean
        
        # Add other parameters if provided
        for param in ['stopLevel', 'stopAmount', 'profitLevel', 'profitDistance', 'profitAmount']:
            if param in kwargs:
                payload[param] = str(kwargs[param])
        
        if not payload:
            logger.warning("No parameters provided for position update")
            return {"status": "error", "message": "No parameters provided for update"}
        
        logger.debug(f"Update position payload: {payload}")
        
        # Update the position
        self.session_manager.create_session()
        url = f"{self.session_manager.server}/api/v1/positions/{deal_id}"
        headers = {
            "CST": str(self.session_manager.CST) if self.session_manager.CST else "",
            "X-SECURITY-TOKEN": str(self.session_manager.X_TOKEN) if self.session_manager.X_TOKEN else "",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.request_handler.make_request("put", url, json.dumps(payload), headers=headers)[0]
            logger.info(f"Position {deal_id} updated successfully")
            return response
        except Exception as e:
            error_msg = f"Error updating position: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

    def schedule_trailing_stop_verification(self, epic, direction):
        """Schedule a verification of trailing stop after position creation"""
        try:
            # Wait 2 seconds to allow position to be created
            time.sleep(2)
            
            # Get all positions
            positions = self.all_positions()
            all_positions = positions.get('positions', [])
            
            # Find the most recently created position matching our epic and direction
            matching_positions = []
            for pos in all_positions:
                position_data = pos.get('position', {})
                market_data = pos.get('market', {})
                
                if market_data.get('epic') == epic and position_data.get('direction') == direction:
                    matching_positions.append(pos)
            
            if matching_positions:
                # Sort by creation time, newest first
                sorted_positions = sorted(matching_positions, 
                                         key=lambda x: x.get('position', {}).get('createdDate', ''), 
                                         reverse=True)
                
                newest_position = sorted_positions[0]
                position_id = newest_position.get('position', {}).get('dealId')
                
                # Check if trailing stop is active
                has_trailing = newest_position.get('position', {}).get('trailingStop', False)
                
                if not has_trailing:
                    logger.warning(f"Position {position_id} was created but trailing stop appears inactive! Attempting to add it...")
                    
                    # Try to update the position to add trailing stop
                    self.update_position(position_id, trailingStop=True, 
                                       stopDistance=newest_position.get('position', {}).get('stopLevel', 0.01))
                    
                    # Verify again
                    time.sleep(1)
                    updated_position = self.position_details(position_id)
                    if updated_position.get('position', {}).get('trailingStop', False):
                        logger.info(f"Successfully added trailing stop to position {position_id}")
                    else:
                        logger.error(f"Failed to add trailing stop to position {position_id}")
                else:
                    logger.info(f"Position {position_id} has trailing stop correctly applied")
                    
        except Exception as e:
            logger.error(f"Error verifying trailing stop: {str(e)}")

    def close_position(self, deal_id: str) -> Dict[str, Any]:
        """
        Close a position by deal ID.
        
        Args:
            deal_id: Deal identifier for the position to close
            
        Returns:
            Position closure response
        """
        logger.info(f"Closing position with deal ID: {deal_id}")
        
        # First get position details to determine direction and size
        position_details = self.position_details(deal_id)
        position_data = position_details.get('position', {})
        
        if not position_data:
            error_msg = f"Position {deal_id} not found or cannot be retrieved"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        # Get the position direction and size
        direction = position_data.get('direction')
        if not direction:
            error_msg = f"Could not determine direction for position {deal_id}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
            
        size = position_data.get('size')
        if not size:
            error_msg = f"Could not determine size for position {deal_id}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        # Determine close direction (opposite of position direction)
        close_direction = "BUY" if direction == "SELL" else "SELL"
        
        # Prepare close position request
        close_data = {
            "dealId": deal_id,
            "direction": close_direction,
            "size": str(size),
            "orderType": "MARKET"
        }
        
        # Ensure we have an active session
        self.session_manager.create_session()
        
        url = f"{self.session_manager.server}/api/v1/positions/otc"
        headers = {
            "CST": str(self.session_manager.CST) if self.session_manager.CST else "",
            "X-SECURITY-TOKEN": str(self.session_manager.X_TOKEN) if self.session_manager.X_TOKEN else "",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.request_handler.make_request("post", url, json.dumps(close_data), headers=headers)[0]
            logger.info(f"Position {deal_id} closed successfully")
            return response
        except Exception as e:
            error_msg = f"Error closing position: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}