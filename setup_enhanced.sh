#!/bin/bash
#
# Jamso AI Server - Enhanced Setup Script
# 
# This script automates the installation and setup process for Jamso AI Server.
# It performs the following tasks:
# - Provides a user-friendly menu interface
# - Checks for and installs Python dependencies
# - Creates a Python virtual environment
# - Installs required packages
# - Sets up necessary directories and configuration files
# - Configures the environment for deployment
# - Supports clean reinstallation
#
# Version: 2.0
# Last updated: May 25, 2025

# Set strict error handling
set -e

# Define color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
PYTHON_VERSION="3.13"
VENV_DIR=".venv"
MIN_PYTHON_VERSION="3.8"
RECOMMENDED_PYTHON_VERSION="3.13"
LOGS_DIR="Logs"
CONFIG_DIR="src/Credentials"
ENV_EXAMPLE="$CONFIG_DIR/env.sh.example"
ENV_FILE="$CONFIG_DIR/env.sh"
DATABASE_DIR="src/Database"
TMP_DIR="tmp"
RESTART_FILE="$TMP_DIR/restart.txt"

# Process command line arguments
NONINTERACTIVE=false
SKIP_PYTHON_CHECK=false
FORCE_RECREATE_VENV=false
INSTALL_DEV_DEPS=false
RECREATE_DB=false
SKIP_DB_INIT=false

# Create and set up log file for installation
mkdir -p "$LOGS_DIR"
INSTALL_LOG="$LOGS_DIR/setup_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    local msg="$1"
    local level="${2:-INFO}"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [$level] $msg" | tee -a "$INSTALL_LOG"
}

# Print banner
print_banner() {
    echo -e "${BLUE}${BOLD}"
    echo "================================================================"
    echo "                 JAMSO AI SERVER SETUP"
    echo "================================================================"
    echo -e "${NC}"
    echo "This script will set up the Jamso AI Server environment."
    echo "It will install Python dependencies, create a virtual environment,"
    echo "and configure the necessary components."
    echo ""
}

# Process command line arguments
process_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --non-interactive)
                NONINTERACTIVE=true
                shift
                ;;
            --skip-python-check)
                SKIP_PYTHON_CHECK=true
                shift
                ;;
            --force-recreate-venv)
                FORCE_RECREATE_VENV=true
                shift
                ;;
            --install-dev-deps)
                INSTALL_DEV_DEPS=true
                shift
                ;;
            --recreate-db)
                RECREATE_DB=true
                shift
                ;;
            --skip-db-init)
                SKIP_DB_INIT=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --non-interactive      Run in non-interactive mode without prompts"
                echo "  --skip-python-check    Skip Python version check"
                echo "  --force-recreate-venv  Force recreation of virtual environment"
                echo "  --install-dev-deps     Install development dependencies"
                echo "  --recreate-db          Recreate the database if it exists"
                echo "  --skip-db-init         Skip database initialization"
                echo "  --help                 Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Create necessary directories including the new structure
create_directories() {
    log_message "Creating necessary directories..."
    
    # Ensure Logs directory exists
    mkdir -p "$LOGS_DIR"
    
    # Create restart trigger directory
    mkdir -p "$TMP_DIR"
    
    # Create database directory
    mkdir -p "$DATABASE_DIR"
    
    # Ensure config directory exists
    mkdir -p "$CONFIG_DIR"
    
    # Create scripts directories
    mkdir -p "Scripts/Maintenance"
    mkdir -p "Scripts/Deployment"
    
    # Create Tools directories
    mkdir -p "Tools/Database"
    
    # Create Tests directories
    mkdir -p "Tests/Unit"
    mkdir -p "Tests/Integration"
    
    log_message "Directories created successfully."
}

