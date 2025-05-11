"""
Centralized logging configuration for Jamso AI Server.

This module provides a unified configuration for all logging throughout the application,
ensuring consistent log formatting, levels, and storage policies.
"""

import os
import json
import sys
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Dependencies handling
try:
    from termcolor import colored
    HAS_COLORED_OUTPUT = True
except ImportError:
    HAS_COLORED_OUTPUT = False
    # Create a simple colored function replacement if termcolor is not available
    def colored(text, color):
        return text

# Create a custom formatter for colored output
class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels in console output"""
    
    COLORS = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red'
    }
    
    def format(self, record):
        # Add the colored level name as a record attribute
        if HAS_COLORED_OUTPUT and record.levelname in self.COLORS:
            record.colored_levelname = colored(record.levelname, self.COLORS[record.levelname])
        else:
            record.colored_levelname = record.levelname
        
        return super().format(record)

# Get the base directory dynamically
def get_base_dir() -> Path:
    """Get the base directory dynamically."""
    # First check from environment variable
    if "ROOT_DIR" in os.environ:
        return Path(os.environ["ROOT_DIR"])
    
    # Next try to determine from script location
    script_path = Path(__file__).resolve()
    # Go up three levels from src/Logging/logging_config.py
    return script_path.parent.parent.parent

# Base directory and log directory
BASE_DIR = get_base_dir()
DEFAULT_LOG_DIR = str(BASE_DIR / "src" / "Logs")
# Ensure log directory exists
Path(DEFAULT_LOG_DIR).mkdir(parents=True, exist_ok=True)

# Log levels
LOG_LEVELS = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0
}

# Default configuration
DEFAULT_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "colored": {
            "format": "%(asctime)s | %(colored_levelname)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(pathname)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "colored" if HAS_COLORED_OUTPUT else "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": os.path.join(DEFAULT_LOG_DIR, "application.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 10,
            "encoding": "utf8"
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": os.path.join(DEFAULT_LOG_DIR, "error.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 10,
            "encoding": "utf8"
        }
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": True
        },
        "src": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False
        },
        "src.Webhook": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False
        },
        "src.Exchange": {
            "level": "INFO",
            "handlers": ["console", "file", "error_file"],
            "propagate": False
        },
        "werkzeug": {
            "level": "WARNING",
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": {
        "root_level": "DEBUG",
        "console_level": "DEBUG",
        "file_level": "DEBUG",
    },
    "testing": {
        "root_level": "DEBUG",
        "console_level": "DEBUG",
        "file_level": "DEBUG",
    },
    "production": {
        "root_level": "INFO",
        "console_level": "WARNING",
        "file_level": "INFO",
    },
}

def get_log_config(
    app_name: str = "jamso_ai",
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    format_type: str = "json",
    include_console: bool = True,
    env: str = "production"
) -> Dict[str, Any]:
    """
    Generate a logging configuration dictionary based on parameters.
    
    Args:
        app_name: Name of the application (used for log file naming)
        log_dir: Directory to store log files (default: Logs)
        log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format (json, standard, detailed)
        include_console: Whether to include console logging
        env: Environment (development, testing, production)
        
    Returns:
        Dictionary containing logging configuration
    """
    # Use a type annotation for the config copy to help the type checker
    config: Dict[str, Any] = DEFAULT_CONFIG.copy()
    
    # Apply environment-specific settings
    env_config = ENVIRONMENT_CONFIGS.get(env.lower(), ENVIRONMENT_CONFIGS["production"])
    
    # Use environment root level if not explicitly provided
    if log_level == "INFO" and "root_level" in env_config:
        log_level = env_config["root_level"]
        
    # Set log directory
    log_directory = log_dir or DEFAULT_LOG_DIR
    Path(log_directory).mkdir(parents=True, exist_ok=True)
    
    # Update log file paths
    config["handlers"]["file"]["filename"] = os.path.join(log_directory, f"{app_name}.log")
    config["handlers"]["error_file"]["filename"] = os.path.join(log_directory, f"{app_name}_error.log")
    
    # Set formatter based on format_type
    formatter = format_type if format_type in config["formatters"] else "standard"
    config["handlers"]["file"]["formatter"] = formatter
    config["handlers"]["console"]["formatter"] = formatter
    
    # Set log levels
    config["loggers"][""]["level"] = log_level
    config["handlers"]["file"]["level"] = env_config.get("file_level", log_level)
    config["handlers"]["console"]["level"] = env_config.get("console_level", log_level)
    
    # Remove console handler if not needed
    if not include_console:
        for logger_name in config["loggers"]:
            if "console" in config["loggers"][logger_name]["handlers"]:
                config["loggers"][logger_name]["handlers"].remove("console")
    
    return config

def write_log_config(config: Dict[str, Any], output_path: str) -> None:
    """
    Write logging configuration to a JSON file.
    
    Args:
        config: Logging configuration dictionary
        output_path: Path to write the configuration file
    """
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=4)

def read_log_config(config_path: str) -> Dict[str, Any]:
    """
    Read logging configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing logging configuration
    """
    with open(config_path, 'r') as f:
        # Add explicit cast to help type checker
        return json.load(f)  # type: ignore[return-value]