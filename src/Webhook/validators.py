from typing import Dict, Any, List, Optional, Tuple, Union
import re
import logging

logger = logging.getLogger(__name__)

def validate_webhook_data(data: Dict[str, Any]) -> List[str]:
    """
    Validates the incoming webhook data for required fields and value ranges.
    Returns a list of error messages, empty if validation succeeds.
    """
    errors = []
    
    # Required fields
    required_fields = ['order_id', 'ticker', 'order_action', 'position_size']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate order action
    if 'order_action' in data:
        valid_actions = ['BUY', 'SELL', 'CLOSE_BUY', 'CLOSE_SELL']
        if data['order_action'].upper() not in valid_actions:
            errors.append(f"Invalid order_action: {data['order_action']}. Must be one of {valid_actions}")
    
    # Validate position size
    if 'position_size' in data:
        try:
            size = float(data['position_size'])
            if size <= 0:
                errors.append("position_size must be greater than 0")
            elif size > 100:  # Example upper limit, adjust based on your risk management
                errors.append(f"position_size exceeds maximum allowed value of 100, got: {size}")
        except ValueError:
            errors.append(f"position_size must be a number, got: {data['position_size']}")
    
    # Validate ticker symbol
    if 'ticker' in data:
        ticker = data['ticker']
        if not isinstance(ticker, str):
            errors.append(f"ticker must be a string, got: {type(ticker).__name__}")
        elif not re.match(r'^[A-Za-z0-9\.\-_]+$', ticker):
            errors.append(f"ticker contains invalid characters: {ticker}")
    
    # Validate order_id
    if 'order_id' in data:
        order_id = data['order_id']
        if not isinstance(order_id, str):
            errors.append(f"order_id must be a string, got: {type(order_id).__name__}")
        elif len(order_id) > 50:
            errors.append(f"order_id exceeds maximum length of 50 characters")
    
    # Validate stop loss and take profit (if provided)
    if 'stop_loss' in data and data['stop_loss']:
        try:
            sl = float(data['stop_loss'])
            if sl <= 0:
                errors.append(f"stop_loss must be positive, got: {sl}")
                
            if 'order_action' in data and 'price' in data and data['price']:
                try:
                    price = float(data['price'])
                    action = data['order_action'].upper()
                    
                    # For long positions, stop loss should be below entry price
                    if action == 'BUY' and sl >= price:
                        errors.append(f"For BUY orders, stop_loss ({sl}) should be below entry price ({price})")
                    # For short positions, stop loss should be above entry price
                    elif action == 'SELL' and sl <= price:
                        errors.append(f"For SELL orders, stop_loss ({sl}) should be above entry price ({price})")
                except ValueError:
                    errors.append(f"price must be a number for stop_loss validation")
        except ValueError:
            errors.append(f"stop_loss must be a number, got: {data['stop_loss']}")
    
    # Validate take profit
    if 'take_profit' in data and data['take_profit']:
        try:
            tp = float(data['take_profit'])
            if tp <= 0:
                errors.append(f"take_profit must be positive, got: {tp}")
                
            if 'order_action' in data and 'price' in data and data['price']:
                try:
                    price = float(data['price'])
                    action = data['order_action'].upper()
                    
                    # For long positions, take profit should be above entry price
                    if action == 'BUY' and tp <= price:
                        errors.append(f"For BUY orders, take_profit ({tp}) should be above entry price ({price})")
                    # For short positions, take profit should be below entry price
                    elif action == 'SELL' and tp >= price:
                        errors.append(f"For SELL orders, take_profit ({tp}) should be below entry price ({price})")
                except ValueError:
                    errors.append(f"price must be a number for take_profit validation")
        except ValueError:
            errors.append(f"take_profit must be a number, got: {data['take_profit']}")
    
    # Validate trailing stop parameters
    if 'trailing_stop' in data and data['trailing_stop'] is True:
        if 'trailing_step_percent' in data:
            try:
                trailing_percent = float(data['trailing_step_percent'])
                if trailing_percent <= 0 or trailing_percent > 50:
                    errors.append(f"trailing_step_percent must be between 0.01 and 50, got: {trailing_percent}")
            except ValueError:
                errors.append(f"trailing_step_percent must be a number, got: {data['trailing_step_percent']}")
        elif 'trailing_offset' in data:
            try:
                trailing_offset = float(data['trailing_offset'])
                if trailing_offset <= 0:
                    errors.append(f"trailing_offset must be positive, got: {trailing_offset}")
            except ValueError:
                errors.append(f"trailing_offset must be a number, got: {data['trailing_offset']}")
        else:
            errors.append("When trailing_stop is enabled, either trailing_step_percent or trailing_offset must be provided")
    
    # Validate hedging parameters
    if 'hedging_enabled' in data:
        if not isinstance(data['hedging_enabled'], bool):
            errors.append(f"hedging_enabled must be a boolean, got: {type(data['hedging_enabled']).__name__}")
    
    logger.debug(f"Validation result for webhook data: {'Success' if not errors else f'Failed with {len(errors)} errors'}")
    return errors

