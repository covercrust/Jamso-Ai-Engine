#!/usr/bin/env python3
"""
AI Module Setup Script

This script sets up the AI trading module environment:
- Creates necessary directories
- Validates the database schema
- Installs required Python packages
- Runs initial data collection

Usage:
    python3 setup_ai_module.py
"""

import os
import sys
import logging
import subprocess
import argparse
import sqlite3
import importlib.util
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Configure logging
log_file = os.path.join(os.path.dirname(__file__), '../../Logs/ai_module_setup.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_package_installed(package_name: str) -> bool:
    """
    Check if a Python package is installed.
    
    Args:
        package_name: Name of the package to check
        
    Returns:
        True if package is installed, False otherwise
    """
    return importlib.util.find_spec(package_name) is not None

def install_requirements() -> bool:
    """
    Install required Python packages.
    
    Returns:
        True if installation was successful, False otherwise
    """
    try:
        requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        
        if not os.path.exists(requirements_path):
            logger.warning(f"Requirements file not found at {requirements_path}")
            return False
            
        logger.info(f"Installing requirements from {requirements_path}")
        
        # Install using pip
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_path
        ])
        
        logger.info("Requirements installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing requirements: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error installing requirements: {e}")
        return False

def validate_database_schema(db_path: str) -> bool:
    """
    Validate that the database has all required tables.
    
    Args:
        db_path: Path to the SQLite database
        
    Returns:
        True if database schema is valid, False otherwise
    """
    required_tables = [
        'market_volatility',
        'volatility_regimes',
        'position_sizing',
        'risk_metrics',
        'market_correlations',
        'account_balances'
    ]
    
    try:
        # Check if database file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            return False
            
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Check if all required tables exist
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"Missing tables in database: {', '.join(missing_tables)}")
            return False
            
        logger.info("Database schema validation successful")
        return True
        
    except Exception as e:
        logger.error(f"Error validating database schema: {e}")
        return False

def create_required_directories() -> bool:
    """
    Create required directories for AI module.
    
    Returns:
        True if directories were created successfully, False otherwise
    """
    required_dirs = [
        os.path.join(os.path.dirname(__file__), 'models'),
        os.path.join(os.path.dirname(__file__), 'utils'),
        os.path.join(os.path.dirname(__file__), 'scripts'),
        os.path.join(os.path.dirname(__file__), '../../Logs/visualizations')
    ]
    
    try:
        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory created/verified: {directory}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def run_initial_data_collection(symbols: List[str]) -> bool:
    """
    Run initial data collection for specified symbols.
    
    Args:
        symbols: List of symbols to collect data for
        
    Returns:
        True if data collection was successful, False otherwise
    """
    try:
        from src.AI.data_collector import create_default_collector
        
        logger.info(f"Running initial data collection for {len(symbols)} symbols")
        
        # Create collector with specified symbols
        collector = create_default_collector(symbols)
        
        # Collect data
        success_count = 0
        for symbol in symbols:
            logger.info(f"Collecting data for {symbol}")
            success = collector.collect_historical_data(symbol)
            if success:
                success_count += 1
                
        logger.info(f"Initial data collection completed: {success_count}/{len(symbols)} symbols successful")
        
        # Get and log data summary
        summary = collector.get_data_summary()
        for symbol, stats in summary.items():
            logger.info(f"{symbol}: {stats.get('record_count', 0)} records")
            
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error in initial data collection: {e}")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Set up AI trading module environment')
    
    parser.add_argument('--skip-install', action='store_true',
                       help='Skip package installation')
    
    parser.add_argument('--symbols', type=str, 
                       default='EURUSD,GBPUSD,USDJPY,BTCUSD,ETHUSD,US500,GOLD,OIL',
                       help='Comma-separated list of symbols for initial data collection')
    
    parser.add_argument('--db-path', type=str,
                       default='/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db',
                       help='Path to the SQLite database')
    
    return parser.parse_args()

def main():
    """Main function to set up AI module."""
    args = parse_args()
    
    logger.info("Starting AI trading module setup")
    
    # Step 1: Create required directories
    logger.info("Step 1: Creating required directories")
    if not create_required_directories():
        logger.error("Failed to create required directories")
        return 1
    
    # Step 2: Install required packages
    if not args.skip_install:
        logger.info("Step 2: Installing required packages")
        if not install_requirements():
            logger.error("Failed to install required packages")
            return 1
    else:
        logger.info("Step 2: Skipping package installation")
    
    # Step 3: Validate database schema
    logger.info("Step 3: Validating database schema")
    if not validate_database_schema(args.db_path):
        logger.error("Failed to validate database schema")
        return 1
    
    # Step 4: Run initial data collection
    logger.info("Step 4: Running initial data collection")
    symbols = args.symbols.split(',')
    if not run_initial_data_collection(symbols):
        logger.error("Failed to run initial data collection")
        return 1
    
    logger.info("AI trading module setup completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
