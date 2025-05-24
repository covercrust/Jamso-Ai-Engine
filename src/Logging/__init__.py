"""
Logging utilities for the Jamso AI Engine.
"""

import logging
from typing import Optional
import os

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Logs')
os.makedirs(log_dir, exist_ok=True)

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger with the specified name and level.
    
    Args:
        name: Logger name
        level: Optional logging level (defaults to INFO if not specified)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Set default level if not already set and level is provided
    if level is not None:
        logger.setLevel(level)
    elif not logger.level:
        logger.setLevel(logging.INFO)
    
    # Add handler if not already added
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = os.path.join(log_dir, 'market_intelligence.log')
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger