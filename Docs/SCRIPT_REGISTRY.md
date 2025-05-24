# Jamso AI Engine - Script Registry

This document provides a centralized registry of all scripts in the Jamso AI Engine project.
Use this as a reference to find and run the appropriate script for your needs.

## Deployment Scripts (located in `Scripts/Deployment/`)

| Script | Purpose |
|--------|---------|
| `run_local.sh` | Start the application in local development mode |
| `run_with_monitoring.sh` | Run the application with resource monitoring |
| `start_jamso.sh` | Start the Jamso AI Engine in production mode |
| `stop_local.sh` | Stop locally running instances of the application |
| `deploy.py` | Python script for deploying the application |
| `deploy_noninteractive.py` | Non-interactive version of the deployment script |

## Maintenance Scripts (located in `Scripts/Maintenance/`)

| Script | Purpose |
|--------|---------|
| `cleanup_cache.sh` | Remove Python cache files and other temporary files |
| `cleanup_redis.sh` | Clean up Redis database |
| `change_summary.sh` | Generate a summary of recent code changes |
| `rebuild_venv.sh` | Rebuild the Python virtual environment from scratch |
| `cleanup.sh` | General cleanup utility |
| `health_check.sh` | Check system health status |

## Test Scripts (located in various test directories)

### Integration Tests (`Tests/Integration/`)
| Script | Purpose |
|--------|---------|
| `test_integration.py` | Run API integration tests |
| `test_mobile_alerts.sh` | Test mobile alert functionality |

### Unit Tests (`Tests/Unit/`)
| Script | Purpose |
|--------|---------|
| `basic_regime_test.py` | Test the regime detector functionality |
| `test_fallback_optimizer.py` | Test fallback optimizer |
| `test_optimizer_fix.py` | Test optimizer fixes |
| `test_regime_detector.py` | Test regime detector |
| `test_sentiment_generation.py` | Test sentiment generation functionality |

## Tool Scripts (located in `Tools/`)

This directory contains various utility scripts, organized by category:

### General Tools

| Script | Purpose |
|--------|---------|
| `check_dependencies.sh` | Check for required dependencies |
| `cleanup_sessions.py` | Clean up expired sessions |
| `deploy.py` | Deployment utility |
| `fix_permissions.sh` | Fix file permissions |
| `health_check.sh` | Check system health |
| `setup_credentials.sh` | Set up credentials |
| `test_integration.py` | Integration test utility |

### Database Tools (`Tools/Database/`)

| Script | Purpose |
|--------|---------|
| `check_sentiment_db.py` | Show statistics about sentiment database |
| `debug_sentiment_db.py` | Debug sentiment database issues |
| `generate_sentiment_data.py` | Generate sentiment data for testing |
| `optimize_db.py` | Optimize database performance |

### Health Check Tools (`Tools/HealthCheck/`)

| Script | Purpose |
|--------|---------|
| `health_check_temp.py` | Verify Python dependencies and imports |
| `simple_memory_monitor.py` | Monitor system memory usage |

## Main Application Scripts (located in root directory)

| Script | Purpose |
|--------|---------|
| `jamso_launcher.py` | Main entry point for launching the application |
| `setup.py` | Python package setup |
| `setup.sh` | Environment setup script |
| `start_app.py` | Alternative application entry point |

## VS Code Tasks

The project includes predefined VS Code tasks for common operations:

1. **Run All API Integration Tests**
   - Command: `python3 ${workspaceFolder}/Tools/test_integration.py --all`

2. **Run Capital.com API Test**
   - Command: `python3 ${workspaceFolder}/Tools/test_integration.py --capital`

3. **Run Telegram API Test**
   - Command: `python3 ${workspaceFolder}/Tools/test_integration.py --telegram`

4. **Run OpenAI API Test**
   - Command: `python3 ${workspaceFolder}/Tools/test_integration.py --openai`

5. **Run Credential System Tests**
   - Command: `bash ${workspaceFolder}/Tools/run_credential_tests.sh`
