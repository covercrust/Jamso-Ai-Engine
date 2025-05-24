# API Key Security Guide

## Introduction

This guide outlines best practices for managing API keys and other sensitive credentials in the Jamso AI Engine project. Proper handling of credentials is essential to protect our services and data from unauthorized access.

## Never Commit API Keys to Git

- **NEVER** commit real API keys, passwords, or other secrets to the Git repository
- Always use placeholder values in example files and documentation
- Use `.gitignore` to exclude files containing real credentials
- Even placeholder values like "YOUR_API_KEY_HERE" should follow conventions to avoid triggering security scanners

## GitHub Secret Scanning

GitHub employs automated secret scanning to prevent API keys and credentials from being accidentally committed. If you attempt to push a commit containing what appears to be a secret:

1. GitHub will block your push with a "GH013: Repository rule violations" error
2. The error will show the file and line number containing the potential secret
3. You must remove the secret before you can push again

To fix a blocked push due to secret scanning:

```bash
# 1. Remove the secret from the file
# 2. Commit the fixed file
git add path/to/file/with/secret
git commit -m "Remove sensitive information"
# 3. Try pushing again
git push origin branch-name
```

## Using Environment Variables

The Jamso AI Engine uses environment variables stored in `src/Credentials/env.sh` to manage sensitive information. This file is automatically loaded when you run the application.

### Setup Process

1. Copy the example file: `cp src/Credentials/env.sh.example src/Credentials/env.sh`
2. Edit the file with your actual API keys: `nano src/Credentials/env.sh`
3. Make sure the file has execution permissions: `chmod +x src/Credentials/env.sh`

## Security Best Practices

- **Rotate keys regularly** - Change API keys periodically
- **Use minimum permissions** - Ensure API keys have only the permissions they need
- **Monitor for unusual activity** - Watch for unexpected usage of your API keys
- **Separate development and production keys** - Use different keys for different environments
- **Set up API key restrictions** - Restrict API keys by IP address or other means where possible

## What to Do If a Key Is Compromised

If you suspect an API key has been compromised:

1. **Revoke the key immediately** - Log in to the service provider and deactivate the key
2. **Generate a new key** - Create a replacement key
3. **Update all instances** - Update the key in your local environment and any deployment environments
4. **Monitor for abuse** - Check for any unauthorized usage that may have occurred
5. **Review code and commits** - Ensure no other keys were accidentally exposed

## Credential Storage Systems

For production environments, consider using a dedicated secrets management solution:

- **HashiCorp Vault** - Enterprise-grade secrets management
- **AWS Secrets Manager** - For AWS environments
- **Azure Key Vault** - For Azure environments
- **Docker secrets** - For Docker environments
- **Kubernetes secrets** - For Kubernetes environments

## Adding New API Services

When adding integration with a new API service:

1. Add placeholder values to `env.sh.example`
2. Document the required credentials in this guide
3. Update the setup script to prompt for the new credentials
4. Add validation to ensure the application fails gracefully if credentials are missing

## Reporting Security Issues

If you discover a security vulnerability or exposed credentials, please report it immediately to the security team and do not disclose it publicly.
