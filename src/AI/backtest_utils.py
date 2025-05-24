"""
Backtest Utilities for Jamso-AI-Engine

This module provides utilities for backtesting trading strategies:
- Loading historical market data from various sources
- Data preprocessing and transformation
- Generating synthetic test data when real data is unavailable
- Saving and loading backtest results
"""

import pandas as pd
import numpy as np
import sqlite3
import os
import json
import sys
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

# Suppress import warnings when running in test mode
if '--use-sample-data' in sys.argv:
    warnings.filterwarnings("ignore", category=ImportWarning)

class DataLoader:
    """Utility to load market data for backtesting from various sources."""
    
    @staticmethod
    def load_from_db(db_path: str, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Load market data from the SQLite database.
        
        Args:
            db_path: Path to the SQLite database
            symbol: Symbol to load data for
            start_date: Optional start date in 'YYYY-MM-DD' format
            end_date: Optional end date in 'YYYY-MM-DD' format
            
        Returns:
            DataFrame with OHLCV data or None if data not available
        """
        try:
            conn = sqlite3.connect(db_path)
            
            query = "SELECT timestamp, close, high, low, volume, atr FROM market_volatility WHERE symbol = ?"
            params = [symbol]
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
                
            query += " ORDER BY timestamp ASC"
            
            # Load data from database
            df = pd.read_sql_query(query, conn, params=tuple(params))
            conn.close()
            
            if df.empty:
                print(f"No data found for {symbol} in the database")
                return None
                
            # Format data for backtesting
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Add fake 'open' column as it's needed for some strategies and missing in our DB schema
            df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
            
            # Reorder columns for compatibility with strategy functions
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'atr']]
            
            print(f"Loaded {len(df)} records for {symbol} from database")
            return df
            
        except Exception as e:
            print(f"Error loading data from database: {e}")
            return None

    @staticmethod
    def load_from_csv(file_path: str) -> Optional[pd.DataFrame]:
        """
        Load market data from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame with OHLCV data or None if file not available
        """
        try:
            df = pd.read_csv(file_path)
            
            # Check required columns
            required_cols = ['timestamp', 'open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                print(f"CSV file missing required columns: {', '.join(required_cols)}")
                return None
                
            # Format data
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if 'volume' not in df.columns:
                df['volume'] = 0
                
            print(f"Loaded {len(df)} records from {file_path}")
            return df
            
        except Exception as e:
            print(f"Error loading data from CSV: {e}")
            return None
            
    @staticmethod
    def generate_sample_data(symbol: str, days: int = 365, volatility: float = 0.015,
                           start_price: float = 100.0, start_date: Optional[str] = None) -> pd.DataFrame:
        """
        Generate synthetic market data for testing when real data is unavailable.
        
        Args:
            symbol: Symbol to generate data for
            days: Number of days to generate
            volatility: Daily price volatility
            start_price: Starting price
            start_date: Optional start date in 'YYYY-MM-DD' format
            
        Returns:
            DataFrame with synthetic OHLCV data
        """
        if start_date:
            start = pd.to_datetime(start_date)
        else:
            start = datetime.now() - timedelta(days=days)
            
        # Generate dates (business days)
        dates = pd.date_range(start=start, periods=days, freq='B')
        
        # Generate random returns
        returns = np.random.normal(0, volatility, days)
        
        # Calculate prices
        prices = start_price * (1 + returns).cumprod()
        
        # Create OHLCV data
        df = pd.DataFrame({
            'timestamp': dates,
            'close': prices,
            'open': prices * (1 + np.random.normal(0, volatility/3, days)),
            'volume': np.random.lognormal(10, 1, days)
        })
        
        # Generate high/low based on open/close
        daily_range = prices * volatility * np.random.uniform(0.5, 2.0, days)
        df['high'] = np.maximum(df['open'], df['close']) + daily_range / 2
        df['low'] = np.minimum(df['open'], df['close']) - daily_range / 2
        
        # Calculate ATR (Average True Range)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=14).mean().fillna(df['tr'])
        
        # Clean up temporary columns
        df = df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1)
        
        print(f"Generated {len(df)} days of synthetic data for {symbol}")
        return df

class ResultSaver:
    """Utility to save and load backtest results."""
    
    @staticmethod
    def save_results(results: Dict[str, Any], file_path: str):
        """
        Save backtest results to JSON file.
        
        Args:
            results: Dictionary containing backtest results
            file_path: Path to save results to
        """
        try:
            # Prepare results for serialization
            serializable_results = results.copy()
            
            # Convert pandas objects to serializable format
            if 'equity_curve' in serializable_results:
                if isinstance(serializable_results['equity_curve'], pd.Series):
                    serializable_results['equity_curve'] = {
                        'timestamps': [t.isoformat() for t in serializable_results['equity_curve'].index],
                        'values': serializable_results['equity_curve'].values.tolist()
                    }
                    
            if 'trades' in serializable_results:
                if isinstance(serializable_results['trades'], pd.DataFrame):
                    serializable_results['trades'] = serializable_results['trades'].to_dict(orient='records')
                    # Convert timestamps in trades
                    for trade in serializable_results['trades']:
                        if isinstance(trade.get('timestamp'), pd.Timestamp):
                            trade['timestamp'] = trade['timestamp'].isoformat()
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(serializable_results, f, indent=2)
                
            print(f"Backtest results saved to {file_path}")
            
        except Exception as e:
            print(f"Error saving backtest results: {e}")
            
    @staticmethod
    def load_results(file_path: str) -> Dict[str, Any]:
        """
        Load backtest results from JSON file.
        
        Args:
            file_path: Path to load results from
            
        Returns:
            Dictionary containing backtest results
        """
        try:
            with open(file_path, 'r') as f:
                results = json.load(f)
                
            # Convert back to pandas objects if needed
            if 'equity_curve' in results and isinstance(results['equity_curve'], dict):
                timestamps = [pd.Timestamp(t) for t in results['equity_curve']['timestamps']]
                values = results['equity_curve']['values']
                results['equity_curve'] = pd.Series(values, index=timestamps)
                
            if 'trades' in results and isinstance(results['trades'], list):
                trades_df = pd.DataFrame(results['trades'])
                if 'timestamp' in trades_df.columns:
                    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
                results['trades'] = trades_df
                
            print(f"Loaded backtest results from {file_path}")
            return results
            
        except Exception as e:
            print(f"Error loading backtest results: {e}")
            return {}
