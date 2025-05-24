#!/bin/bash
# Setup script for Capital.com API Optimization Tools
#
# This script installs all required dependencies and configures
# the environment for the Capital.com API integration.

# Base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")
PARENT_DIR=$(dirname "$BASE_DIR")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Capital.com API Optimization Tools Setup${NC}"
echo ""
echo "This script will install all required dependencies for the Capital.com API integration."
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Some operations may require administrator privileges.${NC}"
    echo "You might be asked for your password during the installation."
    echo ""
fi

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p "$PARENT_DIR/src/AI/config"
mkdir -p "$PARENT_DIR/dashboard"

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip3 install pandas numpy matplotlib hyperopt scikit-learn tabulate python-dotenv requests

if [ $? -ne 0 ]; then
    echo -e "${RED}Error installing Python dependencies.${NC}"
    echo "Please try running:"
    echo "    sudo pip3 install pandas numpy matplotlib hyperopt scikit-learn tabulate python-dotenv requests"
    exit 1
fi

# Copy configuration files if they don't exist
if [ ! -f "$PARENT_DIR/src/AI/config/capital_api_config.json" ]; then
    echo -e "${GREEN}Creating default configuration file...${NC}"
    cat > "$PARENT_DIR/src/AI/config/capital_api_config.json" << 'EOF'
{
    "api_settings": {
        "request_timeout": 30,
        "retry_attempts": 3,
        "retry_delay": 5,
        "max_candles_per_request": 1000
    },
    "default_optimization": {
        "days": 30,
        "max_evals": 20,
        "use_sentiment": true,
        "sentiment_weight": 0.2,
        "train_ratio": 0.7,
        "mc_simulations": 100
    },
    "scheduler": {
        "interval_hours": 24,
        "default_symbols": ["BTCUSD", "EURUSD", "US500", "GOLD"],
        "default_timeframes": ["HOUR", "DAY"],
        "default_objectives": ["sharpe", "risk_adjusted"]
    },
    "markets": {
        "crypto": ["BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "BCHUSD"],
        "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
        "indices": ["US500", "US30", "UK100", "DE40", "JP225"],
        "commodities": ["GOLD", "SILVER", "OIL", "NATGAS", "COPPER"]
    },
    "alerts": {
        "enabled": true,
        "degradation_threshold": {
            "return": 0.2,
            "sharpe": 0.2,
            "drawdown_increase": 0.3,
            "win_rate": 0.15
        },
        "email_notifications": false
    }
}
EOF
fi

if [ ! -f "$PARENT_DIR/src/Credentials/email_config.json" ] && [ -f "$PARENT_DIR/src/Credentials/email_config.json.sample" ]; then
    echo -e "${YELLOW}Email configuration sample file is available at:${NC}"
    echo "$PARENT_DIR/src/Credentials/email_config.json.sample"
    echo "To enable email alerts, copy and edit this file to email_config.json"
fi

# Make scripts executable
echo -e "${GREEN}Making scripts executable...${NC}"
chmod +x "$PARENT_DIR/src/AI/capital_data_optimizer.py"
chmod +x "$PARENT_DIR/src/AI/visualize_capital_data.py"
chmod +x "$PARENT_DIR/src/AI/test_optimized_params.py"
chmod +x "$PARENT_DIR/src/AI/scheduled_optimization.py"
chmod +x "$PARENT_DIR/src/AI/capital_api_utils.py"
chmod +x "$PARENT_DIR/Tools/run_capital_optimization.sh"

echo ""
echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo -e "You can now use the Capital.com API Optimization Tools with the command:"
echo -e "${BLUE}$PARENT_DIR/Tools/run_capital_optimization.sh help${NC}"
echo ""
echo -e "Example commands:"
echo -e "${YELLOW}$PARENT_DIR/Tools/run_capital_optimization.sh optimize --symbol BTCUSD --timeframe HOUR${NC}"
echo -e "${YELLOW}$PARENT_DIR/Tools/run_capital_optimization.sh visualize --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json${NC}"
echo -e "${YELLOW}$PARENT_DIR/Tools/run_capital_optimization.sh test --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json${NC}"
echo ""

exit 0
