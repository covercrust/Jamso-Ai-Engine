#!/bin/bash
# Session cleanup script - prevents session file accumulation

# Set path to session directories
MAIN_SESSION_DIR="/home/jamso-ai-server/Jamso-Ai-Engine/instance/sessions"
DASHBOARD_SESSION_DIR="/home/jamso-ai-server/Jamso-Ai-Engine/instance/dashboard_sessions"

# Log file for tracking cleanup
LOG_FILE="/home/jamso-ai-server/Jamso-Ai-Engine/Logs/session_cleanup.log"

echo "$(date): Starting session cleanup" >> $LOG_FILE

# Remove session files older than 1 hour
find $MAIN_SESSION_DIR -type f -mmin +60 -delete 2>/dev/null
find $DASHBOARD_SESSION_DIR -type f -mmin +60 -delete 2>/dev/null

# Count remaining files
MAIN_COUNT=$(find $MAIN_SESSION_DIR -type f | wc -l)
DASHBOARD_COUNT=$(find $DASHBOARD_SESSION_DIR -type f | wc -l)

echo "$(date): Cleanup complete. Remaining files: $MAIN_COUNT in main, $DASHBOARD_COUNT in dashboard" >> $LOG_FILE

# Add to crontab
# To install this script as a cron job, run:
# crontab -e
# Then add: 
# 0 * * * * /home/jamso-ai-server/Jamso-Ai-Engine/Tools/cleanup_sessions.sh
