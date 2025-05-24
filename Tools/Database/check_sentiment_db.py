#!/usr/bin/env python3
import sqlite3
import os

# Path for sentiment database
db_path = os.path.join("/home/jamso-ai-server/Jamso-Ai-Engine", "src", "Database", "Sentiment", "sentiment_data.db")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get total count of BTCUSD entries
cursor.execute('SELECT COUNT(*) FROM sentiment_data WHERE symbol="BTCUSD"')
total_count = cursor.fetchone()[0]
print(f'Total BTCUSD entries: {total_count}')

# Get count by source
cursor.execute('SELECT source, COUNT(*) FROM sentiment_data WHERE symbol="BTCUSD" GROUP BY source')
print('Entries by source:')
for row in cursor.fetchall():
    print(f'- {row[0]}: {row[1]}')

# Get date range
cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM sentiment_data WHERE symbol="BTCUSD"')
date_range = cursor.fetchone()
print(f'Date range: {date_range[0]} to {date_range[1]}')

conn.close()
