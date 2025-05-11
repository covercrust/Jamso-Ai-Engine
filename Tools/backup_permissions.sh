#!/bin/bash
# Script to backup key file permissions in Jamso AI Server

# Base directory
BASE_DIR="/home/jamso-ai-server/Jamso-Ai-Engine"
BACKUP_FILE="$BASE_DIR/permissions_backup.txt"

# Create the backup file
echo "# Jamso AI Server permissions backup - $(date)" > "$BACKUP_FILE"
echo "# Run this file with 'bash permissions_backup.txt' to restore permissions" >> "$BACKUP_FILE"
echo "" >> "$BACKUP_FILE"

# Add configuration files
echo "# Configuration files" >> "$BACKUP_FILE"
find "$BASE_DIR/src/Credentials" -type f -name "*.json" -o -name "*.sh" | while read file; do
    perms=$(stat -c "%a" "$file")
    echo "chmod $perms \"$file\"" >> "$BACKUP_FILE"
done

# Add database files
echo "" >> "$BACKUP_FILE"
echo "# Database files" >> "$BACKUP_FILE"
find "$BASE_DIR/src/Database" -name "*.db" -type f | while read file; do
    perms=$(stat -c "%a" "$file")
    echo "chmod $perms \"$file\"" >> "$BACKUP_FILE"
done

# Add executable Python scripts
echo "" >> "$BACKUP_FILE"
echo "# Executable Python scripts" >> "$BACKUP_FILE"
find "$BASE_DIR" -name "*.py" -type f -executable -not -path "*/.venv/*" | while read file; do
    echo "chmod 755 \"$file\"" >> "$BACKUP_FILE"
done

# Add executable shell scripts
echo "" >> "$BACKUP_FILE"
echo "# Executable shell scripts" >> "$BACKUP_FILE"
find "$BASE_DIR" -name "*.sh" -type f -executable | while read file; do
    echo "chmod 755 \"$file\"" >> "$BACKUP_FILE"
done

echo "" >> "$BACKUP_FILE"
echo "echo \"Permissions restored!\"" >> "$BACKUP_FILE"

echo "Permissions backup saved to $BACKUP_FILE"
echo "To restore permissions in the future, run: bash $BACKUP_FILE"
