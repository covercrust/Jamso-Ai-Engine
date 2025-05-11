# Database Setup

This document explains how to set up and configure the database for Jamso AI Server.

## Supported Database Systems

The Jamso AI Server supports two database systems:

1. **SQLite** (Default): A file-based database, ideal for small to medium installations
2. **Microsoft SQL Server**: For larger installations requiring more robust database capabilities

## SQLite Setup (Default)

SQLite is the default database system and requires minimal setup:

### Database Location

SQLite database files are stored in the following locations:

- `/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db` - Trading data
- `/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Users/users.db` - User authentication data

### SQLite Initialization

To initialize or reset the SQLite database:

```bash
cd /home/jamso-ai-server/Jamso-Ai-Engine/src/Database
python init_db.py
```

This will create the necessary tables defined in `schema.sql`.

### Manual Initialization

You can also manually initialize the database:

```bash
cd /home/jamso-ai-server/Jamso-Ai-Engine/src/Database
sqlite3 /home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db < schema.sql
```

## Microsoft SQL Server Setup

For larger installations, Microsoft SQL Server provides more robust database capabilities:

### Prerequisites

Install the required Python package:

```bash
pip install pyodbc
```

### Configuration

1. Create a new database in your SQL Server instance
2. Set the following environment variables in `src/Credentials/env.sh`:

```bash
export USE_MSSQL="true"
export MSSQL_CONNECTION_STRING="Driver={ODBC Driver 17 for SQL Server};Server=yourserver.database.windows.net;Database=yourdatabase;Uid=yourusername;Pwd=yourpassword;"
```

### SQL Server Initialization

Initialize the SQL Server database:

```bash
cd /home/jamso-ai-server/Jamso-Ai-Engine/src/Database
python init_db.py
```

The system will detect that SQL Server is configured and use `schema_mssql.sql` instead of `schema.sql`.

## Backup and Restore

### SQLite Backup

To backup the SQLite database:

```bash
sqlite3 /home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db .dump > backup.sql
```

### SQLite Restore

To restore from a backup:

```bash
sqlite3 /home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db < backup.sql
```

### SQL Server Backup

Use standard SQL Server backup procedures or:

```bash
cd /home/jamso-ai-server/Jamso-Ai-EngineTools/fix_permissions.sh
python backup_mssql.py
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure the application has write permissions to the database files and directories
2. **Database Locked**: Another process may be accessing the SQLite database
3. **Connection Failed**: Check your SQL Server connection string
4. **Schema Errors**: Ensure you're using the correct schema file for your database system

### Validation

To validate schema files without applying them:

```bash
cd /home/jamso-ai-server/Jamso-Ai-Engine/src/Database
python validate_schema.py schema.sql        # For SQLite
python validate_schema.py schema_mssql.sql  # For SQL Server
```

## Migration

To migrate from SQLite to SQL Server:

1. Backup your SQLite database
2. Configure SQL Server environment variables
3. Run the migration script:

```bash
cd /home/jamso-ai-server/Jamso-Ai-EngineTools/fix_permissions.sh
python migrate_sqlite_to_mssql.py
```
