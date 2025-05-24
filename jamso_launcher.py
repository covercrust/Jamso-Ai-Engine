#!/usr/bin/env python3
"""
Jamso-AI-Engine Launcher

This script provides a central interface for launching and testing various components
of the Jamso-AI-Engine trading system, including:
- Capital.com API integration
- Sentiment analysis
- Parameter optimization
- Scheduled optimization
- Dashboard visualization
- Mobile alerts
- System configuration with interactive wizard

Usage:
    python jamso_launcher.py
"""

import os
import sys
import argparse
import logging
import json
import subprocess
import time
from datetime import datetime
import signal
import re
import platform
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JamsoLauncher")

# Import environment variables from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables may not be loaded properly.")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Installed and loaded python-dotenv successfully.")
    except Exception as e:
        logger.error(f"Failed to install python-dotenv: {e}")

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def disable():
        """Disable colors if not in compatible terminal"""
        Colors.HEADER = ''
        Colors.BLUE = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''

# Check if we're running in Windows or not a compatible terminal
if platform.system() == "Windows" or not sys.stdout.isatty():
    Colors.disable()

class JamsoLauncher:
    """
    Main launcher class for Jamso-AI-Engine components
    """
    def __init__(self):
        """Initialize the launcher"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.process_list = []
        self.current_menu = "main"
        self.check_environment()
        self.env_file = os.path.join(self.base_dir, ".env")
        self.logs_dir = os.path.join(self.base_dir, "Logs")
        
        # Ensure logs directory exists
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Register signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def check_environment(self):
        """Check the environment for required components"""
        # Check for Python version
        logger.info(f"Running with Python {sys.version}")
        
        # Check for virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.info("Running inside a virtual environment")
        else:
            logger.warning("Not running in a virtual environment")
            
        # Check for required directories
        for dir_name in ["src", "Logs", "src/AI"]:
            dir_path = os.path.join(self.base_dir, dir_name)
            if not os.path.exists(dir_path):
                logger.warning(f"Required directory {dir_name} not found")
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory {dir_name}")
    
    def configuration_wizard(self):
        """
        Interactive wizard to help users set up their environment and configuration
        """
        print(f"\n{Colors.HEADER}Configuration Wizard{Colors.ENDC}")
        print("This wizard will help you set up your Jamso-AI-Engine environment.")
        print("Press Ctrl+C at any time to exit.\n")
        
        # Check if .env file exists
        if os.path.exists(self.env_file):
            print(f"{Colors.YELLOW}An existing .env file was found.{Colors.ENDC}")
            choice = input("Do you want to (1) Use existing file, (2) Edit existing file, or (3) Create new file? [1/2/3]: ")
            
            if choice == "3":
                # Create new file
                self._create_env_file()
            elif choice == "2":
                # Edit existing file
                self._edit_env_file()
            else:
                print(f"{Colors.GREEN}Using existing .env file.{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}No .env file found.{Colors.ENDC}")
            self._create_env_file()
        
        # Check for required dependencies
        self._check_dependencies()
        
        # Setup logging
        self._setup_logging()
        
        print(f"\n{Colors.GREEN}Configuration complete!{Colors.ENDC}")
        print("You can now use the Jamso-AI-Engine with your configuration.")
        print("Press Enter to return to the main menu.")
        input()
    
    def _create_env_file(self):
        """Create a new .env file with user input"""
        print(f"\n{Colors.BLUE}Creating new .env file...{Colors.ENDC}")
        
        # Capital.com API credentials
        print(f"\n{Colors.HEADER}Capital.com API Credentials (optional){Colors.ENDC}")
        print("These are required for live trading and data access.")
        print(f"{Colors.YELLOW}Note: These credentials will be stored in the secure credential database when possible.{Colors.ENDC}")
        capital_api_key = input("Capital.com API Key (leave empty to skip): ").strip()
        capital_api_login = input("Capital.com API Login (leave empty to skip): ").strip()
        capital_api_password = input("Capital.com API Password (leave empty to skip): ").strip()
        
        # Try to store in the credential database first
        if capital_api_key and capital_api_login and capital_api_password:
            try:
                # Import the credential manager
                sys.path.append(self.base_dir)
                from src.Credentials.credentials_manager import CredentialManager
                
                # Initialize CredentialManager
                credential_manager = CredentialManager()
                
                # Store credentials in the database
                credential_manager.set_credential('capital_com', 'CAPITAL_API_KEY', capital_api_key)
                credential_manager.set_credential('capital_com', 'CAPITAL_API_LOGIN', capital_api_login)
                credential_manager.set_credential('capital_com', 'CAPITAL_API_PASSWORD', capital_api_password)
                
                logger.info("Capital.com API credentials stored in credential database")
                print(f"{Colors.GREEN}API credentials stored in secure credential database!{Colors.ENDC}")
            except Exception as e:
                logger.error(f"Error storing credentials in database: {str(e)}")
                print(f"{Colors.YELLOW}Could not store credentials in database, using .env file as fallback.{Colors.ENDC}")
        
        # Email settings
        print(f"\n{Colors.HEADER}Email Alert Settings (optional){Colors.ENDC}")
        print("These are required for email notifications.")
        email_from = input("Email From (leave empty to skip): ").strip()
        email_to = input("Email To (leave empty to skip): ").strip()
        email_password = input("Email Password (leave empty to skip): ").strip()
        smtp_server = input("SMTP Server (default: smtp.gmail.com): ").strip() or "smtp.gmail.com"
        smtp_port = input("SMTP Port (default: 587): ").strip() or "587"
        
        # Mobile alerts settings
        print(f"\n{Colors.HEADER}Mobile Alert Settings{Colors.ENDC}")
        enable_email = input("Enable Email Alerts? [y/N]: ").strip().lower() == 'y'
        enable_sms = input("Enable SMS Alerts? [y/N]: ").strip().lower() == 'y'
        enable_push = input("Enable Push Notifications? [y/N]: ").strip().lower() == 'y'
        enable_webhook = input("Enable Webhook Alerts? [y/N]: ").strip().lower() == 'y'
        
        # Create the .env file
        with open(self.env_file, 'w') as f:
            f.write("# Capital.com API Credentials\n")
            f.write(f"CAPITAL_API_KEY={capital_api_key}\n")
            f.write(f"CAPITAL_API_LOGIN={capital_api_login}\n")
            f.write(f"CAPITAL_API_PASSWORD={capital_api_password}\n\n")
            
            f.write("# Email settings for alerts\n")
            f.write(f"EMAIL_FROM={email_from}\n")
            f.write(f"EMAIL_TO={email_to}\n")
            f.write(f"EMAIL_PASSWORD={email_password}\n")
            f.write(f"SMTP_SERVER={smtp_server}\n")
            f.write(f"SMTP_PORT={smtp_port}\n\n")
            
            f.write("# Mobile Alert Settings\n")
            f.write(f"MOBILE_ALERTS_EMAIL_ENABLED={'true' if enable_email else 'false'}\n")
            f.write(f"MOBILE_ALERTS_SMS_ENABLED={'true' if enable_sms else 'false'}\n")
            f.write(f"MOBILE_ALERTS_PUSH_ENABLED={'true' if enable_push else 'false'}\n")
            f.write(f"MOBILE_ALERTS_WEBHOOK_ENABLED={'true' if enable_webhook else 'false'}\n")
            f.write("MOBILE_ALERTS_MIN_LEVEL=warning\n\n")
            
            if enable_sms:
                f.write("# SMS Gateway settings (if using SMS alerts)\n")
                sms_gateway = input("SMS Gateway (e.g. @txt.att.net): ").strip()
                sms_number = input("SMS Number: ").strip()
                f.write(f"SMS_GATEWAY={sms_gateway}\n")
                f.write(f"SMS_NUMBER={sms_number}\n\n")
            
            if enable_push:
                f.write("# Push notification settings (if using push notifications)\n")
                f.write("PUSH_SERVICE=onesignal\n")
                push_api_key = input("Push API Key: ").strip()
                push_app_id = input("Push App ID: ").strip()
                f.write(f"PUSH_API_KEY={push_api_key}\n")
                f.write(f"PUSH_APP_ID={push_app_id}\n\n")
            
            if enable_webhook:
                f.write("# Webhook settings (if using webhook alerts)\n")
                webhook_url = input("Webhook URL: ").strip()
                webhook_headers = input("Webhook Headers (JSON format, default: {\"Content-Type\": \"application/json\"}): ").strip()
                if not webhook_headers:
                    webhook_headers = "{\"Content-Type\": \"application/json\"}"
                f.write(f"WEBHOOK_ALERT_URL={webhook_url}\n")
                f.write(f"WEBHOOK_ALERT_HEADERS={webhook_headers}\n\n")
            
            f.write("# You need to fill in these values with your actual credentials\n")
            f.write("# For security, do not commit this file to version control\n")
            f.write("# This file should be included in your .gitignore\n")
        
        print(f"{Colors.GREEN}Created .env file at {self.env_file}{Colors.ENDC}")
    
    def _edit_env_file(self):
        """Edit an existing .env file"""
        print(f"\n{Colors.BLUE}Editing existing .env file...{Colors.ENDC}")
        
        # Read existing values
        env_values = {}
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_values[key] = value
        
        # Try to get values from credential database first
        try:
            # Import the credential manager
            sys.path.append(self.base_dir)
            from src.Credentials.credentials_manager import CredentialManager
            
            # Initialize CredentialManager
            credential_manager = CredentialManager()
            
            # Get credentials from database
            db_api_key = credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY')
            db_api_login = credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN')
            db_api_password = credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')
            
            # Update env_values with database values if they exist
            if db_api_key:
                env_values['CAPITAL_API_KEY'] = db_api_key
            if db_api_login:
                env_values['CAPITAL_API_LOGIN'] = db_api_login
            if db_api_password:
                env_values['CAPITAL_API_PASSWORD'] = db_api_password
                
            print(f"{Colors.GREEN}Found credentials in secure database. Using those as defaults.{Colors.ENDC}")
        except Exception as e:
            logger.error(f"Error reading from credential database: {str(e)}")
            print(f"{Colors.YELLOW}Could not access credential database, using .env values as defaults.{Colors.ENDC}")
        
        # Function to get input with existing value as default
        def get_input_with_default(prompt, key):
            default = env_values.get(key, '')
            # Mask password display
            if 'PASSWORD' in key and default:
                display_default = '********'
            else:
                display_default = default
            user_input = input(f"{prompt} [{display_default}]: ").strip()
            return user_input if user_input else default
        
        # Capital.com API credentials
        print(f"\n{Colors.HEADER}Capital.com API Credentials (optional){Colors.ENDC}")
        print(f"{Colors.YELLOW}Note: These credentials will be stored in the secure credential database when possible.{Colors.ENDC}")
        capital_api_key = get_input_with_default("Capital.com API Key", "CAPITAL_API_KEY")
        capital_api_login = get_input_with_default("Capital.com API Login", "CAPITAL_API_LOGIN")
        capital_api_password = get_input_with_default("Capital.com API Password", "CAPITAL_API_PASSWORD")
        
        # Email settings
        print(f"\n{Colors.HEADER}Email Alert Settings (optional){Colors.ENDC}")
        email_from = get_input_with_default("Email From", "EMAIL_FROM")
        email_to = get_input_with_default("Email To", "EMAIL_TO")
        email_password = get_input_with_default("Email Password", "EMAIL_PASSWORD")
        smtp_server = get_input_with_default("SMTP Server", "SMTP_SERVER")
        smtp_port = get_input_with_default("SMTP Port", "SMTP_PORT")
        
        # Mobile alerts settings
        print(f"\n{Colors.HEADER}Mobile Alert Settings{Colors.ENDC}")
        enable_email = input(f"Enable Email Alerts? [y/N] {'Y' if env_values.get('MOBILE_ALERTS_EMAIL_ENABLED') == 'true' else 'N'}: ").strip().lower() == 'y'
        enable_sms = input(f"Enable SMS Alerts? [y/N] {'Y' if env_values.get('MOBILE_ALERTS_SMS_ENABLED') == 'true' else 'N'}: ").strip().lower() == 'y'
        enable_push = input(f"Enable Push Notifications? [y/N] {'Y' if env_values.get('MOBILE_ALERTS_PUSH_ENABLED') == 'true' else 'N'}: ").strip().lower() == 'y'
        enable_webhook = input(f"Enable Webhook Alerts? [y/N] {'Y' if env_values.get('MOBILE_ALERTS_WEBHOOK_ENABLED') == 'true' else 'N'}: ").strip().lower() == 'y'
        
        # Try to save Capital.com credentials to the database first
        if capital_api_key or capital_api_login or capital_api_password:
            try:
                # Import the credential manager
                sys.path.append(self.base_dir)
                from src.Credentials.credentials_manager import CredentialManager
                
                # Initialize CredentialManager
                credential_manager = CredentialManager()
                
                # Store credentials in the database (only if they have values)
                if capital_api_key:
                    credential_manager.set_credential('capital_com', 'CAPITAL_API_KEY', capital_api_key)
                if capital_api_login:
                    credential_manager.set_credential('capital_com', 'CAPITAL_API_LOGIN', capital_api_login)
                if capital_api_password:
                    credential_manager.set_credential('capital_com', 'CAPITAL_API_PASSWORD', capital_api_password)
                
                logger.info("Capital.com API credentials updated in credential database")
                print(f"{Colors.GREEN}API credentials stored in secure credential database!{Colors.ENDC}")
            except Exception as e:
                logger.error(f"Error storing credentials in database: {str(e)}")
                print(f"{Colors.YELLOW}Could not update credentials in database, using .env file as fallback.{Colors.ENDC}")
        
        # Update the .env file
        with open(self.env_file, 'w') as f:
            f.write("# Capital.com API Credentials\n")
            f.write(f"CAPITAL_API_KEY={capital_api_key}\n")
            f.write(f"CAPITAL_API_LOGIN={capital_api_login}\n")
            f.write(f"CAPITAL_API_PASSWORD={capital_api_password}\n\n")
            
            f.write("# Email settings for alerts\n")
            f.write(f"EMAIL_FROM={email_from}\n")
            f.write(f"EMAIL_TO={email_to}\n")
            f.write(f"EMAIL_PASSWORD={email_password}\n")
            f.write(f"SMTP_SERVER={smtp_server}\n")
            f.write(f"SMTP_PORT={smtp_port}\n\n")
            
            f.write("# Mobile Alert Settings\n")
            f.write(f"MOBILE_ALERTS_EMAIL_ENABLED={'true' if enable_email else 'false'}\n")
            f.write(f"MOBILE_ALERTS_SMS_ENABLED={'true' if enable_sms else 'false'}\n")
            f.write(f"MOBILE_ALERTS_PUSH_ENABLED={'true' if enable_push else 'false'}\n")
            f.write(f"MOBILE_ALERTS_WEBHOOK_ENABLED={'true' if enable_webhook else 'false'}\n")
            f.write(f"MOBILE_ALERTS_MIN_LEVEL={env_values.get('MOBILE_ALERTS_MIN_LEVEL', 'warning')}\n\n")
            
            if enable_sms:
                f.write("# SMS Gateway settings (if using SMS alerts)\n")
                sms_gateway = get_input_with_default("SMS Gateway (e.g. @txt.att.net)", "SMS_GATEWAY")
                sms_number = get_input_with_default("SMS Number", "SMS_NUMBER")
                f.write(f"SMS_GATEWAY={sms_gateway}\n")
                f.write(f"SMS_NUMBER={sms_number}\n\n")
            
            if enable_push:
                f.write("# Push notification settings (if using push notifications)\n")
                f.write("PUSH_SERVICE=onesignal\n")
                push_api_key = get_input_with_default("Push API Key", "PUSH_API_KEY")
                push_app_id = get_input_with_default("Push App ID", "PUSH_APP_ID")
                f.write(f"PUSH_API_KEY={push_api_key}\n")
                f.write(f"PUSH_APP_ID={push_app_id}\n\n")
            
            if enable_webhook:
                f.write("# Webhook settings (if using webhook alerts)\n")
                webhook_url = get_input_with_default("Webhook URL", "WEBHOOK_ALERT_URL")
                webhook_headers = get_input_with_default("Webhook Headers (JSON format)", "WEBHOOK_ALERT_HEADERS")
                f.write(f"WEBHOOK_ALERT_URL={webhook_url}\n")
                f.write(f"WEBHOOK_ALERT_HEADERS={webhook_headers}\n\n")
            
            f.write("# You need to fill in these values with your actual credentials\n")
            f.write("# For security, do not commit this file to version control\n")
            f.write("# This file should be included in your .gitignore\n")
        
        print(f"{Colors.GREEN}Updated .env file at {self.env_file}{Colors.ENDC}")
    
    def _check_dependencies(self):
        """Check for required dependencies and install if necessary"""
        print(f"\n{Colors.BLUE}Checking for required dependencies...{Colors.ENDC}")
        
        required_packages = [
            "requests", "numpy", "pandas", "matplotlib", 
            "scikit-learn", "python-dotenv", "flask", "websocket-client"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} is installed")
            except ImportError:
                print(f"❌ {package} is not installed")
                install = input(f"Do you want to install {package}? [Y/n]: ").strip().lower()
                if install != 'n':
                    print(f"Installing {package}...")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                        print(f"✅ {package} installed successfully")
                    except Exception as e:
                        print(f"❌ Failed to install {package}: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        print(f"\n{Colors.BLUE}Setting up logging...{Colors.ENDC}")
        
        log_level = input("Select log level (debug/info/warning/error) [info]: ").strip().lower() or "info"
        log_levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR
        }
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_levels.get(log_level, logging.INFO))
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(self.base_dir, "Logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Ask for log file configuration
        use_file_logging = input("Enable file logging? [Y/n]: ").strip().lower() != 'n'
        if use_file_logging:
            log_file = os.path.join(log_dir, "jamso.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            root_logger.addHandler(file_handler)
            print(f"✅ File logging enabled. Logs will be saved to {log_file}")
        
        print(f"✅ Logging configured with level: {log_level.upper()}")
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if platform.system() == "Windows" else 'clear')
    
    def print_header(self):
        """Print the Jamso-AI-Engine header"""
        self.clear_screen()
        print(Colors.HEADER + Colors.BOLD)
        print("╔════════════════════════════════════════════════════════╗")
        print("║                  JAMSO-AI-ENGINE                       ║")
        print("║       Advanced Parameter Optimization Platform         ║")
        print("╚════════════════════════════════════════════════════════╝")
        print(Colors.ENDC)
        print(f"Current date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Working directory:", self.base_dir)
        print()
    
    def print_menu(self, title, options):
        """Print a formatted menu with options"""
        print(Colors.BLUE + Colors.BOLD + title + Colors.ENDC)
        print("─" * len(title))
        
        for key, option in options.items():
            print(f"{Colors.GREEN}{key}{Colors.ENDC}: {option['title']}")
        
        print()
        return input("Enter your choice (or 'q' to go back/quit): ")
    
    def signal_handler(self, sig, frame):
        """Handle termination signals"""
        print("\nTermination signal received. Cleaning up...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up any running processes"""
        for process in self.process_list:
            if process and isinstance(process, subprocess.Popen) and process.poll() is None:
                try:
                    process.terminate()
                    logger.info(f"Terminated process {process.pid}")
                except Exception as e:
                    logger.error(f"Error terminating process: {e}")
    
    def run_command(self, command, shell=False, background=False, explanation=None):
        """Run a shell command"""
        if explanation:
            print(f"\n{Colors.YELLOW}{explanation}{Colors.ENDC}\n")
        
        print(f"{Colors.BLUE}Running: {Colors.BOLD}{command}{Colors.ENDC}")
        
        try:
            if isinstance(command, str) and not shell:
                command = command.split()
            
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE if background else None,
                stderr=subprocess.PIPE if background else None,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.process_list.append(process)
            
            if not background:
                process.wait()
                print(f"{Colors.GREEN}Command completed with return code: {process.returncode}{Colors.ENDC}")
                input("\nPress Enter to continue...")
                return process.returncode
            else:
                return process
                
        except Exception as e:
            print(f"{Colors.RED}Error executing command: {e}{Colors.ENDC}")
            input("\nPress Enter to continue...")
            return 1
    
    def run_python_module(self, module_path, arguments=None, background=False, explanation=None):
        """Run a Python module"""
        cmd = [sys.executable, module_path]
        if arguments:
            cmd.extend(arguments if isinstance(arguments, list) else arguments.split())
            
        return self.run_command(cmd, background=background, explanation=explanation)
    
    def check_api_credentials(self):
        """Check if Capital.com API credentials are configured"""
        # Try to use the CredentialManager first
        try:
            # Import the credential manager
            sys.path.append(self.base_dir)
            from src.Credentials.credentials_manager import CredentialManager
            
            # Initialize CredentialManager
            credential_manager = CredentialManager()
            
            # Check if Capital.com API credentials exist in the credentials database
            api_key = credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY')
            api_login = credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN')
            api_password = credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')
            
            if api_key and api_login and api_password:
                logger.info("Capital.com API credentials found in credential database")
                print(f"{Colors.GREEN}✓ Secure API credentials found in credential database{Colors.ENDC}")
                return True
                
            logger.warning("Capital.com API credentials not found in credential database, checking .env file")
        except Exception as e:
            logger.error(f"Error accessing credential database: {str(e)}")
            logger.warning("Falling back to .env file for credentials")
            print(f"{Colors.YELLOW}! Could not access credential database: {str(e)}{Colors.ENDC}")
            print(f"{Colors.YELLOW}! Falling back to .env file for credentials{Colors.ENDC}")
        
        # Fall back to .env file if credentials not in database
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                content = f.read()
                
                # Check if credentials are set
                if re.search(r'CAPITAL_API_KEY=\S+', content):
                    return True
        
        print(f"{Colors.YELLOW}Warning: Capital.com API credentials not found in credential database or .env file.{Colors.ENDC}")
        print("You need to configure API credentials.")
        
        choice = input("Do you want to configure credentials now? (y/n): ")
        if choice.lower() == 'y':
            self.configure_api_credentials()
            return True
        
        return False
    
    def configure_api_credentials(self):
        """Configure Capital.com API credentials"""
        self.print_header()
        print(f"{Colors.BLUE}Configure Capital.com API Credentials{Colors.ENDC}")
        print("─" * 40)
        print(f"{Colors.YELLOW}Note: Credentials will be stored in the secure database when possible.{Colors.ENDC}")
        print(f"{Colors.YELLOW}The .env file will be used as a fallback only.{Colors.ENDC}")
        print("")
        
        api_key = input("Enter Capital.com API Key: ")
        api_login = input("Enter Capital.com API Login: ")
        api_password = input("Enter Capital.com API Password: ")
        
        db_success = False
        # Try to store in the credential database first
        try:
            # Import the credential manager
            sys.path.append(self.base_dir)
            from src.Credentials.credentials_manager import CredentialManager
            
            # Initialize CredentialManager
            credential_manager = CredentialManager()
            
            # Store credentials in the database
            if api_key:
                credential_manager.set_credential('capital_com', 'CAPITAL_API_KEY', api_key)
            if api_login:
                credential_manager.set_credential('capital_com', 'CAPITAL_API_LOGIN', api_login)
            if api_password:
                credential_manager.set_credential('capital_com', 'CAPITAL_API_PASSWORD', api_password)
            
            logger.info("Capital.com API credentials stored in credential database")
            print(f"{Colors.GREEN}✓ API credentials stored in secure credential database!{Colors.ENDC}")
            db_success = True
            
            # Verify storage was successful
            stored_key = credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY')
            if api_key and stored_key and stored_key == api_key:
                print(f"{Colors.GREEN}✓ Verified credentials stored correctly{Colors.ENDC}")
            else:
                print(f"{Colors.YELLOW}! Could not verify credentials in database{Colors.ENDC}")
                db_success = False
                
        except Exception as e:
            logger.error(f"Error storing credentials in database: {str(e)}")
            logger.warning("Falling back to .env file for credential storage")
            print(f"{Colors.YELLOW}! Could not store credentials in database: {str(e)}{Colors.ENDC}")
            print(f"{Colors.YELLOW}! Using .env file as fallback.{Colors.ENDC}")
        
        # Always update the .env file as a fallback/backup
        try:
            lines = []
            if os.path.exists(self.env_file):
                with open(self.env_file, 'r') as f:
                    lines = f.readlines()
            
            # Update or add credentials
            updated_key = False
            updated_login = False
            updated_password = False
            
            for i, line in enumerate(lines):
                if line.startswith('CAPITAL_API_KEY='):
                    lines[i] = f'CAPITAL_API_KEY={api_key}\n'
                    updated_key = True
                elif line.startswith('CAPITAL_API_LOGIN='):
                    lines[i] = f'CAPITAL_API_LOGIN={api_login}\n'
                    updated_login = True
                elif line.startswith('CAPITAL_API_PASSWORD='):
                    lines[i] = f'CAPITAL_API_PASSWORD={api_password}\n'
                    updated_password = True
            
            # Add any missing credentials
            if not updated_key and api_key:
                lines.append(f'CAPITAL_API_KEY={api_key}\n')
            if not updated_login and api_login:
                lines.append(f'CAPITAL_API_LOGIN={api_login}\n')
            if not updated_password and api_password:
                lines.append(f'CAPITAL_API_PASSWORD={api_password}\n')
            
            with open(self.env_file, 'w') as f:
                f.writelines(lines)
                
            if not db_success:
                print(f"{Colors.GREEN}✓ API credentials updated in .env file{Colors.ENDC}")
            else:
                print(f"{Colors.BLUE}ℹ .env file updated as backup{Colors.ENDC}")
        except Exception as e:
            logger.error(f"Error updating .env file: {str(e)}")
            print(f"{Colors.RED}✗ Error updating .env file: {str(e)}{Colors.ENDC}")
        
        print(f"\n{Colors.GREEN}API credentials update process completed!{Colors.ENDC}")
        if db_success:
            print(f"{Colors.GREEN}✓ Primary storage: Secure credential database{Colors.ENDC}")
            print(f"{Colors.BLUE}ℹ Backup storage: .env file{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}! Primary storage: .env file (credential database unavailable){Colors.ENDC}")
        
        input("\nPress Enter to continue...")
    
    def configure_mobile_alerts(self):
        """Configure mobile alert settings"""
        self.print_header()
        print(f"{Colors.BLUE}Configure Mobile Alert Settings{Colors.ENDC}")
        print("─" * 40)
        
        print("Select alert methods to enable:")
        
        email_enabled = input("Enable Email Alerts? (y/n): ").lower() == 'y'
        sms_enabled = input("Enable SMS Alerts? (y/n): ").lower() == 'y'
        push_enabled = input("Enable Push Notifications? (y/n): ").lower() == 'y'
        webhook_enabled = input("Enable Webhook Alerts? (y/n): ").lower() == 'y'
        
        alert_level = input("Set minimum alert level (info/warning/critical) [default: warning]: ").lower()
        if alert_level not in ['info', 'warning', 'critical']:
            alert_level = 'warning'
        
        lines = []
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                lines = f.readlines()
        
        # Update alert settings
        settings = {
            'MOBILE_ALERTS_EMAIL_ENABLED': 'true' if email_enabled else 'false',
            'MOBILE_ALERTS_SMS_ENABLED': 'true' if sms_enabled else 'false',
            'MOBILE_ALERTS_PUSH_ENABLED': 'true' if push_enabled else 'false',
            'MOBILE_ALERTS_WEBHOOK_ENABLED': 'true' if webhook_enabled else 'false',
            'MOBILE_ALERTS_MIN_LEVEL': alert_level
        }
        
        # Collect additional settings if needed
        if email_enabled:
            print("\nEnter Email Settings:")
            settings['EMAIL_FROM'] = input("Sender Email: ")
            settings['EMAIL_TO'] = input("Recipient Email: ")
            settings['EMAIL_PASSWORD'] = input("Email Password: ")
            settings['SMTP_SERVER'] = input("SMTP Server [smtp.gmail.com]: ") or 'smtp.gmail.com'
            settings['SMTP_PORT'] = input("SMTP Port [587]: ") or '587'
        
        if sms_enabled:
            print("\nEnter SMS Settings:")
            settings['SMS_GATEWAY'] = input("SMS Gateway (e.g., txt.att.net): ")
            settings['SMS_NUMBER'] = input("Phone Number: ")
        
        # Update or add settings in .env file
        updated_keys = []
        for i, line in enumerate(lines):
            for key in settings:
                if line.startswith(f'{key}='):
                    lines[i] = f'{key}={settings[key]}\n'
                    updated_keys.append(key)
        
        # Add settings not updated
        for key, value in settings.items():
            if key not in updated_keys:
                lines.append(f'{key}={value}\n')
        
        with open(self.env_file, 'w') as f:
            f.writelines(lines)
            
        print(f"\n{Colors.GREEN}Mobile alert settings updated successfully!{Colors.ENDC}")
        input("\nPress Enter to continue...")
    
    def capital_api_menu(self):
        """Show Capital.com API menu"""
        while True:
            self.print_header()
            options = {
                "1": {"title": "Test Capital.com API Connection", "action": self.test_capital_api},
                "2": {"title": "Run Optimization for Symbol", "action": self.run_optimization},
                "3": {"title": "Run Scheduled Optimization", "action": self.run_scheduled_optimization},
                "4": {"title": "Show API Documentation", "action": lambda: self.show_documentation("Capital_API_Documentation.md")},
                "5": {"title": "Configure API Credentials", "action": self.configure_api_credentials},
            }
            
            choice = self.print_menu("CAPITAL.COM API MENU", options)
            
            if choice == 'q':
                return
            elif choice in options:
                options[choice]["action"]()
    
    def test_capital_api(self):
        """Test Capital.com API connection"""
        if not self.check_api_credentials():
            return
        
        test_script = os.path.join(self.base_dir, "Tools", "test_capital_integration.sh")
        if not os.path.exists(test_script):
            print(f"{Colors.RED}Test script not found: {test_script}{Colors.ENDC}")
            input("\nPress Enter to continue...")
            return
        
        self.run_command(f"bash {test_script}", shell=True, explanation="Testing Capital.com API connection")
    
    def run_optimization(self):
        """Run optimization for a symbol"""
        if not self.check_api_credentials():
            return
        
        self.print_header()
        print(f"{Colors.BLUE}Run Capital.com API Optimization{Colors.ENDC}")
        print("─" * 40)
        
        symbol = input("Enter symbol (e.g., BTCUSD, EURUSD): ").upper() or "BTCUSD"
        timeframe = input("Enter timeframe (MINUTE, HOUR, DAY) [default: HOUR]: ").upper() or "HOUR"
        days = input("Number of days for historical data [default: 30]: ") or "30"
        objective = input("Optimization objective (sharpe, return, win_rate, risk_adjusted) [default: sharpe]: ") or "sharpe"
        use_sentiment = input("Use sentiment data? (y/n) [default: y]: ").lower() != 'n'
        
        # Build command
        cmd = [
            sys.executable,
            os.path.join(self.base_dir, "src", "AI", "capital_data_optimizer.py"),
            f"--symbol={symbol}",
            f"--timeframe={timeframe}",
            f"--days={days}",
            f"--objective={objective}"
        ]
        
        if use_sentiment:
            cmd.append("--use-sentiment")
            
        cmd.append("--save-plot")
        
        self.run_command(cmd, explanation=f"Running optimization for {symbol} ({timeframe})")
    
    def run_scheduled_optimization(self):
        """Run scheduled optimization"""
        if not self.check_api_credentials():
            return
        
        self.print_header()
        print(f"{Colors.BLUE}Run Scheduled Optimization{Colors.ENDC}")
        print("─" * 40)
        
        symbols = input("Enter symbols, comma-separated (e.g., BTCUSD,EURUSD) [default: BTCUSD]: ").upper() or "BTCUSD"
        timeframes = input("Enter timeframes, comma-separated (MINUTE,HOUR,DAY) [default: HOUR]: ").upper() or "HOUR"
        interval = input("Hours between optimization runs [default: 24]: ") or "24"
        use_sentiment = input("Use sentiment data? (y/n) [default: y]: ").lower() != 'n'
        use_mobile_alerts = input("Enable mobile alerts? (y/n) [default: y]: ").lower() != 'n'
        run_in_background = input("Run in background? (y/n) [default: n]: ").lower() == 'y'
        
        # Build command
        cmd = [
            sys.executable,
            os.path.join(self.base_dir, "src", "AI", "scheduled_optimization.py"),
            f"--symbols={symbols}",
            f"--timeframes={timeframes}",
            f"--interval={interval}"
        ]
        
        if use_sentiment:
            cmd.append("--use-sentiment")
            
        if use_mobile_alerts:
            cmd.append("--mobile-alerts")
            alert_level = input("Alert level (info/warning/critical) [default: warning]: ").lower() or "warning"
            cmd.append(f"--alert-level={alert_level}")
        
        # Run the command
        explanation = f"Running scheduled optimization for {symbols} ({timeframes})"
        if run_in_background:
            # Create a log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(self.logs_dir, f"scheduled_optimization_{timestamp}.log")
            
            print(f"Starting in background mode. Logs will be written to: {log_file}")
            print("Use 'ps aux | grep scheduled_optimization.py' to find the process")
            print("Use 'kill <PID>' to stop the process")
            
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    cmd, 
                    stdout=f,
                    stderr=f,
                    text=True
                )
                
            if isinstance(process, subprocess.Popen):
                print(f"{Colors.GREEN}Started process with PID: {process.pid}{Colors.ENDC}")
                self.process_list.append(process)
            else:
                print(f"{Colors.GREEN}Process started{Colors.ENDC}")
            input("\nPress Enter to continue...")
        else:
            self.run_command(cmd, explanation=explanation)
    
    def sentiment_analysis_menu(self):
        """Show sentiment analysis menu"""
        while True:
            self.print_header()
            options = {
                "1": {"title": "Test Sentiment Integration", "action": self.test_sentiment_integration},
                "2": {"title": "Get Sentiment Data for Symbol", "action": self.get_sentiment_data},
                "3": {"title": "Show Sentiment Documentation", "action": lambda: self.show_documentation("Capital_API_Sentiment_Integration.md")},
            }
            
            choice = self.print_menu("SENTIMENT ANALYSIS MENU", options)
            
            if choice == 'q':
                return
            elif choice in options:
                options[choice]["action"]()
    
    def test_sentiment_integration(self):
        """Test sentiment integration"""
        test_script = os.path.join(self.base_dir, "Tools", "test_sentiment_integration.sh")
        if not os.path.exists(test_script):
            print(f"{Colors.RED}Test script not found: {test_script}{Colors.ENDC}")
            input("\nPress Enter to continue...")
            return
        
        self.run_command(f"bash {test_script}", shell=True, explanation="Testing sentiment data integration")
    
    def get_sentiment_data(self):
        """Get sentiment data for a symbol"""
        self.print_header()
        print(f"{Colors.BLUE}Get Sentiment Data{Colors.ENDC}")
        print("─" * 40)
        
        symbol = input("Enter symbol (e.g., BTCUSD, EURUSD): ").upper() or "BTCUSD"
        days = input("Number of days of historical data [default: 30]: ") or "30"
        timeframe = input("Timeframe for data (MINUTE, HOUR, DAY) [default: HOUR]: ").upper() or "HOUR"
        save_to_csv = input("Save data to CSV? (y/n) [default: n]: ").lower() == 'y'
        create_plot = input("Create plot? (y/n) [default: y]: ").lower() != 'n'
        
        # Build command
        cmd = [
            sys.executable,
            os.path.join(self.base_dir, "src", "AI", "sentiment_integration.py"),
            f"--symbol={symbol}",
            f"--days={days}",
            f"--timeframe={timeframe}"
        ]
        
        if save_to_csv:
            csv_file = f"{symbol}_sentiment_{datetime.now().strftime('%Y%m%d')}.csv"
            cmd.append(f"--save={csv_file}")
            
        if create_plot:
            cmd.append("--plot")
        
        self.run_command(cmd, explanation=f"Getting sentiment data for {symbol}")
    
    def dashboard_menu(self):
        """Show dashboard menu"""
        while True:
            self.print_header()
            options = {
                "1": {"title": "Launch Optimization Dashboard", "action": self.launch_dashboard},
                "2": {"title": "Generate Static Dashboard", "action": self.generate_static_dashboard},
                "3": {"title": "Show Dashboard Documentation", "action": lambda: self.show_documentation("Dashboard_Guide.md")},
            }
            
            choice = self.print_menu("DASHBOARD MENU", options)
            
            if choice == 'q':
                return
            elif choice in options:
                options[choice]["action"]()
    
    def launch_dashboard(self):
        """Launch the optimization dashboard"""
        dashboard_path = os.path.join(self.base_dir, "src", "AI", "optimization_dashboard.py")
        if not os.path.exists(dashboard_path):
            print(f"{Colors.RED}Dashboard script not found: {dashboard_path}{Colors.ENDC}")
            input("\nPress Enter to continue...")
            return
        
        # Run dashboard in background
        print(f"{Colors.YELLOW}Starting dashboard. Press Ctrl+C to stop.{Colors.ENDC}")
        print("Dashboard will be available at: http://localhost:8050")
        print("Keep this terminal window open while using the dashboard.")
        print(f"{Colors.YELLOW}Press Enter to stop the dashboard and return to the menu...{Colors.ENDC}")
        
        # Start process
        process = self.run_python_module(dashboard_path, background=True)
        
        # Wait for user to stop
        input()
        
        # Kill the dashboard process
        if process and isinstance(process, subprocess.Popen) and process.poll() is None:
            process.terminate()
            print(f"{Colors.GREEN}Dashboard stopped{Colors.ENDC}")
            input("\nPress Enter to continue...")
    
    def generate_static_dashboard(self):
        """Generate a static dashboard"""
        self.print_header()
        print(f"{Colors.BLUE}Generate Static Dashboard{Colors.ENDC}")
        print("─" * 40)
        
        # Find optimization results
        result_files = []
        for file in os.listdir(self.base_dir):
            if file.endswith('.json') and 'optimized_params' in file:
                result_files.append(file)
        
        if not result_files:
            print(f"{Colors.YELLOW}No optimization result files found.{Colors.ENDC}")
            print("Run optimization first or check the base directory for JSON files.")
            input("\nPress Enter to continue...")
            return
        
        print(f"Found {len(result_files)} optimization result files:")
        for i, file in enumerate(result_files):
            print(f"{i+1}. {file}")
        
        print("\nGenerating static dashboard...")
        
        # Build command
        cmd = [
            sys.executable,
            os.path.join(self.base_dir, "src", "AI", "scheduled_optimization.py"),
            "--dashboard-only"
        ]
        
        self.run_command(cmd, explanation="Generating static optimization dashboard")
        
        dashboard_dir = os.path.join(self.base_dir, "dashboard")
        if os.path.exists(dashboard_dir):
            print(f"\n{Colors.GREEN}Dashboard generated in the 'dashboard' directory{Colors.ENDC}")
            print(f"Open {os.path.join(dashboard_dir, 'index.html')} in your browser")
        else:
            print(f"{Colors.YELLOW}Dashboard directory not found. Check the logs for errors.{Colors.ENDC}")
        
        input("\nPress Enter to continue...")
    
    def mobile_alerts_menu(self):
        """Show mobile alerts menu"""
        while True:
            self.print_header()
            options = {
                "1": {"title": "Test Mobile Alerts", "action": self.test_mobile_alerts},
                "2": {"title": "Configure Alert Settings", "action": self.configure_mobile_alerts},
                "3": {"title": "Send Test Alert", "action": self.send_test_alert},
                "4": {"title": "Show Mobile Alerts Documentation", "action": lambda: self.show_documentation("Mobile_Alerts_Integration.md")},
            }
            
            choice = self.print_menu("MOBILE ALERTS MENU", options)
            
            if choice == 'q':
                return
            elif choice in options:
                options[choice]["action"]()
    
    def test_mobile_alerts(self):
        """Test mobile alerts"""
        test_script = os.path.join(self.base_dir, "Tools", "test_mobile_alerts.sh")
        if not os.path.exists(test_script):
            print(f"{Colors.RED}Test script not found: {test_script}{Colors.ENDC}")
            input("\nPress Enter to continue...")
            return
        
        self.run_command(f"bash {test_script}", shell=True, explanation="Testing mobile alerts functionality")
    
    def send_test_alert(self):
        """Send a test alert"""
        self.print_header()
        print(f"{Colors.BLUE}Send Test Alert{Colors.ENDC}")
        print("─" * 40)
        
        # Ask for alert details
        title = input("Alert title [default: Test Alert]: ") or "Test Alert"
        message = input("Alert message [default: This is a test alert from Jamso-AI-Engine]: ") or "This is a test alert from Jamso-AI-Engine"
        level = input("Alert level (info/warning/critical) [default: info]: ").lower() or "info"
        if level not in ['info', 'warning', 'critical']:
            level = 'info'
        
        # Build command
        cmd = [
            sys.executable,
            os.path.join(self.base_dir, "src", "AI", "mobile_alerts.py"),
            f"--title={title}",
            f"--message={message}",
            f"--level={level}"
        ]
        
        self.run_command(cmd, explanation=f"Sending {level} test alert")
    
    def configuration_menu(self):
        """Show configuration menu"""
        while True:
            self.print_header()
            options = {
                "1": {"title": "Run Configuration Wizard", "action": self.configuration_wizard},
                "2": {"title": "Configure API Credentials", "action": self.configure_api_credentials},
                "3": {"title": "Configure Mobile Alerts", "action": self.configure_mobile_alerts},
                "4": {"title": "Edit .env File", "action": self.edit_env_file},
                "5": {"title": "View System Status", "action": self.view_system_status},
                "6": {"title": "Create/Update Cron Jobs", "action": self.setup_cron_jobs},
                "7": {"title": "View Configuration Documentation", "action": lambda: self.show_documentation("AI/Configuration_Wizard_Guide.md")},
            }
            
            choice = self.print_menu("CONFIGURATION MENU", options)
            
            if choice == 'q':
                return
            elif choice in options:
                options[choice]["action"]()
    
    def edit_env_file(self):
        """Edit the .env file"""
        if not os.path.exists(self.env_file):
            print(f"{Colors.YELLOW}Creating new .env file...{Colors.ENDC}")
            with open(self.env_file, 'w') as f:
                f.write("# Capital.com API Credentials\n")
                f.write("CAPITAL_API_KEY=\n")
                f.write("CAPITAL_API_LOGIN=\n")
                f.write("CAPITAL_API_PASSWORD=\n\n")
                f.write("# Email settings for alerts\n")
                f.write("EMAIL_FROM=\n")
                f.write("EMAIL_TO=\n")
                f.write("EMAIL_PASSWORD=\n")
                f.write("SMTP_SERVER=smtp.gmail.com\n")
                f.write("SMTP_PORT=587\n\n")
                f.write("# Mobile Alert Settings\n")
                f.write("MOBILE_ALERTS_EMAIL_ENABLED=false\n")
                f.write("MOBILE_ALERTS_SMS_ENABLED=false\n")
                f.write("MOBILE_ALERTS_PUSH_ENABLED=false\n")
                f.write("MOBILE_ALERTS_WEBHOOK_ENABLED=false\n")
                f.write("MOBILE_ALERTS_MIN_LEVEL=warning\n\n")
                f.write("# You need to fill in these values with your actual credentials\n")
                f.write("# For security, do not commit this file to version control\n")
                f.write("# This file should be included in your .gitignore\n")
        
        # Determine editor to use
        editor = os.environ.get('EDITOR', 'nano')
        
        self.run_command(f"{editor} {self.env_file}", shell=True, explanation=f"Opening {self.env_file} for editing")
    
    def view_system_status(self):
        """View system status"""
        self.print_header()
        print(f"{Colors.BLUE}System Status{Colors.ENDC}")
        print("─" * 40)
        
        # Check Python version
        print(f"Python version: {sys.version}")
        
        # Check virtual environment
        in_venv = sys.prefix != sys.base_prefix
        print(f"Virtual environment: {Colors.GREEN + 'Active' + Colors.ENDC if in_venv else Colors.YELLOW + 'Inactive' + Colors.ENDC}")
        
        # Check required directories
        for dir_name in ["Logs", "src", "Tools", "Docs"]:
            dir_path = os.path.join(self.base_dir, dir_name)
            exists = os.path.isdir(dir_path)
            print(f"Directory '{dir_name}': {Colors.GREEN + '✓' + Colors.ENDC if exists else Colors.RED + '✗' + Colors.ENDC}")
        
        # Check key files
        key_files = [
            ("Capital Data Optimizer", "src/AI/capital_data_optimizer.py"),
            ("Sentiment Integration", "src/AI/sentiment_integration.py"),
            ("Mobile Alerts", "src/AI/mobile_alerts.py"),
            ("Optimization Dashboard", "src/AI/optimization_dashboard.py"),
            ("Scheduled Optimization", "src/AI/scheduled_optimization.py")
        ]
        
        print("\nKey Components:")
        for name, file_path in key_files:
            file_path = os.path.join(self.base_dir, file_path)
            exists = os.path.isfile(file_path)
            print(f"  {name}: {Colors.GREEN + '✓' + Colors.ENDC if exists else Colors.RED + '✗' + Colors.ENDC}")
        
        # Check API credentials
        env_exists = os.path.isfile(self.env_file)
        print(f"\n.env file: {Colors.GREEN + '✓' + Colors.ENDC if env_exists else Colors.RED + '✗' + Colors.ENDC}")
        
        api_configured = False
        if env_exists:
            with open(self.env_file, 'r') as f:
                content = f.read()
                api_configured = re.search(r'CAPITAL_API_KEY=\S+', content) is not None
        
        print(f"API credentials: {Colors.GREEN + '✓' + Colors.ENDC if api_configured else Colors.YELLOW + '✗' + Colors.ENDC}")
        
        # Check running processes
        print("\nRunning Processes:")
        try:
            output = subprocess.check_output(
                "ps aux | grep -E 'optimization|sentiment|mobile_alerts' | grep -v grep", 
                shell=True, 
                text=True
            )
            if output.strip():
                print(output)
            else:
                print("No relevant processes running")
        except subprocess.CalledProcessError:
            print("No relevant processes running")
        
        input("\nPress Enter to continue...")
    
    def setup_cron_jobs(self):
        """Setup or update cron jobs"""
        self.print_header()
        print(f"{Colors.BLUE}Setup/Update Cron Jobs{Colors.ENDC}")
        print("─" * 40)
        
        # Ask which cron jobs to setup
        print("Select cron jobs to setup/update:")
        setup_daily_optimization = input("Setup daily Capital.com optimization? (y/n): ").lower() == 'y'
        setup_ai_cron = input("Setup AI module daily update? (y/n): ").lower() == 'y'
        setup_git_backup = input("Setup Git backup cron job? (y/n): ").lower() == 'y'
        setup_performance = input("Setup performance monitoring cron job? (y/n): ").lower() == 'y'
        
        # Run selected setup scripts
        if setup_daily_optimization:
            script = os.path.join(self.base_dir, "Tools", "setup_capital_optimization.sh")
            if os.path.exists(script):
                self.run_command(f"bash {script}", shell=True, explanation="Setting up daily Capital.com optimization")
            else:
                print(f"{Colors.RED}Script not found: {script}{Colors.ENDC}")
        
        if setup_ai_cron:
            script = os.path.join(self.base_dir, "Tools", "setup_ai_cron.sh")
            if os.path.exists(script):
                self.run_command(f"bash {script}", shell=True, explanation="Setting up AI module daily update")
            else:
                print(f"{Colors.RED}Script not found: {script}{Colors.ENDC}")
        
        if setup_git_backup:
            script = os.path.join(self.base_dir, "Tools", "setup_git_backup_cron.sh")
            if os.path.exists(script):
                self.run_command(f"bash {script}", shell=True, explanation="Setting up Git backup cron job")
            else:
                print(f"{Colors.RED}Script not found: {script}{Colors.ENDC}")
        
        if setup_performance:
            script = os.path.join(self.base_dir, "Tools", "setup_performance_cron.sh")
            if os.path.exists(script):
                self.run_command(f"bash {script}", shell=True, explanation="Setting up performance monitoring cron job")
            else:
                print(f"{Colors.RED}Script not found: {script}{Colors.ENDC}")
        
        if not any([setup_daily_optimization, setup_ai_cron, setup_git_backup, setup_performance]):
            print(f"{Colors.YELLOW}No cron jobs selected for setup.{Colors.ENDC}")
            
        # Show current cron jobs
        print("\nCurrent crontab entries:")
        self.run_command("crontab -l", shell=True)
    
    def show_documentation(self, file_name):
        """Show documentation file"""
        doc_path = os.path.join(self.base_dir, "Docs", "AI", file_name)
        
        if not os.path.exists(doc_path):
            print(f"{Colors.RED}Documentation file not found: {doc_path}{Colors.ENDC}")
            input("\nPress Enter to continue...")
            return
        
        # Determine the pager to use
        pager = os.environ.get('PAGER', 'less')
        
        # Read file content
        try:
            with open(doc_path, 'r') as f:
                content = f.read()
                
            # Print header and first few lines
            self.print_header()
            print(f"{Colors.BLUE}Documentation: {file_name}{Colors.ENDC}")
            print("─" * 40)
            
            lines = content.split('\n')
            for i in range(min(10, len(lines))):
                print(lines[i])
            
            print(f"\n{Colors.YELLOW}Press q to exit the documentation viewer{Colors.ENDC}")
            input("Press Enter to view the full documentation...")
            
            # Use pager to show full content
            self.run_command(f"{pager} {doc_path}", shell=True)
            
        except Exception as e:
            print(f"{Colors.RED}Error reading documentation: {e}{Colors.ENDC}")
            input("\nPress Enter to continue...")
    
    def run(self):
        """Run the main launcher"""
        while True:
            self.print_header()
            
            options = {
                "1": {"title": "Capital.com API Integration", "action": self.capital_api_menu},
                "2": {"title": "Sentiment Analysis", "action": self.sentiment_analysis_menu},
                "3": {"title": "Optimization Dashboard", "action": self.dashboard_menu},
                "4": {"title": "Mobile Alerts", "action": self.mobile_alerts_menu},
                "5": {"title": "System Configuration", "action": self.configuration_menu},
                "6": {"title": "Documentation", "action": lambda: self.show_documentation("Risk_Parameters_Guide.md")},
                "7": {"title": "Exit", "action": lambda: sys.exit(0)}
            }
            
            choice = self.print_menu("MAIN MENU", options)
            
            if choice == 'q':
                self.cleanup()
                sys.exit(0)
            elif choice in options:
                options[choice]["action"]()
            else:
                print(f"{Colors.RED}Invalid choice. Please try again.{Colors.ENDC}")
                time.sleep(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Jamso-AI-Engine Launcher")
    parser.add_argument("--option", type=int, help="Menu option to select automatically")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    
    args = parser.parse_args()
    
    if args.no_color:
        Colors.disable()
    
    launcher = JamsoLauncher()
    
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\nExiting...")
        launcher.cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()
