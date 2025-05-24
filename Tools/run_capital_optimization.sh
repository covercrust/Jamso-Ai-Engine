#!/bin/bash
# Run Capital.com API Optimization Tools
#
# This script provides a convenient way to run various optimization tasks
# with the Capital.com API integration.
#
# Usage: ./run_capital_optimization.sh [command] [options]

# Base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")
PARENT_DIR=$(dirname "$BASE_DIR")

# Check for .env file and create if it doesn't exist
ENV_FILE="$PARENT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Creating .env file for API credentials...${NC}"
    cat > "$ENV_FILE" << 'EOF'
# Capital.com API Credentials
CAPITAL_API_KEY=
CAPITAL_API_LOGIN=
CAPITAL_API_PASSWORD=

# You need to fill in these values with your actual Capital.com API credentials
# For security, do not commit this file to version control
# This file should be included in your .gitignore
EOF
    echo -e "${YELLOW}Please edit $ENV_FILE to add your Capital.com API credentials${NC}"
fi

# Default settings
SYMBOL="BTCUSD"
TIMEFRAME="HOUR"
OBJECTIVE="sharpe"
DAYS=30
MAX_EVALS=20
USE_SENTIMENT=true
PARAMS_FILE=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print help information
show_help() {
    echo -e "${BLUE}Capital.com API Optimization Tools${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  optimize         Run parameter optimization for a market"
    echo "  visualize        Visualize optimization results"
    echo "  test             Test optimized parameters on out-of-sample data"
    echo "  schedule         Schedule regular optimization tasks"
    echo "  dashboard        Generate a performance dashboard"
    echo "  fetch-data       Fetch and save market data to CSV"
    echo "  list-markets     List available market symbols"
    echo "  help             Show this help information"
    echo ""
    echo "Options:"
    echo "  --symbol         Market symbol (e.g., BTCUSD, EURUSD)"
    echo "  --timeframe      Candle timeframe (MINUTE, HOUR, DAY, etc.)"
    echo "  --objective      Optimization objective (sharpe, return, risk_adjusted, win_rate)"
    echo "  --days           Number of days of historical data to use"
    echo "  --max-evals      Maximum parameter combinations to test"
    echo "  --no-sentiment   Don't use sentiment data"
    echo "  --params-file    Path to parameter file for visualization or testing"
    echo ""
    echo "Examples:"
    echo "  $0 optimize --symbol BTCUSD --timeframe HOUR --objective sharpe"
    echo "  $0 visualize --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json"
    echo "  $0 test --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json"
    echo "  $0 schedule --interval 24"
    echo "  $0 fetch-data --symbol EURUSD --timeframe DAY --days 90"
    echo ""
}

# Parse command line arguments
parse_args() {
    COMMAND=$1
    shift
    
    while [[ $# -gt 0 ]]; do
        key="$1"
        case $key in
            --symbol)
            SYMBOL="$2"
            shift 2
            ;;
            --timeframe)
            TIMEFRAME="$2"
            shift 2
            ;;
            --objective)
            OBJECTIVE="$2"
            shift 2
            ;;
            --days)
            DAYS="$2"
            shift 2
            ;;
            --max-evals)
            MAX_EVALS="$2"
            shift 2
            ;;
            --no-sentiment)
            USE_SENTIMENT=false
            shift
            ;;
            --params-file)
            PARAMS_FILE="$2"
            shift 2
            ;;
            --interval)
            INTERVAL="$2"
            shift 2
            ;;
            *)
            echo -e "${RED}Error: Unknown option '$1'${NC}"
            show_help
            exit 1
            ;;
        esac
    done
}

# Run optimization
run_optimize() {
    echo -e "${GREEN}Running optimization for $SYMBOL $TIMEFRAME (objective: $OBJECTIVE)${NC}"
    
    CMD="python3 $PARENT_DIR/src/AI/capital_data_optimizer.py --symbol=$SYMBOL --timeframe=$TIMEFRAME --objective=$OBJECTIVE --days=$DAYS --max-evals=$MAX_EVALS --save-plot"
    
    if [ "$USE_SENTIMENT" = true ]; then
        CMD="$CMD --use-sentiment"
    fi
    
    echo -e "${YELLOW}Command: $CMD${NC}"
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Optimization completed successfully!${NC}"
    else
        echo -e "${RED}Optimization failed with errors.${NC}"
    fi
}

