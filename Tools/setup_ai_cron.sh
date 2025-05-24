#!/bin/bash
# Setup cron job for daily AI update

# Path to crontab file
CRON_FILE=$(mktemp)

# Get current crontab
crontab -l > "$CRON_FILE" 2>/dev/null || echo "# Jamso-AI-Engine cron jobs" > "$CRON_FILE"

# Check if our job is already in the crontab
if ! grep -q "daily_ai_update.sh" "$CRON_FILE"; then
    echo "# Run AI data collection and model training daily at midnight" >> "$CRON_FILE"
    echo "0 0 * * * /home/jamso-ai-server/Jamso-Ai-Engine/Tools/daily_ai_update.sh" >> "$CRON_FILE"
    
    # Install new crontab
    crontab "$CRON_FILE"
    echo "Daily AI update cron job installed successfully"
else
    echo "Daily AI update cron job already exists"
fi

# Cleanup
rm "$CRON_FILE"

echo "To verify cron jobs, run: crontab -l"
