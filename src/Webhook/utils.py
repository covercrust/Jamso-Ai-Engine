import json
import os
import logging
import http.client
import time
import re
import requests  # type: ignore
from typing import Dict, Any, Optional, Union, List, cast, Tuple
from datetime import datetime
from flask import jsonify

from src.Exchanges.capital_com_api.client import Client
from src.Exchanges.capital_com_api.account_config import AccountConfig
from src.Exchanges.capital_com_api.session_manager import SessionManager
from src.Exchanges.capital_com_api.request_handler import RequestHandler
from src.Exchanges.capital_com_api.exceptions import CapitalAPIException
from src.Credentials.credentials import load_credentials, get_api_credentials, get_server_url
from src.Optional.position_validator import validate_position_size

logger = logging.getLogger(__name__)

def get_client() -> Client:
    """Initialize and return a properly authenticated Client instance."""
    try:
        # Ensure credentials are loaded from env.sh
        load_credentials()
        
        # Get API credentials and server URL
        creds = get_api_credentials()
        server = get_server_url()
        
        # Handle missing username field gracefully
        if 'username' not in creds or not creds['username']:
            logger.error("Missing 'username' in credentials")
            raise KeyError("username")
        
        # Log credential status (masked for security)
        logger.info(f"Creating client with server: {server}")
        logger.debug(f"API credentials - Key: {'Present' if creds['api_key'] else 'Missing'}, "
                    f"Username: {'Present' if creds['username'] else 'Missing'}, "
                    f"Password: {'Present' if creds['password'] else 'Missing'}")
        
        # Create session manager with loaded credentials
        session_manager = SessionManager(
            server=server,
            api_key=creds['api_key'],
            username=creds['username'],
            password=creds['password']
        )
        
        # Create client with session manager
        client = Client(session_manager=session_manager)
        
        # Verify authentication works with better error handling
        if not client.session_manager.is_authenticated:
            logger.info("Authenticating with Capital.com...")
            auth_result = client.session_manager.create_session()
            
            # Check authentication result explicitly
            if isinstance(auth_result, dict) and not auth_result.get('success', False):
                error_msg = auth_result.get('error_message', 'Unknown authentication error')
                logger.error(f"Authentication failed: {error_msg}")
                raise Exception(f"Authentication failed: {error_msg}")
            
        if client.session_manager.is_authenticated:
            logger.info("Successfully created authenticated client")
        else:
            error_msg = "Client creation succeeded but authentication did not complete"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        return client
        
    except Exception as e:
        logger.error(f"Failed to initialize client: {str(e)}", exc_info=True)
        raise

def get_position_details(client: Client, deal_reference: str) -> Dict[str, Any]:
    """Retrieve details of a specific position using authenticated client."""
    try:
        if not client.session_manager.is_authenticated:
            client.session_manager.create_session()
            
        conn = http.client.HTTPSConnection(client.session_manager.server.replace('https://', ''))
        headers = {
            'X-SECURITY-TOKEN': client.session_manager.X_TOKEN,
            'CST': client.session_manager.CST,
            'Content-Type': 'application/json'
        }
        
        conn.request("GET", f"/api/v1/confirms/{deal_reference}", '', headers)
        res = conn.getresponse()
        data = res.read()
        
        if res.status != 200:
            raise CapitalAPIException(res.status, res.reason, data.decode("utf-8"))
            
        return json.loads(data.decode("utf-8"))
        
    except Exception as e:
        logger.error(f"Failed to get position details: {str(e)}")
        raise

