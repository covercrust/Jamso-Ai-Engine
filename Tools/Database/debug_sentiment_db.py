#!/usr/bin/env python3
import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path for sentiment database
db_path = os.path.join("/home/jamso-ai-server/Jamso-Ai-Engine", "src", "Database", "Sentiment", "sentiment_data.db")
logger.info(f"Checking database at path: {db_path}")

# Check if file exists
if not os.path.exists(db_path):
    logger.error(f"Database file does not exist: {db_path}")
    # Check if directory exists
    dir_path = os.path.dirname(db_path)
    if os.path.exists(dir_path):
        logger.info(f"Directory exists: {dir_path}")
        # List files in directory
        files = os.listdir(dir_path)
        logger.info(f"Files in directory: {files}")
    else:
        logger.error(f"Directory does not exist: {dir_path}")
    exit(1)

# Connect to the database
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    logger.info("Successfully connected to the database")
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    logger.info(f"Tables in database: {tables}")
    
    if ('sentiment_data',) not in tables:
        logger.error("sentiment_data table does not exist!")
        exit(1)
        
    # Get total count of BTCUSD entries
    cursor.execute('SELECT COUNT(*) FROM sentiment_data WHERE symbol="BTCUSD"')
    total_count = cursor.fetchone()[0]
    print(f'Total BTCUSD entries: {total_count}')

    # Get count by source
    cursor.execute('SELECT source, COUNT(*) FROM sentiment_data WHERE symbol="BTCUSD" GROUP BY source')
    print('Entries by source:')
    for row in cursor.fetchall():
        print(f'- {row[0]}: {row[1]}')

    # Get date range
    cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM sentiment_data WHERE symbol="BTCUSD"')
    date_range = cursor.fetchone()
    print(f'Date range: {date_range[0]} to {date_range[1]}')

    conn.close()
except Exception as e:
    logger.exception(f"Error working with database: {str(e)}")
