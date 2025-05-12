# Jamso AI Server Documentation

This directory contains centralized documentation for the Jamso AI Server platform.

## Table of Contents

1. [Getting Started](#getting-started)

2. [Architecture](#architecture)

3. [User Guide](#user-guide)

4. [API Reference](#api-reference)

5. [Development Guide](#development-guide)

6. [Database](#database)

7. [Trading](#trading)

8. [Recent Improvements](#recent-improvements)

## Getting Started

- [Setup Guide](./Setup_Guide.md) - Instructions for setting up the server

- [Permissions Guide](./Permissions_Guide.md) - File and directory permissions

## Architecture

- [System Architecture](./Architecture/System_Architecture.md) - Overview of the system architecture

- [Component Diagram](./Architecture/Component_Diagram.md) - Diagram of system components

## User Guide

- [Dashboard Guide](./User_Guide/Dashboard.md) - How to use the dashboard

- [Account Management](./User_Guide/Account_Management.md) - Managing trading accounts

- [User Roles and Permissions](./User_Guide/User_Roles.md) - User role system explanation

## API Reference

- [API Endpoints](./API/endpoints.md) - Webhook API endpoints

- [Authentication](./API/Authentication.md) - API authentication methods

## Development Guide

- [Project Structure](./Development/Project_Structure.md) - Overview of the codebase organization

- [Contributing Guidelines](./Development/Contributing.md) - Guidelines for contributors

## Database

- [Database Setup](./Database/Setup.md) - Database configuration

- [Schema Reference](./Database/Schema.md) - Database schema documentation

- [Database Architecture](./Database/Database_Architecture.md) - Explanation of the dual-database architecture

## Trading

- [Trading Roadmap](./Trading_Roadmap.md) - Development roadmap for trading features

- [Pine Script Reference](./Pine_Script_V6_Manual.md) - Pine Script documentation

## Recent Improvements

### Security Enhancements

- All session-related configurations now load from environment variables.

- Secure cookie settings enforced via environment variables.

- Added `.env.example` to document required environment variables.

### Accessibility Improvements

- Enhanced `login.html` and `reset_password.html` templates with ARIA roles and labels.

- Improved usability with client-side validation and better form instructions.

### Codebase Enhancements

- Improved logging and error handling in `dashboard_integration.py`.

- Patched session interface for Python 3.12 compatibility.

- Optimized database initialization and admin user setup.

### Documentation Updates

- Updated `Setup_Guide.md` and `Security_Config_Update_Log.md` to reflect recent changes.
