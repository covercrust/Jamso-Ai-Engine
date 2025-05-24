#!/bin/bash

# JAMSO AI Engine - Clean Environment Setup Script
# This script completely rebuilds the Python virtual environment

echo "🧹 Clean Environment Setup Script"
echo "=================================="
echo "This script will remove the current virtual environment and create a fresh one."
echo ""

# Ask for confirmation
read -p "⚠️  This will delete the current virtual environment. Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Operation cancelled."
    exit 0
fi

# Remove current virtual environment
echo "🗑️  Removing current virtual environment..."
rm -rf .venv

# Create new virtual environment
echo "🔨 Creating new virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Run cleanup script
echo "🧹 Cleaning up cache files..."
./cleanup_cache.sh

echo ""
echo "✅ Environment setup complete! Your virtual environment has been rebuilt."
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"

# Deactivate virtual environment
deactivate
