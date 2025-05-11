#!/bin/bash
# Load API credentials from the credential manager
# This script is called by env.sh

# Set paths
ROOT_DIR="/home/jamso-ai-server/Jamso-Ai-Engine"
PYTHON_PATH="$ROOT_DIR"
CREDENTIALS_SCRIPT="$ROOT_DIR/src/Credentials/credentials_manager.py"

# Load Python environment
if [ -f "$ROOT_DIR/.venv/bin/activate" ]; then
    # If virtual environment exists, use it
    source "$ROOT_DIR/.venv/bin/activate"
fi

# Check if credential manager exists
if [ ! -f "$CREDENTIALS_SCRIPT" ]; then
    echo "ERROR: Credential manager not found at $CREDENTIALS_SCRIPT"
    exit 1
fi

# Generate temporary credentials file
TEMP_CREDS_FILE=$(mktemp)
PYTHONPATH="$PYTHON_PATH" python3 "$CREDENTIALS_SCRIPT" --action env > "$TEMP_CREDS_FILE"

# Source the temporary credentials file
source "$TEMP_CREDS_FILE"

# Clean up
rm "$TEMP_CREDS_FILE"

# Verify credentials were loaded
if [ -z "$CAPITAL_API_KEY" ] || [ -z "$CAPITAL_API_LOGIN" ] || [ -z "$CAPITAL_API_PASSWORD" ]; then
    echo "WARNING: Some Capital.com API credentials could not be loaded from credential manager!"
    echo "Please ensure credentials are properly set up in the dashboard."
else
    echo "Capital.com API credentials loaded successfully from credential manager"
fi
