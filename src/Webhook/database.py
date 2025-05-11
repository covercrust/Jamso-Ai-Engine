import sqlite3
import logging
from flask import g

logger = logging.getLogger(__name__)
DATABASE = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'

def get_db():
    """Connects to the SQLite database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_connection(exception):
    """Closes the database connection after each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db(app):
    """Initializes the database with webhook tables."""
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                order_id TEXT,
                deal_id TEXT,
                symbol TEXT,
                direction TEXT,
                quantity REAL,
                price REAL,
                signal_data TEXT,
                status TEXT DEFAULT 'pending',
                error TEXT,
                position_status TEXT DEFAULT 'open',
                trade_action TEXT,
                trade_direction TEXT,
                position_size REAL,
                hedging_enabled BOOLEAN DEFAULT 0
            )
        ''')
        db.commit()
    app.teardown_appcontext(close_connection)

def save_signal(signal_data):
    """Save incoming trading signal."""
    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO signals (order_id, symbol, direction, quantity, price, signal_data, trade_action, trade_direction, position_size) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                signal_data.get('order_id'),
                signal_data.get('ticker') or signal_data.get('symbol'),
                signal_data.get('direction') or signal_data.get('order_action'),
                signal_data.get('quantity') or signal_data.get('position_size'),
                signal_data.get('price'),
                str(signal_data),
                signal_data.get('trade_action') or signal_data.get('order_action'),
                signal_data.get('trade_direction') or signal_data.get('direction'),
                signal_data.get('position_size') or signal_data.get('quantity')
            )
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise