#!/usr/bin/env python3
"""
Position size validator for Jamso AI Server.
This module validates position sizes for trading operations.
"""

import logging
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

def validate_position_size(
    instrument: str, 
    position_size: float, 
    account_info: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Validate if a position size is appropriate for a given instrument
    
    Args:
        instrument: The trading instrument identifier
        position_size: The size of the position to validate
        account_info: Optional account information for context-aware validation
        
    Returns:
        bool: True if the position size is valid, False otherwise
    """
    # Basic validation - position size must be positive
    if position_size <= 0:
        logger.warning(f"Invalid position size {position_size} for {instrument}: must be positive")
        return False
        
    # Add more sophisticated validation based on account balance and risk management
    if account_info:
        # Example: Check if position size is within account limits
        available_balance = account_info.get('available', 0)
        if available_balance and position_size > available_balance * 0.2:  # 20% max of available balance
            logger.warning(f"Position size {position_size} exceeds 20% of available balance {available_balance}")
            return False
    
    # If we pass all checks
    logger.info(f"Position size {position_size} for {instrument} is valid")
    return True
