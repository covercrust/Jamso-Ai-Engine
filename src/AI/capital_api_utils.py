#!/usr/bin/env python3
"""
Capital.com API Utility Functions

This module provides utility functions for working with Capital.com API
in the context of parameter optimization.

Usage:
    from capital_api_utils import fetch_historical_data, get_all_available_symbols
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Import Capital.com API
from src.Exchanges.capital_com_api.client import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Resolution mapping
RESOLUTION_MAP = {
    'MINUTE': 'MINUTE',
    'MINUTE_5': 'MINUTE_5',
    'MINUTE_15': 'MINUTE_15',
    'MINUTE_30': 'MINUTE_30',
    'HOUR': 'HOUR',
    'HOUR_4': 'HOUR_4',
    'DAY': 'DAY',
    'WEEK': 'WEEK',
    'MONTH': 'MONTH'
}

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'capital_api_config.json')
try:
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = json.load(f)
except Exception as e:
    logger.warning(f"Could not load configuration from {CONFIG_PATH}: {str(e)}")
    CONFIG = {
        "api_settings": {
            "request_timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 5,
            "max_candles_per_request": 1000
        }
    }

def get_client() -> Client:
    """
    Get a configured Capital.com API client
    
    Returns:
    - Capital.com API client instance
    """
    try:
        # Initialize the Capital.com API client
        client = Client()
        return client
    except Exception as e:
        logger.error(f"Error initializing Capital.com API client: {str(e)}")
        raise

def fetch_historical_data(symbol: str, resolution: str = 'HOUR', days: int = 30,
                         include_sentiment: bool = False) -> pd.DataFrame:
    """
    Fetch historical price data from Capital.com API
    
    Parameters:
    - symbol: Market symbol/epic (e.g., 'BTCUSD', 'EURUSD')
    - resolution: Timeframe ('MINUTE', 'HOUR', 'DAY', etc.)
    - days: Number of days of data to fetch
    - include_sentiment: Whether to include sentiment data in the result
    
    Returns:
    - DataFrame with OHLCV data (and sentiment if requested)
    """
    logger.info(f"Fetching {days} days of {resolution} data for {symbol}")
    
    # Calculate number of candles based on resolution and days
    # We need to consider trading hours and weekends for some resolutions
    candle_multiplier = {
        'MINUTE': 24 * 60,    # Minutes per day
        'MINUTE_5': 24 * 12,  # 5-minute candles per day
        'MINUTE_15': 24 * 4,  # 15-minute candles per day
        'MINUTE_30': 24 * 2,  # 30-minute candles per day
        'HOUR': 24,           # Hours per day
        'HOUR_4': 6,          # 4-hour candles per day
        'DAY': 1,             # Days per day
        'WEEK': 1/7,          # Weeks per day
        'MONTH': 1/30         # Months per day (approximate)
    }
    
    # Calculate max parameter for API (max candles to retrieve)
    max_candles = int(days * candle_multiplier.get(resolution, 1))
    
    # Cap at the configured maximum
    max_api_candles = CONFIG["api_settings"]["max_candles_per_request"]
    if max_candles > max_api_candles:
        logger.warning(f"Requested {max_candles} candles, capping at {max_api_candles} (API limit)")
        max_candles = max_api_candles
    
    try:
        # Initialize the Capital.com API client
        client = get_client()
        
        # Fetch historical price data
        price_data = client.market_data_manager.prices(
            epic=symbol,
            resolution=resolution,
            max=max_candles
        )
        
        # Extract price data from the response
        candles = price_data.get('prices', [])
        
        if not candles:
            logger.error(f"No price data returned for {symbol}")
            return pd.DataFrame()
        
        # Convert to pandas DataFrame
        data = []
        for candle in candles:
            # Extract OHLCV data
            timestamp = candle.get('snapshotTimeUTC')
            open_price = candle.get('openPrice', {}).get('bid')
            high_price = candle.get('highPrice', {}).get('bid')
            low_price = candle.get('lowPrice', {}).get('bid')
            close_price = candle.get('closePrice', {}).get('bid')
            volume = candle.get('lastTradedVolume', 0)
            
            # Skip incomplete candles
            if not all([timestamp, open_price, high_price, low_price, close_price]):
                continue
                
            data.append({
                'timestamp': timestamp,
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'close': float(close_price),
                'volume': float(volume)
            })
        
        # Create DataFrame and sort by timestamp
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate ATR (Average True Range)
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            df['atr'] = df['tr'].rolling(window=14).mean().fillna(df['tr'])
            
            # Clean up temporary columns
            df = df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1)
            
            # Add sentiment data if requested
            if include_sentiment:
                sentiment_data = fetch_market_sentiment(symbol)
                sentiment_value = sentiment_data.get('long_position_percentage', 50) / 100
                df['sentiment'] = sentiment_value
            
            logger.info(f"Fetched {len(df)} candles from {df['timestamp'].min()} to {df['timestamp'].max()}")
            return df
        else:
            logger.error("Failed to create DataFrame from candle data")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return pd.DataFrame()

def fetch_market_sentiment(symbol: str) -> dict:
    """
    Fetch market sentiment data from Capital.com API
    
    Parameters:
    - symbol: Market symbol/epic (e.g., 'BTCUSD', 'EURUSD')
    
    Returns:
    - Dictionary with sentiment data
    """
    try:
        # Initialize the Capital.com API client
        client = get_client()
        
        # Fetch sentiment data
        sentiment_data = client.market_data_manager.client_sentiment(symbol)
        
        # Extract relevant information
        if sentiment_data:
            return {
                'long_position_percentage': sentiment_data.get('longPositionPercentage', 50),
                'short_position_percentage': sentiment_data.get('shortPositionPercentage', 50)
            }
        else:
            logger.warning(f"No sentiment data returned for {symbol}")
            return {'long_position_percentage': 50, 'short_position_percentage': 50}
            
    except Exception as e:
        logger.error(f"Error fetching market sentiment: {str(e)}")
        return {'long_position_percentage': 50, 'short_position_percentage': 50}

def get_all_available_symbols() -> List[Dict[str, Any]]:
    """
    Get a list of all available market symbols from Capital.com API
    
    Returns:
    - List of dictionaries with market information
    """
    try:
        # Initialize the Capital.com API client
        client = get_client()
        # The Capital.com API client does not expose a market navigation method in this version.
        # To enable this, implement the correct method in MarketDataManager and update this function.
        logger.error("MarketDataManager has no method for market navigation. Please check the API client implementation.")
        return []
    except Exception as e:
        logger.error(f"Error fetching available symbols: {str(e)}")
        return []

def get_market_categories() -> dict:
    """
    Get market categories and symbols from configuration
    
    Returns:
    - Dictionary with market categories and corresponding symbols
    """
    try:
        # Try to get from configuration
        if CONFIG and 'markets' in CONFIG:
            return CONFIG['markets']
        else:
            # Default categories
            return {
                "crypto": ["BTCUSD", "ETHUSD"],
                "forex": ["EURUSD", "GBPUSD"],
                "indices": ["US500", "US30"],
                "commodities": ["GOLD", "SILVER"]
            }
    except Exception as e:
        logger.error(f"Error getting market categories: {str(e)}")
        return {}

def validate_symbol(symbol: str) -> bool:
    """
    Validate if a symbol is available in the Capital.com API
    
    Parameters:
    - symbol: Market symbol to validate
    
    Returns:
    - True if symbol is valid, False otherwise
    """
    try:
        # Initialize the Capital.com API client
        client = get_client()
        
        # Try to get market details
        market_details = client.market_data_manager.market_details(symbol)
        
        # Check if we got valid market data
        if market_details and 'markets' in market_details and market_details['markets']:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error validating symbol {symbol}: {str(e)}")
        return False

def save_market_data_to_csv(symbol: str, resolution: str = 'HOUR', days: int = 30, 
                          output_dir: 'Optional[str]' = None) -> str | None:
    """
    Fetch market data and save to CSV file
    
    Parameters:
    - symbol: Market symbol/epic (e.g., 'BTCUSD', 'EURUSD')
    - resolution: Timeframe ('MINUTE', 'HOUR', 'DAY', etc.)
    - days: Number of days of data to fetch
    - output_dir: Directory to save the file (default: current directory)
    
    Returns:
    - Path to saved CSV file or None if error occurs
    """
    try:
        # Fetch historical data
        df = fetch_historical_data(symbol, resolution, days)
        
        if df is None or df.empty:
            logger.error("No data to save")
            return None
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.getcwd()
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{resolution}_{days}d_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        logger.info(f"Saved market data to {filepath}")
        
        return filepath
    except Exception as e:
        logger.error(f"Error saving market data: {str(e)}")
        return None

def load_market_data_from_csv(filepath: str) -> pd.DataFrame:
    """
    Load market data from a CSV file
    
    Parameters:
    - filepath: Path to the CSV file
    
    Returns:
    - DataFrame with market data
    """
    try:
        df = pd.read_csv(filepath)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        logger.info(f"Loaded market data from {filepath}: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error loading market data from {filepath}: {str(e)}")
        return pd.DataFrame()

def get_default_parameters() -> Dict[str, Any]:
    """
    Get default optimization parameters from configuration
    
    Returns:
    - Dictionary with default parameters
    """
    try:
        if CONFIG and 'default_optimization' in CONFIG:
            return CONFIG['default_optimization']
        else:
            # Default parameters
            return {
                "days": 30,
                "max_evals": 20,
                "use_sentiment": True,
                "sentiment_weight": 0.2,
                "train_ratio": 0.7,
                "mc_simulations": 100
            }
    except Exception as e:
        logger.error(f"Error getting default parameters: {str(e)}")
        return {}

if __name__ == "__main__":
    # Simple CLI interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Capital.com API Utilities")
    parser.add_argument("--list-symbols", action="store_true", help="List all available symbols")
    parser.add_argument("--get-data", action="store_true", help="Get market data for a symbol")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Market symbol")
    parser.add_argument("--timeframe", type=str, default="HOUR", 
                      choices=list(RESOLUTION_MAP.keys()), help="Timeframe")
    parser.add_argument("--days", type=int, default=30, help="Number of days of data")
    parser.add_argument("--save", action="store_true", help="Save data to CSV")
    parser.add_argument("--sentiment", action="store_true", help="Get market sentiment")
    
    args = parser.parse_args()
    
    if args.list_symbols:
        print("Available market categories:")
        categories = get_market_categories()
        for category, symbols in categories.items():
            print(f"- {category}: {', '.join(symbols)}")
    
    if args.sentiment:
        sentiment = fetch_market_sentiment(args.symbol)
        print(f"Sentiment for {args.symbol}: {sentiment}")
    
    if args.get_data:
        if args.save:
            filepath = save_market_data_to_csv(args.symbol, args.timeframe, args.days)
            if filepath:
                print(f"Data saved to {filepath}")
        else:
            df = fetch_historical_data(args.symbol, args.timeframe, args.days)
            if df is not None:
                print(f"Fetched {len(df)} candles for {args.symbol} ({args.timeframe})")
                print(df.head())
                print("...")
                print(df.tail())
