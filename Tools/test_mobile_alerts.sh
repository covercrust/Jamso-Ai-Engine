#!/bin/bash
# Test script for mobile alerts
#
# This script tests the mobile alert functionality of the Jamso AI Engine

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="mobile_alerts_test_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to $LOG_FILE"
exec > >(tee "$LOG_FILE") 2>&1

# Base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")
PARENT_DIR=$(dirname "$BASE_DIR")

echo -e "${BLUE}Mobile Alerts Test${NC}"
echo "========================"
echo ""

# Step 1: Check for .env file and alert settings
echo -e "${YELLOW}Step 1: Checking for .env file and alert settings${NC}"
ENV_FILE="$PARENT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✓ .env file found${NC}"
    
    # Check if alert settings are configured
    if grep -q "MOBILE_ALERTS_EMAIL_ENABLED=true" "$ENV_FILE" || \
       grep -q "MOBILE_ALERTS_SMS_ENABLED=true" "$ENV_FILE" || \
       grep -q "MOBILE_ALERTS_PUSH_ENABLED=true" "$ENV_FILE" || \
       grep -q "MOBILE_ALERTS_WEBHOOK_ENABLED=true" "$ENV_FILE"; then
        echo -e "${GREEN}✓ At least one alert method is enabled${NC}"
    else
        echo -e "${YELLOW}? No alert method is enabled in .env file${NC}"
        echo "You should enable at least one alert method by setting the corresponding variable to 'true'"
        echo "For example: MOBILE_ALERTS_EMAIL_ENABLED=true"
    fi
    
    # Check for email configuration if email alerts are enabled
    if grep -q "MOBILE_ALERTS_EMAIL_ENABLED=true" "$ENV_FILE"; then
        if grep -q "EMAIL_FROM=" "$ENV_FILE" && grep -q "EMAIL_TO=" "$ENV_FILE" && \
           ! grep -q "EMAIL_FROM=$" "$ENV_FILE" && ! grep -q "EMAIL_TO=$" "$ENV_FILE"; then
            echo -e "${GREEN}✓ Email alert configuration found${NC}"
        else
            echo -e "${YELLOW}? Email alerts are enabled but not fully configured${NC}"
            echo "Please set EMAIL_FROM, EMAIL_TO, and EMAIL_PASSWORD in the .env file"
        fi
    fi
else
    echo -e "${RED}✗ .env file not found${NC}"
    echo "Please create a .env file with alert settings"
    exit 1
fi

# Step 2: Test basic mobile alert functionality
echo -e "\n${YELLOW}Step 2: Testing basic mobile alert functionality${NC}"

MOBILE_ALERTS_SCRIPT="$PARENT_DIR/src/AI/mobile_alerts.py"

if [ -f "$MOBILE_ALERTS_SCRIPT" ]; then
    echo -e "${GREEN}✓ Mobile alerts script found${NC}"
    
    echo "Sending test alert..."
    python3 "$MOBILE_ALERTS_SCRIPT" --title "Test Alert" --message "This is a test alert from the mobile_alerts.py script" --level info
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Alert sent successfully${NC}"
    else
        echo -e "${RED}✗ Failed to send alert${NC}"
        echo "Check the configuration in your .env file"
    fi
else
    echo -e "${RED}✗ Mobile alerts script not found at $MOBILE_ALERTS_SCRIPT${NC}"
    exit 1
fi

# Step 3: Test integration with scheduled optimization
echo -e "\n${YELLOW}Step 3: Testing integration with scheduled optimization${NC}"

SCHEDULER_SCRIPT="$PARENT_DIR/src/AI/scheduled_optimization.py"

if [ -f "$SCHEDULER_SCRIPT" ]; then
    echo -e "${GREEN}✓ Scheduled optimization script found${NC}"
    
    echo "Running scheduled optimization with mobile alerts (will only run for 30 seconds)..."
    python3 "$SCHEDULER_SCRIPT" --symbols BTCUSD --timeframes HOUR --objectives sharpe --interval 0.1 --days 7 --max-evals 2 --mobile-alerts &
    SCHEDULER_PID=$!
    
    echo "Scheduler running with PID $SCHEDULER_PID"
    echo "Waiting for 30 seconds to allow for alerts to be sent..."
    sleep 30
    
    # Kill the scheduler process
    kill $SCHEDULER_PID
    
    echo -e "${GREEN}✓ Scheduler test complete${NC}"
    echo "Check your configured alert methods to see if you received the alerts"
else
    echo -e "${RED}✗ Scheduled optimization script not found at $SCHEDULER_SCRIPT${NC}"
    exit 1
fi

echo -e "\n${BLUE}Test Summary${NC}"
echo "=================="
echo -e "1. Configuration check: ${GREEN}Complete${NC}"
echo -e "2. Basic alert test: ${GREEN}Complete${NC}"
echo -e "3. Integration test: ${GREEN}Complete${NC}"
echo ""
echo -e "${GREEN}All tests completed. See $LOG_FILE for details.${NC}"
echo ""
echo "If you didn't receive any alerts, check your .env configuration and make sure:"
echo "1. At least one alert method is enabled (set to true)"
echo "2. Required credentials for the enabled methods are provided"
echo "3. Your email provider allows sending from third-party applications (if using email alerts)"
echo ""
echo "For email alerts with Gmail, you may need to:"
echo "1. Enable 'Less secure app access' or"
echo "2. Create an app password if you have 2-factor authentication enabled"