def validate_close_position_data(data: Dict[str, Any]) -> List[str]:
    """
    Validates the data for closing a position.
    Returns a list of error messages, empty if validation succeeds.
    """
    errors = []
    
    # Validate required fields
    if 'order_id' not in data:
        errors.append("Missing required field: order_id")
    
    # Validate order_id
    if 'order_id' in data:
        order_id = data['order_id']
        if not isinstance(order_id, str):
            errors.append(f"order_id must be a string, got: {type(order_id).__name__}")
        elif len(order_id) > 50:
            errors.append(f"order_id exceeds maximum length of 50 characters")
    
    # Validate size if present
    if 'size' in data:
        try:
            size = float(data['size'])
            if size <= 0:
                errors.append(f"size must be positive, got: {size}")
        except ValueError:
            errors.append(f"size must be a number, got: {data['size']}")
    
    logger.debug(f"Validation result for close position data: {'Success' if not errors else f'Failed with {len(errors)} errors'}")
    return errors

def sanitize_input(value, expected_type=None, max_length=None):
    import re
    import logging
    logger = logging.getLogger(__name__)

    if expected_type == str or expected_type is None:
        if isinstance(value, str):
            # Extract content from script tags and preserve it
            sanitized_value = re.sub(r'<script[^>]*>(.*?)</script>', r'\1', value, flags=re.IGNORECASE | re.DOTALL)
            # Remove any remaining HTML tags
            sanitized_value = re.sub(r'<[^>]+>', '', sanitized_value)
            # Remove newlines and trim whitespace
            sanitized_value = sanitized_value.replace('\n', '').replace('\r', '').strip()
            if max_length and len(sanitized_value) > max_length:
                sanitized_value = sanitized_value[:max_length]
            return sanitized_value if expected_type is None else (sanitized_value, True)
        return (None, False) if expected_type is not None else None

    if expected_type == int:
        try:
            return int(value), True
        except ValueError:
            return None, False

    if expected_type == float:
        try:
            return float(value), True
        except ValueError:
            return None, False

    if expected_type == bool:
        true_values = {"true", "yes", "1", "on", True, 1}
        false_values = {"false", "no", "0", "off", False, 0}
        if value in true_values:
            return True, True
        if value in false_values:
            return False, True
        return None, False

    return value, True

def validate_api_input(data: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates and sanitizes input against a schema.
    
    Args:
        data: Input data dictionary
        schema: Validation schema with field definitions
        
    Returns:
        Tuple of (sanitized_data, error_messages)
    """
    sanitized = {}
    errors = []
    
    for field, field_schema in schema.items():
        field_type = field_schema.get('type', str)
        required = field_schema.get('required', False)
        max_length = field_schema.get('max_length')
        allowed_values = field_schema.get('allowed_values')
        default = field_schema.get('default')
        
        # Check required fields
        if required and field not in data:
            errors.append(f"Missing required field: {field}")
            continue
        
        # If field is missing but not required, use default or skip
        if field not in data:
            if default is not None:
                sanitized[field] = default
            continue
        
        # Sanitize the value
        value, is_valid = sanitize_input(data[field], field_type, max_length)
        
        if not is_valid:
            errors.append(f"Invalid type for {field}: expected {field_type.__name__}")
            continue
        
        # Validate against allowed values if specified
        if allowed_values and value not in allowed_values:
            errors.append(f"Invalid value for {field}: must be one of {allowed_values}")
            continue
            
        # Additional custom validation if defined in schema
        validator = field_schema.get('validator')
        if validator and callable(validator):
            valid, message = validator(value)
            if not valid:
                errors.append(message)
                continue
        
        sanitized[field] = value
    
    return sanitized, errors
