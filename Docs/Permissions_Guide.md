# Jamso AI Server Permission Structure

This document outlines the permission structure for the Jamso AI Server environment to ensure security and proper functionality.

## Permission Levels

| Permission | Octal | Description | Use Case |
|------------|-------|-------------|----------|
| 755 | rwxr-xr-x | Owner: read/write/execute  | Executable scripts, directories |
|     |           | Group & Others: read/execute |                                 |
| 644 | rw-r--r-- | Owner: read/write          | Regular files (code, docs)      |
|     |           | Group & Others: read        |                                 |
| 600 | rw------- | Owner: read/write          | Sensitive configuration, credentials, databases |
|     |           | Group & Others: none        |                                 |

## Critical Files and Directories

### Configuration Files

- Credentials are now managed securely using a database-based system. The `env.sh` file is no longer used.
- `/home/jamso-ai-server/Jamso-Ai-Engine/src/Credentials/active_account.json` - **600**

### Database Files

- `/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/*.db` - **600**

### Executable Scripts

- All Python application scripts (`*.py`) - **755**
- All shell scripts (`*.sh`) - **755**

### Directories

- All directories - **755**
- Log directories - **755**

## Maintaining Permissions

Two utility scripts have been created to help maintain proper permissions:

1. **Fix Permissions Script**:
   - Location: `/home/jamso-ai-server/Jamso-Ai-EngineTools/fix_permissions.sh/fix_permissions.sh`
   - Use: Run this script to reset all permissions to their proper values
   - Command: `.Tools/fix_permissions.sh/fix_permissions.sh`

2. **Backup Permissions Script**:
   - Location: `/home/jamso-ai-server/Jamso-Ai-EngineTools/fix_permissions.sh/backup_permissions.sh`
   - Use: Run this script to create a restoration script for current permissions
   - Command: `.Tools/fix_permissions.sh/backup_permissions.sh`
   - Restoring: `bash permissions_backup.txt`

## Best Practices

1. **Sensitive Files**:
   - Keep configuration files with credentials at 600 permissions
   - Never commit sensitive files to version control

2. **Executable Files**:
   - All Python scripts intended to be directly executed should:
     - Have a shebang line (`#!/usr/bin/env python3`)
     - Have 755 permissions
   - All shell scripts should have 755 permissions

3. **After Updates**:
   - Run the fix_permissions.sh script after updating the codebase
   - Or restore from a backup using the generated backup file

4. **Troubleshooting**:
   - If you encounter "Permission denied" errors, check the file permissions
   - Use `ls -la filename` to view current permissions
   - Execute `chmod +x filename` to make a file executable