# Check Python version
check_python_version() {
    if [ "$SKIP_PYTHON_CHECK" = true ]; then
        log_message "Skipping Python version check due to --skip-python-check flag"
        PYTHON_CMD="python3"
        return
    }

    log_message "Checking Python version..."
    
    # Check if python3 is installed
    if ! command -v python3 &> /dev/null; then
        log_message "Python 3 not found. Please install Python 3.8 or higher." "ERROR"
        exit 1
    }
    
    # Get installed Python version
    INSTALLED_PYTHON_VERSION=$(python3 --version | sed 's/Python //')
    
    # Function to compare version strings
    version_lt() {
        [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" = "$1" ]
    }
    
    # Check if Python version is sufficient
    if version_lt "$INSTALLED_PYTHON_VERSION" "$MIN_PYTHON_VERSION"; then
        log_message "Installed Python version ($INSTALLED_PYTHON_VERSION) is older than the minimum required version ($MIN_PYTHON_VERSION)." "ERROR"
        log_message "Please install Python $MIN_PYTHON_VERSION or higher." "ERROR"
        exit 1
    }
    
    # Check if Python version matches recommended
    if version_lt "$INSTALLED_PYTHON_VERSION" "$RECOMMENDED_PYTHON_VERSION"; then
        log_message "Installed Python version ($INSTALLED_PYTHON_VERSION) is older than the recommended version ($RECOMMENDED_PYTHON_VERSION)." "WARNING"
        if [ "$NONINTERACTIVE" = false ]; then
            read -p "Continue with Python $INSTALLED_PYTHON_VERSION? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_message "Setup aborted by user." "WARNING"
                exit 0
            fi
        else
            log_message "Continuing with Python $INSTALLED_PYTHON_VERSION in non-interactive mode"
        fi
    else
        log_message "Python $INSTALLED_PYTHON_VERSION detected. This meets the recommended version requirements."
    }
    
    # Determine actual Python command
    if command -v python$RECOMMENDED_PYTHON_VERSION &> /dev/null; then
        PYTHON_CMD="python$RECOMMENDED_PYTHON_VERSION"
    else
        PYTHON_CMD="python3"
    }
    
    log_message "Using Python command: $PYTHON_CMD"
}

# Set up virtual environment
setup_virtual_environment() {
    log_message "Setting up Python virtual environment..."
    
    # Check if virtual environment already exists
    if [ -d "$VENV_DIR" ]; then
        if [ "$FORCE_RECREATE_VENV" = true ]; then
            log_message "Force recreating virtual environment due to --force-recreate-venv flag"
            rm -rf "$VENV_DIR"
        elif [ "$NONINTERACTIVE" = false ]; then
            log_message "Virtual environment already exists. Do you want to recreate it?" "WARNING"
            read -p "Recreate virtual environment? This will delete the existing one. [y/N] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_message "Removing existing virtual environment..."
                rm -rf "$VENV_DIR"
            else
                log_message "Using existing virtual environment."
                return
            fi
        else
            log_message "Using existing virtual environment in non-interactive mode."
            return
        fi
    fi
    
    # Create virtual environment
    log_message "Creating new virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv "$VENV_DIR" || {
        log_message "Failed to create virtual environment. Make sure venv is installed." "ERROR"
        log_message "Try: sudo apt-get install python3-venv" "ERROR"
        exit 1
    }
    
    log_message "Virtual environment created successfully in $VENV_DIR"
    
    # Create activation script for easier activation in the future
    cat > "activate.sh" << 'EOF'
#!/bin/bash
# Helper script to activate the Python virtual environment
source .venv/bin/activate
echo "Virtual environment activated. Use 'deactivate' to exit."
EOF
    chmod +x activate.sh
    log_message "Created activation script: activate.sh"
    
    # Create activate_this.py script for passenger_wsgi.py
    mkdir -p "$VENV_DIR/bin"
    cat > "$VENV_DIR/bin/activate_this.py" << 'EOF'
"""Activate virtualenv for passenger_wsgi.py"""
import os
import sys
import site

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['VIRTUAL_ENV'] = base

# Add the virtual environments site-package to the path
site_packages = os.path.join(
    base, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages'
)
prev = set(sys.path)
site.addsitedir(site_packages)
sys.real_prefix = sys.prefix
sys.prefix = base
EOF
    log_message "Created activate_this.py script for passenger_wsgi.py"
}