def execute_trade(client: Client, data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a trade based on the received signal data."""
    try:
        # Basic validation of required fields
        if not all(key in data for key in ['ticker', 'order_action', 'position_size']):
            raise ValueError("Missing required trading fields")

        # Apply AI-driven trading enhancements
        ai_enhanced_data = apply_ai_trading_logic(data, client)
        
        # Check if AI risk management rejected the trade
        if isinstance(ai_enhanced_data, dict) and ai_enhanced_data.get('status') == 'error':
            logger.warning(f"Trade rejected by AI risk management: {ai_enhanced_data.get('message')}")
            return ai_enhanced_data
        
        # Use the AI-enhanced data from now on
        data = ai_enhanced_data

        # Map webhook fields to API fields
        position_args = {
            'epic': str(data['ticker']),
            'direction': str(data['order_action']).upper(),
            'size': float(data['position_size']),
            'type': 'MARKET',
            'timeInForce': 'FILL_OR_KILL'
        }

        # Check if hedging is enabled (from data or default to False)
        hedging_enabled = data.get('hedging_enabled', False)
        
        # Apply position size validation with additional safety buffer
        validated_size = validate_position_size(position_args['epic'], position_args['size'])
        if validated_size != position_args['size']:
            logger.info(f"Position size adjusted from {position_args['size']} to {validated_size} to meet minimum requirements")
            position_args['size'] = validated_size

        # For CLOSE actions, add flag to create new position if not exists
        if position_args['direction'] in ['CLOSE_SELL', 'CLOSE_BUY']:
            position_args['force_create_if_not_exists'] = data.get('force_create_if_not_exists', False)

        # Handle stop loss and take profit
        if 'stop_loss' in data and float(data['stop_loss']) > 0:
            original_sl = float(data['stop_loss'])
            direction = position_args['direction']
            
            # Widen stop loss by 5% of the distance from current price to provide slippage buffer
            if 'price' in data and data['price']:
                current_price = float(data['price'])
                sl_distance = abs(current_price - original_sl)
                buffer = sl_distance * 0.05  # 5% buffer
                
                if direction in ['BUY', 'CLOSE_SELL']:
                    # For long positions, move stop loss lower
                    position_args['stopLevel'] = original_sl - buffer
                else:
                    # For short positions, move stop loss higher
                    position_args['stopLevel'] = original_sl + buffer
                
                logger.info(f"Added slippage buffer to stop loss: Original {original_sl}, Adjusted {position_args['stopLevel']}")
            else:
                position_args['stopLevel'] = original_sl
            
            # Only set guaranteed stop if trailing stop is not enabled AND hedging is enabled
            if not data.get('trailing_stop', False) and hedging_enabled:
                position_args['useGuaranteedStop'] = True
                logger.info("Using guaranteed stop with hedging enabled")
            elif not data.get('trailing_stop', False) and not hedging_enabled:
                logger.warning("Guaranteed stop requested but hedging is not enabled - using regular stop loss instead")

        # Handle trailing stop if enabled
        if data.get('trailing_stop', False) and data.get('trailing_stop') is True:
            logger.info(f"Trailing stop enabled with step percent: {data.get('trailing_step_percent', 0)}")
            position_args['trailingStop'] = True
            
            # Remove any guaranteed stop parameters since they can't be used together
            position_args.pop('useGuaranteedStop', None)
            position_args.pop('guaranteedStop', None)
            
            if 'trailing_offset' in data:
                # Add validation for trailing stop distance
                try:
                    # Check for None value before conversion to float
                    trailing_offset_value = data.get('trailing_offset')
                    if trailing_offset_value is None:
                        logger.warning("Trailing offset is None. Setting to default 0.2% of price.")
                        trailing_offset = 0
                    else:
                        trailing_offset = float(trailing_offset_value)
                        
                    if trailing_offset <= 0:
                        logger.warning(f"Invalid trailing offset: {trailing_offset}. Setting to default 0.2% of price.")
                        # Use price from webhook data or fetch current price
                        if 'price' in data and data['price']:
                            current_price = float(data['price'])
                            position_args['trailingStopDistance'] = current_price * 0.002  # 0.2% default
                        else:
                            # Fetch current price from market data
                            try:
                                market_data = client.market_data_manager.single_market_details(position_args['epic'])
                                if market_data and 'snapshot' in market_data:
                                    current_price = float(market_data['snapshot']['bid'])
                                    position_args['trailingStopDistance'] = current_price * 0.002  # 0.2% default
                            except Exception as e:
                                logger.warning(f"Could not fetch market price for trailing stop: {e}")
                                # Set a reasonable default
                                position_args['trailingStopDistance'] = 10.0  # Default fallback value
                    else:
                        position_args['trailingStopDistance'] = trailing_offset
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid trailing offset value: {str(e)}. Setting to default.")
                    position_args['trailingStopDistance'] = 10.0  # Default fallback value
            elif 'trailing_step_percent' in data:
                # Calculate trailing stop distance based on percentage if offset not provided
                trailing_percent = float(data.get('trailing_step_percent', 0.2))
                # Use price from webhook data instead of undefined 'close' variable
                if 'price' in data and data['price']:
                    current_price = float(data['price'])
                    position_args['trailingStopDistance'] = current_price * trailing_percent / 100
                else:
                    # Fetch current market price if not provided
                    try:
                        market_data = client.market_data_manager.single_market_details(position_args['epic'])
                        if market_data and 'snapshot' in market_data:
                            current_price = float(market_data['snapshot']['bid'])
                            position_args['trailingStopDistance'] = current_price * trailing_percent / 100
                        else:
                            raise ValueError("Could not determine market price for trailing stop calculation")
                    except Exception as e:
                        logger.error(f"Failed to get market price: {str(e)}")
                        raise ValueError(f"Cannot calculate trailing stop distance: {str(e)}")

        # Add spread costs compensation to take profit levels
        if 'take_profit' in data and float(data['take_profit']) > 0:
            original_tp = float(data['take_profit'])
            direction = position_args['direction']
            
            # Get estimated spread in points for this instrument
            spread_estimate = 0
            try:
                market_data = client.market_data_manager.single_market_details(position_args['epic'])
                if market_data and 'snapshot' in market_data:
                    spread_estimate = abs(float(market_data['snapshot']['offer']) - float(market_data['snapshot']['bid']))
                    logger.info(f"Current spread for {position_args['epic']}: {spread_estimate}")
            except Exception as e:
                logger.warning(f"Could not determine spread: {e}")
            
            # Adjust take profit to account for spread
            if spread_estimate > 0:
                if direction in ['BUY', 'CLOSE_SELL']:
                    # For long positions, move take profit higher
                    position_args['profitLevel'] = original_tp + (spread_estimate * 2)
                else:
                    # For short positions, move take profit lower
                    position_args['profitLevel'] = original_tp - (spread_estimate * 2)
                
                position_args['limitLevel'] = position_args['profitLevel']  # Keep in sync
                logger.info(f"Adjusted take profit to account for spread: Original {original_tp}, Adjusted {position_args['profitLevel']}")
            else:
                # Use profitLevel for take profit according to Capital.com API
                position_args['profitLevel'] = original_tp
                position_args['limitLevel'] = original_tp
            
            logger.info(f"Setting take profit at: {original_tp}")

        logger.info(f"Executing trade with data: {position_args}")
        
        # Enhanced retry logic with more intelligent backoff
        max_retries = 5  # Increase max retries for network issues
        retry_count = 0
        backoff_time = 1
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Ensure client is authenticated before each attempt with more robust checking
                if not client.session_manager.is_authenticated:
                    logger.info("Session not authenticated, creating new session...")
                    auth_result = client.session_manager.create_session()
                    
                    # Check authentication result explicitly
                    if isinstance(auth_result, dict) and not auth_result.get('success', False):
                        error_msg = auth_result.get('error_message', 'Unknown authentication error')
                        logger.warning(f"Authentication failed on retry {retry_count+1}: {error_msg}")
                        # Continue to retry as this might be a temporary issue
                        retry_count += 1
                        time.sleep(backoff_time)
                        backoff_time *= 2
                        continue
                
                # Normal execution through client
                try:
                    response = client.create_position(**position_args)
                    logger.info(f"Trade execution response: {response}")
                    
                    # Check for structured error response
                    if isinstance(response, dict) and response.get('status') == 'error':
                        error_code = response.get('code')
                        error_msg = response.get('message', 'Unknown error')
                        
                        # Gateway timeout or connection errors need longer retry intervals
                        if '504' in error_msg or 'timeout' in error_msg.lower() or 'gateway' in error_msg.lower():
                            logger.warning(f"Network timeout detected, retry {retry_count+1} with longer wait")
                            retry_count += 1
                            # Use longer backoff for network issues
                            time.sleep(backoff_time * 2)  # Double the standard backoff
                            backoff_time *= 2
                            continue
                        
                        # Handle POSITION_NOT_FOUND error
                        if error_code == 'POSITION_NOT_FOUND':
                            available_positions = response.get('available_positions', [])
                            position_info = ", ".join([
                                f"{p.get('epic')}:{p.get('direction')}:{p.get('size')}" 
                                for p in available_positions
                            ])
                            
                            logger.warning(f"Position not found. Available positions: {position_info}")
                            
                            # If we want to create a new position instead
                            if data.get('create_if_not_exists', False):
                                # Convert CLOSE_SELL to BUY and CLOSE_BUY to SELL
                                new_direction = 'BUY' if position_args['direction'] == 'CLOSE_SELL' else 'SELL'
                                logger.info(f"Creating new {new_direction} position instead of closing non-existent position")
                                
                                position_args['direction'] = new_direction
                                position_args.pop('force_create_if_not_exists', None)
                                continue  # Retry with new direction
                            
                            # Return the structured error response
                            return response
                        
                        # Otherwise treat as error
                        raise ValueError(error_msg)
                    
                    return response
                    
                except requests.exceptions.RequestException as e:
                    # Handle network-related exceptions specifically
                    logger.warning(f"Network error on attempt {retry_count+1}: {str(e)}")
                    retry_count += 1
                    # Use longer backoff for network issues
                    time.sleep(backoff_time * 2)
                    backoff_time *= 3  # More aggressive backoff for network issues
                    last_error = e
                    continue
                
                except Exception as e:
                    error_str = str(e)
                    
                    # Handle take profit validation errors
                    if 'error.invalid.takeprofit.maxvalue' in error_str or 'error.invalid.takeprofit.minvalue' in error_str:
                        # Extract the value from the error message
                        match = re.search(r'(error\.invalid\.takeprofit\.(max|min)value):\s*([0-9.]+)', error_str)
                        if match and len(match.groups()) >= 3:
                            adjusted_tp = float(match.group(3))
                            logger.info(f"Adjusting take profit from {position_args.get('profitLevel')} to {adjusted_tp}")
                            position_args['profitLevel'] = adjusted_tp
                            position_args['limitLevel'] = adjusted_tp
                            continue  # Try again with adjusted take profit
                    
                    # Handle stop loss validation errors - CRITICAL FIX
                    if 'error.invalid.stoploss.minvalue' in error_str or 'error.invalid.stoploss.maxvalue' in error_str:
                        # Extract the required value from the error message
                        match = re.search(r'(error\.invalid\.stoploss\.(max|min)value):\s*([0-9.]+)', error_str)
                        if match and len(match.groups()) >= 3:
                            adjusted_sl = float(match.group(3))
                            logger.info(f"Adjusting stop loss from {position_args.get('stopLevel')} to {adjusted_sl}")
                            position_args['stopLevel'] = adjusted_sl
                            continue  # Try again with adjusted stop loss
                    
                    # Check for timeout or network errors
                    error_str = str(e).lower()
                    if '504' in error_str or 'timeout' in error_str or 'connection' in error_str:
                        logger.warning(f"Network timeout/error on attempt {retry_count+1}: {str(e)}")
                        retry_count += 1
                        # Use longer backoff for network issues
                        time.sleep(backoff_time * 2)
                        backoff_time *= 3  # More aggressive backoff for network issues
                        last_error = e
                        continue
                    
                    # For other errors, use standard retry logic
                    raise e
                
            except Exception as e:
                retry_count += 1
                last_error = e
                logger.warning(f"Retry {retry_count}/{max_retries} after error: {str(e)}")
                
                if retry_count == max_retries:
                    logger.error(f"Max retries reached: {str(e)}")
                    break
                
                time.sleep(backoff_time)
                backoff_time *= 2
        
        # If we reached here, all retries failed
        if isinstance(last_error, dict) and last_error.get('status') == 'error':
            # Return structured error responses directly
            return last_error
        
        raise last_error or ValueError("Failed to execute trade after maximum retries")
        
    except Exception as e:
        error_msg = f"Failed to execute trade: {str(e)}"
        logger.error(error_msg)
        
        # Return a structured error response
        return {
            "status": "error",
            "message": error_msg,
            "code": "EXECUTION_FAILED"
        }

def get_symbol(data):
    """Get symbol from data, supporting both 'symbol' and 'ticker' keys for compatibility."""
    return data.get('symbol') or data.get('ticker')

def save_signal(db, data: Dict[str, Any]) -> int:
    """Save trading signal to database."""
    try:
        # Create table if not exists
        db.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Generate order_id if not provided
        order_id = data.get('order_id') or f"{data['direction']}_{int(time.time()*1000)}"
        
        symbol = get_symbol(data)
        
        cursor = db.execute("""
            INSERT INTO signals 
            (order_id, symbol, direction, quantity, price, status) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            symbol,
            data['direction'].upper(),
            float(data['quantity']),
            float(data.get('price', 0)),
            'pending'
        ))
        db.commit()
        return cursor.lastrowid
        
    except Exception as e:
        logger.error(f"Failed to save signal: {str(e)}", exc_info=True)
        db.rollback()
        raise

