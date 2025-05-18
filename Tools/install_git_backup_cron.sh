#!/bin/bash
# Direct cron job installation for Git backup

# Set the base directory to the project root
BASE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
echo "Installing Git backup cron job to run at 2:00 AM daily"

# Add the cron job directly - using the simple backup script which is more reliable
(crontab -l 2>/dev/null | grep -v "git_backup"; echo "0 2 * * * $BASE_DIR/Tools/git_backup_simple.sh > /dev/null 2>&1 # Jamso-AI Git Backup") | crontab -

# Verify installation
if crontab -l | grep -q "git_backup"; then
    echo "Git backup cron job successfully installed!"
    echo "Cron will run the backup script at 2:00 AM every day"
else
    echo "Failed to install the cron job. Please try again manually with:"
    echo "crontab -e"
    echo "And add the following line:"
    echo "0 2 * * * $BASE_DIR/Tools/git_backup.sh >> $BASE_DIR/Logs/git_backup.log 2>&1 # Jamso-AI Git Backup"
fi
