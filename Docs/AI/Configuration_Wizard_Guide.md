# Configuration Wizard Guide

The Configuration Wizard is a powerful feature of the Jamso-AI-Engine that helps you properly set up your environment and configure all the necessary components for optimal operation.

## Accessing the Configuration Wizard

There are two ways to access the Configuration Wizard:

1. **Through the Main Launcher:**
   - Launch the main application: `python jamso_launcher.py`
   - Navigate to "System Configuration" (Option 5)
   - Select "Run Configuration Wizard" (Option 1)

2. **Using the Direct Test Script:**
   - Run the configuration wizard test script: `./Tools/test_config_wizard.sh`

## What the Wizard Configures

The Configuration Wizard guides you through setting up:

### 1. Environment File (.env)

You can either:
- Use an existing .env file
- Edit an existing .env file
- Create a new .env file from scratch

### 2. Capital.com API Credentials

Required for fetching market data and executing trades:
- API Key
- API Login
- API Password

#### Secure Credential Storage System

The Configuration Wizard integrates with a secure credential database system:

- **Primary Storage**: All sensitive credentials are encrypted and stored in a secure SQLite database
- **Security Features**:
  - AES-256 encryption for all stored credentials
  - Role-based access control to limit credential access
  - Audit logging of all credential access attempts
  - PBKDF2 key derivation with multiple iterations for enhanced security
- **Fallback Mechanism**: If the secure database is unavailable, credentials will be stored in the .env file
- **Verification**: The system verifies that credentials were stored correctly in the database
- **Backup**: Credentials are also stored in the .env file as a backup, even when the database is available

#### Testing the Credential System

You can test the credential system using:

```bash
# Run the credential system test script
./Tools/test_credential_system.sh
```

This script provides options to:
- Run comprehensive credential system tests
- Test database access
- Update Capital.com API credentials
- Check synchronization between the database and .env file

### 3. Email Alert Settings

Configure email notifications for important system events:
- Sender email address
- Recipient email address
- Email password
- SMTP server and port

### 4. Mobile Alert Settings

Enable different notification methods:
- Email alerts
- SMS alerts (with gateway configuration)
- Push notifications (with API key and app ID)
- Webhook integrations

### 5. Dependencies

The wizard checks for and offers to install required Python packages:
- requests
- numpy
- pandas
- matplotlib
- scikit-learn
- python-dotenv
- flask
- websocket-client

### 6. Logging Configuration

Set up logging for effective system monitoring:
- Select log level (debug/info/warning/error)
- Enable or disable file logging
- Configure log file location

## Secure Credential Storage

Jamso-AI-Engine uses a secure credential database to store sensitive information like API keys and passwords.

### How It Works

1. **Encryption**: All sensitive data is encrypted before being stored in the database
2. **Access Control**: Role-based access control restricts who can read or write credentials
3. **Audit Trail**: All credential access is logged for security monitoring

### Credential Types Stored

- **Capital.com API credentials** - For trading operations
- **Email credentials** - For alert notifications
- **SMS gateway credentials** - For mobile notifications
- **Push notification credentials** - For app alerts
- **Webhook integration tokens** - For external system integration

### Fallback Mechanism

If the credential database is unavailable (e.g., during initial setup or in case of database issues), the system will fall back to using the `.env` file to store and retrieve credentials.

## Best Practices

- **API Credentials:** Keep your Capital.com API credentials secure and never share them
- **Email Security:** Use app-specific passwords for email services that support them
- **Regular Updates:** Re-run the configuration wizard after major system updates
- **Testing:** After configuration, use the test options in the launcher to verify functionality

## Troubleshooting

If you encounter issues with the configuration:

1. Check the logs in the `Logs` directory
2. Verify your credentials in the .env file
3. Ensure all dependencies are properly installed
4. Make sure your email provider allows SMTP access

For additional help, refer to the main documentation or contact support.
