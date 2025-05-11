#!/usr/bin/env python3
"""
Database initialization script that detects database type and uses the appropriate schema.
"""
import os
import sys
import argparse
import importlib.util
import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_init')

def is_module_available(module_name):
    """Check if a module can be imported"""
    try:
        importlib.util.find_spec(module_name)
        return True
    except ImportError:
        return False

def is_module_usable(module_name):
    """Check if a module can be imported and used"""
    if not is_module_available(module_name):
        return False
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False

def init_sqlite_db(schema_file, db_file):
    """Initialize SQLite database from schema file"""
    logger.info(f"Initializing SQLite database at {db_file} using schema {schema_file}")
    
    # Create parent directory if it doesn't exist
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Read schema SQL
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Connect to database and execute schema
        conn = sqlite3.connect(db_file)
        conn.executescript(schema_sql)
        conn.commit()
        
        # Verify tables were created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Created {len(tables)} tables in SQLite database: {', '.join([t[0] for t in tables])}")
        
        conn.close()
        logger.info(f"SQLite database initialization successful at {db_file}")
        return True
    except Exception as e:
        logger.error(f"SQLite initialization error: {str(e)}")
        return False

def init_mssql_db(schema_file, connection_string):
    """Initialize Microsoft SQL Server database from schema file"""
    logger.info(f"Initializing SQL Server database using schema {schema_file}")
    
    try:
        # Check if pyodbc is available
        if not is_module_available('pyodbc'):
            logger.error("pyodbc module not found.")
            logger.error("To install pyodbc, you need to:")
            logger.error("1. Install system dependencies: sudo apt-get install -y unixodbc-dev")
            logger.error("2. Install the Python package: pip install pyodbc")
            logger.error("Falling back to SQLite for now.")
            return False
        
        # Try to import pyodbc to check for system dependencies
        try:
            import pyodbc
        except ImportError as e:
            if "libodbc.so.2" in str(e):
                logger.error("System dependencies for pyodbc are missing.")
                logger.error("The error was: " + str(e))
                logger.error("To fix this, run: sudo apt-get install -y unixodbc unixodbc-dev")
                logger.error("Falling back to SQLite.")
                return False
            else:
                logger.error("Could not import pyodbc: " + str(e))
                logger.error("Falling back to SQLite.")
                return False
        
        # Read schema SQL
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Connect to the SQL Server
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Split by GO statements if present (common in T-SQL scripts)
        statements = schema_sql.split('GO')
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)
        
        conn.commit()
        logger.info("SQL Server database initialization successful")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"SQL Server initialization error: {str(e)}")
        return False