# Install dependencies
install_dependencies() {
    log_message "Installing Python dependencies..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || {
        log_message "Failed to activate virtual environment." "ERROR"
        exit 1
    }
    
    # Upgrade pip to the latest version
    log_message "Upgrading pip to the latest version..."
    pip install --upgrade pip
    
    # Install wheel for better package installation
    log_message "Installing wheel..."
    pip install wheel
    
    # Install dependencies from requirements.txt
    log_message "Installing dependencies from requirements.txt..."
    if ! pip install -r requirements.txt; then
        log_message "Failed to install some dependencies. Check the log for details." "ERROR"
        log_message "You can try fixing the issues and running the script again."
        deactivate
        exit 1
    fi
    
    log_message "Dependencies installed successfully."
    
    # Check if development dependencies should be installed
    if [ "$INSTALL_DEV_DEPS" = true ]; then
        log_message "Installing development dependencies due to --install-dev-deps flag..."
        pip install pytest pytest-cov flake8 black isort mypy
        log_message "Development dependencies installed."
    elif [ "$NONINTERACTIVE" = false ]; then
        read -p "Install development dependencies (pytest, flake8, etc.)? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_message "Installing development dependencies..."
            pip install pytest pytest-cov flake8 black isort mypy
            log_message "Development dependencies installed."
        fi
    fi
    
    # Deactivate virtual environment
    deactivate
}

# Configure environment
configure_environment() {
    log_message "Configuring environment..."
    
    # Check if env.sh exists, if not create from example
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            log_message "Creating $ENV_FILE from example..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_message "Please update $ENV_FILE with your API credentials and configuration."
        else
            log_message "Creating basic $ENV_FILE..."
            mkdir -p "$(dirname "$ENV_FILE")"
            
            # Create a basic env.sh file
            cat > "$ENV_FILE" << 'EOF'
#!/bin/bash
# Environment variables for Jamso AI Server
export CAPITAL_API_KEY="your_api_key_here"
export CAPITAL_API_SECRET="your_api_secret_here"
export WEBHOOK_TOKEN="your_secure_webhook_token_here"
export ROOT_DIR="$(dirname "$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")")"
export FLASK_ENV="development"
export FLASK_APP="src.Webhook.app"
export LOG_LEVEL="INFO"

# Redis configuration (for production)
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_PASSWORD=""
export REDIS_DB="0"

# Dashboard API authentication key
export DASHBOARD_API_KEY="change_me_in_production"

# CSRF protection
export CSRF_SECRET_KEY="change_me_in_production"

# Secret key for Flask session
export SECRET_KEY="change_me_in_production"
EOF
            chmod +x "$ENV_FILE"
            log_message "Created basic $ENV_FILE. Please update it with your credentials."
        fi
    else
        log_message "$ENV_FILE already exists."
    fi
    
    # Create a helper script to load environment variables
    cat > "load_env.sh" << 'EOF'
#!/bin/bash
# Helper script to load environment variables
source "src/Credentials/env.sh"
echo "Environment variables loaded. You can now run the application."
EOF
    chmod +x load_env.sh
    log_message "Created environment loading script: load_env.sh"
}

# Initialize database
initialize_database() {
    if [ "$SKIP_DB_INIT" = true ]; then
        log_message "Skipping database initialization due to --skip-db-init flag"
        return
    }

    log_message "Initializing database..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || {
        log_message "Failed to activate virtual environment." "ERROR"
        exit 1
    }
    
    # Source environment variables
    source "$ENV_FILE" || {
        log_message "Failed to load environment variables." "ERROR"
        deactivate
        exit 1
    }
    
    # Initialize database if needed
    if [ -f "$DATABASE_DIR/schema.sql" ]; then
        log_message "Initializing database from schema..."
        # Create Webhook database directory if it doesn't exist
        mkdir -p "$DATABASE_DIR/Webhook"
        
        # Check if database files already exist for SQLite
        if [ -f "$DATABASE_DIR/Webhook/trading_signals.db" ] && [ "$USE_MSSQL" != "true" ]; then
            if [ "$RECREATE_DB" = true ]; then
                log_message "Recreating database due to --recreate-db flag"
                rm "$DATABASE_DIR/Webhook/trading_signals.db"
                log_message "Existing database deleted."
            elif [ "$NONINTERACTIVE" = false ]; then
                read -p "SQLite database already exists. Recreate? This will delete all data. [y/N] " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    rm "$DATABASE_DIR/Webhook/trading_signals.db"
                    log_message "Existing database deleted."
                else
                    log_message "Using existing database."
                    deactivate
                    return
                fi
            else
                log_message "Using existing database in non-interactive mode."
                deactivate
                return
            fi
        fi
        
        # Check if the init_db.py script exists
        if [ -f "$DATABASE_DIR/init_db.py" ]; then
            log_message "Running database initialization script..."
            chmod +x "$DATABASE_DIR/init_db.py"
            
            # Run the initialization script
            "$PYTHON_CMD" "$DATABASE_DIR/init_db.py"
            if [ $? -ne 0 ]; then
                log_message "Database initialization script failed." "ERROR"
                read -p "Continue anyway? [y/N] " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_message "Setup aborted due to database initialization failure." "ERROR"
                    exit 1
                fi
            else
                log_message "Database initialized successfully."
            fi
        else
            # Fallback to the old method if init_db.py doesn't exist
            log_message "Creating database from schema..."
            
            # Use sqlite3 if available, otherwise try with Python
            if command -v sqlite3 &> /dev/null && [ "$USE_MSSQL" != "true" ]; then
                sqlite3 "$DATABASE_DIR/Webhook/trading_signals.db" < "$DATABASE_DIR/schema.sql"
            else
                # Create a temporary Python script to initialize the database
                TMP_INIT_SCRIPT=$(mktemp)
                cat > "$TMP_INIT_SCRIPT" << 'EOF'
