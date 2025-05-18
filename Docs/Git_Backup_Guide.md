# Git Backup System for Jamso AI Engine

This document describes the Git backup system for the Jamso AI Engine.

## Overview

The Git backup system provides automated and reliable backups of your codebase to a remote Git repository. The system consists of several scripts:

1. `git_backup_simple.sh` - Simplified and robust backup script (recommended)
2. `git_backup.sh` - Main backup script with advanced features
3. `git_backup_recovery.sh` - Tool to recover from problematic Git states
4. `setup_git_credentials.sh` - Script to configure Git credentials
5. `install_git_backup_cron.sh` - Script to set up automated backups (recommended)
6. `check_git_backup_status.sh` - Script to check backup status
7. `setup_git_backup_cron.sh` - Alternative script to set up automated backups

## Setup Instructions

### 1. Configure Git Credentials

First, set up your Git credentials to allow automated backups:

```bash
Tools/setup_git_credentials.sh
```

Follow the prompts to authenticate with your GitHub account. This script will:
- Configure Git to store your credentials
- Test the connection to GitHub

### 2. Set Up Automated Backups

To configure daily automated backups:

```bash
Tools/install_git_backup_cron.sh
```

This will create a cron job that runs the backup script daily at 2:00 AM.

Alternatively, you can use the other setup script:

```bash
Tools/setup_git_backup_cron.sh
```

## Manual Operations

### Run a Backup Manually

To run a backup manually, we recommend using the simplified backup script:

```bash
Tools/git_backup_simple.sh
```

Alternatively, you can use the more complex script with advanced features:

```bash
Tools/git_backup.sh
```

### Recovering from Problems

If you encounter Git issues, such as diverged branches or failed pushes, use the recovery tool:

```bash
# Show help and options
Tools/git_backup_recovery.sh --help

# Interactive recovery mode
Tools/git_backup_recovery.sh --interactive

# Fix diverged branches automatically
Tools/git_backup_recovery.sh --fix-diverged

# Reset to remote state (caution: local changes will be lost)
Tools/git_backup_recovery.sh --reset-hard

# Create a backup branch of current state
Tools/git_backup_recovery.sh --create-backup
```

## Monitoring

The Git backup system creates logs in the following locations:

- `Logs/git_backup.log` - Main backup log
- `Logs/git_backup_status.log` - Status of the last backup operation
- `Logs/git_backup_error.log` - Created when errors occur
- `Logs/git_recovery.log` - Log for recovery operations

You can check the status of Git backups with:

```bash
Tools/check_git_backup_status.sh
```

This will display detailed backup status including:
- Last backup attempt time
- Current Git repository status
- Scheduled backup information
- Any detected issues

You can also use the system cleanup script which includes backup status:

```bash
Tools/system_cleanup.sh
```

This will display backup status along with other system information.

## Excluded Files

The following types of files are excluded from Git backups:

- Database files (`*.db`)
- Log files (`*.log`)
- Session data in `instance/sessions/`
- Python cache files (`__pycache__`, `*.pyc`)
- Other temporary files

## Troubleshooting

If backups are failing:

1. Check the logs in `Logs/git_backup.log`
2. Verify Git credentials are working
3. Check internet connectivity
4. Run `Tools/git_backup_recovery.sh --interactive` to diagnose and fix issues

For persistent problems, you may need to:

1. Reset Git credentials: `Tools/setup_git_credentials.sh`
2. Check for diverged branches and resolve them
3. Verify your remote repository is accessible

## Security Notes

- Git credentials are stored using Git's credential helper
- Sensitive files like database files and credentials are excluded from backups
- Consider reviewing `.gitignore` to ensure sensitive data isn't included
