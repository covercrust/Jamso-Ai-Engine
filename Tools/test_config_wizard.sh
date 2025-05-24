#!/bin/bash
# Test script for the configuration wizard

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")

# Clear screen
clear

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║${YELLOW}          Configuration Wizard Test Launcher             ${BLUE}║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Make sure we're in the correct directory
cd "$BASE_DIR" || exit 1

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Not running in a virtual environment. Activating...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}Virtual environment activated.${NC}"
    else
        echo -e "${YELLOW}No .venv directory found. Running without virtual environment.${NC}"
    fi
fi

echo "This script will launch the Jamso-AI-Engine with direct access to the Configuration Wizard."
echo "The Configuration Wizard helps you set up:"
echo "  - Capital.com API credentials (stored in secure credential database)"
echo "  - Email notification settings"
echo "  - Mobile alerts configuration" 
echo "  - System dependencies"
echo "  - Logging preferences"
echo ""
echo "After running the Configuration Wizard, you can test the credential system with:"
echo "  ./Tools/test_credential_system.sh   - Full credential system test and utilities"
echo "  ./Tools/test_credentials.py         - Python-based credential system test"
echo ""
echo -e "${GREEN}Press Enter to launch the Configuration Wizard...${NC}"
read -r

# Launch the launcher with the configuration wizard
python "$BASE_DIR/jamso_launcher.py" --option 5
