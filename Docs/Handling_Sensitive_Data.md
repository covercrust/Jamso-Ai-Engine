# Handling Sensitive Data

This document provides guidelines for managing sensitive data like API keys, credentials, and tokens in the Jamso AI Engine project.

## General Principles

1. **Never commit secrets to Git**: Credentials should never be included in version control.
2. **Use environment variables**: Store sensitive information in environment variables.
3. **Implement credential rotation**: Change API keys and tokens periodically.
4. **Principle of least privilege**: Use the most restricted tokens and permissions possible.

## GitHub Secret Scanning

GitHub employs automated secret scanning to protect against accidental credential exposure:

1. **Push Protection**: GitHub will block pushes containing what appear to be API keys or credentials
2. **Error Message**: You'll see a "GH013: Repository rule violations" error with details about the detected secret
3. **Resolution**: You must remove the secret from your commit history before pushing again

If you encounter a blocked push due to secret scanning:

```bash
# 1. Remove the secret from the affected file
# 2. Amend your commit to remove the secret
git add path/to/affected/file
git commit --amend --no-edit
# 3. Try pushing again
git push origin branch-name
```

For more details, see [GitHub's documentation on resolving blocked pushes](https://docs.github.com/code-security/secret-scanning/working-with-secret-scanning-and-push-protection/working-with-push-protection-from-the-command-line#resolving-a-blocked-push).

## Environment Variables

We use environment variables to store sensitive information:

```bash
# Create a new environment file by copying the template
cp src/Credentials/env.sh.template src/Credentials/env.sh

# Edit the file with your credentials
nano src/Credentials/env.sh

# Load the environment variables
source src/Credentials/env.sh
```

## Template Example

Here's an example of what the template looks like (without real credentials):

```bash
#!/bin/bash
# Environment variables for Jamso AI Engine

# API Credentials
export CAPITAL_API_KEY="YOUR_API_KEY_HERE"
export CAPITAL_API_PASSWORD="YOUR_PASSWORD_HERE"
export CAPITAL_API_IDENTIFIER="YOUR_IDENTIFIER_HERE"

# Database Configuration
export DB_USER="db_username"
export DB_PASSWORD="db_password"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="jamso_db"

# Web Service Settings
export FLASK_SECRET_KEY="generate_a_random_key_here"
export WEBHOOK_TOKEN="your_webhook_token"
```

## Security Best Practices

1. **Keep Backup Files Secure**: If you create backup files (like `*.BAK`), ensure they're also excluded from Git.
2. **Use a Password Manager**: Consider using a password manager to generate and store strong passwords.
3. **Implement Secret Rotation**: Rotate secrets regularly, especially after team member changes.
4. **Use Secret Management Services**: For production, consider using services like:
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Docker secrets

## What To Do If Secrets Are Exposed

If sensitive data is accidentally committed to Git:

1. **Revoke the credentials immediately**: Change any exposed API keys, passwords, or tokens.
2. **Remove from Git history**: Use tools like `git filter-branch` or `BFG Repo Cleaner` to remove sensitive data.
3. **Force push changes**: After cleaning history, force push the changes.
4. **Notify relevant parties**: Inform your team and any affected services.

## Contact

For questions about secure credential management, contact the security team.
