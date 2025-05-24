#!/usr/bin/env python3
"""
Telegram notification module for Jamso AI Engine.
This module provides functionality to send alerts and notifications via Telegram.
"""

import os
import logging
import requests
from typing import Optional, Dict, Any, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramAlerts:
    """
    Class for sending notifications via Telegram.
    Uses the Telegram Bot API to send messages to a specified chat.
    """
    
    def __init__(self):
        """
        Initialize the Telegram alerts system.
        
        Loads credentials from the secure credentials database first,
        then falls back to environment variables if needed.
        """
        self.bot_token = None
        self.chat_id = None
        self._load_credentials()
        self._validate_credentials()
        
    def _load_credentials(self):
        """Load credentials from secure database or environment variables."""
        try:
            # First try to load from credentials manager
            try:
                # Import here to avoid circular imports
                from src.Credentials.credentials_manager import CredentialManager
                manager = CredentialManager()
                
                # Get credentials from database
                self.bot_token = manager.get_credential('telegram', 'TELEGRAM_BOT_TOKEN')
                self.chat_id = manager.get_credential('telegram', 'TELEGRAM_CHAT_ID')
                
                if self.bot_token and self.chat_id:
                    logger.info("Loaded Telegram credentials from secure database")
                    return
                    
            except Exception as e:
                logger.warning(f"Failed to load Telegram credentials from database: {e}")
            
            # Fallback to environment variables
            self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
            
            if self.bot_token and self.chat_id:
                logger.info("Loaded Telegram credentials from environment variables")
            else:
                logger.warning("Could not find Telegram credentials in database or environment")
                
        except Exception as e:
            logger.error(f"Error loading Telegram credentials: {e}")
            
    def _validate_credentials(self):
        """Validate that required credentials are available."""
        if not self.bot_token:
            logger.warning("Telegram bot token not set")
            
        if not self.chat_id:
            logger.warning("Telegram chat ID not set")
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        """
        Send a message via Telegram.
        
        Args:
            message: The message text to send
            parse_mode: The parsing mode for the message ('HTML', 'MarkdownV2', or None)
            
        Returns:
            The response from the Telegram API as a dictionary
        
        Raises:
            RuntimeError: If credentials are missing or the API request fails
        """
        if not self.bot_token or not self.chat_id:
            error_msg = "Telegram credentials not properly set"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            logger.info(f"Telegram message sent successfully")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise RuntimeError(f"Failed to send Telegram message: {e}")
    
    def send_alert(self, title: str, message: str, level: str = "INFO") -> Dict[str, Any]:
        """
        Send a formatted alert message with title and severity level.
        
        Args:
            title: The alert title
            message: The alert message body
            level: Alert level ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
            
        Returns:
            The response from the Telegram API
        """
        # Convert level to emoji for visual indication
        level_emoji = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }
        
        emoji = level_emoji.get(level.upper(), "ℹ️")
        formatted_message = f"{emoji} <b>{title}</b>\n\n{message}"
        
        return self.send_message(formatted_message, parse_mode="HTML")
        
    def send_trade_notification(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a notification about a trade execution.
        
        Args:
            trade_data: Dictionary containing trade details
            
        Returns:
            The response from the Telegram API
        """
        # Extract trade details with fallbacks for missing values
        symbol = trade_data.get('symbol', 'Unknown')
        action = trade_data.get('action', 'Unknown').upper()
        price = trade_data.get('price', 0)
        size = trade_data.get('size', 0)
        stop_loss = trade_data.get('stop_loss', 0)
        take_profit = trade_data.get('take_profit', 0)
        
        # Determine emoji based on trade direction
        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
        
        # Format message
        message = (
            f"{emoji} <b>TRADE: {action} {symbol}</b>\n\n"
            f"🔹 <b>Price:</b> {price}\n"
            f"🔹 <b>Size:</b> {size}\n"
        )
        
        # Add optional fields if they exist
        if stop_loss:
            message += f"🔹 <b>Stop Loss:</b> {stop_loss}\n"
        if take_profit:
            message += f"🔹 <b>Take Profit:</b> {take_profit}\n"
            
        # Add timestamp for reference
        message += f"\n<i>Executed at {trade_data.get('timestamp', 'Unknown time')}</i>"
        
        return self.send_message(message, parse_mode="HTML")

# Initialize an instance if this file is imported
telegram_alerts = TelegramAlerts()

def send_message(message: str, parse_mode: str = "HTML") -> Dict[str, Any]:
    """Convenience function to send a message using the global instance."""
    return telegram_alerts.send_message(message, parse_mode)

def send_alert(title: str, message: str, level: str = "INFO") -> Dict[str, Any]:
    """Convenience function to send an alert using the global instance."""
    return telegram_alerts.send_alert(title, message, level)

def send_trade_notification(trade_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to send a trade notification using the global instance."""
    return telegram_alerts.send_trade_notification(trade_data)
