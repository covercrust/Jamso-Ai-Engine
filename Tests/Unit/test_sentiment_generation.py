#!/usr/bin/env python3
import os
import sys
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure database directory exists
db_dir = os.path.join("/home/jamso-ai-server/Jamso-Ai-Engine", "src", "Database", "Sentiment")
os.makedirs(db_dir, exist_ok=True)
logger.info(f"Ensured database directory exists: {db_dir}")

# Database path
db_path = os.path.join(db_dir, "sentiment_data.db")
logger.info(f"Database path: {db_path}")

def create_realistic_market_sentiment(
    symbol: str, 
    days: int = 30, 
    trend_bias: float = 0.0,  # -1 to 1: -1 = bearish, 0 = neutral, 1 = bullish
    volatility: float = 0.1   # 0 to 1: higher means more sentiment swings
) -> pd.DataFrame:
    """
    Create realistic market sentiment data with trends and patterns.
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
    
    # Convert timestamps to strings for consistency
    combined_df['timestamp'] = combined_df['timestamp'].astype(str)
    
    return combined_df

def save_sentiment_data(df: pd.DataFrame):
    """Save sentiment data to SQLite database."""
    logger.info(f"Saving {len(df)} sentiment records to database")
    
    try:
        # Create tables if they don't exist
        conn = sqlite3.connect(db_path)
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
        
        # Insert data, ignoring duplicates
        for i, row in df.iterrows():
            try:
                cursor.execute(
                    '''
                    INSERT OR IGNORE INTO sentiment_data 
                    (symbol, timestamp, long_sentiment, short_sentiment, net_sentiment, sentiment_value, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        row['symbol'],
                        row['timestamp'],
                        row.get('long_sentiment'),
                        row.get('short_sentiment'),
                        row.get('net_sentiment'),
                        row.get('sentiment_value'),
                        row['source']
                    )
                )
                if i % 1000 == 0:
                    conn.commit()
                    logger.info(f"Committed {i} records")
            except Exception as e:
                logger.error(f"Error inserting row {i}: {str(e)}")
        
        conn.commit()
        logger.info("Final commit completed")
        
        # Check how many records were inserted
        cursor.execute("SELECT COUNT(*) FROM sentiment_data WHERE symbol=?", (df.iloc[0]['symbol'],))
        count = cursor.fetchone()[0]
        logger.info(f"Database now has {count} records for {df.iloc[0]['symbol']}")
        
        conn.close()
        logger.info("Database connection closed")
        
    except Exception as e:
        logger.error(f"Error saving sentiment data: {str(e)}")
        raise

# Main function
if __name__ == "__main__":
    symbol = "BTCUSD"
    days = 90
    trend_bias = 0.2
    volatility = 0.4
    
    logger.info(f"Starting sentiment generation for {symbol}")
    
    # Generate sentiment data
    sentiment_df = create_realistic_market_sentiment(
        symbol=symbol,
        days=days,
        trend_bias=trend_bias,
        volatility=volatility
    )
    
    logger.info(f"Generated {len(sentiment_df)} sentiment data points")
    
    # Save to database
    save_sentiment_data(sentiment_df)
    logger.info(f"Finished saving sentiment data for {symbol}")
    
    # Also generate for ETH with slightly different characteristics
    eth_sentiment = create_realistic_market_sentiment(
        symbol="ETHUSD",
        days=days,
        trend_bias=trend_bias * 0.8,  # Slightly different trend
        volatility=volatility * 1.2  # More volatile
    )
    
    save_sentiment_data(eth_sentiment)
    logger.info(f"Finished saving sentiment data for ETHUSD")
    
    # Verify the data was saved
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get counts by symbol and source
        cursor.execute('''
        SELECT symbol, source, COUNT(*) 
        FROM sentiment_data 
        GROUP BY symbol, source
        ''')
        
        print("\nSentiment Data Summary:")
        print("------------------------")
        for row in cursor.fetchall():
            print(f"{row[0]} - {row[1]}: {row[2]} entries")
            
        # Get date ranges
        cursor.execute('''
        SELECT symbol, MIN(timestamp), MAX(timestamp) 
        FROM sentiment_data 
        GROUP BY symbol
        ''')
        
        print("\nDate Ranges:")
        print("------------")
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} to {row[2]}")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"Error verifying data: {str(e)}")
