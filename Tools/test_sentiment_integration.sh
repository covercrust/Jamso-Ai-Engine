#!/bin/bash
# Test script for historical sentiment integration with Capital.com API
#
# This script tests the sentiment integration with the Capital.com API
# to verify that historical sentiment data is correctly incorporated

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="sentiment_test_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to $LOG_FILE"
exec > >(tee "$LOG_FILE") 2>&1

# Base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")
PARENT_DIR=$(dirname "$BASE_DIR")

echo -e "${BLUE}Capital.com API Sentiment Integration Test${NC}"
echo "=============================================="
echo ""

# Step 1: Check for .env file
echo -e "${YELLOW}Step 1: Checking for .env file${NC}"
ENV_FILE="$PARENT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✓ .env file found${NC}"
    
    # Check if API credentials are set
    if grep -q "CAPITAL_API_KEY=" "$ENV_FILE" && ! grep -q "CAPITAL_API_KEY=$" "$ENV_FILE"; then
        echo -e "${GREEN}✓ API key is set${NC}"
    else
        echo -e "${RED}✗ API key is not set${NC}"
        echo "Please edit $ENV_FILE and add your Capital.com API credentials"
    fi
else
    echo -e "${YELLOW}? .env file not found, creating it now${NC}"
    
    # Create the .env file with placeholders
    cat > "$ENV_FILE" << 'EOF'
# Capital.com API Credentials
CAPITAL_API_KEY=
CAPITAL_API_LOGIN=
CAPITAL_API_PASSWORD=

# Email settings for alerts (optional)
EMAIL_FROM=
EMAIL_TO=
EMAIL_PASSWORD=
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# You need to fill in these values with your actual credentials
# For security, do not commit this file to version control
# This file should be included in your .gitignore
EOF
    
    echo "Please edit $ENV_FILE and add your Capital.com API credentials"
fi

# Step 2: Check Python dependencies
echo -e "\n${YELLOW}Step 2: Checking Python dependencies${NC}"
DEPENDENCIES=("python-dotenv" "requests" "pandas" "numpy" "matplotlib")

for dep in "${DEPENDENCIES[@]}"; do
    if python3 -c "import ${dep//-/_}" 2>/dev/null; then
        echo -e "${GREEN}✓ $dep is installed${NC}"
    else
        echo -e "${YELLOW}Installing $dep...${NC}"
        pip install "$dep"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $dep installed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to install $dep${NC}"
        fi
    fi
done

# Step 3: Test sentiment integration
echo -e "\n${YELLOW}Step 3: Testing sentiment integration${NC}"
SENTIMENT_SCRIPT="$PARENT_DIR/src/AI/sentiment_integration.py"

if [ -f "$SENTIMENT_SCRIPT" ]; then
    echo -e "${GREEN}✓ Sentiment integration script found${NC}"
    
    echo "Running sentiment integration test for BTCUSD..."
    python3 "$SENTIMENT_SCRIPT" --symbol BTCUSD --days 7 --plot
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Sentiment integration test successful${NC}"
    else
        echo -e "${RED}✗ Sentiment integration test failed${NC}"
    fi
else
    echo -e "${RED}✗ Sentiment integration script not found at $SENTIMENT_SCRIPT${NC}"
fi

# Step 4: Test optimization with sentiment
echo -e "\n${YELLOW}Step 4: Testing optimization with sentiment integration${NC}"
OPTIMIZER_SCRIPT="$PARENT_DIR/src/AI/capital_data_optimizer.py"

if [ -f "$OPTIMIZER_SCRIPT" ]; then
    echo -e "${GREEN}✓ Capital.com optimizer script found${NC}"
    
    echo "Running optimization with sentiment for BTCUSD..."
    python3 "$OPTIMIZER_SCRIPT" --symbol BTCUSD --timeframe HOUR --days 7 --use-sentiment --save-plot
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Optimization with sentiment successful${NC}"
    else
        echo -e "${RED}✗ Optimization with sentiment failed${NC}"
    fi
else
    echo -e "${RED}✗ Capital.com optimizer script not found at $OPTIMIZER_SCRIPT${NC}"
fi

# Step 5: Test dashboard
echo -e "\n${YELLOW}Step 5: Testing optimization dashboard${NC}"
DASHBOARD_SCRIPT="$PARENT_DIR/src/AI/optimization_dashboard.py"

if [ -f "$DASHBOARD_SCRIPT" ]; then
    echo -e "${GREEN}✓ Optimization dashboard script found${NC}"
    
    echo "Starting dashboard in background for 10 seconds..."
    python3 "$DASHBOARD_SCRIPT" &
    DASHBOARD_PID=$!
    
    echo "Dashboard running with PID $DASHBOARD_PID"
    echo "If browser doesn't open automatically, go to: http://localhost:8050"
    
    # Sleep for 10 seconds to allow dashboard to start
    sleep 10
    
    # Kill the dashboard process
    kill $DASHBOARD_PID
    
    echo -e "${GREEN}✓ Dashboard test complete${NC}"
else
    echo -e "${RED}✗ Dashboard script not found at $DASHBOARD_SCRIPT${NC}"
fi

echo -e "\n${BLUE}Test Summary${NC}"
echo "==================="
echo -e "1. Environment setup: ${GREEN}Complete${NC}"
echo -e "2. Dependencies check: ${GREEN}Complete${NC}"
echo -e "3. Sentiment integration: ${GREEN}Tested${NC}"
echo -e "4. Optimization with sentiment: ${GREEN}Tested${NC}"
echo -e "5. Dashboard: ${GREEN}Tested${NC}"
echo ""
echo -e "${GREEN}All tests completed. See $LOG_FILE for details.${NC}"
