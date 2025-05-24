#!/bin/bash
# Launch script for testing mobile alerts functionality
#
# This script simplifies testing the mobile alerts feature of the Jamso-AI-Engine
# and provides easy access to the test and configuration options.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")

echo -e "${BLUE}Mobile Alerts Test Launcher${NC}"
echo "==========================="

# Make sure we're in the correct directory
cd "$BASE_DIR"

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

# Check if test script exists
TEST_SCRIPT="$BASE_DIR/Tools/test_mobile_alerts.sh"
if [ ! -f "$TEST_SCRIPT" ]; then
    echo -e "${RED}Mobile alerts test script not found at $TEST_SCRIPT${NC}"
    exit 1
fi

# Make sure test script is executable
chmod +x "$TEST_SCRIPT"

# Options menu
while true; do
    echo
    echo "Please select an option:"
    echo "1. Run full mobile alerts test"
    echo "2. Send a test alert"
    echo "3. Edit mobile alert settings (.env file)"
    echo "4. Show documentation"
    echo "5. Exit"
    echo
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            # Run full test
            echo -e "${BLUE}Running full mobile alerts test...${NC}"
            "$TEST_SCRIPT"
            ;;
        2)
            # Send a test alert
            echo -e "${BLUE}Send a test alert${NC}"
            echo "-------------------"
            read -p "Enter alert title (default: Test Alert): " title
            title=${title:-"Test Alert"}
            
            read -p "Enter alert message (default: This is a test alert): " message
            message=${message:-"This is a test alert"}
            
            read -p "Enter alert level (info/warning/critical) (default: info): " level
            level=${level:-"info"}
            
            echo -e "${BLUE}Sending $level alert: $title${NC}"
            python3 "$BASE_DIR/src/AI/mobile_alerts.py" --title="$title" --message="$message" --level="$level"
            ;;
        3)
            # Edit .env file
            echo -e "${BLUE}Editing .env file...${NC}"
            ENV_FILE="$BASE_DIR/.env"
            
            # Check if .env exists
            if [ ! -f "$ENV_FILE" ]; then
                echo "Creating new .env file with mobile alert settings..."
                cat > "$ENV_FILE" << 'EOF'
# Capital.com API Credentials
CAPITAL_API_KEY=
CAPITAL_API_LOGIN=
CAPITAL_API_PASSWORD=

# Email settings for alerts
EMAIL_FROM=
EMAIL_TO=
EMAIL_PASSWORD=
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Mobile Alert Settings
MOBILE_ALERTS_EMAIL_ENABLED=false
MOBILE_ALERTS_SMS_ENABLED=false
MOBILE_ALERTS_PUSH_ENABLED=false
MOBILE_ALERTS_WEBHOOK_ENABLED=false
MOBILE_ALERTS_MIN_LEVEL=warning

# SMS Gateway settings (if using SMS alerts)
SMS_GATEWAY=
SMS_NUMBER=

# Push notification settings (if using push notifications)
PUSH_SERVICE=onesignal
PUSH_API_KEY=
PUSH_APP_ID=

# Webhook settings (if using webhook alerts)
WEBHOOK_ALERT_URL=
WEBHOOK_ALERT_HEADERS={"Content-Type": "application/json", "Authorization": ""}

# You need to fill in these values with your actual credentials
# For security, do not commit this file to version control
# This file should be included in your .gitignore
EOF
            fi
            
            # Determine editor (nano as fallback)
            EDITOR=${EDITOR:-nano}
            
            # Open .env file in editor
            $EDITOR "$ENV_FILE"
            ;;
        4)
            # Show documentation
            echo -e "${BLUE}Mobile Alerts Documentation${NC}"
            DOC_FILE="$BASE_DIR/Docs/AI/Mobile_Alerts_Integration.md"
            
            if [ -f "$DOC_FILE" ]; then
                # Determine pager (less as fallback)
                PAGER=${PAGER:-less}
                
                # Display documentation
                $PAGER "$DOC_FILE"
            else
                echo -e "${RED}Documentation file not found at $DOC_FILE${NC}"
            fi
            ;;
        5)
            # Exit
            echo -e "${GREEN}Exiting mobile alerts test launcher.${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please enter a number between 1 and 5.${NC}"
            ;;
    esac
done
