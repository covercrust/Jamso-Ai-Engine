#!/usr/bin/env python3
"""
Create and store BTCUSD sentiment data for Capital.com API optimizer

This is a simplified script that creates sentiment data and stores it
directly in a format that the optimizer can use.
"""

import os
import sys
import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_realistic_market_sentiment(
    symbol: str, 
    days: int = 90, 
    trend_bias: float = 0.2,  # -1 to 1: -1 = bearish, 0 = neutral, 1 = bullish
    volatility: float = 0.4   # 0 to 1: higher means more sentiment swings
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
    
    # Create hourly timestamps
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
        medium_noise = np.pad(medium_noise, (0, 1))  # Add one more element if needed
    medium_noise = np.repeat(medium_noise, 24)[:len(timestamps)]  # Resize to match timestamps
    
    # 5. Occasional news events (spikes)
    news_events = np.zeros(len(timestamps))
    num_events = int(days / 3)  # On average, one significant news event every 3 days
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
    
    # Convert to DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'symbol': symbol,
        'sentiment': sentiment,
    })
    
    # Convert timestamp to string format
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return df

def save_sentiment_to_json(df: pd.DataFrame, output_path: str):
    """Save sentiment data to a JSON file that can be loaded by the optimizer."""
    
    sentiment_data = {}
    
    # Group data by symbol
    for symbol, group in df.groupby('symbol'):
        sentiment_dict = dict(zip(group['timestamp'], group['sentiment']))
        sentiment_data[symbol] = sentiment_dict
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(sentiment_data, f, indent=2)
    
    logger.info(f"Saved sentiment data to {output_path}")
    return output_path

def load_sentiment_from_json(file_path: str):
    """Load sentiment data from JSON file."""
    with open(file_path, 'r') as f:
        sentiment_data = json.load(f)
    
    # Convert back to DataFrame for analysis
    all_data = []
    for symbol, data in sentiment_data.items():
        for timestamp, sentiment in data.items():
            all_data.append({
                'symbol': symbol,
                'timestamp': timestamp,
                'sentiment': sentiment
            })
    
    return pd.DataFrame(all_data)

def main():
    # Configuration
    symbols = ["BTCUSD", "ETHUSD"]
    days = 90
    output_dir = os.path.join("/home/jamso-ai-server/Jamso-Ai-Engine", "src", "Database", "Sentiment")
    output_file = os.path.join(output_dir, "sentiment_data.json")
    
    all_sentiment_data = []
    
    # Generate data for each symbol
    for symbol in symbols:
        sentiment_df = create_realistic_market_sentiment(
            symbol=symbol,
            days=days,
            trend_bias=0.2 if symbol == "BTCUSD" else 0.15,
            volatility=0.4 if symbol == "BTCUSD" else 0.5
        )
        all_sentiment_data.append(sentiment_df)
        logger.info(f"Generated {len(sentiment_df)} sentiment data points for {symbol}")
    
    # Combine all data
    combined_df = pd.concat(all_sentiment_data, ignore_index=True)
    
    # Save to JSON file
    json_path = save_sentiment_to_json(combined_df, output_file)
    logger.info(f"Saved {len(combined_df)} total sentiment data points to {json_path}")
    
    # Verify data can be loaded back
    loaded_df = load_sentiment_from_json(json_path)
    
    # Print summary
    print("\nSentiment Data Summary:")
    print("------------------------")
    for symbol, group in loaded_df.groupby('symbol'):
        print(f"{symbol}: {len(group)} entries")
        
        # Get min/max timestamps
        min_date = min(pd.to_datetime(group['timestamp']))
        max_date = max(pd.to_datetime(group['timestamp']))
        print(f"  Date range: {min_date} to {max_date}")
        
        # Get sentiment stats
        sentiment_min = group['sentiment'].min()
        sentiment_max = group['sentiment'].max()
        sentiment_mean = group['sentiment'].mean()
        print(f"  Sentiment range: {sentiment_min:.2f} to {sentiment_max:.2f} (avg: {sentiment_mean:.2f})")
        print()
    
    print(f"Data successfully saved to {json_path}")
    print(f"This file can now be used with the Capital.com API optimizer")

if __name__ == "__main__":
    main()
