-- Schema updates for AI trading features
-- This file contains ALTER statements to add AI-related columns to existing tables

-- Add volatility regime columns to signals table
ALTER TABLE signals ADD COLUMN volatility_regime INTEGER;
ALTER TABLE signals ADD COLUMN volatility_level TEXT;
ALTER TABLE signals ADD COLUMN ai_enhanced BOOLEAN DEFAULT 0;
ALTER TABLE signals ADD COLUMN ai_metadata TEXT;
ALTER TABLE signals ADD COLUMN original_position_size REAL;
ALTER TABLE signals ADD COLUMN original_stop_loss REAL;

-- Add indices for AI-related columns
CREATE INDEX IF NOT EXISTS idx_signals_volatility_regime ON signals(volatility_regime);
CREATE INDEX IF NOT EXISTS idx_signals_ai_enhanced ON signals(ai_enhanced);

-- Add risk management columns to positions table
ALTER TABLE positions ADD COLUMN risk_level TEXT;
ALTER TABLE positions ADD COLUMN drawdown_at_entry REAL;
ALTER TABLE positions ADD COLUMN max_drawdown_during REAL;
ALTER TABLE positions ADD COLUMN ai_adjusted BOOLEAN DEFAULT 0;
ALTER TABLE positions ADD COLUMN original_size REAL;
ALTER TABLE positions ADD COLUMN size_adjustment_factor REAL;

-- Create market_volatility table if it doesn't exist
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
);

-- Create volatility_regimes table if it doesn't exist
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
);

-- Create position_sizing table if it doesn't exist
CREATE TABLE IF NOT EXISTS position_sizing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    signal_id INTEGER,
    symbol TEXT,
    original_size REAL,
    adjusted_size REAL,
    account_balance REAL,
    risk_amount REAL,
    risk_percent REAL,
    volatility_regime INTEGER,
    volatility_level TEXT,
    recent_performance REAL,
    risk_adjustment_factor REAL,
    sizing_data TEXT,
    FOREIGN KEY(signal_id) REFERENCES signals(id)
);

-- Create risk_metrics table if it doesn't exist
CREATE TABLE IF NOT EXISTS risk_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    account_id INTEGER,
    daily_risk_used REAL DEFAULT 0.0,
    open_risk REAL DEFAULT 0.0,
    drawdown_percent REAL DEFAULT 0.0,
    max_correlated_exposure REAL DEFAULT 0.0,
    risk_status TEXT DEFAULT 'NORMAL',
    risk_data TEXT
);

-- Create market_correlations table if it doesn't exist
CREATE TABLE IF NOT EXISTS market_correlations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    symbol1 TEXT NOT NULL,
    symbol2 TEXT NOT NULL,
    correlation_90d REAL,
    correlation_30d REAL,
    correlation_7d REAL,
    UNIQUE(symbol1, symbol2)
);

-- Create account_balances table if it doesn't exist
CREATE TABLE IF NOT EXISTS account_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    account_id INTEGER NOT NULL,
    balance REAL NOT NULL,
    equity REAL NOT NULL,
    margin_used REAL,
    peak_balance REAL,
    max_drawdown REAL,
    drawdown_percent REAL,
    source TEXT DEFAULT 'API'
);

-- Create indices for new tables
CREATE INDEX IF NOT EXISTS idx_market_volatility_symbol ON market_volatility(symbol);
CREATE INDEX IF NOT EXISTS idx_market_volatility_timestamp ON market_volatility(timestamp);
CREATE INDEX IF NOT EXISTS idx_volatility_regimes_symbol ON volatility_regimes(symbol);
CREATE INDEX IF NOT EXISTS idx_position_sizing_signal_id ON position_sizing(signal_id);
CREATE INDEX IF NOT EXISTS idx_position_sizing_symbol ON position_sizing(symbol);
CREATE INDEX IF NOT EXISTS idx_risk_metrics_account_id ON risk_metrics(account_id);
CREATE INDEX IF NOT EXISTS idx_risk_metrics_timestamp ON risk_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_correlations_symbols ON market_correlations(symbol1, symbol2);
CREATE INDEX IF NOT EXISTS idx_account_balances_account_id ON account_balances(account_id);
CREATE INDEX IF NOT EXISTS idx_account_balances_timestamp ON account_balances(timestamp);
