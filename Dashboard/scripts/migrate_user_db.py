#!/usr/bin/env python3
"""
Migration script to add first_name and last_name columns to users table

Enhancements:
- Added detailed comments for better understanding.
- Improved logging configuration.
- Enhanced error handling.
"""

import os
import sys
import sqlite3
import logging

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_PATH, 'Logs', 'migration.log'))
    ]
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(BASE_PATH, 'src', 'Database', 'Users', 'users.db')

def migrate_user_table():
    """
    Add first_name and last_name columns to the users table.

    Returns:
        None
    """
    try:
        logger.info("Connecting to the database.")
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Add columns if they do not exist
        logger.info("Checking and adding columns to 'users' table.")
        cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT;")
        cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT;")

        conn.commit()
        logger.info("Migration completed successfully.")
        conn.close()
    except sqlite3.OperationalError as e:
        logger.warning(f"Operational error (likely column already exists): {e}")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    migrate_user_table()
