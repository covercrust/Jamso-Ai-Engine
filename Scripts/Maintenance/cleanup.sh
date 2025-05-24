#!/bin/bash
# Enhanced cleanup script for Python projects
# Removes all cache files and directories

echo "Starting comprehensive cache cleanup..."

# Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Jupyter notebook cache
echo "Removing Jupyter notebook cache..."
find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +

# pytest cache
echo "Removing pytest cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".coverage" -exec rm -rf {} +
find . -type f -name ".coverage" -delete
find . -type f -name "coverage.xml" -delete
find . -type d -name "htmlcov" -exec rm -rf {} +

# mypy cache - enhanced to ensure root directory is included
echo "Removing mypy cache..."
if [ -d ".mypy_cache" ]; then
    echo "Removing root .mypy_cache directory..."
    rm -rf .mypy_cache
fi
find . -type d -name ".mypy_cache" -exec rm -rf {} \; 2>/dev/null

# Python egg and build directories
echo "Removing build artifacts..."
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -type d -name "*.egg" -exec rm -rf {} +
find . -type d -name "build" -prune -exec rm -rf {} +
find . -type d -name "dist" -prune -exec rm -rf {} +
find . -type d -name ".eggs" -exec rm -rf {} +

# pip cache
echo "Removing pip cache in the project..."
find . -type d -name ".pip_cache" -exec rm -rf {} +

# Temporary files
echo "Removing temporary files..."
find . -type f -name "*.log" -not -path "*/Logs/*" -delete
find . -type f -name "*.tmp" -delete
find . -type f -name "*.bak" -delete
find . -type f -name "*.swp" -delete
find . -type f -name "*~" -delete

# VS Code settings that might contain cache
echo "Removing .vscode caches..."
find . -type d -path "*/.vscode/.ropeproject" -exec rm -rf {} +

# Python type stub caches
echo "Removing type stub caches..."
find . -type d -name ".pyre" -exec rm -rf {} +
find . -type d -name ".pytype" -exec rm -rf {} +

# Other common cache directories
echo "Removing other common caches..."
find . -type d -name "__cache__" -exec rm -rf {} +
find . -type d -name ".cache" -exec rm -rf {} +

# Make sure the script is run from the project root
if [ -d "/home/jamso-ai-server/Jamso-Ai-Engine/.mypy_cache" ]; then
    echo "Removing project root .mypy_cache directory..."
    rm -rf /home/jamso-ai-server/Jamso-Ai-Engine/.mypy_cache
fi

echo "Cache cleanup completed successfully!"