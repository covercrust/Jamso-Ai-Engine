# Jamso AI Engine - Project Structure

This document provides an overview of the Jamso AI Engine project structure to help developers understand the organization and navigate the codebase.

## Directory Structure

### Core Directories

- **`src/`**: Main source code directory
  - **`AI/`**: AI models and machine learning components
  - **`Credentials/`**: Credential management (gitignored)
  - **`Database/`**: Database integration and models
  - **`Exchanges/`**: Trading exchange integrations
  - **`Logging/`**: Logging utilities
  - **`Notifications/`**: Alert and notification systems
  - **`Optional/`**: Optional modules and plugins
  - **`PineScripts/`**: TradingView Pine scripts
  - **`Webhook/`**: Webhook handlers and integrations

### Support Directories

- **`Dashboard/`**: Web-based user interface
- **`Docs/`**: Documentation files
  - **`SCRIPT_REGISTRY.md`**: Central registry of all scripts
- **`Tests/`**: Automated tests
  - **`Unit/`**: Unit tests
  - **`Integration/`**: Integration tests
  - **`Performance/`**: Performance tests
  - **`Capital.com/`**: Capital.com-specific tests
  - **`Webhook/`**: Webhook-specific tests
- **`Tools/`**: Utility scripts and tools
- **`Scripts/`**: Organized script directories
  - **`Maintenance/`**: Maintenance scripts
  - **`Deployment/`**: Deployment scripts
- **`Data/`**: Data files
  - **`Charts/`**: Visualization and chart files
  - **`Optimized_Params/`**: Optimization parameter files
- **`Logs/`**: Application logs (gitignored)
- **`Archive/`**: Archived code (not actively used)
- **`tmp/`**: Temporary files (gitignored)
- **`.venv/`**: Python virtual environment (gitignored)

## Key Files

- **`jamso_launcher.py`**: Main application entry point
- **`setup.py`**: Python package setup
- **`requirements.txt`**: Python dependencies
- **`Dockerfile`** & **`docker-compose.yml`**: Docker configuration
- **`setup.sh`**: Environment setup script
- **`README.md`**: Project overview and documentation

## Maintenance Scripts

- **`Scripts/Maintenance/cleanup_cache.sh`**: Removes Python cache files and temporary files
- **`setup.sh`**: Sets up the development environment
- **`Scripts/Deployment/run_local.sh`**: Runs the application locally
- **`Scripts/Deployment/stop_local.sh`**: Stops the locally running application
- **`Scripts/Maintenance/rebuild_venv.sh`**: Rebuilds the virtual environment

## Development Workflow

1. Use `setup.sh` to set up your development environment
2. Run `./cleanup_cache.sh` periodically to remove cache files (symlinked to Scripts/Maintenance)
3. Use `./run_local.sh` to start the application locally (symlinked to Scripts/Deployment)
4. Use `./stop_local.sh` to stop the running application (symlinked to Scripts/Deployment)

## Testing

1. Unit tests are located in `Tests/Unit/`
2. Integration tests are located in `Tests/Integration/`
3. Performance tests are located in `Tests/Performance/`
4. Use VS Code tasks for running common test operations

## Best Practices

- Keep sensitive credentials out of version control
- Run tests before submitting changes
- Update documentation when adding new features
- Follow the existing code structure when adding new modules
- Use the appropriate directory for new files based on their purpose
