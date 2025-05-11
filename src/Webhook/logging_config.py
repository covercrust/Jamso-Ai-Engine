"""
Logging configuration for the Webhook module.
This file imports and uses the centralized logging configuration system.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import the centralized configuration and logging system
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Config.logging_config import get_component_config, get_standard_context
from Utils.logger import get_logger, initialize_logging, log_function, with_context

def configure_logging(config: Optional[Dict[str, Any]] = None):
    """
    Configure logging for the Webhook module using the centralized logging system.
    
    Args:
        config: Optional configuration dictionary that can override defaults
        
    Returns:
        The configured webhook logger instance
    """
    # Get component-specific configuration
    component_config = get_component_config('webhook')
    
    # Override with any provided config
    if config:
        component_config.update(config)
    
    # Initialize logging with component configuration
    initialize_logging(**component_config)
    
    # Get the main webhook logger
    webhook_logger = get_logger('webhook')
    
    # Add standard context data
    webhook_logger.add_context(**get_standard_context())
    
    # Add request tracking context
    webhook_logger.add_context(
        component='webhook',
    )
    
    webhook_logger.info("Webhook logging configured successfully")
    return webhook_logger

# Default logger instance for the webhook module
logger = get_logger('webhook')
