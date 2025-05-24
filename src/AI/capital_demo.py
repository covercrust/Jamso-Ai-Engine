#!/usr/bin/env python3
"""
Capital.com API Demo Script

This script demonstrates how to use the Capital.com API integration
to fetch market data and perform a simple parameter optimization.

Usage:
    python capital_demo.py --symbol BTCUSD --days 7
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import argparse
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import dotenv for loading environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables may not be loaded.")

# Add parent directory to path to access the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

def main():
    """Main function to run the demo."""
    parser = argparse.ArgumentParser(description="Capital.com API Demo")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Market symbol")
    parser.add_argument("--days", type=int, default=7, help="Number of days of data")
    parser.add_argument("--save", action="store_true", help="Save data to CSV")
    args = parser.parse_args()
    
    logger.info(f"Starting Capital.com API demo for {args.symbol}")
    
    # Try to import our fallback API first (minimal dependencies)
    try:
        from src.AI.fallback_capital_api import FallbackApiClient
        logger.info("Using fallback Capital.com API client")
        
        # Create client
        client = FallbackApiClient()
        
        # Fetch historical price data
        logger.info(f"Fetching {args.days} days of hourly data for {args.symbol}")
        candles = client.get_historical_prices(
            symbol=args.symbol,
            resolution='HOUR',
            days=args.days,
            max_candles=1000
        )
        
        if candles:
            logger.info(f"Successfully fetched {len(candles)} candles")
            
            # Convert to DataFrame
            df = client.convert_to_dataframe(candles)
            
            if df is not None:
                # Display data summary
                logger.info(f"Data summary for {args.symbol}:")
                logger.info(f"Time range: {df.index.min()} to {df.index.max()}")
                logger.info(f"Price range: {df['close'].min():.2f} to {df['close'].max():.2f}")
                
                # Create a simple plot
                plt.figure(figsize=(12, 6))
                plt.plot(df.index, df['close'], label='Close Price')
                plt.title(f"{args.symbol} Price Chart")
                plt.xlabel("Date")
                plt.ylabel("Price")
                plt.grid(True)
                plt.legend()
                
                # Save plot
                plot_file = f"{args.symbol}_price_chart.png"
                plt.savefig(plot_file)
                logger.info(f"Price chart saved to {plot_file}")
                
                # Save data if requested
                if args.save:
                    csv_file = f"{args.symbol}_price_data.csv"
                    df.to_csv(csv_file)
                    logger.info(f"Price data saved to {csv_file}")
                
                logger.info("Demo completed successfully!")
            else:
                logger.error("Failed to convert data to DataFrame")
        else:
            logger.error("Failed to fetch price data")
    
    except ImportError:
        logger.error("Failed to import Capital.com API modules")
        logger.error("Make sure python-dotenv and requests are installed:")
        logger.error("    pip install python-dotenv requests pandas matplotlib")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
