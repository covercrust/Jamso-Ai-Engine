#!/bin/bash
# Daily AI data collection and regime training script
# Recommended to run as a daily cron job

# Change to the project directory
cd /home/jamso-ai-server/Jamso-Ai-Engine || exit 1

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set up logging
LOG_DIR="./Logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/daily_ai_update_$TIMESTAMP.log"

echo "Starting daily AI data collection and regime training at $(date)" | tee -a "$LOG_FILE"

# Step 1: Collect market data
echo "Step 1: Collecting market data..." | tee -a "$LOG_FILE"
python3 src/AI/scripts/collect_market_data.py | tee -a "$LOG_FILE"

# Step 2: Train regime detection models
echo "Step 2: Training volatility regime models..." | tee -a "$LOG_FILE"
python3 src/AI/scripts/train_regime_models.py --visualize | tee -a "$LOG_FILE"

# Step 3: Run AI module tests
echo "Step 3: Running AI module tests..." | tee -a "$LOG_FILE"
python3 src/AI/scripts/test_ai_modules.py | tee -a "$LOG_FILE"

echo "Daily AI update completed at $(date)" | tee -a "$LOG_FILE"

# Example cron setup (add with crontab -e):
# 0 0 * * * /home/jamso-ai-server/Jamso-Ai-Engine/Tools/daily_ai_update.sh
