#!/bin/bash
# Quick start script for Jamso-AI-Engine
#
# This script provides a quick way to launch Jamso-AI-Engine and displays
# a welcome message with instructions for first-time users.

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")

# Clear screen
clear

# Display welcome message
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   JAMSO-AI-ENGINE                          ║${NC}"
echo -e "${BLUE}║              Advanced Trading Platform                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Welcome to Jamso-AI-Engine!${NC}"
echo ""
echo "This quick-start script will help you get started with the platform."
echo ""

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Not running in a virtual environment.${NC}"
    if [ -d "$BASE_DIR/.venv" ]; then
        echo "Activating virtual environment..."
        source "$BASE_DIR/.venv/bin/activate"
        echo -e "${GREEN}Virtual environment activated.${NC}"
    else
        echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
        python3 -m venv "$BASE_DIR/.venv"
        source "$BASE_DIR/.venv/bin/activate"
        echo -e "${GREEN}Virtual environment created and activated.${NC}"
        
        # Install dependencies
        echo "Installing dependencies..."
        pip install --upgrade pip
        pip install -r "$BASE_DIR/requirements.txt"
        echo -e "${GREEN}Dependencies installed.${NC}"
    fi
fi

echo ""
echo "Choose what you'd like to do:"
echo ""
echo "1) Launch the main application (recommended for first-time users)"
echo "2) Test mobile alerts functionality"
echo "3) Run Capital.com API optimization"
echo "4) Show change summary"
echo "5) Exit"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        # Launch main application
        echo "Starting Jamso-AI-Engine launcher..."
        python "$BASE_DIR/jamso_launcher.py"
        ;;
    2)
        # Test mobile alerts
        echo "Starting mobile alerts test..."
        "$BASE_DIR/test_mobile_alerts.sh"
        ;;
    3)
        # Run Capital.com API optimization
        echo "Starting Capital.com optimization..."
        cd "$BASE_DIR"
        python src/AI/capital_data_optimizer.py
        ;;
    4)
        # Show change summary
        "$BASE_DIR/change_summary.sh"
        ;;
    5)
        # Exit
        echo "Exiting. Thanks for using Jamso-AI-Engine!"
        exit 0
        ;;
    *)
        echo -e "${YELLOW}Invalid choice. Starting main launcher...${NC}"
        python "$BASE_DIR/jamso_launcher.py"
        ;;
esac
