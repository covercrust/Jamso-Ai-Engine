#!/bin/bash
# Update sentiment data daily
# 
# This script is intended to be run from a cron job to update sentiment data daily
# Suggested cron entry: 0 1 * * * /home/jamso-ai-server/Jamso-Ai-Engine/Tools/update_sentiment_daily.sh
#
# It will update the sentiment data for commonly used cryptocurrency pairs

# Set the working directory
cd /home/jamso-ai-server/Jamso-Ai-Engine

# Log file for updates
LOG_FILE="Logs/sentiment_updates.log"
mkdir -p $(dirname "$LOG_FILE")

# Log start time
echo "==============================================" >> "$LOG_FILE"
echo "Sentiment update started at $(date)" >> "$LOG_FILE"

# Run the sentiment import script with force flag to overwrite existing data
# Include additional cryptocurrency pairs as needed
python3 Tools/capital_sentiment_import.py --symbols BTCUSD,ETHUSD,XRPUSD,LTCUSD,ADAUSD --days 90 --force >> "$LOG_FILE" 2>&1

# Check if the script was successful
if [ $? -eq 0 ]; then
    echo "Sentiment data updated successfully at $(date)" >> "$LOG_FILE"
else
    echo "Error updating sentiment data at $(date)" >> "$LOG_FILE"
fi

echo "==============================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
