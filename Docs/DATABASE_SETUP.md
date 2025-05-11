# Database Setup Guide

This document provides guidance on setting up and connecting to databases for the Jamso AI Server.

## Database Support

The Jamso AI Server primarily uses SQLite for its database needs, but it can also be configured to use Microsoft SQL Server.

### Database Structure

The system uses two separate databases:

1. **Trading Database**: Stores trading data, signals, and positions
2. **Credentials Database**: Stores encrypted API keys and sensitive information

### SQLite (Default)

SQLite is used by default and requires no additional configuration. The database files are stored in:

- `/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db` (Trading data)
- `/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Credentials/credentials.db` (Credentials)

### Microsoft SQL Server

To use Microsoft SQL Server, you need to:

1. Install the required Python package:

   ```bash
   pip install pyodbc
   ```

2. Set the following environment variables in your `src/Credentials/env.sh`:

   ```bash
   export USE_MSSQL="true"
   export MSSQL_CONNECTION_STRING="Driver={ODBC Driver 17 for SQL Server};Server=yourserver.database.windows.net;Database=yourdatabase;Uid=yourusername;Pwd=yourpassword;"
   ```

3. Run the database initialization script:

   ```bash
   cd /home/jamso-ai-server/Jamso-Ai-Engine/src/Database
   ./init_db.py
   ```

## SQL Dialect Differences

The project now maintains separate schema files for each database type:

- For SQLite:
  - `schema.sqlite.sql`: Main database schema
  - `Credentials/schema.sqlite.sql`: Credentials database schema

- For SQL Server:
  - `schema.sql`: Main database schema
  - `schema_mssql.sql`: Backup/legacy SQL Server schema
  - `Credentials/schema.sql`: Credentials database schema

### Converting Between Schemas

Use the `convert_schema.py` script to convert between SQLite and SQL Server formats:

```bash
# Convert SQL Server to SQLite
python3 convert_schema.py schema.sql --to-sqlite -o schema.sqlite.sql

# Convert SQLite to SQL Server
python3 convert_schema.py schema.sqlite.sql -o schema.sql
```

### Common Error: "Incorrect syntax near ','. Expecting ID, QUOTED_ID, STRING, or TEXT_LEX"

This error occurs when a file marked for SQL Server use contains SQLite syntax. Make sure you're using the correct schema file for your database system:

- For SQLite, use `*.sqlite.sql` files
- For SQL Server, use `*.sql` files (not including `*.sqlite.sql`)

## Validating Schema Files

To validate a schema file without applying it to a database, use the validation script:

```bash
cd /home/jamso-ai-server/Jamso-Ai-Engine/src/Database
./validate_schema.py schema.sql        # For SQLite
./validate_schema.py schema_mssql.sql  # For SQL Server (if pyodbc is installed)
```

## Manual Database Initialization

If you need to manually initialize the database:

### For SQLite

```bash
sqlite3 /home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db < /home/jamso-ai-server/Jamso-Ai-Engine/src/Database/schema.sql
```

### For SQL Server

Use SQL Server Management Studio or the sqlcmd utility to execute the `schema_mssql.sql` file.

## Backup and Restore

### SQLite Backup

```bash
sqlite3 /home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db .dump > backup.sql
```

### SQLite Restore

```bash
sqlite3 /home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db < backup.sql
```

For SQL Server, use standard backup and restore procedures or export/import tools.