def detect_and_init_db():
    """Detect database type and initialize with appropriate schema"""
    # Default paths
    base_dir = Path(__file__).resolve().parent
    sqlite_schema = base_dir / "schema.sqlite.sql"
    mssql_schema = base_dir / "schema.sql"
    sqlite_db_file = base_dir / "Webhook" / "trading_signals.db"
    
    # Check for SQL Server environment variables
    mssql_conn_str = os.environ.get('MSSQL_CONNECTION_STRING')
    use_mssql = os.environ.get('USE_MSSQL', 'false').lower() == 'true'
    
    # Verify schemas exist
    if not os.path.exists(sqlite_schema):
        logger.error(f"SQLite schema file not found: {sqlite_schema}")
        # Fall back to trying the main schema file
        sqlite_schema = base_dir / "schema.sql"
        if not os.path.exists(sqlite_schema):
            logger.error(f"No schema file found at {sqlite_schema}")
            return False
    
    # Determine which database type to use
    if use_mssql and mssql_conn_str:
        logger.info("Using Microsoft SQL Server as database")
        
        # Check if MS SQL schema exists
        if not os.path.exists(mssql_schema):
            logger.error(f"SQL Server schema file not found: {mssql_schema}")
            logger.warning("Falling back to SQLite")
            return init_sqlite_db(sqlite_schema, sqlite_db_file)
            
        # Check if pyodbc is available and usable before attempting to initialize MS SQL
        if not is_module_available('pyodbc'):
            logger.error("pyodbc module not found but MS SQL Server is requested.")
            logger.error("To install pyodbc, you need to:")
            logger.error("1. Install system dependencies: sudo apt-get install -y unixodbc-dev")
            logger.error("2. Install the Python package: pip install pyodbc")
            
            # In interactive mode, ask user if they want to continue with SQLite
            use_sqlite_instead = True
            if 'INTERACTIVE' in globals() and INTERACTIVE:
                use_sqlite_instead = input("Do you want to use SQLite instead? (Y/n): ").strip().lower() != 'n'
            
            if use_sqlite_instead:
                logger.warning("Falling back to SQLite")
                return init_sqlite_db(sqlite_schema, sqlite_db_file)
            else:
                logger.error("Aborting database initialization")
                return False
        elif not is_module_usable('pyodbc'):
            logger.error("pyodbc is installed but cannot be imported.")
            logger.error("This is likely due to missing system dependencies.")
            logger.error("To fix this, install the required system packages:")
            logger.error("   sudo apt-get install -y unixodbc-dev")
            
            # In interactive mode, ask user if they want to continue with SQLite
            use_sqlite_instead = True
            if 'INTERACTIVE' in globals() and INTERACTIVE:
                use_sqlite_instead = input("Do you want to use SQLite instead? (Y/n): ").strip().lower() != 'n'
            
            if use_sqlite_instead:
                logger.warning("Falling back to SQLite")
                return init_sqlite_db(sqlite_schema, sqlite_db_file)
            else:
                logger.error("Aborting database initialization")
                return False
        
        # Try to initialize MS SQL
        mssql_result = init_mssql_db(mssql_schema, mssql_conn_str)
        
        # If MS SQL initialization fails, offer to fall back to SQLite
        if not mssql_result:
            logger.error("Failed to initialize MS SQL Server database")
            
            # In interactive mode, ask user if they want to continue with SQLite
            use_sqlite_instead = True
            if 'INTERACTIVE' in globals() and INTERACTIVE:
                use_sqlite_instead = input("Do you want to use SQLite instead? (Y/n): ").strip().lower() != 'n'
            
            if use_sqlite_instead:
                logger.warning("Falling back to SQLite")
                return init_sqlite_db(sqlite_schema, sqlite_db_file)
            else:
                logger.error("Aborting database initialization")
                return False
                
        return mssql_result
    else:
        logger.info("Using SQLite as database")
        return init_sqlite_db(sqlite_schema, sqlite_db_file)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Initialize database for Jamso AI Server")
    parser.add_argument("--non-interactive", action="store_true", 
                        help="Run in non-interactive mode (no prompts)")
    parser.add_argument("--force-sqlite", action="store_true", 
                        help="Force using SQLite regardless of environment settings")
    args = parser.parse_args()
    
    logger.info("Starting database initialization")
    
    # Check for non-interactive mode flag from args or environment
    noninteractive = args.non_interactive or os.environ.get('NONINTERACTIVE', 'false').lower() == 'true'
    
    # Handle force-sqlite flag
    if args.force_sqlite:
        logger.info("Forcing SQLite database use as requested")
        os.environ['USE_MSSQL'] = 'false'
    
    # If in non-interactive mode, set USE_MSSQL to false if pyodbc is not available
    if noninteractive and os.environ.get('USE_MSSQL', 'false').lower() == 'true':
        if not is_module_available('pyodbc'):
            logger.warning("Running in non-interactive mode and pyodbc is not available.")
            logger.warning("Setting USE_MSSQL=false to fall back to SQLite")
            os.environ['USE_MSSQL'] = 'false'
    
    # Set a global flag for interactive prompts
    global INTERACTIVE
    INTERACTIVE = not noninteractive
    
    success = detect_and_init_db()
    if success:
        logger.info("Database initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("Database initialization failed")
        sys.exit(1)
