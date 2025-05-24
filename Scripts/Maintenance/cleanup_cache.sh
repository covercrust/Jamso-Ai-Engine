#!/bin/bash

# JAMSO AI Engine - Cache Cleanup Script
# This script removes Python cache files and other temporary files

echo "Starting cleanup process..."

# Find and remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -exec rm -f {} +
find . -type f -name "*.pyo" -exec rm -f {} +
find . -type f -name "*.pyd" -exec rm -f {} +

# Remove pytest cache
echo "Removing pytest cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Remove temporary files
echo "Removing temporary files..."
find . -type f -name "*.bak" -exec rm -f {} +
find . -type f -name "*.tmp" -exec rm -f {} +
find . -type f -name "*.swp" -exec rm -f {} +
find . -type f -name "*.swo" -exec rm -f {} +

# Remove empty directories (optional)
# echo "Removing empty directories..."
# find . -type d -empty -delete

echo "Cache cleanup complete!"

# Note: This script does NOT remove the virtual environment (.venv)
# If you want to rebuild the virtual environment, run:
# echo "To rebuild virtual environment, use: rm -rf .venv && python -m venv .venv"