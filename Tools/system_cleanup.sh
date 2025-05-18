#!/bin/bash
# Comprehensive System Cleanup Script for Jamso AI Engine
# This script combines all cleanup operations into one command

echo "===== Starting Comprehensive System Cleanup ====="
echo "$(date)"
echo "---------------------------------------------"

# Change to project root directory
BASE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$BASE_DIR" || exit 1

# Stop running services if any
if [ -f "./stop_local.sh" ]; then
    echo "Stopping any running services..."
    ./stop_local.sh
fi

# Check Git backup status
echo "Checking Git backup status..."
if [ -f "./Logs/git_backup_status.log" ]; then
    echo "Git backup status:"
    cat "./Logs/git_backup_status.log"
elif [ -f "./Logs/git_backup.log" ]; then
    echo "Last Git backup attempt:"
    tail -n 5 "./Logs/git_backup.log"
else
    echo "No Git backup log found."
    echo "To set up Git backups, run: Tools/setup_git_credentials.sh"
fi

# Check for Git backup errors
if [ -f "./Logs/git_backup_error.log" ]; then
    echo "WARNING: Git backup errors detected!"
    cat "./Logs/git_backup_error.log"
    echo "To resolve Git issues, run: Tools/git_backup_recovery.sh --interactive"
fi

# Check Git repository status
if [ -d ".git" ]; then
    echo "Checking Git repository status..."
    # Check for diverged branches
    LOCAL_COMMITS=$(git rev-list --count master ^origin/master 2>/dev/null || echo "0")
    REMOTE_COMMITS=$(git rev-list --count origin/master ^master 2>/dev/null || echo "0")
    
    if [ "$LOCAL_COMMITS" -gt 0 ] && [ "$REMOTE_COMMITS" -gt 0 ]; then
        echo "ALERT: Git branches have diverged ($LOCAL_COMMITS local commits, $REMOTE_COMMITS remote commits)"
        echo "To fix this, run: Tools/git_backup_recovery.sh --fix-diverged"
    elif [ "$LOCAL_COMMITS" -gt 0 ]; then
        echo "INFO: $LOCAL_COMMITS local Git commits need to be pushed"
    elif [ "$REMOTE_COMMITS" -gt 0 ]; then
        echo "INFO: $REMOTE_COMMITS remote Git commits need to be pulled"
    fi
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
