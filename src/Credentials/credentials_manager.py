#!/usr/bin/env python3
"""
Credential Manager for Jamso AI Server
Provides secure storage and retrieval of API credentials
Integrates with the dashboard for admin credential management
"""
import os
import sys
import logging
import sqlite3
import json
from datetime import datetime
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Configure logger
from src.Logging.logger import get_logger
logger = get_logger(__name__)

class CredentialManager:
    """
    Securely manages API credentials with role-based access control
    """
    DB_PATH = os.path.join(BASE_PATH, 'src', 'Database', 'Credentials', 'credentials.db')
    
    def __init__(self, master_key=None):
        """Initialize the credential manager"""
        # Set up encryption
        self.master_key = master_key or os.environ.get('CREDENTIAL_MASTER_KEY')
        if not self.master_key:
            # Generate a default key if none provided - this should be set in production
            self.master_key = self._generate_default_key()
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        
        # Initialize database
        self._init_db()
        
    def _generate_default_key(self):
        """Generate a default encryption key based on machine info"""
        # WARNING: This is less secure than using a proper environment variable
        # Only used as a fallback in development
        machine_id = ""
        try:
            with open('/etc/machine-id', 'r') as f:
                machine_id = f.read().strip()
        except:
            machine_id = "jamso-ai-default-key"
        
        return hashlib.sha256(machine_id.encode()).hexdigest()[:32]
    
    def _get_cipher(self):
        """Get a cipher for encryption/decryption"""
        password = self.master_key.encode()
        salt = b'jamsoaisalt'  # Fixed salt - you might want to store this securely
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def _encrypt(self, data):
        """Encrypt data with the master key"""
        if not data:
            return None
        cipher = self._get_cipher()
        return cipher.encrypt(data.encode()).decode()
    
    def _decrypt(self, encrypted_data):
        """Decrypt data with the master key"""
        if not encrypted_data:
            return None
        cipher = self._get_cipher()
        try:
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            return None
    
    def _init_db(self):
        """Initialize the credentials database"""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                credential_key TEXT NOT NULL,
                credential_value TEXT NOT NULL,
                is_encrypted INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                UNIQUE(service_name, credential_key)
            )
            ''')
            
            # Create access control table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS credential_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                role TEXT NOT NULL,
                can_read INTEGER DEFAULT 1,
                can_write INTEGER DEFAULT 0,
                UNIQUE(service_name, role)
            )
            ''')
            
            # Create audit log table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS credential_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                credential_key TEXT NOT NULL,
                action TEXT NOT NULL,
                user_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.debug("Credential database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing credential database: {str(e)}")
            raise
    
    def set_credential(self, service_name, credential_key, credential_value, user_id=None, encrypt=True):
        """
        Set or update a credential
        
        Args:
            service_name: The service this credential is for (e.g., 'capital_com')
            credential_key: The key name (e.g., 'api_key')
            credential_value: The value to store
            user_id: The user ID making this change (for audit)
            encrypt: Whether to encrypt the value (default: True)
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            # Check if credential exists
            cursor.execute(
                "SELECT id FROM credentials WHERE service_name = ? AND credential_key = ?",
                (service_name, credential_key)
            )
            result = cursor.fetchone()
            
            # Encrypt the value if needed
            stored_value = self._encrypt(credential_value) if encrypt else credential_value
            
            if result:
                # Update existing credential
                cursor.execute(
                    "UPDATE credentials SET credential_value = ?, is_encrypted = ?, updated_at = CURRENT_TIMESTAMP WHERE service_name = ? AND credential_key = ?",
                    (stored_value, 1 if encrypt else 0, service_name, credential_key)
                )
                action = "UPDATE"
            else:
                # Insert new credential
                cursor.execute(
                    "INSERT INTO credentials (service_name, credential_key, credential_value, is_encrypted, created_by) VALUES (?, ?, ?, ?, ?)",
                    (service_name, credential_key, stored_value, 1 if encrypt else 0, user_id)
                )
                action = "INSERT"
            
            # Log the action
            cursor.execute(
                "INSERT INTO credential_audit_log (service_name, credential_key, action, user_id) VALUES (?, ?, ?, ?)",
                (service_name, credential_key, action, user_id)
            )
            
            conn.commit()
            conn.close()
            logger.info(f"Credential {service_name}.{credential_key} {action.lower()}d successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting credential: {str(e)}")
            return False
    
    def get_credential(self, service_name, credential_key, user_id=None):
        """
        Get a credential
        
        Args:
            service_name: The service this credential is for
            credential_key: The key name
            user_id: The user ID retrieving this credential (for audit)
        
        Returns:
            The credential value or None if not found
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            logger.debug(f"Querying credential for service: {service_name}, key: {credential_key}")
            cursor.execute(
                "SELECT credential_value, is_encrypted FROM credentials WHERE service_name = ? AND credential_key = ?",
                (service_name, credential_key)
            )
            result = cursor.fetchone()
            
            if not result:
                logger.debug(f"No credential found for service: {service_name}, key: {credential_key}")
                conn.close()
                return None
                
            value, is_encrypted = result
            logger.debug(f"Retrieved credential: {value}, Encrypted: {is_encrypted}")
            
            # Log the retrieval
            if user_id:
                cursor.execute(
                    "INSERT INTO credential_audit_log (service_name, credential_key, action, user_id) VALUES (?, ?, ?, ?)",
                    (service_name, credential_key, "READ", user_id)
                )
                conn.commit()
            
            conn.close()
            
            # Decrypt if needed
            if is_encrypted:
                logger.debug(f"Decrypting credential for service: {service_name}, key: {credential_key}")
                return self._decrypt(value)
            else:
                return value
                
        except Exception as e:
            logger.error(f"Error getting credential: {str(e)}")
            return None
    
    def get_all_service_credentials(self, service_name, user_id=None):
        """
        Get all credentials for a service
        
        Args:
            service_name: The service to get credentials for
            user_id: The user ID retrieving these credentials (for audit)
        
        Returns:
            Dictionary of credentials for the service
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT credential_key, credential_value, is_encrypted FROM credentials WHERE service_name = ?",
                (service_name,)
            )
            results = cursor.fetchall()
            
            # Log the retrieval
            if user_id and results:
                cursor.execute(
                    "INSERT INTO credential_audit_log (service_name, credential_key, action, user_id) VALUES (?, ?, ?, ?)",
                    (service_name, "ALL", "READ_ALL", user_id)
                )
                conn.commit()
            
            conn.close()
            
            credentials = {}
            for key, value, is_encrypted in results:
                if is_encrypted:
                    credentials[key] = self._decrypt(value)
                else:
                    credentials[key] = value
                    
            return credentials
                
        except Exception as e:
            logger.error(f"Error getting service credentials: {str(e)}")
            return {}
    
    def delete_credential(self, service_name, credential_key, user_id=None):
        """
        Delete a credential
        
        Args:
            service_name: The service this credential is for
            credential_key: The key name
            user_id: The user ID making this change (for audit)
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM credentials WHERE service_name = ? AND credential_key = ?",
                (service_name, credential_key)
            )
            
            # Log the action
            cursor.execute(
                "INSERT INTO credential_audit_log (service_name, credential_key, action, user_id) VALUES (?, ?, ?, ?)",
                (service_name, credential_key, "DELETE", user_id)
            )
            
            conn.commit()
            conn.close()
            logger.info(f"Credential {service_name}.{credential_key} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting credential: {str(e)}")
            return False
    
    def set_access_control(self, service_name, role, can_read=True, can_write=False):
        """
        Set access control for a service and role
        
        Args:
            service_name: The service to set access for
            role: The role to set access for (e.g., 'admin', 'user')
            can_read: Whether this role can read the credentials
            can_write: Whether this role can modify the credentials
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM credential_access WHERE service_name = ? AND role = ?",
                (service_name, role)
            )
            result = cursor.fetchone()
            
            if result:
                # Update existing access control
                cursor.execute(
                    "UPDATE credential_access SET can_read = ?, can_write = ? WHERE service_name = ? AND role = ?",
                    (1 if can_read else 0, 1 if can_write else 0, service_name, role)
                )
            else:
                # Insert new access control
                cursor.execute(
                    "INSERT INTO credential_access (service_name, role, can_read, can_write) VALUES (?, ?, ?, ?)",
                    (service_name, role, 1 if can_read else 0, 1 if can_write else 0)
                )
            
            conn.commit()
            conn.close()
            logger.info(f"Access control for {service_name}.{role} set successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting access control: {str(e)}")
            return False
    
    def check_access(self, service_name, role, access_type='read'):
        """
        Check if a role has access to a service's credentials
        
        Args:
            service_name: The service to check access for
            role: The role to check (e.g., 'admin', 'user')
            access_type: The type of access to check ('read' or 'write')
            
        Returns:
            Boolean indicating if access is allowed
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            # Admin role always has full access
            if role == 'admin':
                conn.close()
                return True
            
            access_column = 'can_read' if access_type == 'read' else 'can_write'
            
            cursor.execute(
                f"SELECT {access_column} FROM credential_access WHERE service_name = ? AND role = ?",
                (service_name, role)
            )
            result = cursor.fetchone()
            
            conn.close()
            
            # If no explicit rule is found, deny access
            if not result:
                return False
                
            return result[0] == 1
                
        except Exception as e:
            logger.error(f"Error checking access: {str(e)}")
            return False
    
    def get_audit_log(self, service_name=None, limit=100):
        """
        Get the credential audit log
        
        Args:
            service_name: Optional filter for a specific service
            limit: Maximum number of log entries to return
            
        Returns:
            List of audit log entries
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if service_name:
                cursor.execute(
                    "SELECT * FROM credential_audit_log WHERE service_name = ? ORDER BY timestamp DESC LIMIT ?",
                    (service_name, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM credential_audit_log ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                
            results = cursor.fetchall()
            conn.close()
            
            # Convert rows to dictionaries
            log_entries = []
            for row in results:
                log_entries.append(dict(row))
                
            return log_entries
                
        except Exception as e:
            logger.error(f"Error getting audit log: {str(e)}")
            return []
    
    def export_credentials(self, service_name=None, user_id=None):
        """
        Export credentials to a dictionary (for env.sh generation)
        
        Args:
            service_name: Optional filter for a specific service
            user_id: The user ID exporting these credentials (for audit)
            
        Returns:
            Dictionary of all credentials
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            if service_name:
                cursor.execute(
                    "SELECT service_name, credential_key, credential_value, is_encrypted FROM credentials WHERE service_name = ?",
                    (service_name,)
                )
            else:
                cursor.execute(
                    "SELECT service_name, credential_key, credential_value, is_encrypted FROM credentials"
                )
                
            results = cursor.fetchall()
            
            # Log the export
            if user_id:
                service_str = service_name if service_name else "ALL"
                cursor.execute(
                    "INSERT INTO credential_audit_log (service_name, credential_key, action, user_id) VALUES (?, ?, ?, ?)",
                    (service_str, "ALL", "EXPORT", user_id)
                )
                conn.commit()
            
            conn.close()
            
            # Organize by service
            credentials = {}
            for service, key, value, is_encrypted in results:
                if service not in credentials:
                    credentials[service] = {}
                    
                if is_encrypted:
                    credentials[service][key] = self._decrypt(value)
                else:
                    credentials[service][key] = value
                    
            return credentials
                
        except Exception as e:
            logger.error(f"Error exporting credentials: {str(e)}")
            return {}

    def generate_env_variables(self, service_name=None):
        """
        Generate environment variable export statements for env.sh
        
        Args:
            service_name: Optional filter for a specific service
            
        Returns:
            String of export statements for env.sh
        """
        credentials = self.export_credentials(service_name)
        
        env_lines = []
        for service, creds in credentials.items():
            env_lines.append(f"# {service.upper()} API credentials")
            
            for key, value in creds.items():
                # Convert credential keys to environment variable format
                # Example: capital_com.api_key -> CAPITAL_API_KEY
                env_var = f"{service.upper()}_{key.upper()}"
                
                # Special handling for specific services like Capital.com
                if service == "capital_com":
                    # Use the conventional naming for Capital.com variables
                    if key == "api_key":
                        env_var = "CAPITAL_API_KEY"
                    elif key == "api_login":
                        env_var = "CAPITAL_API_LOGIN"
                    elif key == "api_password":
                        env_var = "CAPITAL_API_PASSWORD"
                
                # Escape any special characters in the value
                escaped_value = value.replace('"', '\\"').replace('$', '\\$')
                env_lines.append(f'export {env_var}="{escaped_value}"')
            
            env_lines.append("")  # Add blank line between services
        
        return "\n".join(env_lines)

