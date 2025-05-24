#!/bin/bash
# Dependency checker and installer for Capital.com API testing

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")

echo -e "${BLUE}Checking for required Python dependencies...${NC}"
echo "============================================"

# List of required packages for Capital.com API tests
REQUIRED_PACKAGES=(
    "pandas"
    "numpy"
    "matplotlib"
    "requests"
    "python-dotenv"
    "cryptography"
)

# Check each package and install if missing
for package in "${REQUIRED_PACKAGES[@]}"; do
    echo -n "Checking for $package... "
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓ Installed${NC}"
    else
        echo -e "${YELLOW}✗ Missing${NC}"
        echo -n "Installing $package... "
        if pip3 install "$package"; then
            echo -e "${GREEN}✓ Success${NC}"
        else
            echo -e "${RED}✗ Failed${NC}"
            echo "Please run: pip install $package"
        fi
    fi
done

echo -e "\n${GREEN}Dependency check complete!${NC}"
echo "You should now be able to run the Capital.com API tests successfully."