import sqlite3
import os
import sys

schema_file = sys.argv[1]
db_file = sys.argv[2]

# Create database directory if it doesn't exist
os.makedirs(os.path.dirname(db_file), exist_ok=True)

# Read schema SQL
with open(schema_file, 'r') as f:
    schema_sql = f.read()

# Connect to database and execute schema
conn = sqlite3.connect(db_file)
conn.executescript(schema_sql)
conn.commit()
conn.close()

print(f"Database initialized at {db_file}")
EOF
                # Execute the temporary script
                "$PYTHON_CMD" "$TMP_INIT_SCRIPT" "$DATABASE_DIR/schema.sql" "$DATABASE_DIR/Webhook/trading_signals.db"
                # Remove the temporary script
                rm "$TMP_INIT_SCRIPT"
            fi
        fi
        
        log_message "Database initialized successfully."
    else
        log_message "Schema file not found. Database initialization skipped." "WARNING"
    fi
    
    # Deactivate virtual environment
    deactivate
}

# Final configuration and verification
finalize_setup() {
    log_message "Finalizing setup..."
    
    # Create restart trigger file for Passenger
    touch "$RESTART_FILE"
    log_message "Created restart trigger file: $RESTART_FILE"
    
    # Verify passenger_wsgi.py exists
    if [ ! -f "passenger_wsgi.py" ]; then
        log_message "passenger_wsgi.py not found. Creating a basic version..." "WARNING"
        
        cat > "passenger_wsgi.py" << 'EOF'
#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Configure logging
LOG_DIR = Path(__file__).resolve().parent / "Logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "passenger.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('passenger_wsgi')

# Setup environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ['PYTHONPATH'] = str(BASE_DIR)

# Activate virtual environment
activate_script = BASE_DIR / '.venv/bin/activate_this.py'
if activate_script.exists():
    with open(activate_script) as f:
        exec(f.read(), {'__file__': str(activate_script)})
    logger.info("Virtual environment activated")
else:
    logger.warning(f"Virtual environment activate script not found at {activate_script}")

# Import the Flask application
try:
    from src.Webhook.app import flask_app as application
    logger.info("Flask application imported successfully")
except Exception as e:
    logger.critical(f"Error importing Flask application: {str(e)}")
    
    def application(environ, start_response):
        status = '500 Internal Server Error'
        error_message = f"Error initializing application: {str(e)}"
        error_details = f"Check logs in {LOG_DIR} for more information."
        output = f"{error_message}\n\n{error_details}".encode()
        response_headers = [
            ('Content-type', 'text/plain'),
            ('Content-Length', str(len(output)))
        ]
        start_response(status, response_headers)
        return [output]
EOF
        log_message "Basic passenger_wsgi.py created."
    else
        log_message "passenger_wsgi.py found."
    fi
    
    # Create run script for local development
    cat > "run_local.sh" << 'EOF'
#!/bin/bash
# Run Jamso AI Server locally for development
source .venv/bin/activate
source src/Credentials/env.sh
export FLASK_ENV=development
export FLASK_DEBUG=1
python -m src.Webhook.app
EOF
    chmod +x run_local.sh
    log_message "Created local development script: run_local.sh"
    
    # Create stop script for local development
    cat > "stop_local.sh" << 'EOF'
#!/bin/bash
# Stop Jamso AI Server running locally
echo "Stopping local development server..."
pkill -f "python -m src.Webhook.app" || echo "No running server found."
EOF
    chmod +x stop_local.sh
    log_message "Created stop script: stop_local.sh"
    
    # Create cleanup script
    cat > "Scripts/Maintenance/cleanup_cache.sh" << 'EOF'
#!/bin/bash
# Clean up Python cache files
echo "Cleaning Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete
echo "Cache files cleaned successfully."
EOF
    chmod +x "Scripts/Maintenance/cleanup_cache.sh"
    log_message "Created cache cleanup script: Scripts/Maintenance/cleanup_cache.sh"
    
    # Create a copy in the root directory for backward compatibility
    cp "Scripts/Maintenance/cleanup_cache.sh" "cleanup_cache.sh"
    chmod +x "cleanup_cache.sh"
    
    # Create health check script
    cat > "Scripts/Maintenance/health_check.sh" << 'EOF'
#!/bin/bash
# Health check script for Jamso AI Server
echo "Running health check..."

# Check Python version
python3 --version

# Check virtual environment
if [ -d ".venv" ]; then
    echo "Virtual environment exists: OK"
else
    echo "Virtual environment missing: FAIL"
fi

# Check environment configuration
if [ -f "src/Credentials/env.sh" ]; then
    echo "Environment configuration exists: OK"
else
    echo "Environment configuration missing: FAIL"
fi

# Check database
if [ -f "src/Database/Webhook/trading_signals.db" ]; then
    echo "Database exists: OK"
else
    echo "Database missing: FAIL"
fi

# Check if required directories exist
for dir in "Logs" "tmp" "src/Database" "src/Credentials" "Scripts"; do
    if [ -d "$dir" ]; then
        echo "Directory $dir exists: OK"
    else
        echo "Directory $dir missing: FAIL"
    fi
done

echo "Health check completed."
EOF
    chmod +x "Scripts/Maintenance/health_check.sh"
    log_message "Created health check script: Scripts/Maintenance/health_check.sh"
    
    # Create a Makefile for common tasks
    cat > "Makefile" << 'EOF'
.PHONY: run test lint clean restart install_deps help

# Default target
all: install_deps

# Help
help:
	@echo "Jamso AI Server Makefile Commands:"
	@echo "  make run            - Run the application locally for development"
	@echo "  make test           - Run tests with pytest"
	@echo "  make lint           - Run code quality checks (flake8, black)"
	@echo "  make format         - Format code with black and isort"
	@echo "  make clean          - Remove generated files and caches"
	@echo "  make restart        - Restart the application (touch restart.txt)"
	@echo "  make install_deps   - Install Python dependencies from requirements.txt"

# Run the application locally
run:
	./run_local.sh

# Run tests
test:
	source .venv/bin/activate && \
	pytest

# Lint the code
lint:
	source .venv/bin/activate && \
	flake8 src/ && \
	black --check src/

# Format the code
format:
	source .venv/bin/activate && \
	black src/ && \
	isort src/

# Clean generated files
clean:
	find . -name __pycache__ -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".coverage" -delete
	find . -name ".coverage.*" -delete
	find . -name "htmlcov" -type d -exec rm -rf {} +
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
	find . -name ".hypothesis" -type d -exec rm -rf {} +

# Restart the application
restart:
	touch tmp/restart.txt
	@echo "Restart signal sent"

# Install dependencies
install_deps:
	source .venv/bin/activate && \
	pip install -r requirements.txt
EOF
    log_message "Created Makefile for common tasks."
}

