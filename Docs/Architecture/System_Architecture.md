# System Architecture

This document provides an overview of the Jamso AI Server architecture.

## Overview

The Jamso AI Server is a comprehensive platform for automated trading with Capital.com, consisting of several main components:

1. **Backend API Server** - Handles webhook requests and executes trades
2. **Dashboard** - Web interface for monitoring and configuration
3. **Database** - Stores trading data, signals, and user information
4. **Capital.com Integration** - API integration with Capital.com
5. **Authentication System** - User authentication and role management

## Component Relationships

The system is designed with the following relationships between components:

- **Backend API Server** receives webhook signals and processes them through the Capital.com API
- **Dashboard** provides a web interface to the system, displaying data from the database
- **Database** serves as the central storage for all system data
- **Authentication System** manages user access across all components

## Deployment Architecture

The system is designed to be deployed:
- As a standalone server on Linux
- With a reverse proxy for HTTPS termination
- With database support for both SQLite (default) and SQL Server

## Security Architecture

Security is implemented through multiple layers:
- HTTPS for all external communications
- API key authentication for webhook endpoints
- Role-based access control for the dashboard
- Encrypted storage of credentials
- Session management for web interface

## Data Flow

1. Trading signals enter the system via webhooks
2. Signals are validated and processed
3. Trade orders are placed via the Capital.com API
4. Trade results are stored in the database
5. Dashboard displays real-time updates