def save_trade_result(db, signal_id: int, result: Dict[str, Any]) -> int:
    """Save trade execution result to database."""
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO positions (signal_id, deal_id, symbol, direction, size, entry_price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            signal_id,
            result.get('dealId'),
            result.get('epic'),
            result.get('direction'),
            result.get('size'),
            result.get('level')
        ))
        db.commit()
        return cursor.lastrowid
        
    except Exception as e:
        logger.error(f"Failed to save trade result: {str(e)}")
        db.rollback()
        raise

def process_webhook_signal(data: dict, headers: dict) -> dict:
    """Process incoming webhook signal."""
    try:
        # Validate required fields
        required_fields = ["order_id", "order_action", "position_size", "ticker"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Always reload credentials to ensure they're available
        load_credentials()
        
        # Initialize client
        client = get_client()
        
        # Execute trade
        result = execute_trade(client, data)
        
        # Check if result is a structured error response
        if isinstance(result, dict) and result.get('status') == 'error':
            # Log the error but don't raise an exception - return the structured error
            logger.error(f"Trade execution failed: {result.get('message')}")
            return result
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to process webhook: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "code": "WEBHOOK_PROCESSING_ERROR"
        }

def create_error_response(message: str, status_code: int = 400, error_code: str = None, details: Any = None) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized error response.
    
    Args:
        message: Human-readable error message
        status_code: HTTP status code
        error_code: Machine-readable error code (e.g., 'VALIDATION_ERROR')
        details: Additional error details (optional)
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "status": "error",
        "message": message,
    }
    
    if error_code:
        response["code"] = error_code
        
    if details:
        response["details"] = details
        
    return response, status_code

