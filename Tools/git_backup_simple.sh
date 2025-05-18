#!/bin/bash
# Simple Git Backup Script for Jamso AI Engine
# This script performs automatic git backups without complex error handling

# Set the base directory to the project root
BASE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$BASE_DIR" || { echo "Failed to change directory to $BASE_DIR"; exit 1; }

# Timestamp for logs
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="$BASE_DIR/Logs/git_backup_simple.log"

# Ensure log directory exists
mkdir -p "$BASE_DIR/Logs"

# Begin log entry
echo "===== Git Backup Started - $TIMESTAMP =====" > "$LOG_FILE"

# Function for logging
log() {
  echo "$1" >> "$LOG_FILE"
  echo "$1"
}

# Check if this is a Git repository
if [ ! -d ".git" ]; then
  log "ERROR: Not a Git repository"
  exit 1
fi

log "Setting Git pull strategy to merge..."
git config pull.rebase false

# Stage all changes (excluding those in .gitignore)
log "Checking for changes..."
git add -A

# Check if there are staged changes
if git diff --cached --quiet; then
  log "No changes to commit"
else
  # Commit changes
  log "Committing changes..."
  git commit -m "Automated backup - $TIMESTAMP" >> "$LOG_FILE" 2>&1
  if [ $? -eq 0 ]; then
    log "Changes committed successfully"
  else
    log "Failed to commit changes"
  fi
fi

# Update from remote
log "Fetching from remote..."
git fetch origin >> "$LOG_FILE" 2>&1

# Check if local and remote have diverged
LOCAL_REV=$(git rev-parse HEAD)
REMOTE_REV=$(git rev-parse origin/master 2>/dev/null || git rev-parse origin/main 2>/dev/null)

if [ "$LOCAL_REV" != "$REMOTE_REV" ]; then
  log "Local and remote repositories have different commits"
  log "Attempting to merge changes..."
  git merge --no-edit origin/master >> "$LOG_FILE" 2>&1 || git merge --no-edit origin/main >> "$LOG_FILE" 2>&1
  MERGE_STATUS=$?
  
  if [ $MERGE_STATUS -ne 0 ]; then
    log "Merge failed, creating backup branch..."
    BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
    git branch "$BACKUP_BRANCH" >> "$LOG_FILE" 2>&1
    log "Created backup branch: $BACKUP_BRANCH"
    
    log "Resetting to remote state..."
    git reset --hard origin/master >> "$LOG_FILE" 2>&1 || git reset --hard origin/main >> "$LOG_FILE" 2>&1
  else
    log "Merge completed successfully"
  fi
fi

# Push changes
log "Pushing changes to remote repository..."
git push >> "$LOG_FILE" 2>&1
PUSH_STATUS=$?

if [ $PUSH_STATUS -eq 0 ]; then
  log "Push successful!"
  echo "SUCCESS: $(date '+%Y-%m-%d %H:%M:%S')" > "$BASE_DIR/Logs/git_backup_status.log"
else
  log "Push failed with exit code: $PUSH_STATUS"
  echo "FAILED: $(date '+%Y-%m-%d %H:%M:%S')" > "$BASE_DIR/Logs/git_backup_status.log"
fi

log "===== Git Backup Completed - $(date '+%Y-%m-%d %H:%M:%S') ====="
