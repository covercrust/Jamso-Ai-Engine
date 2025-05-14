#!/bin/bash
# logrotate_logs.sh - Rotates and compresses log files in the Logs/ directory
# Keeps the last 5 rotated logs for each file

LOG_DIR="Logs"
MAX_LOGS=5

for logfile in "$LOG_DIR"/*.log; do
    [ -e "$logfile" ] || continue
    # Rotate logs
    for ((i=MAX_LOGS; i>=1; i--)); do
        if [ -e "$logfile.$i.gz" ]; then
            if [ $i -eq $MAX_LOGS ]; then
                rm -f "$logfile.$i.gz"
            else
                mv "$logfile.$i.gz" "$logfile.$((i+1)).gz"
            fi
        fi
    done
    if [ -s "$logfile" ]; then
        mv "$logfile" "$logfile.1"
        gzip "$logfile.1"
        touch "$logfile"
    fi
    # Set permissions
    chmod 640 "$logfile"*
done
