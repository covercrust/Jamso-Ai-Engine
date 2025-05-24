#!/bin/bash
# Cleanup script for Jamso AI Engine cache files
# This helps maintain performance by removing temporary files

echo "Cleaning up cache files..."

# Define directories to clean
CACHE_DIRS=(
    "./tmp"
    "./.pytest_cache"
    "./instance"
    "./__pycache__"
    "./src/__pycache__"
)

# Clean Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Clean temporary files
find ./tmp -type f -mtime +7 -delete 2>/dev/null

# Clean Flask instance folder
find ./instance -type f -name "*.sqlite" -mtime +30 -delete 2>/dev/null

# Clean Redis cache if available
if [ -f "./Tools/cleanup_redis.sh" ]; then
    echo "Running Redis cache cleanup..."
    ./Tools/cleanup_redis.sh
fi

echo "Cache cleanup complete!"
