"""
User model for dashboard authentication

Enhancements:
- Added detailed comments for better understanding.
- Improved logging configuration.
- Enhanced error handling.
"""

import os
import sys
import sqlite3
import hashlib
import secrets
import logging
from datetime import datetime

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File-level comment: This module implements the User model for authentication and authorization.

class User:
    """
    User model for authentication and authorization.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): Username of the user.
        password_hash (str): Hashed password for authentication.
        email (str): Email address of the user.
        role (str): Role of the user (admin, user, viewer).
        created_at (datetime): Timestamp of user creation.
        last_login (datetime): Timestamp of last login.
        api_key (str): API key associated with the user.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
    """

    # Updated to use the correct database path where we created the users
    DB_PATH = os.path.join(BASE_PATH, 'src', 'Database', 'Users', 'users.db')
    
    # User roles
    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'
    ROLE_VIEWER = 'viewer'
    
    # Role permissions
    PERMISSIONS = {
        ROLE_ADMIN: [
            'view_dashboard',
            'manage_users',
            'manage_settings',
            'execute_trades',
            'view_trades',
            'view_signals',
            'view_analytics',
            'manage_accounts',
            'view_logs',
            'manage_api_keys',
            'manage_webhooks'
        ],
        ROLE_USER: [
            'view_dashboard',
            'execute_trades',
            'view_trades',
            'view_signals',
            'view_analytics',
            'manage_accounts',
            'manage_api_keys',
            'manage_webhooks'
        ],
        ROLE_VIEWER: [
            'view_dashboard',
            'view_trades',
            'view_signals',
            'view_analytics'
        ]
    }
    
    def __init__(self, id=None, username=None, password_hash=None, email=None, 
                 role=None, created_at=None, last_login=None, api_key=None,
                 first_name=None, last_name=None, **kwargs):
        """
        Initialize a User instance.

        Args:
            id (int): Unique identifier for the user.
            username (str): Username of the user.
            password_hash (str): Hashed password for authentication.
            email (str): Email address of the user.
            role (str): Role of the user (admin, user, viewer).
            created_at (datetime): Timestamp of user creation.
            last_login (datetime): Timestamp of last login.
            api_key (str): API key associated with the user.
            first_name (str): First name of the user.
            last_name (str): Last name of the user.
        """
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.role = role or self.ROLE_USER
        self.created_at = created_at or datetime.now().isoformat()
        self.last_login = last_login
        self.api_key = api_key
        self.first_name = first_name or ''
        self.last_name = last_name or ''
        
        # Ignore any other keyword arguments
        for key, value in kwargs.items():
            logger.debug(f"Ignored unknown parameter in User constructor: {key}")
    
    @classmethod
    def get_db_connection(cls):
        """
        Get a connection to the database.

        Returns:
            sqlite3.Connection: Database connection object.
        """
        try:
            os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
            conn = sqlite3.connect(cls.DB_PATH)
            return conn
        except Exception as e:
            logger.error(f"Error getting database connection: {e}")
            raise
    
    @staticmethod
    def dict_factory(cursor, row):
        """
        Convert database row to dictionary.

        Args:
            cursor (sqlite3.Cursor): Database cursor.
            row (tuple): Row data.

        Returns:
            dict: Dictionary representation of the row.
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    @classmethod
    def init_db(cls):
        """
        Initialize the users database with required tables.

        Returns:
            bool: True if initialization is successful, False otherwise.
        """
        try:
            os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
            
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                api_key TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
            ''')
            
            # Create API tokens table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_tokens (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                last_used TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {cls.DB_PATH}")
            return True
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            return False
    
    @classmethod
    def create_admin_if_not_exists(cls):
        """
        Create an admin user if one doesn't exist.
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            cursor = conn.cursor()
            
            # Check if admin exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (cls.ROLE_ADMIN,))
            admin_count = cursor.fetchone()[0]
            
            if admin_count == 0:
                # Generate a strong password
                default_password = secrets.token_urlsafe(12)
                password_hash = cls.hash_password(default_password)
                
                # Create admin user
                cursor.execute(
                    "INSERT INTO users (username, password_hash, email, role, created_at) VALUES (?, ?, ?, ?, ?)",
                    ('admin', password_hash, 'admin@example.com', cls.ROLE_ADMIN, datetime.now().isoformat())
                )
                
                conn.commit()
                logger.info(f"Admin user created with default password: {default_password}")
                print(f"Admin user created with default password: {default_password}")
                print("Please change this password immediately after logging in!")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
    
    @staticmethod
    def hash_password(password):
        """
        Hash a plaintext password using SHA-256.

        Args:
            password (str): Plaintext password.

        Returns:
            str: Hashed password.
        """
        try:
            logger.info("Hashing password.")
            return hashlib.sha256(password.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    @staticmethod
    def verify_password(password, password_hash):
        """
        Verify a password against its hash.

        Args:
            password (str): Plaintext password.
            password_hash (str): Hashed password.

        Returns:
            bool: True if the password matches the hash, False otherwise.
        """
        try:
            # Generate hash of the provided password and compare
            provided_hash = hashlib.sha256(password.encode()).hexdigest()
            match = provided_hash == password_hash
            
            logger.debug(f"Password verification - Stored hash: {password_hash[:6]}[...]")
            logger.debug(f"Password verification - Provided hash: {provided_hash[:6]}[...]")
            logger.debug(f"Password verification result: {match}")
            
            return match
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            raise
    
    def save(self):
        """
        Save user to database.

        Returns:
            bool: True if save is successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            
            if self.id:
                # Update existing user
                cursor.execute('''
                UPDATE users 
                SET username = ?, password_hash = ?, email = ?, role = ?, last_login = ?, api_key = ?, first_name = ?, last_name = ? 
                WHERE id = ?
                ''', (self.username, self.password_hash, self.email, self.role, self.last_login, self.api_key, self.first_name, self.last_name, self.id))
            else:
                # Insert new user
                cursor.execute('''
                INSERT INTO users (username, password_hash, email, role, created_at, last_login, api_key, first_name, last_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.username, self.password_hash, self.email, self.role, self.created_at, self.last_login, self.api_key, self.first_name, self.last_name))
                self.id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False
    
    @classmethod
    def find_by_username(cls, username):
        """
        Find a user by username.

        Args:
            username (str): Username to search for.

        Returns:
            User: User instance if found, None otherwise.
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                return cls(**dict(user_data))
            return None
        except Exception as e:
            logger.error(f"Error finding user by username: {e}")
            return None
    
    @classmethod
    def find_by_email(cls, email):
        """
        Find a user by email.

        Args:
            email (str): Email to search for.

        Returns:
            User: User instance if found, None otherwise.
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                return cls(**dict(user_data))
            return None
        except Exception as e:
            logger.error(f"Error finding user by email: {e}")
            return None
    
    @classmethod
    def find_by_id(cls, user_id):
        """
        Find a user by ID.

        Args:
            user_id (int): User ID to search for.

        Returns:
            User: User instance if found, None otherwise.
        """
        try:
            conn = sqlite3.connect(cls.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                return cls(**dict(user_data))
            return None
        except Exception as e:
            logger.error(f"Error finding user by ID: {e}")
            return None
    
    @classmethod
    def get_all_users(cls):
        """
        Get all users from the database.

        Returns:
            list: List of all users.
        """
        try:
            conn = cls.get_db_connection()
            conn.row_factory = cls.dict_factory
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users ORDER BY username")
            users = cursor.fetchall()
            conn.close()
            
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    @classmethod
    def delete_user(cls, user_id):
        """
        Delete a user by ID.

        Args:
            user_id (int): ID of the user to delete.

        Returns:
            bool: True if deletion is successful, False otherwise.
        """
        try:
            conn = cls.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def update_last_login(self):
        """
        Update the last login timestamp.
        """
        self.last_login = datetime.now().isoformat()
        self.save()
    
    def has_permission(self, permission):
        """
        Check if user has a specific permission.

        Args:
            permission (str): Permission to check.

        Returns:
            bool: True if the user has the permission, False otherwise.
        """
        if not self.role or self.role not in self.PERMISSIONS:
            return False
        return permission in self.PERMISSIONS[self.role]
    
    def get_permissions(self):
        """
        Get all permissions for this user.

        Returns:
            list: List of permissions.
        """
        if not self.role or self.role not in self.PERMISSIONS:
            return []
        return self.PERMISSIONS[self.role]