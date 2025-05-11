IF OBJECT_ID('signals', 'U') IS NOT NULL DROP TABLE signals;
IF OBJECT_ID('positions', 'U') IS NOT NULL DROP TABLE positions;
IF OBJECT_ID('user_api_keys', 'U') IS NOT NULL DROP TABLE user_api_keys;

CREATE TABLE signals (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id NVARCHAR(255) UNIQUE,
    symbol NVARCHAR(50) NOT NULL,
    direction NVARCHAR(10) NOT NULL, 
    quantity FLOAT NOT NULL,
    price FLOAT NOT NULL,
    status NVARCHAR(50) DEFAULT 'pending',
    error NVARCHAR(MAX),
    position_status NVARCHAR(50),
    trade_action NVARCHAR(50),
    trade_direction NVARCHAR(10),
    position_size FLOAT,
    hedging_enabled BIT DEFAULT 0,
    deal_id NVARCHAR(255),
    signal_data NVARCHAR(MAX),
    timestamp DATETIME DEFAULT GETDATE()
);

CREATE TABLE positions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    signal_id INT,
    deal_id NVARCHAR(255) UNIQUE,
    symbol NVARCHAR(50) NOT NULL,
    direction NVARCHAR(10) NOT NULL,
    size FLOAT NOT NULL,
    entry_price FLOAT NOT NULL,
    status NVARCHAR(50) DEFAULT 'open',
    exit_price FLOAT,
    profit_loss FLOAT,
    exit_timestamp DATETIME,
    timestamp DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_positions_signals FOREIGN KEY (signal_id) REFERENCES signals (id)
);

-- User API keys table
CREATE TABLE user_api_keys (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    capital_key NVARCHAR(255),
    capital_secret NVARCHAR(255),
    capital_demo BIT DEFAULT 1,
    webhook_key NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_user_api_keys_user_id UNIQUE(user_id)
);

-- Core indices for primary lookup fields
CREATE INDEX idx_signals_order_id ON signals(order_id);
CREATE INDEX idx_positions_deal_id ON positions(deal_id);

-- Additional indices for frequently queried fields
CREATE INDEX idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_position_status ON signals(position_status);
CREATE INDEX idx_signals_deal_id ON signals(deal_id);

CREATE INDEX idx_positions_signal_id ON positions(signal_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_timestamp ON positions(timestamp DESC);

-- Combined indices for common query patterns
CREATE INDEX idx_signals_symbol_direction ON signals(symbol, direction);
CREATE INDEX idx_positions_symbol_direction ON positions(symbol, direction);
CREATE INDEX idx_signals_status_timestamp ON signals(status, timestamp);
CREATE INDEX idx_positions_status_timestamp ON positions(status, timestamp);

-- Index for user_api_keys
CREATE INDEX idx_user_api_keys_user_id ON user_api_keys(user_id);

