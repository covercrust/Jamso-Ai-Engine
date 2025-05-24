"""
Market Data Collector Module

This module provides functionality to collect and store market data for AI analysis:
- Scheduled historical data collection for volatility analysis
- Real-time market data updates
- Storage of market metrics in the database

Usage:
    1. Instantiate the MarketDataCollector
    2. Call collect_historical_data() to gather historical data
    3. Schedule regular updates using start_scheduled_collection()
"""

import logging
import sqlite3
import pandas as pd
import numpy as np
import time
import threading
import schedule
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import json

# Import trading API clients
from src.Exchanges.capital_com_api.client import Client
from src.Credentials.credentials import load_credentials, get_api_credentials, get_server_url
from src.Webhook.utils import get_client

# Configure logger
logger = logging.getLogger(__name__)

class MarketDataCollector:
    """
    Collects and stores market data for AI analysis.
    
    Attributes:
        symbols (List[str]): List of market symbols to collect data for
        db_path (str): Path to the SQLite database
        lookback_days (int): Days of historical data to collect
        client (Client): Authenticated trading API client
    """
    
    def __init__(self, 
                symbols: Optional[List[str]] = None,
                db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db',
                lookback_days: int = 120):
        """
        Initialize the market data collector.
        
        Args:
            symbols: List of market symbols to collect data for (e.g. ['EURUSD', 'BTCUSD'])
            db_path: Path to the SQLite database
            lookback_days: Days of historical data to collect
        """
        self.symbols = symbols or []
        self.db_path = db_path
        self.lookback_days = lookback_days
        self.client = None
        self.collection_thread = None
        self.is_running = False
        
        # Ensure necessary tables exist
        self._create_tables()
        
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create market_volatility table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_volatility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                close REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                volume REAL,
                atr REAL,
                volatility REAL,
                UNIQUE(symbol, timestamp)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Market data tables verified")
        except Exception as e:
            logger.error(f"Error creating market data tables: {e}")
    
    def _initialize_client(self) -> bool:
        """Initialize trading API client."""
        try:
            if not self.client:
                self.client = get_client()
                logger.info("Trading API client initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing trading API client: {e}")
            return False
    
    def collect_historical_data(self, symbol: str, days: Optional[int] = None) -> bool:
        """
        Collect historical data for a symbol.
        
        Args:
            symbol: Market symbol to collect data for
            days: Number of days of historical data to collect (default: self.lookback_days)
            
        Returns:
            True if data collection was successful, False otherwise
        """
        days = days or self.lookback_days
        
        try:
            # Initialize client if needed
            if not self._initialize_client():
                return False
                
            # Get historical candles (OHLCV) from trading API
            logger.info(f"Collecting {days} days of historical data for {symbol}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get candles from API (implementation depends on specific broker API)
            # This is a generic approach - adjust to your specific API
            if not hasattr(self.client, "get_candles"):
                logger.error("Client does not have a get_candles method. Please implement it in your API client.")
                return False
            candles = self.client.get_candles(  # type: ignore[attr-defined]
                symbol=symbol,
                resolution='D1',  # Daily candles
                from_time=int(start_date.timestamp()),
                to_time=int(end_date.timestamp())
            )
            
            if not candles or len(candles) < 2:
                logger.warning(f"Insufficient historical data received for {symbol}")
                return False
                
            # Convert to DataFrame and calculate metrics
            df = pd.DataFrame(candles)
            
            # Calculate volatility metrics
            df['returns'] = df['close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)  # Annualized
            
            # Calculate ATR (Average True Range)
            df['tr1'] = abs(df['high'] - df['low'])
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            df['atr'] = df['tr'].rolling(window=14).mean()
            
            # Store in database
            records = []
            for _, row in df.iterrows():
                if pd.isna(row['atr']) or pd.isna(row['volatility']):
                    continue
                    
                record = (
                    symbol,
                    row['timestamp'],
                    row['close'],
                    row['high'],
                    row['low'],
                    row.get('volume', 0),
                    row['atr'],
                    row['volatility']
                )
                records.append(record)
            
            # Bulk insert into database
            if records:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.executemany('''
                INSERT INTO market_volatility 
                (symbol, timestamp, close, high, low, volume, atr, volatility)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timestamp) 
                DO UPDATE SET 
                    close = excluded.close,
                    high = excluded.high,
                    low = excluded.low,
                    volume = excluded.volume,
                    atr = excluded.atr,
                    volatility = excluded.volatility
                ''', records)
                
                conn.commit()
                conn.close()
                
                logger.info(f"Stored {len(records)} volatility records for {symbol}")
                return True
                
            logger.warning(f"No valid records to store for {symbol}")
            return False
            
        except Exception as e:
            logger.error(f"Error collecting historical data for {symbol}: {e}")
            return False
    
    def collect_data_for_all_symbols(self):
        """Collect data for all configured symbols."""
        success_count = 0
        for symbol in self.symbols:
            success = self.collect_historical_data(symbol)
            if success:
                success_count += 1
                
        logger.info(f"Completed data collection for {success_count}/{len(self.symbols)} symbols")
        
    def start_scheduled_collection(self, schedule_time: str = "00:00"):
        """
        Start scheduled data collection thread.
        
        Args:
            schedule_time: Time of day to run collection in HH:MM format (default: "00:00")
        """
        if self.is_running:
            logger.warning("Scheduled data collection is already running")
            return
            
        def run_threaded():
            self.is_running = True
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check schedule every minute
                
        # Schedule daily collection
        schedule.every().day.at(schedule_time).do(self.collect_data_for_all_symbols)
        
        # Start collection thread
        self.collection_thread = threading.Thread(target=run_threaded, daemon=True)
        self.collection_thread.start()
        
        logger.info(f"Scheduled daily data collection at {schedule_time}")
        
    def stop_scheduled_collection(self):
        """Stop scheduled data collection."""
        if not self.is_running:
            logger.warning("Scheduled data collection is not running")
            return
            
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
            self.collection_thread = None
            
        schedule.clear()
        logger.info("Stopped scheduled data collection")
        
    def get_available_symbols(self) -> List[str]:
        """
        Get list of symbols with available data.
        
        Returns:
            List of symbols with data in the database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT symbol FROM market_volatility")
            symbols = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return symbols
        except Exception as e:
            logger.error(f"Error getting available symbols: {e}")
            return []
            
    def get_data_summary(self) -> Dict[str, Dict]:
        """
        Get summary of collected data.
        
        Returns:
            Dictionary with data summary by symbol
        """
        summary = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT 
                symbol, 
                COUNT(*) as record_count,
                MIN(timestamp) as oldest_record,
                MAX(timestamp) as newest_record,
                AVG(volatility) as avg_volatility,
                AVG(atr) as avg_atr
            FROM market_volatility
            GROUP BY symbol
            """)
            
            for row in cursor.fetchall():
                symbol, count, oldest, newest, avg_vol, avg_atr = row
                summary[symbol] = {
                    'record_count': count,
                    'date_range': f"{oldest} to {newest}",
                    'avg_volatility': round(avg_vol, 4) if avg_vol else None,
                    'avg_atr': round(avg_atr, 4) if avg_atr else None
                }
                
            conn.close()
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            
        return summary

# Utility function to create a collector instance with default symbols
def create_default_collector(symbols: Optional[List[str]] = None) -> MarketDataCollector:
    """
    Create a market data collector with default or specified symbols.
    
    Args:
        symbols: List of symbols to collect data for (optional)
        
    Returns:
        Initialized MarketDataCollector instance
    """
    default_symbols = symbols or [
        'EURUSD', 'GBPUSD', 'USDJPY',  # Major forex pairs
        'BTCUSD', 'ETHUSD',            # Crypto
        'US500', 'GOLD', 'OIL'         # Indices and commodities
    ]
    return MarketDataCollector(symbols=default_symbols)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    collector = create_default_collector()
    
    # Collect historical data for all symbols
    collector.collect_data_for_all_symbols()
    
    # Show data summary
    summary = collector.get_data_summary()
    print("Data Collection Summary:")
    for symbol, stats in summary.items():
        print(f"{symbol}: {stats['record_count']} records from {stats['date_range']}")
    
    # Start scheduled collection if running as main script
    # collector.start_scheduled_collection("00:00")
