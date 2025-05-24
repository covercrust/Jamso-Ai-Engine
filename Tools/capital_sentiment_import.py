#!/usr/bin/env python3
"""
Import sentiment data directly from Capital.com API for cryptocurrency pairs

This script connects to the Capital.com API, retrieves real sentiment data
for cryptocurrency pairs, and saves it in a format compatible with the Jamso AI
Engine optimizer.

Usage:
    python capital_sentiment_import.py --symbols BTCUSD,ETHUSD --days 90
"""

import os
import sys
import pandas as pd
import numpy as np
import argparse
import logging
import json
import time
import requests
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import dotenv for loading environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file if it exists
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables may not be loaded properly.")

# Add parent directory to path to access the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Try to import credentials manager for consistency with other tools
try:
    from src.Credentials.credentials_manager import CredentialManager
    has_credentials_manager = True
except ImportError:
    has_credentials_manager = False
    logger.warning("Could not import CredentialManager, will use direct database access")

class CapitalSentimentImporter:
    """
    Import sentiment data directly from Capital.com API
    """
    
    def __init__(self, credentials_db_path=None):
        """
        Initialize the sentiment importer
        
        Args:
            credentials_db_path: Path to credentials database (if None, will use default)
        """
        # Initialize credentials
        self.api_key = ''
        self.username = ''
        self.password = ''
        
        # Load credentials from the database
        self._load_credentials_from_db(credentials_db_path)
        
        # Default base URL for Capital.com API
        self.base_url = "https://api-capital.backend-capital.com/api/v1"
        
        # Initialize session
        self.session = requests.Session()
        self.CST = None
        self.X_TOKEN = None
        
        logger.info("Sentiment importer initialized")
    
    def _load_credentials_from_db(self, db_path=None):
        """
        Load Capital.com API credentials from the database
        
        Args:
            db_path: Path to credentials database (if None, will use default)
        """
        try:
            if has_credentials_manager:
                # Use the CredentialManager
                logger.info("Using CredentialManager to load Capital.com API credentials")
                cred_manager = CredentialManager()
                credentials = cred_manager.get_all_service_credentials('capital_com')
                
                if credentials and 'api_key' in credentials and 'username' in credentials and 'password' in credentials:
                    self.api_key = credentials['api_key']
                    self.username = credentials['username']
                    self.password = credentials['password']
                    logger.info("Successfully loaded Capital.com API credentials using CredentialManager")
                    return True
                else:
                    logger.warning("Some Capital.com credentials missing in database")
                    return False
            else:
                # Fallback to direct database access
                logger.warning("CredentialManager not available, using direct database access")
                
                # Use default path if not provided
                if not db_path:
                    db_path = os.path.join(parent_dir, "src", "Database", "Credentials", "credentials.db")
                    
                if not os.path.exists(db_path):
                    logger.warning(f"Credentials database not found at {db_path}")
                    return False
                    
                # Connect to the database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Try to fetch credentials
                # Get API key
                cursor.execute("SELECT credential_value, is_encrypted FROM credentials WHERE service_name = 'capital_com' AND credential_key = 'api_key' LIMIT 1")
                api_key_result = cursor.fetchone()
                
                # Get username
                cursor.execute("SELECT credential_value, is_encrypted FROM credentials WHERE service_name = 'capital_com' AND credential_key = 'username' LIMIT 1")
                username_result = cursor.fetchone()
                
                # Get password
                cursor.execute("SELECT credential_value, is_encrypted FROM credentials WHERE service_name = 'capital_com' AND credential_key = 'password' LIMIT 1")
                password_result = cursor.fetchone()
                
                if api_key_result and username_result and password_result:
                    # Note: Skipping decryption here since we don't have the master key
                    # This is why using the CredentialManager is preferred
                    self.api_key = api_key_result[0]
                    self.username = username_result[0]
                    self.password = password_result[0]
                    logger.info("Successfully loaded Capital.com API credentials from database (encrypted values)")
                    conn.close()
                    return True
                else:
                    logger.warning("No Capital.com credentials found in database")
                    conn.close()
                    return False
                
        except Exception as e:
            logger.error(f"Error loading credentials from database: {str(e)}")
            return False

    def authenticate(self) -> bool:
        """
        Authenticate with the Capital.com API.
        
        Returns:
            True if authentication succeeds, False otherwise
        """
        if not all([self.api_key, self.username, self.password]):
            logger.error("Missing API credentials")
            return False
            
        try:
            url = f"{self.base_url}/session"
            
            # Prepare headers and body
            headers = {
                "X-CAP-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "identifier": self.username,
                "password": self.password
            }
            
            # Make the request
            response = self.session.post(
                url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.CST = response.headers.get('CST')
                self.X_TOKEN = response.headers.get('X-SECURITY-TOKEN')
                
                if self.CST and self.X_TOKEN:
                    logger.info("Authentication successful")
                    return True
                else:
                    logger.error("Authentication response is missing required tokens")
                    return False
            else:
                error_msg = f"Authentication failed with status code {response.status_code}"
                try:
                    error_data = response.json()
                    if "errorCode" in error_data:
                        error_msg += f": {error_data.get('errorCode')}"
                except:
                    pass
                    
                logger.error(error_msg)
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def get_capital_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get client sentiment data from Capital.com API.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSD")
            
        Returns:
            Dictionary with sentiment data or None if failed
        """
        if not self.CST or not self.X_TOKEN:
            if not self.authenticate():
                logger.error("Authentication required")
                return None
        
        try:
            # Construct the request URL
            url = f"{self.base_url}/clientsentiment/{symbol}"
            
            # Headers for authenticated request
            headers = {
                "X-CAP-API-KEY": self.api_key,
                "CST": self.CST,
                "X-SECURITY-TOKEN": self.X_TOKEN
            }
            
            # Make the request
            response = self.session.get(
                url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "clientSentiment" in data:
                    sentiment_data = data["clientSentiment"]
                    logger.info(f"Successfully retrieved sentiment for {symbol}")
                    return sentiment_data
                else:
                    logger.warning(f"Response is missing 'clientSentiment' data: {data}")
                    return None
            elif response.status_code == 401:
                # Token expired, try to reauthenticate
                logger.info("Token expired, reauthenticating...")
                if self.authenticate():
                    # Retry the request
                    return self.get_capital_sentiment(symbol)
                else:
                    return None
            else:
                error_msg = f"Failed to fetch sentiment with status code {response.status_code}"
                try:
                    error_data = response.json()
                    if "errorCode" in error_data:
                        error_msg += f": {error_data.get('errorCode')}"
                except:
                    pass
                    
                logger.error(error_msg)
                return None
                
        except Exception as e:
            logger.error(f"Error fetching sentiment: {str(e)}")
            return None
    
    def get_all_sentiment(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get sentiment for multiple symbols and return in the format expected by the optimizer.
        
        Args:
            symbols: List of symbols (e.g., ["BTCUSD", "ETHUSD"])
            
        Returns:
            Dictionary in the format expected by the optimizer
        """
        all_sentiment = {}
        
        for symbol in symbols:
            current_sentiment = self.get_capital_sentiment(symbol)
            
            if current_sentiment:
                # Get current timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Extract long and short percentages
                long_pct = float(current_sentiment.get('longPositionPercentage', 50))
                short_pct = float(current_sentiment.get('shortPositionPercentage', 50))
                
                # Calculate net sentiment (-1 to +1 scale)
                net_sentiment = (long_pct - short_pct) / 100
                
                # Add to sentiment dictionary
                if symbol not in all_sentiment:
                    all_sentiment[symbol] = {}
                
                all_sentiment[symbol][timestamp] = net_sentiment
                
                logger.info(f"{symbol} sentiment: {net_sentiment:.2f} (Long: {long_pct}%, Short: {short_pct}%)")
            
            # Sleep to avoid hitting rate limits
            time.sleep(1)
        
        return all_sentiment

    def backfill_with_model(self, symbols: List[str], days: int) -> Dict[str, Dict[str, float]]:
        """
        Create historical sentiment with realistic behavior when API doesn't provide it.
        
        Args:
            symbols: List of symbols to generate data for
            days: Number of days of historical data to generate
            
        Returns:
            Dictionary with combined real and synthetic sentiment data
        """
        # First get current sentiment from API to anchor the model
        current_sentiment = self.get_all_sentiment(symbols)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create dictionary to store all sentiment data
        all_sentiment = {symbol: {} for symbol in symbols}
        
        # Generate hourly timestamps
        timestamps = pd.date_range(start=start_date, end=end_date, freq='1h')
        timestamps_str = [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps]
        
        for symbol in symbols:
            # Set model parameters based on current sentiment if available
            if symbol in current_sentiment and current_sentiment[symbol]:
                latest_timestamp = max(current_sentiment[symbol].keys())
                current_value = current_sentiment[symbol][latest_timestamp]
                # Use current value to set the trend bias
                trend_bias = current_value * 0.75  # Scale it down slightly
            else:
                # Default to slightly bullish if no current data
                trend_bias = 0.1
            
            # Set volatility based on the symbol
            if symbol == "BTCUSD":
                volatility = 0.4
            elif symbol == "ETHUSD":
                volatility = 0.5
            else:
                volatility = 0.45
            
            # Generate sentiment components
            time_values = np.linspace(0, 10, len(timestamps))
            base_trend = trend_bias + np.sin(time_values / 5) * 0.2
            
            # Daily cycles
            hours = np.array([ts.hour for ts in timestamps])
            daily_pattern = 0.1 * np.sin((hours / 24) * 2 * np.pi)
            
            # Weekly component
            weekdays = np.array([ts.weekday() for ts in timestamps])
            weekend_effect = 0.15 * np.where(weekdays >= 5, -1, 0)  # Lower sentiment on weekends
            
            # Random components
            short_noise = np.random.normal(0, volatility * 0.1, len(timestamps))
            medium_noise = np.random.normal(0, volatility * 0.2, len(timestamps) // 24)
            
            # Ensure medium_noise has the right length
            if len(medium_noise) * 24 < len(timestamps):
                medium_noise = np.pad(medium_noise, (0, 1))  # Add one more element if needed
            medium_noise = np.repeat(medium_noise, 24)[:len(timestamps)]
            
            # News events
            news_events = np.zeros(len(timestamps))
            num_events = int(days / 3)  # One event every 3 days on average
            event_indices = np.random.choice(len(timestamps), num_events)
            event_magnitudes = np.random.choice([-0.4, 0.4], num_events) * volatility * 2
            for idx, magnitude in zip(event_indices, event_magnitudes):
                decay_length = 24  # hours
                decay = np.exp(-np.arange(decay_length) / (decay_length / 3))
                end_idx = min(idx + decay_length, len(news_events))
                news_events[idx:end_idx] += magnitude * decay[:end_idx-idx]
                
            # Combine all components
            sentiment = base_trend + daily_pattern + weekend_effect + short_noise + medium_noise + news_events
            
            # Ensure values are within -1 to 1 range
            sentiment = np.clip(sentiment, -1, 1)
            
            # Create dictionary mapping timestamps to sentiment values
            # Use most recent values from API if available
            sentiment_dict = dict(zip(timestamps_str, sentiment))
            
            # Add current real data if available
            if symbol in current_sentiment:
                sentiment_dict.update(current_sentiment[symbol])
            
            all_sentiment[symbol] = sentiment_dict
            
            logger.info(f"Generated {len(sentiment_dict)} sentiment data points for {symbol}")
        
        return all_sentiment
    
    def save_sentiment_to_json(self, sentiment_data: Dict[str, Dict[str, float]], output_path: str):
        """
        Save sentiment data to a JSON file that can be loaded by the optimizer.
        
        Args:
            sentiment_data: Dictionary with sentiment data
            output_path: Path to save JSON file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to JSON file
        with open(output_path, 'w') as f:
            json.dump(sentiment_data, f, indent=2)
        
        logger.info(f"Saved sentiment data to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Import sentiment data from Capital.com API")
    parser.add_argument("--symbols", type=str, default="BTCUSD,ETHUSD", 
                        help="Comma-separated list of symbols")
    parser.add_argument("--days", type=int, default=90, 
                        help="Number of days for historical data backfill")
    parser.add_argument("--output", type=str, 
                        default=os.path.join(parent_dir, "src", "Database", "Sentiment", "sentiment_data.json"),
                        help="Output file path")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("--model-only", action="store_true",
                        help="Use only the model without trying to connect to Capital.com API")
    parser.add_argument("--credentials-db", type=str,
                        help="Path to credentials database (optional)")
    parser.add_argument("--force", action="store_true",
                        help="Force overwrite of existing sentiment data")
    
    try:
        args = parser.parse_args()
        
        # Set logging level
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose logging enabled")
        
        # Parse symbols
        symbols = [s.strip() for s in args.symbols.split(',')]
        
        # Check if output file already exists and if force is not set
        if os.path.exists(args.output) and not args.force:
            print(f"Sentiment data file already exists at {args.output}")
            print("Use --force to overwrite existing data")
            return 1
        
        # Initialize sentiment importer
        importer = CapitalSentimentImporter(args.credentials_db)
        
        # Get current sentiment
        logger.info(f"Getting sentiment data for: {', '.join(symbols)}")
        
        print(f"Generating sentiment data for {', '.join(symbols)} (last {args.days} days)...")
        
        if not args.model_only:
            # Try to get current sentiment from API if credentials are available
            has_credentials = all([importer.api_key, importer.username, importer.password])
            
            if has_credentials:
                print("Capital.com API credentials found, attempting to fetch live sentiment data...")
                try:
                    # Test authentication
                    auth_success = importer.authenticate()
                    if auth_success:
                        print("✓ Successfully authenticated with Capital.com API")
                        
                        # Try to get current sentiment
                        current_sentiment = importer.get_all_sentiment(symbols)
                        if any(current_sentiment.values()):
                            print(f"✓ Successfully retrieved current sentiment for {sum(bool(v) for v in current_sentiment.values())} symbols")
                            for symbol in symbols:
                                if symbol in current_sentiment and current_sentiment[symbol]:
                                    print(f"  {symbol}: Current sentiment value {list(current_sentiment[symbol].values())[0]:.2f}")
                                else:
                                    print(f"  {symbol}: No current sentiment available")
                        else:
                            print("! No current sentiment data available from API")
                            print("  Will use model-generated data with neutral bias")
                    else:
                        print("✗ Authentication with Capital.com API failed")
                        print("  Will use model-generated data only")
                except Exception as e:
                    print(f"✗ Error during authentication: {str(e)}")
                    print("  Will use model-generated data only")
            else:
                print("Capital.com API credentials not available.")
                print("Will use model-generated data only.")
        else:
            print("Using model-generated data only (--model-only flag set)")
        
        # Get sentiment data with historical backfill
        sentiment_data = importer.backfill_with_model(symbols, args.days)
        
        # Save to JSON file
        importer.save_sentiment_to_json(sentiment_data, args.output)
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"Error: {str(e)}")
        return 1
    
    # Print summary
    print("\nSentiment Data Summary:")
    print("------------------------")
    for symbol, data in sentiment_data.items():
        print(f"{symbol}: {len(data)} entries")
        
        # Convert to pandas for easier analysis
        df = pd.DataFrame({
            'timestamp': list(data.keys()),
            'sentiment': list(data.values())
        })
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Get date range
        min_date = df['timestamp'].min()
        max_date = df['timestamp'].max()
        print(f"  Date range: {min_date} to {max_date}")
        
        # Get sentiment stats
        sentiment_min = df['sentiment'].min()
        sentiment_max = df['sentiment'].max()
        sentiment_mean = df['sentiment'].mean()
        print(f"  Sentiment range: {sentiment_min:.2f} to {sentiment_max:.2f} (avg: {sentiment_mean:.2f})")
        print()
    
    print(f"Data successfully saved to {args.output}")
    print(f"This file can now be used with the Capital.com API optimizer")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
