# Jamso AI Server

A robust server implementation for Jamso AI Bot, providing webhook functionality and API integration.

> **Note:** This project has undergone a directory structure migration from `/Backend/` to `/src/`. For details, see the [Migration Guide](Docs/Migration_Guide.md).

## System Requirements

- Linux-based OS (Ubuntu/Debian recommended)
- Python 3.8+ (Python 3.13 recommended)
- pip package manager

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

### Local Development

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

### Production Deployment

The application is configured to run with Phusion Passenger. After setup:

1. Ensure the `passenger_wsgi.py` file is in the root directory
2. To restart the application after changes:

   ```bash
   touch tmp/restart.txt
   ```

## Directory Structure

Jamso_AI_Server/
├── src/
│   ├── Database/       # Database models and interaction
│   ├── Credentials/    # API credentials and configuration
│   ├── Exchanges/      # Exchange API implementations
│   └── Webhook/        # Webhook implementation
│       ├── static/     # Static files (CSS, JS)
│       └── templates/  # HTML templates
├── Logs/               # Application logs
├── Tests/              # Test scripts
├── Tools/              # Utility scripts
├── .venv/              # Python virtual environment
├── requirements.txt    # Python dependencies
├── setup.sh            # Setup script
└── passenger_wsgi.py   # WSGI entry point

## Troubleshooting

If you encounter issues during setup:

1. Check the log files in `Logs/`
2. Ensure all environment variables are correctly set
3. Verify Python version with `python --version`
4. Make sure all dependencies are installed with `pip list`

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.
