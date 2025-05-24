# Jamso AI Engine

An advanced trading system with AI-powered parameter optimization, sentiment analysis integration, and real-time monitoring.

> **Note:** This project has undergone a directory structure migration from `/Backend/` to `/src/`. For details, see the [Migration Guide](Docs/Migration_Guide.md).

## Quick Start

The easiest way to get started with Jamso AI Engine is to use the launcher:

```bash
# Start the main launcher
python jamso_launcher.py
```

### Project Structure

This project has been organized according to a clean directory structure to improve maintainability:

- **`src/`** - Core source code
- **`Tests/`** - All test files (Unit, Integration, Performance)
- **`Scripts/`** - Deployment and maintenance scripts
- **`Data/`** - Chart outputs and optimization parameters
- **`Docs/`** - Documentation files

For a complete overview, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) and [Docs/SCRIPT_REGISTRY.md](Docs/SCRIPT_REGISTRY.md).

### Configuration Wizard

For new installations, run the Configuration Wizard from the launcher's Configuration menu to set up your environment:

1. Launch the application: `python jamso_launcher.py`
2. Navigate to "System Configuration" (Option 5)
3. Select "Run Configuration Wizard" (Option 1)

The wizard will guide you through:
- Setting up API credentials (securely stored in database)
- Configuring email and mobile alerts
- Installing required dependencies
- Setting up logging preferences

#### Secure Credential System

Jamso AI Engine uses a secure credential management system that:
- Encrypts all sensitive credentials in a database using AES-256 encryption
- Provides role-based access control for credential access
- Maintains a comprehensive audit log of all credential access and changes
- Automatically falls back to .env file when the database is unavailable
- Verifies credential integrity after storage
- Maintains synchronized copies in both the database and .env file for redundancy

The Configuration Wizard automatically integrates with this system when setting API credentials.

For detailed documentation about the credential system, see [Secure Credential System](Docs/Credentials/Secure_Credential_System.md).

To test and manage the credential system:
```bash
# Run the unified credential test suite
./Tools/run_credential_tests.sh

# Or run the credential system configuration tool
./Tools/setup_credentials.sh
```

The unified test suite provides a comprehensive set of tests for all credential types and integration points, including:
- Capital.com API credentials
- Telegram bot credentials
- OpenAI API credentials
- Environment variable synchronization
- Database storage and encryption

The credential system configuration tool provides options to:
1. Run comprehensive credential system tests
2. Test database access directly
3. Update Capital.com API credentials 
4. Check synchronization between database and .env file
5. Run the configuration wizard

For developers, a Python test script is also available:
```bash
# Run Python-based credential tests
python Tools/test_credentials.py
```

Alternatively, you can test specific features directly:

```bash
# Test mobile alerts
./test_mobile_alerts.sh

# Run Capital.com API optimization
python src/AI/capital_data_optimizer.py --symbol BTCUSD --timeframe HOUR --days 30 --use-sentiment
```

## System Requirements

- Linux-based OS (Ubuntu/Debian recommended)
- Python 3.8+ (Python 3.13 recommended)
- pip package manager
- Virtual environment (.venv recommended)

## GitHub Repository Setup

This project is configured to use GitHub for version control. To set up the GitHub repository:

1. Follow the instructions in [GitHub Setup Guide](Docs/GitHub_Setup_Guide.md)
2. For authentication help, see [GitHub Authentication Guide](Docs/GitHub_Authentication_Guide.md)
3. Or use our automated tool:

   ```bash
   python Tools/create_github_repo.py
   ```

   This will create a new GitHub repository and push your local code to it.

## Installation

### Automatic Setup (Recommended)

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/Jamso_AI_Server.git
   cd Jamso_AI_Server
   ```

2. Run the setup script:

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   This script will:
   - Check for and install the latest Python version if needed
   - Create a Python virtual environment
   - Install all required dependencies
   - Set up necessary directories and configuration files
   - Configure the Passenger WSGI file for deployment

3. Configure your environment variables:

   ```bash
   nano src/Credentials/env.sh
   ```

   Update the API credentials and other configuration options.

4. Load your environment variables:

   ```bash
   source src/Credentials/env.sh
   ```

### Manual Setup

If you prefer to set up manually:

1. Install Python 3.13:

   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y software-properties-common
   sudo add-apt-repository -y ppa:deadsnakes/ppa
   sudo apt-get update
   sudo apt-get install -y python3.13 python3.13-venv python3.13-dev
   ```

2. Create a virtual environment:

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   ```bash
   cp src/Credentials/env.sh.example src/Credentials/env.sh
   nano src/Credentials/env.sh
   ```

