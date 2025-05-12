#!/bin/bash
# Setup performance optimization cron jobs for Jamso-AI Engine
# This script sets up cron jobs that will run at regular intervals to optimize system performance

# Base directory of Jamso-AI Engine
BASE_DIR="/home/jamso-ai-server/Jamso-Ai-Engine"

# Current timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Create temporary file for cron jobs
TEMP_CRON_FILE=$(mktemp)

# Get current crontab
crontab -l > "$TEMP_CRON_FILE" 2>/dev/null || echo "# Jamso-AI Engine Cron Jobs" > "$TEMP_CRON_FILE"

# Check if our cron jobs are already added
if ! grep -q "# Jamso-AI Engine Performance Optimization Jobs" "$TEMP_CRON_FILE"; then
    echo "" >> "$TEMP_CRON_FILE"
    echo "# Jamso-AI Engine Performance Optimization Jobs - Added on $TIMESTAMP" >> "$TEMP_CRON_FILE"
    echo "# Run database optimization every day at 3:00 AM" >> "$TEMP_CRON_FILE"
    echo "0 3 * * * python3 $BASE_DIR/Tools/optimize_db.py >> $BASE_DIR/Logs/cron_db_optimize.log 2>&1" >> "$TEMP_CRON_FILE"
    echo "# Monitor memory usage every hour" >> "$TEMP_CRON_FILE"
    echo "0 * * * * python3 $BASE_DIR/Tools/memory_monitor.py >> $BASE_DIR/Logs/cron_memory_monitor.log 2>&1" >> "$TEMP_CRON_FILE"
    echo "# Restart Gunicorn once a week (Sunday at 4:00 AM) to prevent memory leaks" >> "$TEMP_CRON_FILE"
    echo "0 4 * * 0 pkill -f gunicorn && cd $BASE_DIR && python start_app.py >> $BASE_DIR/Logs/cron_restart.log 2>&1" >> "$TEMP_CRON_FILE"
    
    # Install new crontab
    crontab "$TEMP_CRON_FILE"
    echo "Performance optimization cron jobs have been added."
else
    echo "Performance optimization cron jobs already exist."
fi

# Clean up
rm "$TEMP_CRON_FILE"

echo "Cron job setup completed."
