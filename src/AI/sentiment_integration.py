#!/usr/bin/env python3
"""
Historical Sentiment Data Integration for Capital.com API

This module fetches and integrates historical sentiment data for use with 
the Capital.com API parameter optimization process. It provides sentiment
scores that can be incorporated into trading strategies.

Usage:
    python sentiment_integration.py --symbol BTCUSD --days 30 --save sentiment_data.csv
"""

import os
import sys
import argparse
import logging
import json
import time
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import sqlite3
from pathlib import Path

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
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Path for sentiment database
SENTIMENT_DB_PATH = os.path.join(parent_dir, "src", "Database", "Sentiment", "sentiment_data.db")

class SentimentIntegration:
    """
    Historical sentiment data integration for trading strategies.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the sentiment integration module.
        
        Args:
            db_path: Path to the sentiment database file
        """
        self.api_key = os.environ.get('CAPITAL_API_KEY', '')
        self.username = os.environ.get('CAPITAL_API_LOGIN', '')
        self.password = os.environ.get('CAPITAL_API_PASSWORD', '')
        
        if not self.api_key or not self.username or not self.password:
            logger.warning("Missing Capital.com API credentials in environment variables")
            logger.warning("Please set CAPITAL_API_KEY, CAPITAL_API_LOGIN, and CAPITAL_API_PASSWORD")
        
        # Set up database path
        if db_path:
            self.db_path = db_path
        else:
            os.makedirs(os.path.dirname(SENTIMENT_DB_PATH), exist_ok=True)
            self.db_path = SENTIMENT_DB_PATH
            
        # Initialize database
        self._initialize_database()
        
        # Default base URL for Capital.com API
        self.base_url = "https://api-capital.backend-capital.com/api/v1"
        
        # Initialize session
        self.session = requests.Session()
        self.CST = None
        self.X_TOKEN = None
        
        logger.info("Sentiment integration initialized")
    
    def _initialize_database(self):
        """Initialize the sentiment database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table for sentiment data
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                long_sentiment REAL,
                short_sentiment REAL,
                net_sentiment REAL,
                sentiment_value REAL,
                source TEXT,
                UNIQUE(symbol, timestamp, source)
            )
            ''')
            
            # Create table for sentiment sources
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                weight REAL DEFAULT 1.0
            )
            ''')
            
            # Add default sources if they don't exist
            cursor.execute('''
            INSERT OR IGNORE INTO sentiment_sources (name, description, weight) 
            VALUES 
                ('capital_com', 'Capital.com Client Sentiment', 1.0),
                ('twitter', 'Twitter/X Social Sentiment', 0.7),
                ('news', 'Financial News Sentiment Analysis', 0.8)
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Sentiment database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing sentiment database: {str(e)}")
    
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
    
    def fetch_historical_social_sentiment(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Fetch historical social media sentiment for a symbol.
        This is a placeholder that would normally integrate with a social media API.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSD")
            days: Number of days of historical data
            
        Returns:
            DataFrame with sentiment data
        """
        # This is a placeholder for actual social media sentiment API integration
        # In a real implementation, this would connect to Twitter/X API or a sentiment provider
        
        logger.info(f"Generating simulated social sentiment data for {symbol} (last {days} days)")
        
        # Generate simulated data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create date range with hourly intervals
        date_range = pd.date_range(start=start_date, end=end_date, freq='1H')
        
        # Generate base sentiment with some trending component
        base_sentiment = np.random.normal(0, 0.1, len(date_range))
        trend = np.cumsum(np.random.normal(0, 0.01, len(date_range)))
        
        # Create dataframe
        df = pd.DataFrame({
            'timestamp': date_range,
            'sentiment_value': np.clip(base_sentiment + trend, -1, 1)
        })
        
        # Add symbol and source
        df['symbol'] = symbol
        df['source'] = 'twitter'
        
        return df
    
    def fetch_historical_news_sentiment(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Fetch historical news sentiment for a symbol.
        This is a placeholder that would normally integrate with a news sentiment API.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSD")
            days: Number of days of historical data
            
        Returns:
            DataFrame with sentiment data
        """
        # This is a placeholder for actual news sentiment API integration
        # In a real implementation, this would connect to a service like GDELT or RavenPack
        
        logger.info(f"Generating simulated news sentiment data for {symbol} (last {days} days)")
        
        # Generate simulated data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create date range with 3-hour intervals (news sentiment updates less frequently)
        date_range = pd.date_range(start=start_date, end=end_date, freq='3H')
        
        # Generate news sentiment (more spikes than social)
        base = np.random.normal(0, 0.15, len(date_range))
        spikes = np.random.choice([-0.5, 0, 0.5], len(date_range), p=[0.1, 0.8, 0.1])
        
        # Create dataframe
        df = pd.DataFrame({
            'timestamp': date_range,
            'sentiment_value': np.clip(base + spikes, -1, 1)
        })
        
        # Add symbol and source
        df['symbol'] = symbol
        df['source'] = 'news'
        
        return df
        
    def save_sentiment_data(self, df: pd.DataFrame):
        """
        Save sentiment data to the database.
        
        Args:
            df: DataFrame with sentiment data
        """
        if df.empty:
            logger.warning("No sentiment data to save")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Make sure timestamps are strings in ISO format
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert data into sentiment_data table
            df.to_sql('sentiment_data', conn, if_exists='append', index=False)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(df)} sentiment records to database")
            
        except Exception as e:
            logger.error(f"Error saving sentiment data: {str(e)}")
    
    def fetch_all_sentiment(self, symbol: str, days: int = 30, save: bool = True) -> pd.DataFrame:
        """
        Fetch sentiment data from all available sources and save to the database.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSD")
            days: Number of days of historical data
            save: Whether to save the data to the database
            
        Returns:
            DataFrame with combined sentiment data
        """
        sentiment_dfs = []
        
        # 1. Fetch Capital.com client sentiment
        try:
            capital_sentiment = self.get_capital_sentiment(symbol)
            if capital_sentiment:
                # Current sentiment (only available as current snapshot)
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                long_pct = float(capital_sentiment.get('longPositionPercentage', 50))
                short_pct = float(capital_sentiment.get('shortPositionPercentage', 50))
                
                # Calculate net sentiment (-1 to +1 scale)
                net_sentiment = (long_pct - short_pct) / 100
                
                capital_df = pd.DataFrame({
                    'timestamp': [now],
                    'symbol': [symbol],
                    'long_sentiment': [long_pct],
                    'short_sentiment': [short_pct],
                    'net_sentiment': [net_sentiment],
                    'sentiment_value': [net_sentiment],
                    'source': ['capital_com']
                })
                
                sentiment_dfs.append(capital_df)
        except Exception as e:
            logger.error(f"Error fetching Capital.com sentiment: {str(e)}")
            
        # 2. Fetch social sentiment
        try:
            social_df = self.fetch_historical_social_sentiment(symbol, days)
            sentiment_dfs.append(social_df)
        except Exception as e:
            logger.error(f"Error fetching social sentiment: {str(e)}")
            
        # 3. Fetch news sentiment
        try:
            news_df = self.fetch_historical_news_sentiment(symbol, days)
            sentiment_dfs.append(news_df)
        except Exception as e:
            logger.error(f"Error fetching news sentiment: {str(e)}")
            
        # Combine all sentiment data
        if sentiment_dfs:
            combined_df = pd.concat(sentiment_dfs, ignore_index=True)
            
            # Save to database if requested
            if save:
                self.save_sentiment_data(combined_df)
                
            return combined_df
        else:
            logger.warning("No sentiment data available from any source")
            return pd.DataFrame()
    
    def get_historical_sentiment(self, symbol: str, start_date: Optional[str] = None, 
                                end_date: Optional[str] = None, source: Optional[str] = None) -> pd.DataFrame:
        """
        Get historical sentiment data from the database.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSD")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            source: Sentiment source (None for all sources)
            
        Returns:
            DataFrame with sentiment data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM sentiment_data WHERE symbol = ?"
            params = [symbol]
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date} 00:00:00")
                
            if end_date:
                query += " AND timestamp <= ?"
                params.append(f"{end_date} 23:59:59")
                
            if source:
                query += " AND source = ?"
                params.append(source)
                
            query += " ORDER BY timestamp"
            
            # Execute query
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if df.empty:
                logger.warning(f"No sentiment data found for {symbol}")
                return df
                
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"Retrieved {len(df)} sentiment records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving sentiment data: {str(e)}")
            return pd.DataFrame()
    
    def get_combined_sentiment_series(self, symbol: str, timeframe: str, 
                                     start_date: Optional[str] = None,
                                     end_date: Optional[str] = None) -> pd.Series:
        """
        Get historical sentiment data as a resampled time series.
        
        Args:
            symbol: Market symbol (e.g., "BTCUSD")
            timeframe: Timeframe for resampling ('MINUTE', 'HOUR', 'DAY', etc.)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Series with sentiment values indexed by timestamp
        """
        # Get raw sentiment data
        df = self.get_historical_sentiment(symbol, start_date, end_date)
        
        if df.empty:
            logger.warning(f"No sentiment data found for {symbol}, returning neutral sentiment")
            # Return neutral sentiment if no data is available
            if start_date and end_date:
                # Create date range with neutral sentiment
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                return pd.Series(0, index=date_range, name='sentiment')
            else:
                # Just return empty series if no date range specified
                return pd.Series(name='sentiment')
        
        # Convert timeframe to pandas frequency string
        freq_map = {
            'MINUTE': 'T',
            'MINUTE_5': '5T',
            'MINUTE_15': '15T',
            'MINUTE_30': '30T',
            'HOUR': 'H',
            'HOUR_4': '4H',
            'DAY': 'D',
            'WEEK': 'W',
            'MONTH': 'M'
        }
        freq = freq_map.get(timeframe, 'D')  # Default to daily if not recognized
        
        # Get source weights from database
        try:
            conn = sqlite3.connect(self.db_path)
            weights_df = pd.read_sql_query("SELECT name, weight FROM sentiment_sources", conn)
            conn.close()
            
            # Convert to dictionary for easier lookup
            weights = dict(zip(weights_df['name'], weights_df['weight']))
        except Exception as e:
            logger.error(f"Error retrieving source weights: {str(e)}")
            # Default weights if database access fails
            weights = {'capital_com': 1.0, 'twitter': 0.7, 'news': 0.8}
        
        # Apply weights to sentiment values
        df['weighted_sentiment'] = df.apply(
            lambda row: row['sentiment_value'] * weights.get(row['source'], 1.0), 
            axis=1
        )
        
        # Group by timestamp and calculate weighted average
        df = df.set_index('timestamp')
        
        # Resample to the desired timeframe
        resampled = df.groupby('source').resample(freq)['weighted_sentiment'].mean()
        
        # Unstack to get separate columns for each source
        unstacked = resampled.unstack(level=0)
        
        # Combine the sources with weighted average
        weight_sum = sum(w for s, w in weights.items() if s in unstacked.columns)
        if weight_sum > 0:
            # If we have any applicable weights, use them
            combined = sum(unstacked[s] * weights.get(s, 1.0) for s in unstacked.columns 
                          if s in weights) / weight_sum
        else:
            # Otherwise just use simple average
            combined = unstacked.mean(axis=1)
        
        # Fill missing values
        combined = combined.fillna(method='ffill').fillna(0)
        
        # Name the series for clarity
        combined.name = 'sentiment'
        
        logger.info(f"Created combined sentiment series with {len(combined)} points for {symbol}")
        return combined

