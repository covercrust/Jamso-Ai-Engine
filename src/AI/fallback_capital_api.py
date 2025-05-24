#!/usr/bin/env python3
"""
Fallback Capital.com API Client

This is a simplified standalone implementation of the Capital.com API client
that can be used when the main API integration fails due to dependency issues.
It provides basic functionality for fetching historical market data.
"""

import os
import sys
import json
import time
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple, Union, TYPE_CHECKING
from datetime import datetime, timedelta

# For type annotations only
if TYPE_CHECKING:
    import pandas as pd

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
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables may not be loaded properly.")

class FallbackApiClient:
    """
    A simplified API client for Capital.com that doesn't rely on the complex dependency chain.
    """
    
    def __init__(self):
        """Initialize the fallback API client with credentials from database or environment variables."""
        # First try to access the secure credential database
        try:
            # Get base directory
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            sys.path.append(base_dir)
            
            # Import the credential manager
            from src.Credentials.credentials_manager import CredentialManager
            credential_manager = CredentialManager()
            
            # Try to get credentials from the secure database first
            db_api_key = credential_manager.get_credential('capital_com', 'CAPITAL_API_KEY')
            db_api_login = credential_manager.get_credential('capital_com', 'CAPITAL_API_LOGIN')
            db_api_password = credential_manager.get_credential('capital_com', 'CAPITAL_API_PASSWORD')
            
            # Use database credentials if available
            if db_api_key and db_api_login and db_api_password:
                self.api_key = db_api_key
                self.username = db_api_login
                self.password = db_api_password
                logger.info("Using API credentials from secure credential database")
                # No need to check environment variables
                self._have_credentials = True
                return
            else:
                logger.warning("Some credentials missing from secure database, checking environment variables")
        except Exception as e:
            logger.warning(f"Could not access credential database: {str(e)}")
            logger.warning("Falling back to environment variables for credentials")
        
        # Fall back to environment variables if database access failed
        self.api_key = os.environ.get('CAPITAL_API_KEY', '')
        self.username = os.environ.get('CAPITAL_API_LOGIN', '')
        self.password = os.environ.get('CAPITAL_API_PASSWORD', '')
        
        if not self.api_key or not self.username or not self.password:
            logger.warning("Missing Capital.com API credentials in environment variables")
            logger.warning("Please set CAPITAL_API_KEY, CAPITAL_API_LOGIN, and CAPITAL_API_PASSWORD")
            self._have_credentials = False
        else:
            self._have_credentials = True
        
        self.base_url = "https://api-capital.backend-capital.com/api/v1"
        self.session = requests.Session()
        
        # Request timeout and retry settings
        self.request_timeout = 30
        self.max_retries = 3
        self.retry_delay = 5
        
        # Auth tokens
        self.CST = ""
        self.X_TOKEN = ""
        self.is_authenticated = False
    
    def authenticate(self) -> bool:
        """
        Authenticate with Capital.com API.
        
        Returns:
            bool: True if authentication succeeded, False otherwise.
        """
        if self.is_authenticated:
            return True
            
        if not hasattr(self, '_have_credentials') or not self._have_credentials:
            logger.error("Missing API credentials")
            logger.error("Authentication required for API calls")
            return False
            
        try:
            # Authentication endpoint
            url = f"{self.base_url}/session"
            
            # Headers and payload
            headers = {
                "X-CAP-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "identifier": self.username,
                "password": self.password
            }
            
            # Make the authentication request
            response = self.session.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                # Save authentication tokens
                self.CST = response.headers.get('CST', '')
                self.X_TOKEN = response.headers.get('X-SECURITY-TOKEN', '')
                
                if self.CST and self.X_TOKEN:
                    self.is_authenticated = True
                    logger.info("Successfully authenticated with Capital.com API")
                    return True
                else:
                    logger.error("Authentication succeeded but tokens are missing")
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
    
    def get_historical_prices(self, 
                             symbol: str,
                             resolution: str = 'HOUR', 
                             days: int = 30,
                             max_candles: int = 1000) -> Optional[List[Dict]]:
        """
        Get historical price data for a market symbol.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSD", "EURUSD")
            resolution: Candle timeframe (e.g., "MINUTE", "HOUR", "DAY")
            days: Number of days of historical data to fetch
            max_candles: Maximum number of candles to fetch per request
            
        Returns:
            List of candle data dictionaries or None if failed
        """
        if not self.authenticate():
            logger.error("Authentication required for API calls")
            return None
            
        try:
            # Calculate from and to dates
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Convert dates to milliseconds since epoch
            to_ms = int(to_date.timestamp() * 1000)
            from_ms = int(from_date.timestamp() * 1000)
            
            # Construct the request URL
            url = f"{self.base_url}/prices/{symbol}"
            
            # Headers for authenticated request
            headers = {
                "X-CAP-API-KEY": self.api_key,
                "CST": self.CST,
                "X-SECURITY-TOKEN": self.X_TOKEN,
                "Content-Type": "application/json"
            }
            
            # Parameters
            params = {
                "resolution": resolution,
                "from": from_ms,
                "to": to_ms,
                "max": max_candles
            }
            
            # Make the request
            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if "prices" in data:
                    logger.info(f"Successfully retrieved {len(data['prices'])} candles for {symbol}")
                    return data["prices"]
                else:
                    logger.warning(f"Response is missing 'prices' data: {data}")
                    return []
            else:
                error_msg = f"Failed to fetch prices with status code {response.status_code}"
                try:
                    error_data = response.json()
                    if "errorCode" in error_data:
                        error_msg += f": {error_data.get('errorCode')}"
                except:
                    pass
                    
                logger.error(error_msg)
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical prices: {str(e)}")
            return None
    
    def convert_to_dataframe(self, candles: List[Dict]) -> Optional[Any]:
        """
        Convert candle data to pandas DataFrame.
        
        Args:
            candles: List of candle dictionaries
            
        Returns:
            pandas DataFrame or None if conversion fails
        """
        try:
            import pandas as pd
            
            # Create dataframe from candle data
            df = pd.DataFrame(candles)
            
            # Rename columns to match expected format
            column_mapping = {
                'openPrice': 'open',
                'closePrice': 'close',
                'highPrice': 'high',
                'lowPrice': 'low',
                'lastTradedVolume': 'volume',
                'snapshotTimeUTC': 'datetime'
            }
            
            # Rename columns if they exist
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})
            
            # Convert datetime string to datetime object
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.set_index('datetime')
            
            # Make sure we have the necessary OHLC columns
            required_columns = ['open', 'high', 'low', 'close']
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"Missing required column {col} in data")
            
            # Convert numeric columns to float
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except ImportError:
            logger.error("pandas not installed. Cannot convert to DataFrame.")
            return None
        except Exception as e:
            logger.error(f"Error converting data to DataFrame: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch historical price data from Capital.com API")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Market symbol")
    parser.add_argument("--resolution", type=str, default="HOUR", help="Candle timeframe")
    parser.add_argument("--days", type=int, default=30, help="Number of days of historical data")
    parser.add_argument("--output", type=str, default="", help="Output CSV file")
    
    args = parser.parse_args()
    
    # Create the API client
    client = FallbackApiClient()
    
    # Fetch historical prices
    candles = client.get_historical_prices(
        symbol=args.symbol,
        resolution=args.resolution,
        days=args.days
    )
    
    if candles:
        # Convert to DataFrame
        df = client.convert_to_dataframe(candles)
        
        if df is not None:
            print(f"Retrieved {len(df)} candles for {args.symbol}")
            print(df.head())
            
            # Save to CSV if output file specified
            if args.output:
                df.to_csv(args.output)
                print(f"Data saved to {args.output}")
        else:
            print("Failed to convert data to DataFrame")
    else:
        print("Failed to fetch historical prices")
