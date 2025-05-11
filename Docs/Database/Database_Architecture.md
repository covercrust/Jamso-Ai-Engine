# Database Architecture

This document explains the database architecture of the Jamso AI Server.

## Database Structure

The Jamso AI Server utilizes a dual-database approach for improved security and separation of concerns:

1. **Main Database (trading_signals.db)**
   - Contains trading-related data
   - Located at `/src/Database/Webhook/trading_signals.db`
   - Schema defined in `/src/Database/schema.sql`

2. **Credentials Database (credentials.db)**
   - Contains sensitive credential information with encryption
   - Located at `/src/Database/Credentials/credentials.db`
   - Schema defined in `/src/Database/Credentials/schema.sql`

## Database Type Support

Each database supports both SQLite and Microsoft SQL Server:

- **SQLite** (Default): Used for development, testing, and smaller deployments
- **SQL Server**: Used for production and larger-scale deployments

## Schema Files

There are multiple schema files in the project:

1. **For the main trading database:**
   - `schema.sql`: SQL Server version of the main schema - this is a SQL Server (T-SQL) file
   - `schema.sqlite.sql`: SQLite version of the main schema for development use
   - `schema_mssql.sql`: Legacy SQL Server schema file - use this only if `schema.sql` causes issues with SQL Server

2. **For the credentials database:**
   - `Credentials/schema.sql`: SQL Server version of the credentials schema
   - `Credentials/schema.sqlite.sql`: SQLite version of the credentials schema for development use

## Schema Conversion Tool

A Python script is provided to help convert between SQLite and SQL Server schemas:

```bash
# Convert from SQL Server to SQLite
python3 convert_schema.py schema.sql --to-sqlite -o schema.sqlite.sql

# Convert from SQLite to SQL Server
python3 convert_schema.py schema.sqlite.sql -o schema.sql
```

### Usage Instructions

The tool accepts the following arguments:

- `input_file`: Path to the schema file to convert
- `--output` or `-o`: Output file path (defaults to input_file.converted)
- `--to-sqlite`: Convert from SQL Server to SQLite (default is SQLite to SQL Server)

## File Ownership

Schema files owned by "mssql" will be used with the SQL Server database and must use valid T-SQL syntax. The error "Incorrect syntax near ','. Expecting ID, QUOTED_ID, STRING, or TEXT_LEX" indicates a syntax issue where SQLite syntax is being used in a file that needs SQL Server syntax.

## Initialization Process

- Main database: Initialized through `src/Database/init_db.py`
- Credentials database: Initialized by the `CredentialManager` class (`src/Credentials/credential_manager.py`)

## Accessing Databases

- Main database: Direct access via SQLite/SQL Server connection
- Credentials database: Accessed through the `CredentialManager` class, which handles encryption/decryption

## Security Considerations

1. Sensitive data (API keys, passwords) is stored in the credentials database
2. The `CredentialManager` provides encryption for sensitive values
3. Role-based access control is implemented for credential access
4. Audit logging tracks all credential access and modifications

## Backup and Recovery

Both databases should be included in backup procedures:

- `/src/Database/Webhook/trading_signals.db`
- `/src/Database/Credentials/credentials.db`
