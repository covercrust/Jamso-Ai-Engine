"""Backend Webhook package initialization."""
import os

from .utils import (
    get_client,
    get_position_details,
    execute_trade,
    save_signal,
    save_trade_result
)
from .database import get_db

# Import config to get the default token
from .config import WEBHOOK_TOKEN as DEFAULT_TOKEN

# Get token from environment variable with fallback to config
WEBHOOK_TOKEN = os.getenv('WEBHOOK_TOKEN', DEFAULT_TOKEN)

# Base path for the application
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'

__all__ = [
    'get_client',
    'get_position_details',
    'execute_trade',
    'save_signal',
    'save_trade_result',
    'get_db',
    'WEBHOOK_TOKEN',
    'BASE_PATH'
]

