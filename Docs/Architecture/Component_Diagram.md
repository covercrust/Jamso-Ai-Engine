# Component Diagram

This document provides a component diagram and explanation of the Jamso AI Server system.

```
┌───────────────────────────────────────────────────────────────┐
│                      Jamso AI Server                          │
│                                                               │
│  ┌─────────────┐      ┌─────────────┐     ┌───────────────┐   │
│  │             │      │             │     │               │   │
│  │   Webhook   │      │  Dashboard  │     │  Database     │   │
│  │   Server    │──────┤   Server    │─────┤  (SQLite/     │   │
│  │             │      │             │     │   SQL Server) │   │
│  └──────┬──────┘      └──────┬──────┘     └───────────────┘   │
│         │                    │                                 │
│         │                    │                                 │
│  ┌──────▼──────┐      ┌──────▼──────┐                         │
│  │             │      │             │                         │
│  │ Capital.com │      │   User      │                         │
│  │ API Client  │      │ Management  │                         │
│  │             │      │             │                         │
│  └─────────────┘      └─────────────┘                         │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Key Components

### Webhook Server
- Receives trading signals from external systems
- Validates and processes incoming requests
- Forwards validated signals to the trading system

### Dashboard Server
- Provides web interface for system management
- Displays trading activity and system status
- Manages user authentication and permissions

### Database
- Stores trading data, system configuration, and user information
- Supports both SQLite (default) and SQL Server

### Capital.com API Client
- Handles communication with Capital.com trading platform
- Manages authentication with Capital.com
- Executes trades and monitors positions

### User Management
- Handles user authentication and authorization
- Manages role-based access control
- Provides user administration capabilities

## Communication Flow

1. External systems send trading signals to the Webhook Server
2. Webhook Server validates signals and passes them to the Capital.com API Client
3. Capital.com API Client executes trades on the trading platform
4. Results are stored in the Database
5. Dashboard Server retrieves data from the Database and displays it to users
6. User Management controls access to the Dashboard Server
