# Database Schema

This document provides a detailed reference of the Jamso AI Server database schema.

## Overview

The Jamso AI Server uses SQLite by default but can be configured to use Microsoft SQL Server. The database stores trading signals, positions, user information, and system configuration.

## Schema Diagram

```
┌────────────────┐       ┌────────────────┐       ┌────────────────┐
│    signals     │       │   positions    │       │    users       │
├────────────────┤       ├────────────────┤       ├────────────────┤
│ id             │       │ id             │       │ id             │
│ order_id       │──┐    │ signal_id      │───┐   │ username       │
│ symbol         │  │    │ deal_id        │   │   │ password_hash  │
│ direction      │  │    │ symbol         │   │   │ email          │
│ quantity       │  │    │ direction      │   │   │ role           │
│ price          │  │    │ size           │   │   │ api_key        │
│ status         │  │    │ entry_price    │   │   │ created_at     │
│ error          │  │    │ status         │   │   │ last_login     │
│ position_status│  │    │ exit_price     │   │   └────────────────┘
│ trade_action   │  │    │ profit_loss    │   │            │
│ trade_direction│  │    │ exit_timestamp │   │            │
│ position_size  │  │    │ timestamp      │   │            │
│ hedging_enabled│  │    └────────┬───────┘   │            │
│ deal_id        │<─┘             │           │            │
│ signal_data    │                │           │   ┌────────▼───────┐
│ timestamp      │<───────────────┘           │   │ user_api_keys   │
└────────────────┘                            │   ├────────────────┤
                                              │   │ id             │
┌────────────────┐                            │   │ user_id        │
│   api_tokens   │                            │   │ capital_key    │
├────────────────┤                            │   │ capital_secret │
│ id             │                            │   │ capital_demo   │
│ user_id        │───────────────────────────┘   │ webhook_key    │
│ token          │                                │ created_at     │
│ description    │                                │ updated_at     │
│ created_at     │                                └────────────────┘
│ expires_at     │
│ last_used      │
└────────────────┘
```

## Table Definitions

### signals

Stores incoming trading signals:

| Column           | Type       | Description                             |
|------------------|-----------|-----------------------------------------|
| id               | INTEGER    | Primary key                             |
| order_id         | TEXT      | Unique order identifier                  |
| symbol           | TEXT      | Trading symbol (e.g., BTC/USD)           |
| direction        | TEXT      | BUY or SELL                              |
| quantity         | REAL      | Trading quantity                         |
| price            | REAL      | Signal price                             |
| status           | TEXT      | Signal status (pending, processed, etc.) |
| error            | TEXT      | Error message if processing failed       |
| position_status  | TEXT      | Associated position status               |
| trade_action     | TEXT      | Action to take (open, close, modify)     |
| trade_direction  | TEXT      | Trading direction                        |
| position_size    | REAL      | Size of the position                     |
| hedging_enabled  | BOOLEAN   | Whether hedging is enabled               |
| deal_id          | TEXT      | Associated deal ID                       |
| signal_data      | TEXT      | Additional JSON signal data              |
| timestamp        | DATETIME  | Signal timestamp                         |

### positions

Stores trading positions:

| Column         | Type       | Description                           |
|----------------|-----------|---------------------------------------|
| id             | INTEGER    | Primary key                           |
| signal_id      | INTEGER    | Foreign key to signals.id             |
| deal_id        | TEXT      | Unique deal identifier                |
| symbol         | TEXT      | Trading symbol                        |
| direction      | TEXT      | Position direction (BUY or SELL)      |
| size           | REAL      | Position size                         |
| entry_price    | REAL      | Entry price                           |
| status         | TEXT      | Position status (open, closed)        |
| exit_price     | REAL      | Exit price (if closed)                |
| profit_loss    | REAL      | Profit or loss amount                 |
| exit_timestamp | DATETIME  | When position was closed              |
| timestamp      | DATETIME  | When position was opened              |

### users

Stores user information:

| Column        | Type       | Description                    |
|---------------|-----------|--------------------------------|
| id            | INTEGER    | Primary key                    |
| username      | TEXT      | Unique username                |
| password_hash | TEXT      | Hashed password                |
| email         | TEXT      | User email                     |
| role          | TEXT      | User role (admin, user, viewer)|
| api_key       | TEXT      | User API key                   |
| created_at    | DATETIME  | Account creation timestamp     |
| last_login    | DATETIME  | Last login timestamp           |

### user_api_keys

Stores user API keys:

| Column         | Type       | Description                    |
|----------------|-----------|--------------------------------|
| id             | INTEGER    | Primary key                    |
| user_id        | INTEGER    | Foreign key to users.id        |
| capital_key    | TEXT      | Capital.com API key            |
| capital_secret | TEXT      | Capital.com API secret         |
| capital_demo   | BOOLEAN   | Whether using demo environment  |
| webhook_key    | TEXT      | Webhook authentication key     |
| created_at     | DATETIME  | Creation timestamp             |
| updated_at     | DATETIME  | Last update timestamp          |

### api_tokens

Stores API authentication tokens:

| Column      | Type       | Description                    |
|-------------|-----------|--------------------------------|
| id          | INTEGER    | Primary key                    |
| user_id     | INTEGER    | Foreign key to users.id        |
| token       | TEXT      | Authentication token           |
| description | TEXT      | Token description              |
| created_at  | DATETIME  | Creation timestamp             |
| expires_at  | DATETIME  | Expiration timestamp           |
| last_used   | DATETIME  | Last used timestamp            |

## Indices

The following indices are used to optimize database performance:

- idx_signals_order_id: Primary lookup for signals by order_id
- idx_positions_deal_id: Primary lookup for positions by deal_id
- idx_signals_timestamp: Query signals by timestamp (descending)
- idx_signals_symbol: Query signals by trading symbol
- idx_signals_status: Query signals by status
- idx_positions_signal_id: Join positions with signals
- idx_positions_symbol: Query positions by trading symbol
- idx_positions_status: Query positions by status
- idx_positions_timestamp: Query positions by timestamp
- idx_user_api_keys_user_id: Join user_api_keys with users

## Relationships

- signals → positions: One-to-one relationship via signal_id
- users → user_api_keys: One-to-one relationship via user_id 
- users → api_tokens: One-to-many relationship via user_id
