#!/bin/bash
# Test script for git backup

echo "Starting git backup test script"
echo "Current directory: $(pwd)"
echo "Script file: $0"

# Set the base directory
BASE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
echo "Base directory: $BASE_DIR"

# Check if directories exist
echo "Checking directories..."
if [ -d "$BASE_DIR" ]; then
    echo "Base directory exists"
else
    echo "Base directory doesn't exist"
fi

if [ -d "$BASE_DIR/Logs" ]; then
    echo "Logs directory exists"
else
    echo "Logs directory doesn't exist, creating..."
    mkdir -p "$BASE_DIR/Logs"
fi

# Test writing to the logs
echo "Testing log writing..."
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
TEST_LOG="$BASE_DIR/Logs/git_test.log"
echo "===== Git Test Started - $TIMESTAMP =====" > "$TEST_LOG"
echo "Test log written to: $TEST_LOG"
cat "$TEST_LOG"

# Test Git operations
echo "Testing Git operations..."
cd "$BASE_DIR" || exit 1
echo "Current directory now: $(pwd)"

echo "Git status:"
git status

echo "Checking Git configuration:"
git config pull.rebase

echo "Testing Git diff:"
git diff

echo "Test completed successfully"
