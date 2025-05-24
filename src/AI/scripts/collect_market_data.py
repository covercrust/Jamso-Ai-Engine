#!/usr/bin/env python3
"""
Scheduled Market Data Collection Script

This script collects historical market data for AI trading analysis.
It should be run daily via cron job to maintain up-to-date market data.

Usage:
    python3 collect_market_data.py [--symbols SYMBOL1,SYMBOL2,...] [--days DAYS]

Example:
    python3 collect_market_data.py --symbols EURUSD,BTCUSD,US500 --days 60
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from typing import List

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the data collector
from src.AI.data_collector import create_default_collector

# Configure logging
log_file = os.path.join(os.path.dirname(__file__), '../../Logs/market_data_collection.log')
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

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Collect market data for AI analysis')
    
    parser.add_argument('--symbols', type=str, default='',
                       help='Comma-separated list of symbols to collect data for')
    
    parser.add_argument('--days', type=int, default=60,
                       help='Number of days of historical data to collect')
    
    return parser.parse_args()

def main():
    """Main function to collect market data."""
    args = parse_args()
    
    # Get symbols from arguments or use defaults
    symbols = args.symbols.split(',') if args.symbols else None
    
    # Log start of collection
    logger.info(f"Starting market data collection for {symbols or 'default symbols'}")
    start_time = time.time()
    
    try:
        # Create collector with specified or default symbols
        collector = create_default_collector(symbols)
        
        # Set custom lookback days if specified
        if args.days != 60:  # 60 is the default in the collector
            collector.lookback_days = args.days
            logger.info(f"Set lookback period to {args.days} days")
        
        # Collect data for all symbols
        collector.collect_data_for_all_symbols()
        
        # Get and log collection summary
        summary = collector.get_data_summary()
        logger.info("Data Collection Summary:")
        for symbol, stats in summary.items():
            logger.info(f"{symbol}: {stats['record_count']} records from {stats['date_range']}")
        
    except Exception as e:
        logger.error(f"Error in market data collection: {e}", exc_info=True)
        return 1
    
    # Log completion time
    elapsed_time = time.time() - start_time
    logger.info(f"Market data collection completed in {elapsed_time:.2f} seconds")
    return 0

if __name__ == "__main__":
    sys.exit(main())
