#!/usr/bin/env python3
"""
Test type annotations in the Jamso-AI-Engine codebase.
This script imports functions from various modules to test if Pylance detects any type issues.
"""

# Import from capital_api_utils
from src.AI.capital_api_utils import fetch_historical_data, save_market_data_to_csv

# Import from capital_data_optimizer
from src.AI.capital_data_optimizer import fetch_market_data

# Import from visualize_capital_data
from src.AI.visualize_capital_data import apply_strategy_with_parameters

# Import from visualize_optimization
from src.AI.visualize_optimization import load_parameters

# Simple test
def test_imports():
    print("Successfully imported all functions")

if __name__ == "__main__":
    test_imports()
    print("All imports succeeded. Type checking should be working correctly.")
