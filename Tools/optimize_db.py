#!/usr/bin/env python3
"""
SQLite Database Optimizer

This script optimizes the SQLite databases used by Jamso-AI Engine to improve performance
and memory utilization. It performs the following optimizations:

1. VACUUM - Rebuilds the database to reclaim unused space
2. ANALYZE - Updates statistics for the query planner
3. Sets PRAGMA settings for better performance
4. Creates missing indices if needed for performance

Run this script periodically to maintain optimal database performance.
"""
import os
import sys
import sqlite3
import logging
from pathlib import Path

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_PATH, 'Logs', 'db_optimizer.log'))
    ]
)
logger = logging.getLogger('db_optimizer')

# Database paths
DB_PATHS = [
    os.path.join(BASE_PATH, 'src', 'Database', 'Webhook', 'trading_signals.db'),
    os.path.join(BASE_PATH, 'src', 'Database', 'Credentials', 'credentials.db'),
    os.path.join(BASE_PATH, 'src', 'Database', 'Users', 'users.db'),
]

def optimize_database(db_path):
    """Optimize a SQLite database file"""
    if not os.path.exists(db_path):
        logger.warning(f"Database file not found: {db_path}")
        return False
    
    logger.info(f"Optimizing database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get database size before optimization
        db_size_before = os.path.getsize(db_path) / (1024 * 1024)  # MB
        logger.info(f"Database size before optimization: {db_size_before:.2f} MB")
        
        # Set optimal PRAGMA settings for better memory usage
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = 10000")  # Increased cache size (in pages)
        cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB memory map
        cursor.execute("PRAGMA temp_store = MEMORY")  # Store temp tables in memory
        
        # Run ANALYZE to update statistics
        logger.info("Running ANALYZE...")
        cursor.execute("ANALYZE")
        
        # Run VACUUM to rebuild the database
        logger.info("Running VACUUM...")
        cursor.execute("VACUUM")
        
        # Create some common performance indices if they don't exist
        # Users database indices
        if 'users.db' in db_path:
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """)
        
        # Trading signals database indices
        if 'trading_signals.db' in db_path:
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_positions_timestamp ON positions(timestamp DESC);
            """)
        
        # Commit changes and close
        conn.commit()
        conn.close()
        
        # Get database size after optimization
        db_size_after = os.path.getsize(db_path) / (1024 * 1024)  # MB
        logger.info(f"Database size after optimization: {db_size_after:.2f} MB")
        logger.info(f"Space saved: {db_size_before - db_size_after:.2f} MB")
        
        return True
    except sqlite3.Error as e:
        logger.error(f"Error optimizing database {db_path}: {str(e)}")
        return False

def optimize_all_databases():
    """Optimize all SQLite databases in the project"""
    success_count = 0
    
    for db_path in DB_PATHS:
        if optimize_database(db_path):
            success_count += 1
    
    logger.info(f"Optimized {success_count} out of {len(DB_PATHS)} databases")
    return success_count == len(DB_PATHS)

if __name__ == "__main__":
    logger.info("Starting database optimization")
    success = optimize_all_databases()
    sys.exit(0 if success else 1)
