#!/bin/bash
# Git Backup Recovery Script for Jamso AI Engine
# This script attempts to recover from problematic Git states

# Set the base directory to the project root
BASE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$BASE_DIR" || exit 1

# Timestamp for logs
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="$BASE_DIR/Logs/git_recovery.log"

# Create log entry
echo "===== Git Backup Recovery Started - $TIMESTAMP =====" >> "$LOG_FILE"

# Function to check if we're in a git repo
check_git_repo() {
  if [ ! -d ".git" ]; then
    echo "ERROR: Not in a Git repository." >> "$LOG_FILE"
    exit 1
  fi
}

# Function to display help
show_help() {
  echo "Usage: $0 [OPTION]"
  echo "Git backup recovery options:"
  echo "  --reset-hard       Reset to remote master (CAUTION: lose local changes)"
  echo "  --create-backup    Create a backup branch of current state"
  echo "  --interactive      Interactive recovery mode"
  echo "  --restore VERSION  Restore from a specific version (commit hash or tag)"
  echo "  --fix-diverged     Attempt to fix diverged branches"
  echo "  --help             Show this help message"
}

# Check git repository
check_git_repo

# Process command line arguments
if [ "$1" == "--help" ]; then
  show_help
  exit 0
elif [ "$1" == "--reset-hard" ]; then
  echo "WARNING: Resetting to remote master. All local changes will be lost." >> "$LOG_FILE"
  echo "Creating backup branch first..." >> "$LOG_FILE"
  BACKUP_BRANCH="backup-before-reset-$(date +%Y%m%d-%H%M%S)"
  git branch $BACKUP_BRANCH >> "$LOG_FILE" 2>&1
  echo "Backup branch '$BACKUP_BRANCH' created." >> "$LOG_FILE"
  git fetch origin >> "$LOG_FILE" 2>&1
  git reset --hard origin/master >> "$LOG_FILE" 2>&1
  echo "Reset to origin/master completed." >> "$LOG_FILE"
elif [ "$1" == "--create-backup" ]; then
  BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
  echo "Creating backup branch '$BACKUP_BRANCH'..." >> "$LOG_FILE"
  git branch $BACKUP_BRANCH >> "$LOG_FILE" 2>&1
  echo "Backup branch created. To view it, run: git branch" >> "$LOG_FILE"
elif [ "$1" == "--restore" ] && [ -n "$2" ]; then
  VERSION="$2"
  echo "Attempting to restore to version: $VERSION" >> "$LOG_FILE"
  BACKUP_BRANCH="backup-before-restore-$(date +%Y%m%d-%H%M%S)"
  git branch $BACKUP_BRANCH >> "$LOG_FILE" 2>&1
  git checkout $VERSION -b restore-$VERSION >> "$LOG_FILE" 2>&1
  echo "Restored to $VERSION. Now on branch restore-$VERSION." >> "$LOG_FILE"
  echo "Original state saved in branch $BACKUP_BRANCH." >> "$LOG_FILE"
