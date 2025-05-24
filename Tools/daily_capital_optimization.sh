#!/bin/bash
# Daily optimization script for Capital.com API
# 
# This script runs scheduled optimization for the specified market symbols.
# It's designed to be run from a cron job, e.g., once per day.
#
# Example crontab entry:
# 0 1 * * * /home/jamso-ai-server/Jamso-Ai-Engine/Tools/daily_capital_optimization.sh > /home/jamso-ai-server/Jamso-Ai-Engine/src/Logs/capital_optimization.log 2>&1

# Base directory
BASE_DIR=$(dirname "$(readlink -f "$0")")
PARENT_DIR=$(dirname "$BASE_DIR")

# Log directory
LOG_DIR="$PARENT_DIR/src/Logs"
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="$LOG_DIR/capital_optimization_$(date +%Y%m%d).log"

# Default symbols and timeframes
SYMBOLS="BTCUSD,EURUSD,US500,GOLD"
TIMEFRAMES="HOUR,DAY"
OBJECTIVES="sharpe,risk_adjusted"
DAYS=30
MAX_EVALS=20

# Log start time
echo "==================================================" >> "$LOG_FILE"
echo "Starting daily Capital.com optimization: $(date)" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"

# Run optimization for each symbol and timeframe
IFS=',' read -ra SYMBOL_ARRAY <<< "$SYMBOLS"
IFS=',' read -ra TIMEFRAME_ARRAY <<< "$TIMEFRAMES"
IFS=',' read -ra OBJECTIVE_ARRAY <<< "$OBJECTIVES"

for symbol in "${SYMBOL_ARRAY[@]}"; do
    for timeframe in "${TIMEFRAME_ARRAY[@]}"; do
        for objective in "${OBJECTIVE_ARRAY[@]}"; do
            echo "Optimizing $symbol $timeframe $objective..." >> "$LOG_FILE"
            
            # Run optimization
            python3 "$PARENT_DIR/src/AI/capital_data_optimizer.py" \
                --symbol "$symbol" \
                --timeframe "$timeframe" \
                --objective "$objective" \
                --days "$DAYS" \
                --max-evals "$MAX_EVALS" \
                --use-sentiment \
                --save-plot >> "$LOG_FILE" 2>&1
            
            # Run out-of-sample test
            PARAMS_FILE="$PARENT_DIR/capital_com_optimized_params_${symbol}_${timeframe}_${objective}.json"
            if [ -f "$PARAMS_FILE" ]; then
                echo "Testing $PARAMS_FILE on out-of-sample data..." >> "$LOG_FILE"
                python3 "$PARENT_DIR/src/AI/test_optimized_params.py" \
                    --params-file "$PARAMS_FILE" \
                    --days 60 \
                    --mc-simulations 50 >> "$LOG_FILE" 2>&1
            fi
        done
    done
done

# Generate dashboard
echo "Generating optimization dashboard..." >> "$LOG_FILE"
python3 "$PARENT_DIR/src/AI/scheduled_optimization.py" --dashboard-only >> "$LOG_FILE" 2>&1

# Log completion time
echo "==================================================" >> "$LOG_FILE"
echo "Daily Capital.com optimization completed: $(date)" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"

exit 0
