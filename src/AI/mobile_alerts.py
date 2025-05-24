#!/usr/bin/env python3
"""
Mobile Alerts for Capital.com API Optimization

This module provides mobile notification capabilities for the optimization
and monitoring system, allowing users to receive alerts about critical
performance degradation, optimization results, and trading opportunities.

Supported notification methods:
1. Email notifications
2. SMS notifications (via email-to-SMS gateways)
3. Web push notifications
4. Webhook integrations (for custom notification systems)

Usage:
    from src.AI.mobile_alerts import MobileAlertManager
    
    # Initialize alert manager
    alert_manager = MobileAlertManager()
    
    # Send critical alert
    alert_manager.send_alert(
        "Performance Degradation",
        "BTCUSD strategy performance decreased by 15%",
        level="critical"
    )
"""

import os
import sys
import logging
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path to access the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Try to import dotenv for loading environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file if it exists
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables may not be loaded properly.")

class MobileAlertManager:
    """
    Manager for sending mobile alerts through various channels.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the mobile alert manager.
        
        Args:
            config_file: Optional path to a JSON configuration file
        """
        self.config = self._load_config(config_file)
        self.alert_history = []
        self.rate_limits = {
            'info': {'max': 10, 'count': 0, 'period': 3600},  # 10 per hour
            'warning': {'max': 5, 'count': 0, 'period': 3600},  # 5 per hour
            'critical': {'max': 3, 'count': 0, 'period': 3600},  # 3 per hour
        }
        
        # Reset rate limits periodically
        self._start_rate_limit_reset_timer()
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file or environment variables.
        
        Args:
            config_file: Path to JSON configuration file
            
        Returns:
            Dictionary with configuration settings
        """
        config = {
            'email': {
                'enabled': os.getenv('MOBILE_ALERTS_EMAIL_ENABLED', 'false').lower() == 'true',
                'from': os.getenv('EMAIL_FROM', ''),
                'to': os.getenv('EMAIL_TO', ''),
                'password': os.getenv('EMAIL_PASSWORD', ''),
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            },
            'sms': {
                'enabled': os.getenv('MOBILE_ALERTS_SMS_ENABLED', 'false').lower() == 'true',
                'gateway': os.getenv('SMS_GATEWAY', ''),
                'number': os.getenv('SMS_NUMBER', ''),
            },
            'push': {
                'enabled': os.getenv('MOBILE_ALERTS_PUSH_ENABLED', 'false').lower() == 'true',
                'api_key': os.getenv('PUSH_API_KEY', ''),
                'app_id': os.getenv('PUSH_APP_ID', ''),
                'service': os.getenv('PUSH_SERVICE', 'onesignal'),  # onesignal, firebase, etc.
            },
            'webhook': {
                'enabled': os.getenv('MOBILE_ALERTS_WEBHOOK_ENABLED', 'false').lower() == 'true',
                'url': os.getenv('WEBHOOK_ALERT_URL', ''),
                'headers': json.loads(os.getenv('WEBHOOK_ALERT_HEADERS', '{}')),
            },
            'general': {
                'min_level': os.getenv('MOBILE_ALERTS_MIN_LEVEL', 'warning'),  # info, warning, critical
            }
        }
        
        # Override with configuration file if provided
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                
                # Update config with file values (deep merge)
                for section, values in file_config.items():
                    if section in config:
                        config[section].update(values)
                    else:
                        config[section] = values
                        
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration file: {str(e)}")
        
        return config
    
    def _start_rate_limit_reset_timer(self):
        """Start a timer to reset rate limits periodically."""
        for level, data in self.rate_limits.items():
            data['count'] = 0
            
        # Schedule the next reset
        timer = threading.Timer(3600, self._start_rate_limit_reset_timer)
        timer.daemon = True
        timer.start()
    
    def _check_rate_limit(self, level: str) -> bool:
        """
        Check if sending an alert would exceed the rate limit.
        
        Args:
            level: Alert level (info, warning, critical)
            
        Returns:
            True if within rate limit, False otherwise
        """
        if level not in self.rate_limits:
            return True
            
        limit_data = self.rate_limits[level]
        if limit_data['count'] >= limit_data['max']:
            return False
            
        limit_data['count'] += 1
        return True
    
    def _get_level_priority(self, level: str) -> int:
        """Get numeric priority value for alert level."""
        levels = {'info': 0, 'warning': 1, 'critical': 2}
        return levels.get(level.lower(), 0)
    
    def _should_send_alert(self, level: str) -> bool:
        """
        Determine if an alert should be sent based on minimum level setting.
        
        Args:
            level: Alert level (info, warning, critical)
            
        Returns:
            True if alert should be sent, False otherwise
        """
        min_level = self.config['general']['min_level'].lower()
        return self._get_level_priority(level) >= self._get_level_priority(min_level)
    
    def send_alert(self, title: str, message: str, level: str = 'info', 
                  data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send an alert through configured notification channels.
        
        Args:
            title: Alert title
            message: Alert message body
            level: Alert level (info, warning, critical)
            data: Optional additional data to include
            
        Returns:
            True if alert was sent successfully through at least one channel
        """
        if not self._should_send_alert(level):
            logger.debug(f"Alert '{title}' not sent due to level filter ({level} < {self.config['general']['min_level']})")
            return False
            
        if not self._check_rate_limit(level):
            logger.warning(f"Rate limit exceeded for {level} alerts, not sending '{title}'")
            return False
            
        # Record in alert history
        timestamp = datetime.now().isoformat()
        alert_record = {
            'timestamp': timestamp,
            'title': title,
            'message': message,
            'level': level,
            'data': data or {}
        }
        self.alert_history.append(alert_record)
        
        # Try all enabled notification methods
        success = False
        
        # Email notifications
        if self.config['email']['enabled']:
            email_success = self._send_email_alert(title, message, level, data)
            success = success or email_success
            
        # SMS notifications (via email gateway)
        if self.config['sms']['enabled']:
            sms_success = self._send_sms_alert(title, message, level, data)
            success = success or sms_success
            
        # Push notifications
        if self.config['push']['enabled']:
            push_success = self._send_push_alert(title, message, level, data)
            success = success or push_success
            
        # Webhook notifications
        if self.config['webhook']['enabled']:
            webhook_success = self._send_webhook_alert(title, message, level, data)
            success = success or webhook_success
            
        if success:
            logger.info(f"Successfully sent {level} alert: {title}")
        else:
            logger.error(f"Failed to send {level} alert: {title}")
            
        return success
    
    def _send_email_alert(self, title: str, message: str, level: str,
                        data: Optional[Dict[str, Any]] = None) -> bool:
        """Send an alert via email."""
        try:
            config = self.config['email']
            
            if not config['from'] or not config['to'] or not config['password']:
                logger.warning("Email configuration incomplete, skipping email alert")
                return False
                
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = config['from']
            msg['To'] = config['to']
            msg['Subject'] = f"[{level.upper()}] {title}"
            
            # Format message body
            body = f"{message}\n\n"
            if data:
                body += "Additional Information:\n"
                for key, value in data.items():
                    body += f"{key}: {value}\n"
            body += f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['from'], config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.debug(f"Sent email alert: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def _send_sms_alert(self, title: str, message: str, level: str,
                      data: Optional[Dict[str, Any]] = None) -> bool:
        """Send an alert via SMS (using email-to-SMS gateway)."""
        try:
            config = self.config['sms']
            
            if not config['gateway'] or not config['number']:
                logger.warning("SMS configuration incomplete, skipping SMS alert")
                return False
                
            # Format shorter message for SMS
            sms_message = f"{level.upper()}: {title} - {message}"
            if len(sms_message) > 160:
                sms_message = sms_message[:157] + "..."
                
            # Create email message for SMS gateway
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['from']
            msg['To'] = f"{config['number']}@{config['gateway']}"
            msg['Subject'] = ""  # No subject for SMS
            
            msg.attach(MIMEText(sms_message, 'plain'))
            
            # Connect to SMTP server and send
            server = smtplib.SMTP(self.config['email']['smtp_server'], 
                                 self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['from'], 
                        self.config['email']['password'])
            server.send_message(msg)
            server.quit()
            
            logger.debug(f"Sent SMS alert: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS alert: {str(e)}")
            return False
    
    def _send_push_alert(self, title: str, message: str, level: str,
                       data: Optional[Dict[str, Any]] = None) -> bool:
        """Send an alert via push notification service."""
        try:
            config = self.config['push']
            
            if not config['api_key'] or not config['app_id']:
                logger.warning("Push notification configuration incomplete, skipping push alert")
                return False
                
            # Prepare push notification based on service type
            if config['service'].lower() == 'onesignal':
                return self._send_onesignal_alert(title, message, level, data)
            elif config['service'].lower() == 'firebase':
                return self._send_firebase_alert(title, message, level, data)
            else:
                logger.warning(f"Unsupported push notification service: {config['service']}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending push alert: {str(e)}")
            return False
    
    def _send_onesignal_alert(self, title: str, message: str, level: str,
                            data: Optional[Dict[str, Any]] = None) -> bool:
        """Send alert using OneSignal push notification service."""
        try:
            config = self.config['push']
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {config['api_key']}"
            }
            
            payload = {
                "app_id": config['app_id'],
                "headings": {"en": f"[{level.upper()}] {title}"},
                "contents": {"en": message},
                "included_segments": ["All"],
                "data": data or {}
            }
            
            response = requests.post(
                "https://onesignal.com/api/v1/notifications",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                logger.debug(f"Sent OneSignal push alert: {title}")
                return True
            else:
                logger.error(f"OneSignal API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending OneSignal alert: {str(e)}")
            return False
    
    def _send_firebase_alert(self, title: str, message: str, level: str,
                           data: Optional[Dict[str, Any]] = None) -> bool:
        """Send alert using Firebase Cloud Messaging."""
        try:
            config = self.config['push']
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"key={config['api_key']}"
            }
            
            payload = {
                "notification": {
                    "title": f"[{level.upper()}] {title}",
                    "body": message
                },
                "data": data or {},
                "to": "/topics/all"  # Send to all devices subscribed to 'all' topic
            }
            
            response = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                logger.debug(f"Sent Firebase push alert: {title}")
                return True
            else:
                logger.error(f"Firebase API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Firebase alert: {str(e)}")
            return False
    
    def _send_webhook_alert(self, title: str, message: str, level: str,
                          data: Optional[Dict[str, Any]] = None) -> bool:
        """Send an alert via webhook to a custom notification system."""
        try:
            config = self.config['webhook']
            
            if not config['url']:
                logger.warning("Webhook configuration incomplete, skipping webhook alert")
                return False
                
            # Prepare webhook payload
            payload = {
                "title": title,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "data": data or {}
            }
            
            # Send webhook
            response = requests.post(
                config['url'],
                headers=config.get('headers', {}),
                json=payload
            )
            
            if response.status_code in [200, 201, 202]:
                logger.debug(f"Sent webhook alert: {title}")
                return True
            else:
                logger.error(f"Webhook error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending webhook alert: {str(e)}")
            return False
    
    def get_alert_history(self, limit: int = 100, 
                        level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent alert history.
        
        Args:
            limit: Maximum number of alerts to return
            level: Filter by alert level
            
        Returns:
            List of alert records
        """
        filtered = self.alert_history
        
        if level:
            filtered = [a for a in filtered if a['level'] == level]
            
        return sorted(filtered, key=lambda a: a['timestamp'], reverse=True)[:limit]


def main():
    """Standalone test function for mobile alerts."""
    parser = argparse.ArgumentParser(description="Test mobile alerts")
    parser.add_argument("--title", type=str, default="Test Alert",
                      help="Alert title")
    parser.add_argument("--message", type=str, default="This is a test alert from Jamso-AI-Engine",
                      help="Alert message")
    parser.add_argument("--level", type=str, default="info", 
                      choices=["info", "warning", "critical"],
                      help="Alert level")
    parser.add_argument("--config", type=str, help="Path to config file")
    
    args = parser.parse_args()
    
    alert_manager = MobileAlertManager(args.config)
    success = alert_manager.send_alert(args.title, args.message, args.level)
    
    if success:
        print(f"Successfully sent {args.level} alert: {args.title}")
    else:
        print(f"Failed to send alert. Check logs for details.")
    
    return 0 if success else 1


if __name__ == "__main__":
    import argparse
    sys.exit(main())
