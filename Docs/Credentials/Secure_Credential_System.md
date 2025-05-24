# Secure Credential System Documentation

## Overview

The Jamso-AI-Engine implements a secure credential management system that stores sensitive API keys, passwords, 
and other credentials in an encrypted database. The system prioritizes security while maintaining compatibility
with legacy components through fallback mechanisms.

## Key Features

- **AES-256 Encryption**: All credentials are encrypted in the database using AES-256 encryption
- **Secure Storage**: Credentials are stored in an SQLite database with proper permissions
- **Fallback Mechanism**: Automatically falls back to .env file if the database is unavailable
- **Bridge to Legacy Scripts**: Credential adapter for seamless integration with shell scripts
- **Audit Logging**: All credential access is logged for security auditing
- **User-friendly Configuration**: Configuration wizard with clear feedback

## Directory Structure

```
Jamso-AI-Engine/
  ├── src/
  │   ├── Credentials/         # Credential system directory
  │   │   ├── credentials_manager.py  # Main credential manager class
  │   │   ├── credentials.py   # Credential helper module for legacy code
  │   │   └── env.sh           # Shell script for exporting credentials to environment
  │   └── Database/
  │       └── Credentials/
  │           ├── credentials.db        # Encrypted credential database
  │           └── encryption.key        # Encryption key (secured with proper permissions)
  ├── Tools/
  │   ├── sync_credentials.py           # Tool for syncing credentials between DB and files
  │   ├── test_credential_adapter.py    # Bridge adapter for shell scripts
  │   ├── test_secure_credentials.sh    # Comprehensive credential system test
  │   ├── test_credentials.py           # Python test script for credential system
  │   └── test_env_variables.py         # Tool for testing environment variable loading
  └── .env                              # Environment file (used as fallback)
```

## Usage

### Storing Credentials

Credentials are automatically stored in the secure database when you run the configuration wizard:

```bash
python jamso_launcher.py --configure
# or select "Configure API Credentials" from the menu
```

You can also use the sync_credentials.py tool to import existing credentials from .env or env.sh:

```bash
python Tools/sync_credentials.py --import
```

### Accessing Credentials in Code

To access credentials in your Python code, use the CredentialManager:

```python
from src.Credentials.credentials_manager import CredentialManager

# Initialize the manager
manager = CredentialManager()

# Get a credential
api_key = manager.get_credential('service_name', 'credential_key')
```

For legacy components, the credentials.py helper module provides compatibility:

```python
from src.Credentials.credentials import get_api_credentials

# Get all Capital.com API credentials
creds = get_api_credentials()
api_key = creds['api_key']
username = creds['username']
password = creds['password']
```

### Using Credentials in Shell Scripts

For shell scripts, you can use the credential adapter:

```bash
# In your shell script, source the credentials:
eval "$(python Tools/test_credential_adapter.py --export)"

# Then use them like any environment variable:
echo "Using API key: $CAPITAL_API_KEY"
```

Alternatively, source the env.sh file directly:

```bash
source src/Credentials/env.sh
```

## Fallback Mechanism

The credential system implements a fallback strategy:

1. First try to access credentials from the secure database
2. If the database is unavailable, fall back to .env file
3. If neither is available, report an error

This ensures maximum availability while maintaining security.

## Testing the Credential System

A unified test runner is provided to verify all aspects of the credential system:

```bash
# Run the unified credential test suite
./Tools/run_credential_tests.sh
```

This interactive script allows you to run individual tests or all tests at once.

You can also run specific test tools directly:

```bash
# Comprehensive credential system test
./Tools/test_secure_credentials.sh

# Test specific credential access
python Tools/test_credentials.py

# Test environment variable loading
python Tools/test_env_variables.py

# Test the fallback API client
python Tools/test_fallback_api.py

# Test Telegram and OpenAI credential integration
python Tools/test_telegram_openai_integration.py

# Run end-to-end API integration tests
python Tools/test_integration.py
```

## Security Best Practices

- Never commit credential files to version control
- Keep the encryption key secure and with proper permissions
- Regularly audit credential access logs
- Rotate credentials periodically
- Use the configuration wizard to properly store credentials

## API Integration Testing

The enhanced integration test script (`test_integration.py`) verifies that the secure credential system correctly integrates with all external APIs:

```bash
# Run all API integration tests
python Tools/test_integration.py --all

# Test specific APIs
python Tools/test_integration.py --capital  # Test only Capital.com API
python Tools/test_integration.py --telegram  # Test only Telegram API
python Tools/test_integration.py --openai  # Test only OpenAI API

# Run with advanced options
python Tools/test_integration.py --all --retry-failed --retries 3  # Run all tests with retries
python Tools/test_integration.py --capital --format json  # Run Capital.com test with JSON report only
python Tools/test_integration.py --telegram --report-dir ./custom_reports  # Custom report location
```

This comprehensive test performs actual API calls to verify:
- Credentials are properly retrieved from the secure database
- Authentication with external APIs succeeds
- Basic API functionality works (market data retrieval for multiple symbols, message sending, AI responses)
- Error handling functions correctly in various scenarios
- Proper masking of sensitive information in logs and reports
- Performance metrics for API interactions

The test generates detailed reports:
1. JSON report with comprehensive test results, timestamps, and performance metrics
2. Text summary report with key findings and system information
3. Terminal output with color-coded status indicators for easy reading

## Troubleshooting

If you encounter issues with the credential system:

1. Check if the database file exists: `src/Database/Credentials/credentials.db`
2. Verify the encryption key: `src/Database/Credentials/encryption.key`
3. Ensure proper permissions: `chmod 600 src/Database/Credentials/encryption.key`
4. Check for errors in `Logs/jamso.log`
5. Run `./Tools/test_secure_credentials.sh` to diagnose issues
6. Verify credentials are exported: `source src/Credentials/env.sh && echo $CAPITAL_API_KEY`

If all else fails, the system will use credentials from the .env file.

## Integration

The credential system is integrated with:

- Configuration wizard in jamso_launcher.py
- Capital.com API clients
- Telegram alert system
- OpenAI API for AI Engine components
- Mobile alerts system
- All components requiring secure credential storage
