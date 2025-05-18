#!/bin/bash
# Git Backup Status Checker
# This script provides a quick overview of the Git backup status

# Set the base directory to the project root
BASE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$BASE_DIR" || exit 1

echo "===== Git Backup Status Report ====="
echo "Generated on: $(date '+%Y-%m-%d %H:%M:%S')"
echo "-------------------------------------"

# Check if either backup log exists
if [ -f "$BASE_DIR/Logs/git_backup_simple.log" ]; then
    # Get the last backup timestamp from the simple log
    LAST_BACKUP=$(grep -a "Git Backup Started" "$BASE_DIR/Logs/git_backup_simple.log" | tail -1 | sed 's/.*Git Backup Started - \(.*\) =.*/\1/')
    
    if [ -n "$LAST_BACKUP" ]; then
        echo "Last backup attempt: $LAST_BACKUP (simple backup)"
    else
        echo "No backup attempts found in simple log file."
    fi
    
    # Check for most recent status
    echo ""
    echo "Most recent backup status:"
    grep -a -A 20 "===== Git Backup Started - " "$BASE_DIR/Logs/git_backup_simple.log" | tail -25
elif [ -f "$BASE_DIR/Logs/git_backup.log" ]; then
    # Get the last backup timestamp from the original log
    LAST_BACKUP=$(grep -a "Git Backup Started" "$BASE_DIR/Logs/git_backup.log" | tail -1 | sed 's/.*Git Backup Started - \(.*\) =.*/\1/')
    
    if [ -n "$LAST_BACKUP" ]; then
        echo "Last backup attempt: $LAST_BACKUP"
    else
        echo "No backup attempts found in log file."
    fi
    
    # Check for most recent status
    echo ""
    echo "Most recent backup status:"
    grep -a -A 20 "===== Git Backup Started - " "$BASE_DIR/Logs/git_backup.log" | tail -25
else
    echo "No backup logs found"
    echo "Git backup system may not be properly set up."
fi

# Check status file if it exists
if [ -f "$BASE_DIR/Logs/git_backup_status.log" ]; then
    echo ""
    echo "Current backup status:"
    cat "$BASE_DIR/Logs/git_backup_status.log"
fi

# Check for error file
if [ -f "$BASE_DIR/Logs/git_backup_error.log" ]; then
    echo ""
    echo "ERROR: Backup issues detected!"
    cat "$BASE_DIR/Logs/git_backup_error.log"
    echo ""
    echo "To resolve these issues, run: Tools/git_backup_recovery.sh --interactive"
fi

# Check Git repository state
echo ""
echo "Current Git repository status:"
if [ -d ".git" ]; then
    git status -s
    
    # Check for diverged branches
    LOCAL_COMMITS=$(git rev-list --count master ^origin/master 2>/dev/null || echo "0")
    REMOTE_COMMITS=$(git rev-list --count origin/master ^master 2>/dev/null || echo "0")
    
    echo ""
    if [ "$LOCAL_COMMITS" -gt 0 ] && [ "$REMOTE_COMMITS" -gt 0 ]; then
        echo "ALERT: Git branches have diverged ($LOCAL_COMMITS local commits, $REMOTE_COMMITS remote commits)"
        echo "To fix this, run: Tools/git_backup_recovery.sh --fix-diverged"
    elif [ "$LOCAL_COMMITS" -gt 0 ]; then
        echo "INFO: $LOCAL_COMMITS local Git commits need to be pushed"
    elif [ "$REMOTE_COMMITS" -gt 0 ]; then
        echo "INFO: $REMOTE_COMMITS remote Git commits need to be pulled"
    else
        echo "Repository is up to date with remote"
    fi
else
    echo "Not a Git repository"
fi

# Check cron job status
echo ""
echo "Backup schedule:"
if crontab -l | grep -q "git_backup"; then
    echo "Automatic backups are scheduled. Details:"
    crontab -l | grep "git_backup"
else
    echo "No automatic backups scheduled."
    echo "To set up automatic backups, run: Tools/install_git_backup_cron.sh"
fi

echo ""
echo "===== End of Status Report ====="
