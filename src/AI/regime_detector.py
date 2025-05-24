"""
Volatility Regime Detector Module

This module provides functionality to detect market volatility regimes using K-means clustering.
The detector analyzes historical price data to identify different market states (regimes)
with distinct volatility characteristics.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import logging
import sqlite3
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional, Any, Union

# Import AI cache utilities
from src.AI.utils.cache import regime_cache, cached

# Configure logger
logger = logging.getLogger(__name__)

class VolatilityRegimeDetector:
    """
    Detects market volatility regimes using K-means clustering.
    
    Attributes:
        n_clusters (int): Number of volatility regimes to detect
        lookback_days (int): Number of days of historical data to analyze
        features (list): List of features to use for clustering
        model (KMeans): The trained K-means clustering model
        scaler (StandardScaler): Data scaler for normalizing features
        db_path (str): Path to the SQLite database
    """
    
    def __init__(self, n_clusters: int = 3, lookback_days: int = 60, 
                 db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'):
        """
        Initialize the volatility regime detector.
        
        Args:
            n_clusters: Number of volatility regimes to detect (default: 3)
            lookback_days: Number of days of historical data to analyze (default: 60)
            db_path: Path to the SQLite database
        """
        self.n_clusters = n_clusters
        self.lookback_days = lookback_days
        self.db_path = db_path
        self.model = None
        self.scaler = StandardScaler()
        self.features = ['atr_normalized', 'volume_change', 'price_range', 'volatility']
        self.regime_characteristics = {}
        
        # Create regimes table if it doesn't exist
        self._create_tables()
        
    def _create_tables(self):
        """Create necessary tables for storing regime data if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create market_data table if it doesn't exist
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
            
            # Create regimes table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS volatility_regimes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                regime_id INTEGER NOT NULL,
                description TEXT,
                volatility_level TEXT,
                atr_average REAL,
                volume_change_average REAL,
                regime_data TEXT,
                UNIQUE(symbol, timestamp)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Volatility regime tables created successfully")
        except Exception as e:
            logger.error(f"Error creating volatility regime tables: {e}")
            
    def _fetch_market_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch historical market data for the given symbol.
        
        Args:
            symbol: The market symbol to fetch data for
            
        Returns:
            DataFrame containing market data
        """
        try:
            # Calculate the start date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            
            # Query market data
            query = f"""
            SELECT timestamp, close, high, low, volume, atr, volatility
            FROM market_volatility
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol, start_date))
            conn.close()
            
            if len(df) < 30:  # Need minimum data points
                logger.warning(f"Insufficient data for {symbol}: {len(df)} data points")
                return pd.DataFrame()
                
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return pd.DataFrame()
            
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for clustering.
        
        Args:
            df: DataFrame with market data
            
        Returns:
            DataFrame with features for clustering
        """
        if df.empty:
            return pd.DataFrame()
            
        try:
            # Create features for regime detection
            features_df = pd.DataFrame()
            
            # 1. Normalized ATR (Average True Range)
            if 'atr' in df.columns:
                features_df['atr_normalized'] = df['atr'] / df['close']
            else:
                # Calculate ATR if not available
                df['tr1'] = abs(df['high'] - df['low'])
                df['tr2'] = abs(df['high'] - df['close'].shift(1))
                df['tr3'] = abs(df['low'] - df['close'].shift(1))
                df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
                df['atr'] = df['tr'].rolling(window=14).mean()
                features_df['atr_normalized'] = df['atr'] / df['close']
            
            # 2. Volume change percentage
            if 'volume' in df.columns:
                features_df['volume_change'] = df['volume'].pct_change().rolling(window=5).mean()
            else:
                features_df['volume_change'] = 0  # Default if volume data not available
            
            # 3. Price range (High-Low) / Close
            features_df['price_range'] = (df['high'] - df['low']) / df['close']
            
            # 4. Volatility (standard deviation of returns)
            if 'volatility' in df.columns:
                features_df['volatility'] = df['volatility']
            else:
                returns = df['close'].pct_change().rolling(window=20).std() * (252**0.5)  # Annualized
                features_df['volatility'] = returns
            
            # Drop NAs from feature engineering
            features_df = features_df.dropna()
            
            return features_df
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return pd.DataFrame()
            
    def train(self, symbol: str) -> int:
        """
        Train the regime detection model for the given symbol.
        
        Args:
            symbol: The market symbol to analyze
            
        Returns:
            Current regime ID (0 to n_clusters-1) or -1 if training failed
        """
        try:
            # Fetch market data
            market_data = self._fetch_market_data(symbol)
            if market_data.empty:
                logger.warning(f"No market data available for {symbol}")
                return -1
                
            # Prepare features
            features_df = self._prepare_features(market_data)
            if features_df.empty or len(features_df) < 10:
                logger.warning(f"Insufficient feature data for {symbol}")
                return -1
                
            # Scale features
            X = self.scaler.fit_transform(features_df)
            
            # Train K-means model
            self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            clusters = self.model.fit_predict(X)
            
            # Analyze cluster characteristics
            for i in range(self.n_clusters):
                cluster_data = features_df.iloc[clusters == i]
                
                # Store regime characteristics
                self.regime_characteristics[i] = {
                    'atr_avg': float(cluster_data['atr_normalized'].mean()),
                    'volume_change_avg': float(cluster_data['volume_change'].mean()),
                    'price_range_avg': float(cluster_data['price_range'].mean()),
                    'volatility_avg': float(cluster_data['volatility'].mean()),
                    'count': int(len(cluster_data)),
                    'volatility_level': self._get_volatility_level(cluster_data['volatility'].mean())
                }
                
            # Determine current regime (latest data point)
            latest_features = self.scaler.transform(features_df.iloc[[-1]])
            current_regime = int(self.model.predict(latest_features)[0])
            
            # Save regime information
            self._save_regime_data(symbol, current_regime)
            
            logger.info(f"Volatility regime model trained for {symbol}. Current regime: {current_regime}")
            return current_regime
            
        except Exception as e:
            logger.error(f"Error training volatility regime model: {e}")
            return -1
            
    def _get_volatility_level(self, volatility: float) -> str:
        """
        Classify volatility level based on the volatility value.
        
        Args:
            volatility: Volatility value to classify
            
        Returns:
            String classification of volatility level
        """
        if volatility < 0.15:
            return "LOW"
        elif volatility < 0.30:
            return "MEDIUM" 
        else:
            return "HIGH"
            
    def _save_regime_data(self, symbol: str, current_regime: int):
        """
        Save regime data to the database.
        
        Args:
            symbol: The market symbol
            current_regime: Current regime ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            regime_data = json.dumps(self.regime_characteristics)
            regime_info = self.regime_characteristics[current_regime]
            
            cursor.execute('''
            INSERT OR REPLACE INTO volatility_regimes
            (symbol, timestamp, regime_id, description, volatility_level, atr_average, 
             volume_change_average, regime_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, 
                now, 
                current_regime,
                f"Regime {current_regime}",
                regime_info['volatility_level'],
                regime_info['atr_avg'],
                regime_info['volume_change_avg'],
                regime_data
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving regime data: {e}")
            
    @cached(regime_cache, key_prefix='regime')
    def detect_current_regime(self, symbol: str) -> int:
        """
        Detect the current volatility regime ID for the given symbol.
        
        Args:
            symbol: The market symbol
            
        Returns:
            Current regime ID (int) or -1 if detection failed
        """
        try:
            # Get the full regime information
            regime_info = self.get_current_regime(symbol)
            
            # Check if regime_info is valid and contains regime_id
            if not regime_info or 'regime_id' not in regime_info:
                logger.warning(f"No valid regime information found for {symbol}")
                return -1
                
            # Extract and return just the regime ID
            return regime_info.get('regime_id', -1)
            
        except Exception as e:
            logger.error(f"Error detecting current regime for {symbol}: {e}")
            return -1
    
    def get_current_regime(self, symbol: str) -> Dict[str, Any]:
        """
        Get the current volatility regime for the given symbol.
        
        Args:
            symbol: The market symbol
            
        Returns:
            Dictionary containing current regime information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT regime_id, description, volatility_level, atr_average, 
                   volume_change_average, regime_data
            FROM volatility_regimes
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
            ''', (symbol,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                regime_id, description, vol_level, atr_avg, vol_change_avg, regime_data = row
                regime_data = json.loads(regime_data) if regime_data else {}
                
                return {
                    'regime_id': regime_id,
                    'description': description,
                    'volatility_level': vol_level,
                    'atr_average': atr_avg,
                    'volume_change_average': vol_change_avg,
                    'regime_characteristics': regime_data,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                # No regime data found, train new model
                current_regime = self.train(symbol)
                if current_regime >= 0:
                    return self.get_current_regime(symbol)
                else:
                    return {
                        'regime_id': -1,
                        'description': "Unknown Regime",
                        'volatility_level': "UNKNOWN",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                
        except Exception as e:
            logger.error(f"Error getting current regime: {e}")
            return {
                'regime_id': -1,
                'description': f"Error: {str(e)}",
                'volatility_level': "ERROR",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
    def update_market_data(self, symbol: str, timestamp: str, close: float, 
                          high: float, low: float, volume: float = 0, 
                          atr: float = 0, volatility: float = 0):
        """
        Update market data in the database.
        
        Args:
            symbol: The market symbol
            timestamp: Timestamp for the data point
            close: Closing price
            high: High price
            low: Low price
            volume: Trading volume
            atr: Average True Range
            volatility: Volatility measurement
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO market_volatility
            (symbol, timestamp, close, high, low, volume, atr, volatility)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, timestamp, close, high, low, volume, atr, volatility))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