# Rebuild environment completely (clean install)
clean_reinstall() {
    log_message "Starting clean reinstallation..." "WARNING"
    
    # Confirm with the user
    if [ "$NONINTERACTIVE" = false ]; then
        read -p "This will delete all existing configuration, virtual environment, and database. Continue? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_message "Clean reinstallation aborted by user." "WARNING"
            return
        fi
    fi
    
    # Remove existing virtual environment
    if [ -d "$VENV_DIR" ]; then
        log_message "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    fi
    
    # Remove existing database
    if [ -f "$DATABASE_DIR/Webhook/trading_signals.db" ]; then
        log_message "Removing existing database..."
        rm "$DATABASE_DIR/Webhook/trading_signals.db"
    fi
    
    # Remove environment configuration
    if [ -f "$ENV_FILE" ]; then
        log_message "Removing existing environment configuration..."
        rm "$ENV_FILE"
    fi
    
    # Clean Python cache
    log_message "Cleaning Python cache files..."
    find . -name "__pycache__" -type d -exec rm -rf {} +
    find . -name "*.pyc" -delete
    find . -name "*.pyo" -delete
    find . -name "*.pyd" -delete
    
    # Set flags for full reinstallation
    FORCE_RECREATE_VENV=true
    RECREATE_DB=true
    
    # Run installation process
    create_directories
    check_python_version
    setup_virtual_environment
    install_dependencies
    configure_environment
    initialize_database
    finalize_setup
    
    log_message "Clean reinstallation completed successfully."
}

