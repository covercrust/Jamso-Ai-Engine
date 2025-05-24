#!/usr/bin/env python3
"""
Test script for the fallback optimizer to check type fixes.
"""

import pandas as pd
import numpy as np
import logging
import sys
import os

# Add project root to path for proper imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Configure logging to see details
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

# Import our modules
try:
    from src.AI.fallback_optimizer import (
        supertrend_strategy, 
        backtest_strategy,
        calculate_metrics,
        optimize_parameters
    )
    print("Successfully imported modules from fallback_optimizer")
except Exception as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def main():
    """Run a simple test of the optimizer"""
    try:
        # Create test data with proper datetime index
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        
        df = pd.DataFrame({
            'open': np.random.random(100) * 100 + 50,
            'high': np.random.random(100) * 100 + 60,
            'low': np.random.random(100) * 100 + 40,
            'close': np.random.random(100) * 100 + 50
        }, index=dates)
        
        # Make sure high is always higher than low
        for i in range(len(df)):
            max_val = max(df.iloc[i]['open'], df.iloc[i]['close'], df.iloc[i]['high'])
            min_val = min(df.iloc[i]['open'], df.iloc[i]['close'], df.iloc[i]['low'])
            df.iloc[i, df.columns.get_loc('high')] = max_val
            df.iloc[i, df.columns.get_loc('low')] = min_val
        
        print("Created test DataFrame")
        
        # First try just applying the strategy
        print("Testing supertrend_strategy function...")
        params = {'atr_period': 14, 'atr_multiplier': 3.0}
        strategy_df = supertrend_strategy(df, params)
        print(f"Strategy applied successfully, shape: {strategy_df.shape}")
        
        # Now test the backtest function
        print("\nTesting backtest_strategy function...")
        trades_df, equity_curve = backtest_strategy(df, params)
        print(f"Backtest completed, {len(trades_df)} trades generated")
        print(f"Initial equity: {equity_curve[0]}, Final equity: {equity_curve[-1]}")
        
        # Test metrics calculation
        print("\nTesting calculate_metrics function...")
        metrics = calculate_metrics(equity_curve, trades_df)
        print(f"Metrics calculated: {metrics}")
        
        # Finally test the optimizer
        print("\nTesting optimize_parameters function...")
        search_space = {
            'atr_period': list(range(10, 20)),
            'atr_multiplier': [x / 10 for x in range(20, 40)]
        }
        
        best_params, best_value, results = optimize_parameters(
            df, 
            supertrend_strategy, 
            search_space, 
            objective_name='sharpe',
            num_evals=5
        )
        
        print("\nOptimization complete!")
        print(f"Best parameters: {best_params}")
        print(f"Best value: {best_value}")
        print(f"Results count: {len(results)}")
        
        return 0
    
    except Exception as e:
        import traceback
        print(f"Error in main function: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
