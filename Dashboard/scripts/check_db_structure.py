#!/usr/bin/env python3
"""
Script to check the structure of the users table

Enhancements:
- Added detailed comments for better understanding.
- Improved error handling and logging.
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
        logging.FileHandler(os.path.join(BASE_PATH, 'Logs', 'db_structure_check.log'))
    ]
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(BASE_PATH, 'src', 'Database', 'Users', 'users.db')

def check_table_structure():
    """
    Check the structure of the users table.

    Returns:
        None
    """
    try:
        logger.info("Connecting to the database.")
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Query the table structure
        logger.info("Fetching table structure for 'users'.")
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()

        # Log the table structure
        for column in columns:
            logger.info(f"Column: {column}")

        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    check_table_structure()
