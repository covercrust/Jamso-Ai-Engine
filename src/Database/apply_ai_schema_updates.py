#!/usr/bin/env python3
"""
Script to apply AI-related database schema updates.
This script adds columns and tables necessary for the AI trading functionality.
"""

import sqlite3
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_schema_update')

def apply_schema_updates(db_path, schema_file):
    """
    Apply SQL schema updates to the database.
    
    Args:
        db_path: Path to the SQLite database file
        schema_file: Path to the SQL schema file
    """
    try:
        # Check if database file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file does not exist: {db_path}")
            return False
            
        # Read schema file
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
            
        # Split into individual statements
        statements = schema_sql.split(';')
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute each statement
        success_count = 0
        error_count = 0
        
        for stmt in statements:
            # Skip empty statements
            stmt = stmt.strip()
            if not stmt:
                continue
                
            try:
                cursor.execute(stmt)
                success_count += 1
                logger.info(f"Successfully executed: {stmt[:60]}...")
            except sqlite3.Error as e:
                error_count += 1
                # Don't treat column already exists as an error
                if 'duplicate column name' in str(e):
                    logger.info(f"Column already exists: {e}")
                else:
                    logger.warning(f"Error executing statement: {stmt[:60]}...: {e}")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info(f"Schema update completed with {success_count} successful statements and {error_count} errors")
        return True
        
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
        return False

def main():
    """Main function to run the schema update."""
    # Define paths
    project_root = Path('/home/jamso-ai-server/Jamso-Ai-Engine')
    db_path = project_root / 'src' / 'Database' / 'Webhook' / 'trading_signals.db'
    schema_file = project_root / 'src' / 'Database' / 'ai_schema_updates.sql'
    
    # Ensure database directory exists
    db_dir = db_path.parent
    if not db_dir.exists():
        logger.info(f"Creating database directory: {db_dir}")
        db_dir.mkdir(parents=True, exist_ok=True)
    
    # Apply updates
    logger.info(f"Starting database schema updates from {schema_file} on {db_path}")
    if apply_schema_updates(db_path, schema_file):
        logger.info("Database schema updates completed successfully")
        return 0
    else:
        logger.error("Database schema updates failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
