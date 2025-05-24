#!/usr/bin/env bash
# 
# Jamso AI Engine - Multi-Strategy Backtest Script
#
# This script runs multiple backtests with different parameters for comparison
# and generates a summary report of performance metrics.
#

# Set working directory to the project root
cd "$(dirname "$0")/../.." || exit 1

# Output directory for results
OUTPUT_DIR="./backtest_results"
mkdir -p "$OUTPUT_DIR"

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$OUTPUT_DIR/backtest_report_${TIMESTAMP}.txt"

# Log header
echo "====================================================" > "$REPORT_FILE"
echo "Jamso AI Engine - Backtest Comparison Report" >> "$REPORT_FILE"
echo "Run Date: $(date)" >> "$REPORT_FILE"
echo "====================================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Function to run backtest and extract metrics
run_backtest() {
  local name=$1
  local strat=$2
  shift 2
  local params=("$@")
  
  echo "Running backtest: $name"
  echo "---------------------------------------------------" >> "$REPORT_FILE"
  echo "Strategy: $name" >> "$REPORT_FILE"
  echo "Parameters: ${params[*]}" >> "$REPORT_FILE"
  
  # Run backtest and capture output
  RESULTS=$(python src/AI/run_backtest.py --strategy "$strat" --use-sample-data --days 252 "${params[@]}" --verbose)
  
  # Extract and log metrics
  echo "$RESULTS" | grep -E "Total Return:|Max Drawdown:|Sharpe Ratio:|Win Rate:|Num Trades:" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  
  # Save full results to separate file
  echo "$RESULTS" > "$OUTPUT_DIR/details_${name// /_}_${TIMESTAMP}.txt"
}

# Run a series of backtests with different parameters
echo "Starting backtest comparisons..."

# Run conservative SuperTrend
run_backtest "SuperTrend Conservative" "supertrend" --fact 3.5 --risk-percent 0.5 --sl-percent 1.0

# Run balanced SuperTrend
run_backtest "SuperTrend Balanced" "supertrend" --fact 3.0 --risk-percent 1.0 --sl-percent 0.5

# Run aggressive SuperTrend
run_backtest "SuperTrend Aggressive" "supertrend" --fact 2.0 --risk-percent 2.0 --sl-percent 0.3

# Run optimized parameters (if available)
if [ -f "$OUTPUT_DIR/optimization_results.json" ]; then
  # Extract best parameters from optimization results
  echo "Running backtest with optimized parameters..."
  # This would require parsing the JSON file - simplified for this example
  run_backtest "SuperTrend Optimized" "supertrend" --fact 2.5 --risk-percent 1.5 --sl-percent 0.4
fi

# Generate comparison summary
echo "---------------------------------------------------" >> "$REPORT_FILE"
echo "Summary Comparison" >> "$REPORT_FILE"
echo "---------------------------------------------------" >> "$REPORT_FILE"

# Extract specific metrics for comparison
echo "Strategy        | Total Return | Max Drawdown | Sharpe Ratio | Win Rate" >> "$REPORT_FILE"
echo "--------------- | ------------ | ------------ | ------------ | --------" >> "$REPORT_FILE"

# Process each result file and extract key metrics
for file in "$OUTPUT_DIR/details_"*"_${TIMESTAMP}.txt"; do
  strategy=$(basename "$file" | sed "s/details_\(.*\)_${TIMESTAMP}.txt/\1/" | tr '_' ' ')
  
  # Extract metrics
  total_return=$(grep "Total Return:" "$file" | awk '{print $3}')
  max_drawdown=$(grep "Max Drawdown:" "$file" | awk '{print $3}')
  sharpe=$(grep "Sharpe Ratio:" "$file" | awk '{print $3}')
  win_rate=$(grep "Win Rate:" "$file" | awk '{print $3}')
  
  # Add to summary
  printf "%-15s | %-12s | %-12s | %-12s | %-8s\n" "$strategy" "$total_return" "$max_drawdown" "$sharpe" "$win_rate" >> "$REPORT_FILE"
done

echo "" >> "$REPORT_FILE"
echo "Complete backtest report saved to: $REPORT_FILE"
echo "See individual backtest details in the $OUTPUT_DIR directory."

echo "Backtest comparison completed."
echo "Report available at: $REPORT_FILE"