# Run visualization
run_visualize() {
    if [ -z "$PARAMS_FILE" ]; then
        echo -e "${RED}Error: No parameter file specified. Use --params-file option.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Visualizing results from $PARAMS_FILE${NC}"
    CMD="python3 $PARENT_DIR/src/AI/visualize_capital_data.py --params-file $PARAMS_FILE"
    
    echo -e "${YELLOW}Command: $CMD${NC}"
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Visualization completed successfully!${NC}"
    else
        echo -e "${RED}Visualization failed with errors.${NC}"
    fi
}

# Run comparison visualization
run_compare() {
    echo -e "${GREEN}Comparing optimization results for $SYMBOL $TIMEFRAME${NC}"
    CMD="python3 $PARENT_DIR/src/AI/visualize_capital_data.py --compare --symbol $SYMBOL --timeframe $TIMEFRAME"
    
    echo -e "${YELLOW}Command: $CMD${NC}"
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Comparison completed successfully!${NC}"
    else
        echo -e "${RED}Comparison failed with errors.${NC}"
    fi
}

# Run out-of-sample testing
run_test() {
    if [ -z "$PARAMS_FILE" ]; then
        echo -e "${RED}Error: No parameter file specified. Use --params-file option.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Testing parameters from $PARAMS_FILE${NC}"
    CMD="python3 $PARENT_DIR/src/AI/test_optimized_params.py --params-file $PARAMS_FILE --days 60"
    
    echo -e "${YELLOW}Command: $CMD${NC}"
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Testing completed successfully!${NC}"
    else
        echo -e "${RED}Testing failed with errors.${NC}"
    fi
}

# Run scheduled optimization
run_schedule() {
    INTERVAL=${INTERVAL:-24}
    
    echo -e "${GREEN}Starting scheduled optimization (interval: $INTERVAL hours)${NC}"
    CMD="python3 $PARENT_DIR/src/AI/scheduled_optimization.py --interval $INTERVAL --symbols $SYMBOL"
    
    echo -e "${YELLOW}Command: $CMD${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop the scheduler${NC}"
    eval $CMD
}

# Generate dashboard
run_dashboard() {
    echo -e "${GREEN}Generating optimization dashboard${NC}"
    CMD="python3 $PARENT_DIR/src/AI/scheduled_optimization.py --dashboard-only"
    
    echo -e "${YELLOW}Command: $CMD${NC}"
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Dashboard generated successfully!${NC}"
        echo -e "${GREEN}You can find it at: $PARENT_DIR/dashboard/index.html${NC}"
    else
        echo -e "${RED}Dashboard generation failed with errors.${NC}"
    fi
}

# Fetch market data
fetch_data() {
    echo -e "${GREEN}Fetching $DAYS days of $TIMEFRAME data for $SYMBOL${NC}"
    CMD="python3 $PARENT_DIR/src/AI/capital_api_utils.py --get-data --symbol $SYMBOL --timeframe $TIMEFRAME --days $DAYS --save"
    
    echo -e "${YELLOW}Command: $CMD${NC}"
    eval $CMD
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Data fetched successfully!${NC}"
    else
        echo -e "${RED}Data fetch failed with errors.${NC}"
    fi
}

# List available markets
list_markets() {
    echo -e "${GREEN}Listing available markets${NC}"
    CMD="python3 $PARENT_DIR/src/AI/capital_api_utils.py --list-symbols"
    
    echo -e "${YELLOW}Command: $CMD${NC}"
    eval $CMD
}

# Main script logic
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    optimize)
    parse_args "$COMMAND" "$@"
    run_optimize
    ;;
    visualize)
    parse_args "$COMMAND" "$@"
    run_visualize
    ;;
    compare)
    parse_args "$COMMAND" "$@"
    run_compare
    ;;
    test)
    parse_args "$COMMAND" "$@"
    run_test
    ;;
    schedule)
    parse_args "$COMMAND" "$@"
    run_schedule
    ;;
    dashboard)
    run_dashboard
    ;;
    fetch-data)
    parse_args "$COMMAND" "$@"
    fetch_data
    ;;
    list-markets)
    list_markets
    ;;
    help)
    show_help
    ;;
    *)
    echo -e "${RED}Error: Unknown command '$COMMAND'${NC}"
    show_help
    exit 1
    ;;
esac

exit 0