## Running the Application

### Using the Launcher (Recommended)

The Jamso AI Engine now includes a comprehensive launcher that provides a user-friendly interface for all features:

1. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

2. Run the launcher:

   ```bash
   python jamso_launcher.py
   ```

The launcher provides access to:

- Capital.com API integration
- Sentiment analysis
- Optimization dashboard
- Mobile alerts
- System configuration
- Documentation

### Local Development (Manual Method)

1. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

2. Load environment variables:

   ```bash
   source src/Credentials/env.sh
   ```

3. Run the application:

   ```bash
   python src/Webhook/app.py
   ```

Alternatively, use the provided development scripts:

```bash
# Start the application
./run_local.sh

# Stop the application
./stop_local.sh

# Clean up cache files
./cleanup_cache.sh

# Rebuild virtual environment from scratch
Scripts/Maintenance/rebuild_venv.sh
```

### Production Deployment

The application is configured to run with Phusion Passenger. After setup:

1. Ensure the `passenger_wsgi.py` file is in the root directory
2. To restart the application after changes:

   ```bash
   touch tmp/restart.txt
   ```

## Directory Structure

Jamso_AI_Engine/
├── src/
│   ├── AI/             # AI and optimization modules
│   │   ├── capital_data_optimizer.py   # Capital.com API integration
│   │   ├── sentiment_integration.py    # Sentiment analysis integration
│   │   ├── optimization_dashboard.py   # Visualization dashboard
│   │   ├── scheduled_optimization.py   # Scheduled optimization
│   │   └── mobile_alerts.py           # Mobile alerts system
│   ├── Database/       # Database models and interaction
│   ├── Credentials/    # API credentials and configuration
│   ├── Exchanges/      # Exchange API implementations
│   └── Webhook/        # Webhook implementation
│       ├── static/     # Static files (CSS, JS)
│       └── templates/  # HTML templates
├── Docs/               # Documentation
│   └── AI/             # AI module documentation
├── Logs/               # Application logs
├── Tests/              # Test scripts
├── Tools/              # Utility scripts
│   ├── test_mobile_alerts.sh          # Mobile alerts test script
│   └── test_sentiment_integration.sh  # Sentiment integration test
├── dashboard/          # Generated static dashboard
├── .venv/              # Python virtual environment
├── jamso_launcher.py   # Main application launcher
├── test_mobile_alerts.sh  # Mobile alerts launch script
├── requirements.txt    # Python dependencies
└── setup.sh            # Setup script

## [2025-05-19] New Features: Mobile Alerts and Central Launcher

## Mobile Alerts System

The Jamso AI Engine now includes a comprehensive mobile alerts system that provides real-time notifications about critical events:

- **Multiple Channels**: Support for email, SMS, push notifications, and webhook integrations
- **Priority Levels**: Different alert levels (info, warning, critical) for appropriate escalation
- **Configuration Options**: Extensive customization through `.env` file
- **Rate Limiting**: Prevents alert fatigue with configurable rate limits

To test the mobile alerts system:

```bash
# Using the launcher
python jamso_launcher.py
# Select option 4 (Mobile Alerts)

# Or using the direct script
./test_mobile_alerts.sh
```

For more details, see [Mobile Alerts Integration](Docs/AI/Mobile_Alerts_Integration.md).

## Central Launcher

A new central launcher provides a unified interface for all Jamso AI Engine features:

```bash
python jamso_launcher.py
```

The launcher offers:
- Interactive menus for all features
- Simplified configuration and testing
- Guided setup for API credentials
- Access to documentation
- System status monitoring

# [2025-05-12] Migration Note: Dashboard app.py renamed

- `Dashboard/app.py` has been renamed to `Dashboard/dashboard_app.py` to avoid confusion with `src/Webhook/app.py`.

- Update your scripts and documentation to use the new filename for running or importing the dashboard app.

## [2025-05-12] Performance: Redis Session Support

- Dashboard now supports Redis for session storage. Set `SESSION_TYPE=redis` and `REDIS_URL` in your `.env` to enable.

- This offloads session management from CPU to memory, making better use of available RAM and improving performance on systems with lots of memory.

## Troubleshooting

If you encounter issues during setup:

1. Check the log files in `Logs/`
2. Ensure all environment variables are correctly set
3. Verify Python version with `python --version`
4. Make sure all dependencies are installed with `pip list`
5. Run the health check: `Scripts/Maintenance/health_check.sh`
6. Check for cache issues: `./cleanup_cache.sh`

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.
