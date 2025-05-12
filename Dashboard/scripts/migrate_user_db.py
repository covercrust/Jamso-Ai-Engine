#!/usr/bin/env python3
"""
Migration script to add first_name and last_name columns to users table
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

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    return any(col[1] == column for col in columns)

def add_column_if_not_exists(conn, table, column, type_def):
    """Add a column to a table if it doesn't exist"""
    cursor = conn.cursor()
    
    if not check_column_exists(cursor, table, column):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
            logger.info(f"Added column '{column}' to table '{table}'")
            return True
        except Exception as e:
            logger.error(f"Error adding column '{column}' to table '{table}': {str(e)}")
            return False
    else:
        logger.info(f"Column '{column}' already exists in table '{table}'")
        return True

def migrate_database():
    """Perform the migration"""
    try:
        logger.info(f"Starting migration on database: {DB_PATH}")
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        
        # Add first_name and last_name columns if they don't exist
        add_column_if_not_exists(conn, 'users', 'first_name', 'TEXT')
        add_column_if_not_exists(conn, 'users', 'last_name', 'TEXT')
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