def handle_request_error(e: Exception, default_status: int = 500) -> Tuple[Dict[str, Any], int]:
    """
    Handle exceptions during request processing and return standardized error responses.
    
    Args:
        e: The exception that was raised
        default_status: Default HTTP status code if not determinable from exception
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    error_message = str(e)
    error_code = "INTERNAL_ERROR"
    status_code = default_status
    
    # Log the full exception with stack trace
    logger.error(f"Error handling request: {error_message}", exc_info=True)
    
    # Determine appropriate status code and error code based on exception type
    if isinstance(e, ValueError):
        error_code = "VALIDATION_ERROR"
        status_code = 400
    elif isinstance(e, CapitalAPIException):
        error_code = "API_ERROR"
        status_code = 502  # Bad Gateway for API errors
    elif isinstance(e, requests.exceptions.Timeout):
        error_code = "TIMEOUT_ERROR"
        status_code = 504  # Gateway Timeout
    elif isinstance(e, requests.exceptions.ConnectionError):
        error_code = "CONNECTION_ERROR"
        status_code = 503  # Service Unavailable
    elif isinstance(e, KeyError):
        error_code = "MISSING_FIELD"
        status_code = 400
    elif isinstance(e, PermissionError):
        error_code = "PERMISSION_DENIED"
        status_code = 403
    
    # Create standardized error response
    return create_error_response(
        message=error_message,
        status_code=status_code,
        error_code=error_code
    )

def jsonify_error(error_data: Tuple[Dict[str, Any], int]):
    """
    Convert error tuple to a Flask JSON response.
    
    Args:
        error_data: Tuple of (error_dict, status_code) from create_error_response
        
    Returns:
        Flask JSON response
    """
    response_dict, status_code = error_data
    return jsonify(response_dict), status_code

def apply_ai_trading_logic(data: Dict[str, Any], client: Client) -> Dict[str, Any]:
    """
    Apply AI-driven trading enhancements including:
    - Volatility regime detection
    - Dynamic position sizing
    - Risk management
    
    Args:
        data: Trading signal data from webhook
        client: Authenticated Capital.com client
        
    Returns:
        Modified trading signal data with AI enhancements
    """
    try:
        # Get required modules
        from src.AI.regime_detector import VolatilityRegimeDetector
        from src.AI.position_sizer import AdaptivePositionSizer
        from src.AI.risk_manager import RiskManager
        
        # Extract key signal parameters
        symbol = data.get('ticker') or data.get('symbol')
        direction = data.get('order_action') or data.get('direction')
        original_size = float(data.get('position_size', data.get('quantity', 1.0)))
        
        # Default account_id - in production should be extracted from appropriate source
        account_id = int(data.get('account_id', 1))
        
        # Extract price and stop loss if available
        price = float(data.get('price', 0)) if data.get('price') else None
        stop_loss = float(data.get('stop_loss', 0)) if data.get('stop_loss') else None
        
        # Step 1: Detect current volatility regime
        logger.info(f"Analyzing volatility regime for {symbol}")
        regime_detector = VolatilityRegimeDetector()
        regime_info = regime_detector.get_current_regime(symbol)
        
        vol_regime = regime_info.get('regime_id', -1)
        vol_level = regime_info.get('volatility_level', 'MEDIUM')  # Default to medium if unknown
        
        # Add regime information to signal data for reference
        data['volatility_regime'] = vol_regime
        data['volatility_level'] = vol_level
        
        # Log regime detection
        logger.info(f"Detected volatility regime for {symbol}: {vol_regime} ({vol_level})")
        
        # Step 2: Apply dynamic position sizing
        logger.info(f"Calculating optimal position size for {symbol}")
        position_sizer = AdaptivePositionSizer()
        sizing_result = position_sizer.calculate_position_size(
            symbol=symbol,
            account_id=account_id,
            original_size=original_size,
            price=price,
            stop_loss=stop_loss
        )
        
        # Update position size with AI-optimized value
        adjusted_size = sizing_result.get('adjusted_size', original_size)
        data['position_size'] = adjusted_size
        data['original_position_size'] = original_size
        data['position_size_adjustment_factor'] = sizing_result.get('total_adjustment_factor', 1.0)
        
        # Log position sizing adjustment
        logger.info(f"Adjusted position size for {symbol}: {original_size} -> {adjusted_size} " +
                    f"(adjustment factor: {sizing_result.get('total_adjustment_factor', 1.0):.2f})")
        
        # Step 3: Apply risk management logic
        logger.info(f"Evaluating trade risk for {symbol}")
        risk_manager = RiskManager()
        risk_evaluation = risk_manager.evaluate_trade_risk(data, account_id)
        
        # Apply risk-based adjustments
        if risk_evaluation.get('status') == 'REJECTED':
            logger.warning(f"Trade rejected by risk management: {risk_evaluation.get('rejection_reason')}")
            # Return error response to prevent trade execution
            return {
                'status': 'error',
                'message': f"Trade rejected: {risk_evaluation.get('rejection_reason')}",
                'code': 'RISK_MANAGEMENT_REJECTION',
                'data': data,
                'risk_evaluation': risk_evaluation
            }
        
        elif risk_evaluation.get('status') == 'ADJUST_SIZE':
            # Apply risk-based size adjustment
            risk_adjusted_size = risk_evaluation.get('adjusted_size', adjusted_size)
            data['position_size'] = risk_adjusted_size
            data['risk_size_adjustment_factor'] = risk_evaluation.get('size_adjustment_factor', 1.0)
            logger.info(f"Risk management adjusted position size: {adjusted_size} -> {risk_adjusted_size}")
        
        # Step 4: Adjust stop loss based on volatility if needed
        if stop_loss and vol_level != 'UNKNOWN':
            # Adjust stop loss to account for volatility
            adjusted_stop = risk_manager.adjust_stop_loss(
                symbol=symbol,
                current_price=price,
                original_stop=stop_loss,
                position_direction=direction,
                volatility_level=vol_level
            )
            
            # Update stop loss in signal data
            data['original_stop_loss'] = stop_loss
            data['stop_loss'] = adjusted_stop
            logger.info(f"Adjusted stop loss based on {vol_level} volatility: {stop_loss} -> {adjusted_stop}")
        
        # Add AI metadata to signal
        data['ai_enhanced'] = True
        data['ai_metadata'] = {
            'volatility_regime': vol_regime,
            'volatility_level': vol_level,
            'position_sizing': {
                'original': original_size,
                'ai_adjusted': adjusted_size,
                'final': data['position_size']
            },
            'risk_evaluation': {
                'status': risk_evaluation.get('status'),
                'daily_risk_used': risk_evaluation.get('daily_risk', {}).get('used_risk_percent', 0),
                'drawdown': risk_evaluation.get('drawdown', {}).get('drawdown_percent', 0)
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return data
    
    except Exception as e:
        logger.error(f"Error in AI trading logic: {str(e)}", exc_info=True)
        # Return original data if AI enhancement fails
        return data