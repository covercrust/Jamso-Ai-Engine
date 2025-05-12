# Jamso AI Server Setup Guide

## Installation Date

Mon 28 Apr 2025 08:47:37 PM EEST

## Server Path

/home/jamso-ai-server/Jamso-Ai-Engine

## Hardware Configuration

- CPU: Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz (4 cores)
- Memory: 31919 MB
- Available Disk: 865G
- Python Version: Python 3.12.3

## Installation Steps

1. Clone the repository
2. Run the setup script: `./setup.sh`
3. Configure environment variables: `nano src/Credentials/env.sh`
4. Load environment: `source src/Credentials/env.sh`
5. Configure session settings in `.env`:

   ```env
   SESSION_TYPE=filesystem
   SESSION_FILE_DIR=/home/jamso-ai-server/Jamso-Ai-Engine/instance/dashboard_sessions
   SESSION_COOKIE_SECURE=True
   SESSION_COOKIE_HTTPONLY=True
   SESSION_COOKIE_SAMESITE=Lax
   ```

6. Start the application: `python start_app.py`

## Hardware Optimizations

- Low Memory Mode: false
- Multi-Core Processing: true

## Troubleshooting

Check logs in `Logs/` directory