def main():
    """Main function to run sentiment integration."""
    parser = argparse.ArgumentParser(description="Historical Sentiment Integration")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Market symbol")
    parser.add_argument("--days", type=int, default=30, help="Number of days of historical data")
    parser.add_argument("--save", type=str, help="Save to CSV file")
    parser.add_argument("--timeframe", type=str, default="HOUR", help="Timeframe for resampling")
    parser.add_argument("--fetch", action="store_true", help="Fetch new data from sources")
    parser.add_argument("--plot", action="store_true", help="Plot sentiment data")
    args = parser.parse_args()
    
    try:
        # Initialize sentiment integration
        sentiment = SentimentIntegration()
        
        # Fetch new data if requested
        if args.fetch:
            sentiment.fetch_all_sentiment(args.symbol, args.days)
        
        # Get start and end dates
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
        
        # Get sentiment data
        sentiment_series = sentiment.get_combined_sentiment_series(
            args.symbol, 
            args.timeframe, 
            start_date, 
            end_date
        )
        
        if sentiment_series.empty:
            logger.error("No sentiment data available")
            return 1
            
        logger.info(f"Got {len(sentiment_series)} sentiment data points")
        logger.info(f"Date range: {sentiment_series.index.min()} to {sentiment_series.index.max()}")
        logger.info(f"Sentiment range: {sentiment_series.min():.2f} to {sentiment_series.max():.2f}")
        logger.info(f"Average sentiment: {sentiment_series.mean():.2f}")
        
        # Plot if requested
        if args.plot:
            try:
                import matplotlib.pyplot as plt
                
                plt.figure(figsize=(12, 6))
                plt.plot(sentiment_series.index, sentiment_series.values)
                plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
                plt.title(f"{args.symbol} Sentiment ({args.timeframe} timeframe)")
                plt.xlabel("Date")
                plt.ylabel("Sentiment (-1 to +1)")
                plt.grid(True, alpha=0.3)
                
                # Save plot
                plot_file = f"{args.symbol}_sentiment_plot.png"
                plt.savefig(plot_file)
                logger.info(f"Plot saved to {plot_file}")
                
                # Show plot if in interactive mode
                plt.show()
                
            except Exception as e:
                logger.error(f"Error creating plot: {str(e)}")
        
        # Save to CSV if requested
        if args.save:
            sentiment_series.to_csv(args.save)
            logger.info(f"Sentiment data saved to {args.save}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
