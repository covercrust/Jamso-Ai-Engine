#!/bin/bash
# Redis cache cleaning script for Jamso AI Engine
# Created: May 16, 2025

echo "===== Starting Redis Cache Cleanup ====="

# Check if redis-cli is installed
if command -v redis-cli >/dev/null 2>&1; then
    echo "Flushing Redis cache..."
    redis-cli -h localhost -p 6379 FLUSHALL
    echo "Redis cache cleared successfully."
else
    echo "redis-cli not found. Please install Redis CLI tools to clear Redis cache."
    echo "You can install it with: sudo apt-get install redis-tools"
fi

echo "===== Redis cache cleanup completed ====="
