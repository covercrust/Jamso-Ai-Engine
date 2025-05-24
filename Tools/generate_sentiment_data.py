#!/usr/bin/env python3
"""
Add sample sentiment data to the database for BTCUSD

This script creates realistic sample sentiment data for Bitcoin and 
adds it to the sentiment database for use in strategy optimization.
"""

import os
import sys
import pandas as pd
import numpy as np
import argparse
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path to access the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.AI.sentiment_integration import SentimentIntegration

def create_realistic_market_sentiment(
    symbol: str, 
    days: int = 30, 
    trend_bias: float = 0.0,  # -1 to 1: -1 = bearish, 0 = neutral, 1 = bullish
    volatility: float = 0.1   # 0 to 1: higher means more sentiment swings
) -> pd.DataFrame:
    """
    Create realistic market sentiment data with trends and patterns.
    
    Args:
        symbol: Market symbol (e.g., "BTCUSD")
        days: Number of days to generate data for
        trend_bias: Long-term sentiment bias (-1 to 1)
        volatility: Amount of sentiment volatility (0 to 1)
    
    Returns:
        DataFrame with sentiment data
    """
    logger.info(f"Generating realistic sentiment data for {symbol} (last {days} days)")
    
    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Create hourly timestamps (using 'h' instead of 'H' to avoid deprecation warning)
    timestamps = pd.date_range(start=start_date, end=end_date, freq='1h')
    
    # Generate sentiment components:
    
    # 1. Base trend (slow moving)
    time = np.linspace(0, 10, len(timestamps))
    base_trend = trend_bias + np.sin(time / 5) * 0.2
    
    # 2. Daily cycles (sentiment often follows daily patterns)
    hours = np.array([ts.hour for ts in timestamps])
    daily_pattern = 0.1 * np.sin((hours / 24) * 2 * np.pi)
    
    # 3. Weekly component (weekend effects)
    weekdays = np.array([ts.weekday() for ts in timestamps])
    weekend_effect = 0.15 * np.where(weekdays >= 5, -1, 0)  # Lower sentiment on weekends
    
    # 4. Random noise components
    short_noise = np.random.normal(0, volatility * 0.1, len(timestamps))  # hourly variations
    medium_noise = np.random.normal(0, volatility * 0.2, len(timestamps) // 24)  # daily variations
    # Ensure medium_noise has the right length by padding or truncating
    if len(medium_noise) * 24 < len(timestamps):
        medium_noise = np.pad(medium_noise, (0, (len(timestamps) // 24) - len(medium_noise) + 1))
    medium_noise = np.repeat(medium_noise, 24)[:len(timestamps)]
    
    # 5. Occasional news events (spikes)
    news_events = np.zeros(len(timestamps))
    num_events = int(days / 3)  # On average, one significant news event every 3 days
    event_indices = np.random.choice(len(timestamps), num_events)
    event_magnitudes = np.random.choice([-0.4, 0.4], num_events) * volatility * 2
    for idx, magnitude in zip(event_indices, event_magnitudes):
        # Create a spike that decays over 24 hours
        decay_length = 24  # hours
        decay = np.exp(-np.arange(decay_length) / (decay_length / 3))
        end_idx = min(idx + decay_length, len(news_events))
        news_events[idx:end_idx] += magnitude * decay[:end_idx-idx]

    # Combine all components
    sentiment = base_trend + daily_pattern + weekend_effect + short_noise + medium_noise + news_events
    
    # Ensure values are within -1 to 1 range
    sentiment = np.clip(sentiment, -1, 1)
    
    # Convert to 0-1 scale (as often used in sentiment scores)
    sentiment_0_1 = (sentiment + 1) / 2
    
    # Create dataframe for each source
    capital_df = pd.DataFrame({
        'timestamp': timestamps,
        'symbol': symbol,
        'long_sentiment': np.clip(sentiment_0_1 + np.random.normal(0, 0.05, len(timestamps)), 0, 1),
        'short_sentiment': np.clip(1 - sentiment_0_1 + np.random.normal(0, 0.05, len(timestamps)), 0, 1),
        'net_sentiment': sentiment,
        'sentiment_value': sentiment,
        'source': 'capital_com'
    })
    
    # Twitter sentiment (more volatile)
    twitter_timestamps = pd.date_range(start=start_date, end=end_date, freq='30min')
    twitter_sentiment = np.interp(
        np.linspace(0, len(sentiment), len(twitter_timestamps)), 
        np.arange(len(sentiment)), 
        sentiment
    )
    twitter_noise = np.random.normal(0, volatility * 0.3, len(twitter_timestamps))
    twitter_sentiment = np.clip(twitter_sentiment + twitter_noise, -1, 1)
    
    twitter_df = pd.DataFrame({
        'timestamp': twitter_timestamps,
        'symbol': symbol,
        'sentiment_value': twitter_sentiment,
        'source': 'twitter'
    })
    
    # News sentiment (less frequent, but more impactful)
    news_timestamps = pd.date_range(start=start_date, end=end_date, freq='3h')
    news_sentiment = np.interp(
        np.linspace(0, len(sentiment), len(news_timestamps)), 
        np.arange(len(sentiment)), 
        sentiment
    )
    # Add stronger spikes
    news_spikes = np.zeros(len(news_timestamps))
    num_spikes = int(days / 2)  # News events every 2 days on average
    spike_indices = np.random.choice(len(news_timestamps), num_spikes)
    spike_magnitudes = np.random.choice([-0.6, 0.6], num_spikes)
    news_spikes[spike_indices] = spike_magnitudes
    
    news_sentiment = np.clip(news_sentiment + news_spikes, -1, 1)
    
    news_df = pd.DataFrame({
        'timestamp': news_timestamps,
        'symbol': symbol,
        'sentiment_value': news_sentiment,
        'source': 'news'
    })
    
    # Combine all sources
    combined_df = pd.concat([capital_df, twitter_df, news_df], ignore_index=True)
    
    return combined_df

def main():
    parser = argparse.ArgumentParser(description="Add sample sentiment data to the database")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Market symbol")
    parser.add_argument("--days", type=int, default=60, help="Number of days of data")
    parser.add_argument("--trend", type=float, default=0.1, help="Trend bias (-1 to 1)")
    parser.add_argument("--volatility", type=float, default=0.3, help="Sentiment volatility (0 to 1)")
    
    args = parser.parse_args()
    
    # Create sentiment data
    sentiment_df = create_realistic_market_sentiment(
        symbol=args.symbol, 
        days=args.days,
        trend_bias=args.trend,
        volatility=args.volatility
    )
    
    # Initialize sentiment integration
    sentiment_integration = SentimentIntegration()
    
    # Save to database
    sentiment_integration.save_sentiment_data(sentiment_df)
    logger.info(f"Added {len(sentiment_df)} sentiment data points to database for {args.symbol}")
    
    # Add additional symbols if needed
    if args.symbol == "BTCUSD":
        # Also add some data for ETHUSD with correlation but different characteristics
        eth_sentiment = create_realistic_market_sentiment(
            symbol="ETHUSD", 
            days=args.days,
            trend_bias=args.trend * 0.8,  # Slightly different trend
            volatility=args.volatility * 1.2  # More volatile
        )
        sentiment_integration.save_sentiment_data(eth_sentiment)
        logger.info(f"Added {len(eth_sentiment)} sentiment data points for ETHUSD")

if __name__ == "__main__":
    main()
