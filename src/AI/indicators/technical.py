"""
Technical Indicators Module

This module provides various technical indicators for market analysis,
optimized for use with AI-driven trading systems.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from src.AI.indicators.alt_functions import alt_obv, alt_volatility

# Configure logger
logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """
    Technical indicators for financial market analysis.
    """
    
    @staticmethod
    def sma(data: pd.Series, window: int) -> pd.Series:
        """
        Simple Moving Average.
        
        Args:
            data: Price series
            window: Window size
            
        Returns:
            Series with SMA values
        """
        return data.rolling(window=window).mean()
    
    @staticmethod
    def ema(data: pd.Series, window: int) -> pd.Series:
        """
        Exponential Moving Average.
        
        Args:
            data: Price series
            window: Window size
            
        Returns:
            Series with EMA values
        """
        return data.ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        """
        Bollinger Bands.
        
        Args:
            data: Price series
            window: Window size
            num_std: Number of standard deviations for bands
            
        Returns:
            DataFrame with upper, middle, and lower bands
        """
        sma = TechnicalIndicators.sma(data, window)
        std = data.rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return pd.DataFrame({
            'middle_band': sma,
            'upper_band': upper_band,
            'lower_band': lower_band
        })
    
    @staticmethod
    def macd(data: pd.Series, fast_window: int = 12, slow_window: int = 26, signal_window: int = 9) -> pd.DataFrame:
        """
        Moving Average Convergence Divergence.
        
        Args:
            data: Price series
            fast_window: Fast EMA window
            slow_window: Slow EMA window
            signal_window: Signal EMA window
            
        Returns:
            DataFrame with MACD line, signal line, and histogram
        """
        fast_ema = TechnicalIndicators.ema(data, fast_window)
        slow_ema = TechnicalIndicators.ema(data, slow_window)
        macd_line = fast_ema - slow_ema
        signal_line = TechnicalIndicators.ema(macd_line, signal_window)
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        })
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """
        Relative Strength Index.
        
        Args:
            data: Price series
            window: Window size
            
        Returns:
            Series with RSI values
        """
        # Calculate price changes
        delta = data.diff()
        
        # Separate gains and losses
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        # Calculate average gain and average loss
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """
        Average True Range.
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            window: Window size
            
        Returns:
            Series with ATR values
        """
        # Calculate True Range
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = tr.rolling(window=window).mean()
        
        return atr
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> pd.DataFrame:
        """
        Stochastic Oscillator.
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            k_window: %K window
            d_window: %D window
            
        Returns:
            DataFrame with %K and %D values
        """
        # Calculate %K
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # Calculate %D
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return pd.DataFrame({
            'k_percent': k_percent,
            'd_percent': d_percent
        })
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.DataFrame:
        """
        Average Directional Index.
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            window: Window size
            
        Returns:
            DataFrame with ADX, +DI, and -DI values
        """
        # Calculate True Range
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        
        # Calculate Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        pos_dm = ((up_move > down_move) & (up_move > 0)) * up_move
        neg_dm = ((down_move > up_move) & (down_move > 0)) * down_move
        
        # Calculate Directional Indicators
        pos_di = 100 * (pos_dm.rolling(window=window).mean() / atr)
        neg_di = 100 * (neg_dm.rolling(window=window).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * ((pos_di - neg_di).abs() / (pos_di + neg_di))
        adx = dx.rolling(window=window).mean()
        
        return pd.DataFrame({
            'adx': adx,
            'pos_di': pos_di,
            'neg_di': neg_di
        })
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume.
        
        Args:
            close: Close price series
            volume: Volume series
            
        Returns:
            Series with OBV values
        """
        # Call fixed implementation to avoid type errors
        return alt_obv(close, volume)
    
    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, 
                 conversion_period: int = 9, base_period: int = 26, 
                 lagging_span2_period: int = 52, displacement: int = 26) -> pd.DataFrame:
        """
        Ichimoku Cloud.
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            conversion_period: Conversion line period
            base_period: Base line period
            lagging_span2_period: Lagging span 2 period
            displacement: Cloud displacement period
            
        Returns:
            DataFrame with Ichimoku components
        """
        # Conversion Line (Tenkan-sen)
        conversion_high = high.rolling(window=conversion_period).max()
        conversion_low = low.rolling(window=conversion_period).min()
        conversion_line = (conversion_high + conversion_low) / 2
        
        # Base Line (Kijun-sen)
        base_high = high.rolling(window=base_period).max()
        base_low = low.rolling(window=base_period).min()
        base_line = (base_high + base_low) / 2
        
        # Leading Span A (Senkou Span A)
        leading_span_a = ((conversion_line + base_line) / 2).shift(displacement)
        
        # Leading Span B (Senkou Span B)
        leading_high = high.rolling(window=lagging_span2_period).max()
        leading_low = low.rolling(window=lagging_span2_period).min()
        leading_span_b = ((leading_high + leading_low) / 2).shift(displacement)
        
        # Lagging Span (Chikou Span)
        lagging_span = close.shift(-displacement)
        
        return pd.DataFrame({
            'conversion_line': conversion_line,
            'base_line': base_line,
            'leading_span_a': leading_span_a,
            'leading_span_b': leading_span_b,
            'lagging_span': lagging_span
        })
    
    @staticmethod
    def fibonacci_levels(high: pd.Series, low: pd.Series, is_uptrend: bool = True) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels.
        
        Args:
            high: High price series (or highest high in trend)
            low: Low price series (or lowest low in trend)
            is_uptrend: True if the trend is upward, False if downward
            
        Returns:
            Dictionary with Fibonacci levels
        """
        if is_uptrend:
            diff = high.max() - low.min()
            max_price = high.max()
            
            return {
                'level_0': max_price,
                'level_0.236': max_price - 0.236 * diff,
                'level_0.382': max_price - 0.382 * diff,
                'level_0.5': max_price - 0.5 * diff,
                'level_0.618': max_price - 0.618 * diff,
                'level_0.786': max_price - 0.786 * diff,
                'level_1': max_price - diff
            }
        else:
            diff = high.max() - low.min()
            min_price = low.min()
            
            return {
                'level_0': min_price,
                'level_0.236': min_price + 0.236 * diff,
                'level_0.382': min_price + 0.382 * diff,
                'level_0.5': min_price + 0.5 * diff,
                'level_0.618': min_price + 0.618 * diff,
                'level_0.786': min_price + 0.786 * diff,
                'level_1': min_price + diff
            }
    
    @staticmethod
    def volatility(close: pd.Series, window: int = 20) -> pd.DataFrame:
        """
        Calculate different volatility measures.
        
        Args:
            close: Close price series
            window: Window size for calculations
            
        Returns:
            DataFrame with volatility measures
        """
        # Call alternative implementation to avoid type errors
        return alt_volatility(close, window)
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all indicators to a DataFrame with OHLCV data.
        
        Args:
            df: DataFrame with 'open', 'high', 'low', 'close', 'volume' columns
            
        Returns:
            DataFrame with additional technical indicators
        """
        result = df.copy()
        
        # Add SMA indicators
        result['sma_5'] = TechnicalIndicators.sma(df['close'], 5)
        result['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
        result['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
        result['sma_200'] = TechnicalIndicators.sma(df['close'], 200)
        
        # Add EMA indicators
        result['ema_5'] = TechnicalIndicators.ema(df['close'], 5)
        result['ema_20'] = TechnicalIndicators.ema(df['close'], 20)
        result['ema_50'] = TechnicalIndicators.ema(df['close'], 50)
        result['ema_200'] = TechnicalIndicators.ema(df['close'], 200)
        
        # Add Bollinger Bands
        bollinger = TechnicalIndicators.bollinger_bands(df['close'])
        result['bb_middle'] = bollinger['middle_band']
        result['bb_upper'] = bollinger['upper_band']
        result['bb_lower'] = bollinger['lower_band']
        
        # Add MACD
        macd = TechnicalIndicators.macd(df['close'])
        result['macd_line'] = macd['macd_line']
        result['macd_signal'] = macd['signal_line']
        result['macd_hist'] = macd['histogram']
        
        # Add RSI
        result['rsi'] = TechnicalIndicators.rsi(df['close'])
        
        # Add ATR
        result['atr'] = TechnicalIndicators.atr(df['high'], df['low'], df['close'])
        
        # Add Stochastic
        stoch = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
        result['stoch_k'] = stoch['k_percent']
        result['stoch_d'] = stoch['d_percent']
        
        # Add ADX
        adx = TechnicalIndicators.adx(df['high'], df['low'], df['close'])
        result['adx'] = adx['adx']
        result['di_plus'] = adx['pos_di']
        result['di_minus'] = adx['neg_di']
        
        # Add OBV
        result['obv'] = TechnicalIndicators.obv(df['close'], df['volume'])
        
        # Add volatility measures
        volatility = TechnicalIndicators.volatility(df['close'])
        result['hist_volatility'] = volatility['hist_volatility']
        
        return result
    
    @staticmethod
    def get_signal_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract key features for AI model training from a DataFrame with technical indicators.
        
        Args:
            df: DataFrame with technical indicators
            
        Returns:
            DataFrame with selected features for AI models
        """
        if 'close' not in df.columns:
            logger.error("Input DataFrame must contain 'close' column")
            return df
            
        features = pd.DataFrame(index=df.index)
        
        # Price-based features
        if 'sma_20' in df.columns:
            features['close_vs_sma20'] = (df['close'] / df['sma_20'] - 1) * 100
        
        if 'sma_50' in df.columns:
            features['close_vs_sma50'] = (df['close'] / df['sma_50'] - 1) * 100
        
        if 'sma_200' in df.columns:
            features['close_vs_sma200'] = (df['close'] / df['sma_200'] - 1) * 100
            
        # MACD features
        if 'macd_line' in df.columns and 'macd_signal' in df.columns:
            features['macd_diff'] = df['macd_line'] - df['macd_signal']
            
        # RSI features
        if 'rsi' in df.columns:
            features['rsi'] = df['rsi']
            features['rsi_oversold'] = (df['rsi'] < 30).astype(int)
            features['rsi_overbought'] = (df['rsi'] > 70).astype(int)
            
        # Bollinger Band features
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            features['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            features['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
        # ADX features
        if 'adx' in df.columns:
            features['adx'] = df['adx']
            features['trend_strength'] = (df['adx'] > 25).astype(int)
            if 'di_plus' in df.columns and 'di_minus' in df.columns:
                features['di_spread'] = df['di_plus'] - df['di_minus']
                features['di_trend'] = np.where(df['di_plus'] > df['di_minus'], 1, -1)
                
        # Volatility features
        if 'atr' in df.columns:
            features['atr'] = df['atr']
            if 'close' in df.columns:
                features['atr_percent'] = df['atr'] / df['close'] * 100
                
        if 'hist_volatility' in df.columns:
            features['volatility'] = df['hist_volatility']
            
        # Volume features
        if 'volume' in df.columns:
            features['volume_change'] = df['volume'].pct_change()
            features['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
                
        # Stochastic features
        if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
            features['stoch_diff'] = df['stoch_k'] - df['stoch_d']
            features['stoch_oversold'] = ((df['stoch_k'] < 20) & (df['stoch_d'] < 20)).astype(int)
            features['stoch_overbought'] = ((df['stoch_k'] > 80) & (df['stoch_d'] > 80)).astype(int)
            
        return features