elif [ "$1" == "--fix-diverged" ]; then
  echo "Attempting to fix diverged branches..." >> "$LOG_FILE"
  
  # Make sure we have the latest information about the remote
  echo "Fetching latest updates from remote..." >> "$LOG_FILE"
  git fetch origin >> "$LOG_FILE" 2>&1
  
  # Check if branches have diverged
  LOCAL_COMMITS=$(git rev-list --count master ^origin/master 2>/dev/null || echo "0")
  REMOTE_COMMITS=$(git rev-list --count origin/master ^master 2>/dev/null || echo "0")
  
  echo "Local commits not in remote: $LOCAL_COMMITS" >> "$LOG_FILE"
  echo "Remote commits not in local: $REMOTE_COMMITS" >> "$LOG_FILE"
  
  # Set Git configuration for pull strategy
  git config pull.rebase false >> "$LOG_FILE" 2>&1
  
  if [ "$LOCAL_COMMITS" -gt 0 ] && [ "$REMOTE_COMMITS" -gt 0 ]; then
    # Create backup branch
    BACKUP_BRANCH="backup-diverged-$(date +%Y%m%d-%H%M%S)"
    git branch $BACKUP_BRANCH >> "$LOG_FILE" 2>&1
    echo "Backup branch '$BACKUP_BRANCH' created." >> "$LOG_FILE"
    
    # Add untracked Git backup files
    echo "Adding Git backup scripts to repository..." >> "$LOG_FILE"
    if [ -f "$BASE_DIR/Tools/git_backup.sh" ]; then
      git add "$BASE_DIR/Tools/git_backup.sh" >> "$LOG_FILE" 2>&1
    fi
    if [ -f "$BASE_DIR/Tools/git_backup_recovery.sh" ]; then
      git add "$BASE_DIR/Tools/git_backup_recovery.sh" >> "$LOG_FILE" 2>&1
    fi
    if [ -f "$BASE_DIR/Tools/setup_git_backup_cron.sh" ]; then
      git add "$BASE_DIR/Tools/setup_git_backup_cron.sh" >> "$LOG_FILE" 2>&1
    fi
    if [ -f "$BASE_DIR/Tools/system_cleanup.sh" ]; then
      git add "$BASE_DIR/Tools/system_cleanup.sh" >> "$LOG_FILE" 2>&1
    fi
    
    # Commit the backup tools
    git commit -m "Adding Git backup tools" >> "$LOG_FILE" 2>&1
    
    # Try merge with default strategy first
    echo "Attempting merge with default strategy..." >> "$LOG_FILE"
    git merge origin/master >> "$LOG_FILE" 2>&1
    MERGE_STATUS=$?
    
    if [ $MERGE_STATUS -ne 0 ]; then
      echo "Automatic merge failed. Trying alternative approach." >> "$LOG_FILE"
      git merge --abort >> "$LOG_FILE" 2>&1
      
      echo "Options:"
      echo "1) Keep local changes and force push (may overwrite remote changes)"
      echo "2) Discard local changes and pull from remote"
      echo "3) Create new branch with local changes and reset master to remote"
      echo "4) Abort and resolve manually"
      
      # Default to option 3 (safest option) for non-interactive usage
      choice="3"
      
      # If running in a terminal, ask for input
      if [ -t 0 ]; then
        read -p "Choose an option (1-4): " choice
      else
        echo "Non-interactive mode. Defaulting to option 3 (create new branch and reset)." >> "$LOG_FILE"
      fi
      
      case $choice in
        1)
          echo "Forcing push of local changes..." >> "$LOG_FILE"
          git push --force origin master >> "$LOG_FILE" 2>&1
          echo "Local changes have been pushed to remote, potentially overwriting remote changes." >> "$LOG_FILE"
          ;;
        2)
          echo "Discarding local changes and pulling from remote..." >> "$LOG_FILE"
          git reset --hard origin/master >> "$LOG_FILE" 2>&1
          echo "Local branch has been reset to match remote state." >> "$LOG_FILE"
          ;;
        3)
          echo "Creating a new branch with local changes..." >> "$LOG_FILE"
          NEW_BRANCH="local-changes-$(date +%Y%m%d-%H%M%S)"
          git checkout -b $NEW_BRANCH >> "$LOG_FILE" 2>&1
          echo "Local changes preserved in branch $NEW_BRANCH." >> "$LOG_FILE"
          
          echo "Resetting master branch to match remote..." >> "$LOG_FILE"
          git checkout master >> "$LOG_FILE" 2>&1
          git reset --hard origin/master >> "$LOG_FILE" 2>&1
          echo "Master branch now matches remote state." >> "$LOG_FILE"
          
          echo "To incorporate your local changes, use: git checkout $NEW_BRANCH" >> "$LOG_FILE"
          echo "Then merge specific changes back to master as needed." >> "$LOG_FILE"
          ;;
        4)
          echo "Recovery aborted. Please resolve conflicts manually." >> "$LOG_FILE"
          echo "Your current state is preserved, and a backup is available in branch '$BACKUP_BRANCH'." >> "$LOG_FILE"
          ;;
        *)
          echo "Invalid option. Recovery aborted." >> "$LOG_FILE"
          ;;
      esac
    else
      echo "Merge successful. Pushing changes..." >> "$LOG_FILE"
      git push origin master >> "$LOG_FILE" 2>&1
      PUSH_STATUS=$?
      
      if [ $PUSH_STATUS -eq 0 ]; then
        echo "Changes successfully pushed to remote." >> "$LOG_FILE"
      else
        echo "Push failed. You may need to fix additional conflicts." >> "$LOG_FILE"
      fi
    fi
  elif [ "$LOCAL_COMMITS" -gt 0 ]; then
    echo "Local is ahead of remote. Pushing local changes..." >> "$LOG_FILE"
    git push origin master >> "$LOG_FILE" 2>&1
  elif [ "$REMOTE_COMMITS" -gt 0 ]; then
    echo "Remote is ahead of local. Pulling remote changes..." >> "$LOG_FILE"
    git pull --no-edit origin master >> "$LOG_FILE" 2>&1
  else
    echo "Branches are not diverged. No action needed." >> "$LOG_FILE"
  fi
