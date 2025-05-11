import requests
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = "/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/capital_com/market_data.db"

def get_db():
    """Get a connection to the database."""
    return sqlite3.connect(DATABASE_PATH)

def create_table():
    """Create the market_data table if it does not exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                epic TEXT PRIMARY KEY,
                name TEXT,
                instrument_type TEXT,
                lot_size REAL,
                currency TEXT,
                leverage REAL,
                margin_rate REAL,
                timestamp INTEGER,
                bid REAL,
                ask REAL,
                last REAL,
                high REAL,
                low REAL,
                volume REAL
            )
        """)
        conn.commit()
    logger.info("Table market_data created successfully.")

def save_market_data(**data):
    """Save market data to the database."""
    required_keys = [
        "epic", "name", "instrument_type", "lot_size", "currency", 
        "bid", "ask", "last", "high", "low", "volume"
    ]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO market_data (
                epic, name, instrument_type, lot_size, currency, leverage, 
                margin_rate, timestamp, bid, ask, last, high, low, volume
            ) VALUES (
                :epic, :name, :instrument_type, :lot_size, :currency, :leverage,
                :margin_rate, :timestamp, :bid, :ask, :last, :high, :low, :volume
            )
            ON CONFLICT(epic) DO UPDATE SET
                name=excluded.name,
                instrument_type=excluded.instrument_type,
                lot_size=excluded.lot_size,
                currency=excluded.currency,
                leverage=excluded.leverage,
                margin_rate=excluded.margin_rate,
                timestamp=excluded.timestamp,
                bid=excluded.bid,
                ask=excluded.ask,
                last=excluded.last,
                high=excluded.high,
                low=excluded.low,
                volume=excluded.volume
        """, data)
        conn.commit()
    logger.info(f"Market data for {data['epic']} saved successfully.")
    return True

def fetch_and_save_market_details(epic):
    """Fetch market details from the API and save to the database."""
    url = f"https://api.example.com/market_details/{epic}"  # Replace with actual API URL
    response = requests.get(url)
    response.raise_for_status()
    market_data = response.json()
    save_market_data(**market_data)
    return True