# Singleton instance for easy access
_credential_manager = None

def get_credential_manager():
    """Get the singleton credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager

if __name__ == "__main__":
    # Test the credential manager
    import argparse
    
    parser = argparse.ArgumentParser(description='Credential Manager CLI')
    parser.add_argument('--action', choices=['set', 'get', 'delete', 'export', 'env'], required=True, help='Action to perform')
    parser.add_argument('--service', help='Service name')
    parser.add_argument('--key', help='Credential key')
    parser.add_argument('--value', help='Credential value (for set action)')
    parser.add_argument('--user', help='User ID (for audit)')
    
    args = parser.parse_args()
    
    manager = get_credential_manager()
    
    if args.action == 'set' and args.service and args.key and args.value:
        result = manager.set_credential(args.service, args.key, args.value, args.user)
        print(f"Set credential: {'Success' if result else 'Failed'}")
        
    elif args.action == 'get' and args.service and args.key:
        value = manager.get_credential(args.service, args.key, args.user)
        print(f"Credential value: {value}")
        
    elif args.action == 'delete' and args.service and args.key:
        result = manager.delete_credential(args.service, args.key, args.user)
        print(f"Delete credential: {'Success' if result else 'Failed'}")
        
    elif args.action == 'export':
        credentials = manager.export_credentials(args.service, args.user)
        print(json.dumps(credentials, indent=2))
        
    elif args.action == 'env':
        env_text = manager.generate_env_variables(args.service)
        print(env_text)
        
    else:
        print("Invalid arguments. Run with --help for usage information.")
