#!/bin/bash
# Comprehensive System Cleanup Script for Jamso AI Engine
# This script combines all cleanup operations into one command

echo "===== Starting Comprehensive System Cleanup ====="
echo "$(date)"
echo "---------------------------------------------"

# Change to project root directory
cd "$(dirname "$0")/.."

# Stop running services if any
if [ -f "./stop_local.sh" ]; then
    echo "Stopping any running services..."
    ./stop_local.sh
fi

# Clean Python cache files
echo "Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type f -name "*.pyd" -delete 2>/dev/null

# Clean temporary files
echo "Cleaning temporary files..."
find ./tmp -type f -mtime +3 -delete 2>/dev/null
find ./Logs -type f -name "*.log.*" -mtime +30 -delete 2>/dev/null

# Clean Flask instance folder
echo "Cleaning Flask instance folder..."
find ./instance -type f -mtime +30 -delete 2>/dev/null

# Clean sessions
if [ -f "./Tools/cleanup_sessions.py" ]; then
    echo "Cleaning expired sessions..."
    python3 ./Tools/cleanup_sessions.py || echo "Session cleanup failed."
fi

# Clean Redis cache
if [ -f "./Tools/cleanup_redis.sh" ]; then
    echo "Cleaning Redis cache..."
    ./Tools/cleanup_redis.sh
fi

# Optimize database if script exists
if [ -f "./Tools/optimize_db.py" ]; then
    echo "Optimizing database..."
    python3 ./Tools/optimize_db.py || echo "Database optimization failed."
fi

# Ensure proper permissions
if [ -f "./Tools/fix_permissions.sh" ]; then
    echo "Fixing permissions..."
    ./Tools/fix_permissions.sh
fi

echo "---------------------------------------------"
echo "Comprehensive system cleanup completed"
echo "$(date)"
echo "===== Cleanup Finished ====="
