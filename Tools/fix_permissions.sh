#!/bin/bash
# Script to set proper permissions for all files in Jamso AI Server

# Base directory
BASE_DIR="/home/jamso-ai-server/Jamso-Ai-Engine"

# Set secure permissions for configuration files
echo "Setting secure permissions for configuration files..."
chmod 600 "$BASE_DIR/src/Credentials/env.sh"
chmod 600 "$BASE_DIR/src/Credentials/active_account.json"

# Set secure permissions for database files
echo "Setting secure permissions for database files..."
chmod 600 "$BASE_DIR/src/Database/Webhook/trading_signals.db"
chmod 600 "$BASE_DIR/src/Database/Users/users.db"

# Make all Python scripts executable
echo "Making Python scripts executable..."
find "$BASE_DIR" -name "*.py" -type f -not -path "*/.venv/*" -exec chmod 755 {} \;

# Make all shell scripts executable
echo "Making shell scripts executable..."
find "$BASE_DIR" -name "*.sh" -type f -exec chmod 755 {} \;

# Ensure log directories exist with correct permissions
echo "Setting up log directories..."
mkdir -p "$BASE_DIR/Logs" "$BASE_DIR/Logs"
chmod 755 "$BASE_DIR/Logs" "$BASE_DIR/Logs"

# Ensure instance directories have correct permissions
echo "Setting up instance directories..."
mkdir -p "$BASE_DIR/dashboard/instance/sessions"
chmod 755 "$BASE_DIR/dashboard/instance"
chmod 755 "$BASE_DIR/dashboard/instance/sessions"

# Set proper permissions on static directories
echo "Setting up static content directories..."
find "$BASE_DIR" -type d -name "static" -exec chmod 755 {} \;
find "$BASE_DIR" -type d -name "templates" -exec chmod 755 {} \;

echo "Permission setup complete!"
