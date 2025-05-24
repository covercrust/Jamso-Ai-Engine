#!/bin/bash
# Test script for Capital.com API optimization
#
# This script runs a comprehensive test of the Capital.com API integration
# to verify that all components are working correctly.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Send all output to both console and log file
LOG_FILE="/tmp/capital_api_test_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee "$LOG_FILE") 2>&1
echo "Logging output to $LOG_FILE"

# Base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")
PARENT_DIR=$(dirname "$BASE_DIR")

echo -e "${BLUE}Capital.com API Integration Test${NC}"
echo "============================================"
echo ""

# Step 1: Check for credentials in secure database or .env file
echo -e "${YELLOW}Step 1: Checking for API credentials${NC}"

# Try to get credentials from the credential adapter
if python3 "$BASE_DIR/test_credential_adapter.py" --test; then
    echo -e "${GREEN}✓ API credentials found in secure storage${NC}"
    # Export credentials to environment variables for this script
    eval "$(python3 "$BASE_DIR/test_credential_adapter.py" --export)"
    if [ "$CAPITAL_CREDENTIALS_LOADED" == "true" ]; then
        echo -e "${GREEN}✓ API credentials loaded into environment${NC}"
    else
        echo -e "${RED}✗ Failed to load API credentials into environment${NC}"
    fi
else
    echo -e "${YELLOW}! Secure credentials not found, checking .env file${NC}"
    
    # Fall back to checking .env file directly
    ENV_FILE="$PARENT_DIR/.env"
    if [ -f "$ENV_FILE" ]; then
        echo -e "${GREEN}✓ .env file found${NC}"
        
        # Check if API credentials are set
        if grep -q "CAPITAL_API_KEY=" "$ENV_FILE" && ! grep -q "CAPITAL_API_KEY=$" "$ENV_FILE"; then
            echo -e "${GREEN}✓ API key is set in .env file${NC}"
        else
            echo -e "${RED}✗ API key is not set in .env file${NC}"
            echo "Please edit $ENV_FILE and add your Capital.com API credentials"
        fi
    else
        echo -e "${RED}✗ .env file not found${NC}"
        echo "Creating .env file..."
    
    cat > "$ENV_FILE" << 'EOF'
# Capital.com API Credentials
CAPITAL_API_KEY=
CAPITAL_API_LOGIN=
CAPITAL_API_PASSWORD=

# You need to fill in these values with your actual Capital.com API credentials
# For security, do not commit this file to version control
# This file should be included in your .gitignore
EOF
    
    echo "Please edit $ENV_FILE and add your Capital.com API credentials"
fi

echo ""

# Step 2: Check python-dotenv installation
echo -e "${YELLOW}Step 2: Checking for python-dotenv installation${NC}"
if python3 -c "import dotenv" 2>/dev/null; then
    echo -e "${GREEN}✓ python-dotenv is installed${NC}"
else
    echo -e "${RED}✗ python-dotenv is not installed${NC}"
    echo "Installing python-dotenv..."
    pip3 install python-dotenv
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ python-dotenv installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install python-dotenv${NC}"
        echo "Please run: pip3 install python-dotenv"
    fi
fi

echo ""

# Step 3: Test environment variable loading
echo -e "${YELLOW}Step 3: Testing environment variable loading${NC}"
# Check if our new test script exists first
if [ -f "$BASE_DIR/test_env_variables.py" ]; then
    # Make it executable
    chmod +x "$BASE_DIR/test_env_variables.py"
    # Run our improved test script
    python3 "$BASE_DIR/test_env_variables.py"
else
    # Fall back to old script
    python3 "$PARENT_DIR/src/AI/test_env_loading.py"
fi

echo ""

# Step 4: Test credential adapter directly
echo -e "${YELLOW}Step 4: Testing credential adapter${NC}"
if [ -f "$BASE_DIR/test_credential_adapter.py" ]; then
    python3 "$BASE_DIR/test_credential_adapter.py"
    
    echo -e "\n${YELLOW}Exporting credentials to environment if available...${NC}"
    eval "$(python3 "$BASE_DIR/test_credential_adapter.py" --export)"
    if [ "$CAPITAL_CREDENTIALS_LOADED" == "true" ]; then
        echo -e "${GREEN}✓ Credentials exported successfully${NC}"
    else
        echo -e "${RED}✗ No valid credentials found to export${NC}"
    fi
else
    echo -e "${RED}✗ Credential adapter not found${NC}"
    echo "The credential adapter script is missing"
fi

echo ""

# Step 5: Test fallback API client
echo -e "${YELLOW}Step 4: Testing fallback API client${NC}"
echo "This will attempt to connect to the Capital.com API using the fallback client."
echo "If your API credentials are set correctly in the .env file, this should succeed."
echo ""

python3 "$PARENT_DIR/src/AI/fallback_capital_api.py" --symbol BTCUSD --days 1 --output "$PARENT_DIR/test_data.csv"

if [ $? -eq 0 ] && [ -f "$PARENT_DIR/test_data.csv" ]; then
    echo -e "${GREEN}✓ Fallback API client test succeeded${NC}"
    echo "Data was successfully retrieved and saved to test_data.csv"
    
    # Show first few lines of the CSV file
    echo ""
    echo "Preview of retrieved data:"
    head -n 5 "$PARENT_DIR/test_data.csv"
    echo "..."
else
    echo -e "${RED}✗ Fallback API client test failed${NC}"
    echo "Could not retrieve data from Capital.com API"
    echo "Please check your API credentials in the .env file"
fi

echo ""

# Step 5: Test full optimization process
echo -e "${YELLOW}Step 5: Testing full optimization process${NC}"
echo "This will run a small optimization test using the BTCUSD symbol with 10 evaluations."
echo "This may take a few minutes to complete..."
echo ""

"$PARENT_DIR/Tools/run_capital_optimization.sh" optimize --symbol BTCUSD --timeframe HOUR --days 7 --max-evals 10

echo ""
echo "============================================"
echo -e "${BLUE}Test completed${NC}"
echo ""