# Setup menu
show_setup_menu() {
    # Clear the screen
    clear
    
    # Display the banner
    print_banner
    
    # Menu options
    echo -e "${BOLD}Setup Options:${NC}"
    echo "1) Standard Installation"
    echo "2) Clean Reinstallation (removes existing setup)"
    echo "3) Advanced Installation Options"
    echo "4) Check System Requirements"
    echo "5) Run Health Check"
    echo "q) Quit"
    echo ""
    
    # Get user choice
    read -p "Enter your choice: " choice
    
    case $choice in
        1)
            log_message "Starting standard installation..."
            process_args "$@"
            create_directories
            check_python_version
            setup_virtual_environment
            install_dependencies
            configure_environment
            initialize_database
            finalize_setup
            print_completion_message
            ;;
        2)
            log_message "Starting clean reinstallation..."
            clean_reinstall
            print_completion_message
            ;;
        3)
            show_advanced_menu
            ;;
        4)
            check_system_requirements
            read -p "Press Enter to continue..."
            show_setup_menu
            ;;
        5)
            run_health_check
            read -p "Press Enter to continue..."
            show_setup_menu
            ;;
        q|Q)
            log_message "Setup exited by user."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            sleep 2
            show_setup_menu
            ;;
    esac
}

# Advanced options menu
show_advanced_menu() {
    # Clear the screen
    clear
    
    # Display the banner
    print_banner
    
    # Menu options
    echo -e "${BOLD}Advanced Installation Options:${NC}"
    echo "1) Install with Development Dependencies"
    echo "2) Skip Python Version Check"
    echo "3) Skip Database Initialization"
    echo "4) Force Recreate Virtual Environment"
    echo "5) Recreate Database Only"
    echo "6) Non-Interactive Installation (use defaults)"
    echo "b) Back to Main Menu"
    echo "q) Quit"
    echo ""
    
    # Get user choice
    read -p "Enter your choice: " choice
    
    case $choice in
        1)
            log_message "Starting installation with development dependencies..."
            INSTALL_DEV_DEPS=true
            create_directories
            check_python_version
            setup_virtual_environment
            install_dependencies
            configure_environment
            initialize_database
            finalize_setup
            print_completion_message
            ;;
        2)
            log_message "Starting installation with Python version check skipped..."
            SKIP_PYTHON_CHECK=true
            create_directories
            check_python_version
            setup_virtual_environment
            install_dependencies
            configure_environment
            initialize_database
            finalize_setup
            print_completion_message
            ;;
        3)
            log_message "Starting installation with database initialization skipped..."
            SKIP_DB_INIT=true
            create_directories
            check_python_version
            setup_virtual_environment
            install_dependencies
            configure_environment
            initialize_database
            finalize_setup
            print_completion_message
            ;;
        4)
            log_message "Starting installation with forced virtual environment recreation..."
            FORCE_RECREATE_VENV=true
            create_directories
            check_python_version
            setup_virtual_environment
            install_dependencies
            configure_environment
            initialize_database
            finalize_setup
            print_completion_message
            ;;
        5)
            log_message "Starting database recreation only..."
            RECREATE_DB=true
            initialize_database
            log_message "Database recreation completed."
            read -p "Press Enter to continue..."
            show_advanced_menu
            ;;
        6)
            log_message "Starting non-interactive installation with default values..."
            NONINTERACTIVE=true
            create_directories
            check_python_version
            setup_virtual_environment
            install_dependencies
            configure_environment
            initialize_database
            finalize_setup
            print_completion_message
            ;;
        b|B)
            show_setup_menu
            ;;
        q|Q)
            log_message "Setup exited by user."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            sleep 2
            show_advanced_menu
            ;;
    esac
}