elif [ "$1" == "--interactive" ]; then
  echo "Interactive recovery mode"
  echo "Current Git status:"
  git status
  
  echo -e "\nOptions:"
  echo "1) Fix diverged branches"
  echo "2) Create backup branch"
  echo "3) Reset to remote (discard local changes)"
  echo "4) Show commit history"
  echo "5) Exit"
  
  read -p "Choose an option (1-5): " choice
  
  case $choice in
    1)
      echo "Executing: $0 --fix-diverged"
      $0 --fix-diverged
      ;;
    2)
      echo "Executing: $0 --create-backup"
      $0 --create-backup
      ;;
    3)
      echo "Executing: $0 --reset-hard"
      $0 --reset-hard
      ;;
    4)
      echo "Local commits not in remote:"
      git log --oneline --graph master ^origin/master
      echo -e "\nRemote commits not in local:"
      git log --oneline --graph origin/master ^master
      ;;
    5)
      echo "Exiting interactive mode."
      ;;
    *)
      echo "Invalid option. Exiting."
      ;;
  esac
else
  # Default behavior - display current Git status
  echo "Current Git Status:" >> "$LOG_FILE"
  git status >> "$LOG_FILE" 2>&1
  
  # Check for diverged branches
  LOCAL_COMMITS=$(git rev-list --count master ^origin/master 2>/dev/null || echo "0")
  REMOTE_COMMITS=$(git rev-list --count origin/master ^master 2>/dev/null || echo "0")
  
  if [ "$LOCAL_COMMITS" -gt 0 ] && [ "$REMOTE_COMMITS" -gt 0 ]; then
    echo "ALERT: Branches have diverged ($LOCAL_COMMITS local commits, $REMOTE_COMMITS remote commits)" >> "$LOG_FILE"
    echo "To fix this, run: $0 --fix-diverged" >> "$LOG_FILE"
  elif [ "$LOCAL_COMMITS" -gt 0 ]; then
    echo "INFO: $LOCAL_COMMITS local commits need to be pushed" >> "$LOG_FILE"
  elif [ "$REMOTE_COMMITS" -gt 0 ]; then
    echo "INFO: $REMOTE_COMMITS remote commits need to be pulled" >> "$LOG_FILE"
  else
    echo "INFO: Local and remote branches are in sync" >> "$LOG_FILE"
  fi
  
  show_help
fi

echo "===== Git Backup Recovery Completed - $(date '+%Y-%m-%d %H:%M:%S') =====" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Make the script executable
chmod +x "$0"