# Check system requirements
check_system_requirements() {
    echo -e "${BOLD}System Requirements Check:${NC}"
    echo "--------------------------"
    
    # Check Python
    echo -n "Python 3.8+: "
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | sed 's/Python //')
        if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" = "3.8" ]; then
            echo -e "${GREEN}PASS${NC} ($python_version)"
        else
            echo -e "${RED}FAIL${NC} ($python_version - need 3.8+)"
        fi
    else
        echo -e "${RED}FAIL${NC} (not found)"
    fi
    
    # Check pip
    echo -n "pip: "
    if command -v pip3 &> /dev/null; then
        echo -e "${GREEN}PASS${NC} ($(pip3 --version))"
    else
        echo -e "${RED}FAIL${NC} (not found)"
    fi
    
    # Check venv
    echo -n "venv module: "
    if python3 -c "import venv" &> /dev/null; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC} (not found - install python3-venv package)"
    fi
    
    # Check SQLite
    echo -n "SQLite: "
    if command -v sqlite3 &> /dev/null; then
        echo -e "${GREEN}PASS${NC} ($(sqlite3 --version))"
    else
        echo -e "${YELLOW}WARNING${NC} (not found - will use Python SQLite instead)"
    fi
    
    # Check disk space
    echo -n "Disk space: "
    disk_space=$(df -h . | awk 'NR==2 {print $4}')
    echo -e "${GREEN}$disk_space available${NC}"
    
    # Check memory
    echo -n "Memory: "
    if command -v free &> /dev/null; then
        memory=$(free -h | awk 'NR==2 {print $4}')
        echo -e "${GREEN}$memory available${NC}"
    else
        echo -e "${YELLOW}Unable to determine${NC}"
    fi
    
    echo "--------------------------"
    echo "System check complete."
    echo ""
}

# Run health check
run_health_check() {
    if [ -f "Scripts/Maintenance/health_check.sh" ]; then
        bash Scripts/Maintenance/health_check.sh
    else
        echo "Health check script not found. Please complete installation first."
    fi
}

# Print completion message
print_completion_message() {
    echo -e "${GREEN}${BOLD}"
    echo "================================================================"
    echo "           JAMSO AI SERVER SETUP COMPLETED SUCCESSFULLY!"
    echo "================================================================"
    echo -e "${NC}"
    echo ""
    echo "To activate the virtual environment:"
    echo "  $ source .venv/bin/activate"
    echo "  OR"
    echo "  $ ./activate.sh"
    echo ""
    echo "To load environment variables:"
    echo "  $ source src/Credentials/env.sh"
    echo "  OR"
    echo "  $ ./load_env.sh"
    echo ""
    echo "Before running the application, please:"
    echo "  1. Update your API credentials in src/Credentials/env.sh"
    echo "  2. Ensure all configuration settings are correct"
    echo ""
    echo "To run the application locally for development:"
    echo "  $ ./run_local.sh"
    echo ""
    echo "To restart the application in Passenger:"
    echo "  $ touch tmp/restart.txt"
    echo "  OR"
    echo "  $ make restart"
    echo ""
    echo "For main application menu:"
    echo "  $ ./start.sh"
    echo ""
    echo -e "${YELLOW}Setup log saved to: $INSTALL_LOG${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

# Main function to run the setup
main() {
    trap 'log_message "Setup interrupted." "ERROR"; exit 1' INT TERM
    
    # If running in non-interactive mode, bypass menu
    if [[ "$*" == *"--non-interactive"* ]]; then
        log_message "Running in non-interactive mode, bypassing menu..."
        process_args "$@"
        create_directories
        check_python_version
        setup_virtual_environment
        install_dependencies
        configure_environment
        initialize_database
        finalize_setup
        return 0
    fi
    
    # Otherwise show the menu
    show_setup_menu "$@"
    return 0
}

# Execute main function
main "$@"
