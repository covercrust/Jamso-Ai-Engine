#!/usr/bin/env python3
"""
Simple Parameter Optimization Script
This minimal script demonstrates the core functionality of parameter optimization
without complex dependencies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_data(days=100):
    """Generate synthetic price data for testing."""
    # Generate dates
    start = datetime.now() - timedelta(days=days)
    dates = pd.date_range(start=start, periods=days)
    
    # Generate random prices
    price = 100.0
    prices = []
    
    for _ in range(days):
        price = price * (1 + np.random.normal(0, 0.015))
        prices.append(price)
    
    # Create dataframe
    df = pd.DataFrame({
        'date': dates,
        'price': prices
    })
    
    return df

def moving_average_strategy(data, short_period=10, long_period=30):
    """Simple moving average crossover strategy."""
    df = data.copy()
    
    # Calculate moving averages
    df['short_ma'] = df['price'].rolling(window=short_period).mean()
    df['long_ma'] = df['price'].rolling(window=long_period).mean()
    
    # Generate trading signals (1 for buy, -1 for sell, 0 for hold)
    signals = np.zeros(len(df))
    
    for i in range(long_period, len(df)):
        if df['short_ma'].iloc[i] > df['long_ma'].iloc[i] and df['short_ma'].iloc[i-1] <= df['long_ma'].iloc[i-1]:
            signals[i] = 1  # Buy signal
        elif df['short_ma'].iloc[i] < df['long_ma'].iloc[i] and df['short_ma'].iloc[i-1] >= df['long_ma'].iloc[i-1]:
            signals[i] = -1  # Sell signal
    
    df['signal'] = signals
    
    # Calculate strategy performance
    df['position'] = df['signal'].replace(to_replace=0, method='ffill')
    df['returns'] = df['price'].pct_change() * df['position'].shift(1)
    
    # Calculate metrics
    total_return = (1 + df['returns']).prod() - 1
    sharpe_ratio = df['returns'].mean() / df['returns'].std() * np.sqrt(252) if df['returns'].std() > 0 else 0
    
    return {
        'short_period': short_period,
        'long_period': long_period,
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio
    }

def optimize_parameters(data, param_grid):
    """Optimize strategy parameters using grid search."""
    results = []
    
    # Try all parameter combinations
    for short_period in param_grid['short_period']:
        for long_period in param_grid['long_period']:
            if short_period >= long_period:
                continue  # Skip invalid combinations
                
            # Run strategy with these parameters
            result = moving_average_strategy(data, short_period, long_period)
            results.append(result)
    
    # Sort by Sharpe ratio (descending)
    results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
    
    return results

def main():
    print("Jamso AI Engine - Simple Parameter Optimizer Demo")
    print("================================================")
    
    # Generate sample data
    data = generate_sample_data(days=252)  # One year of data
    print(f"Generated {len(data)} days of sample data")
    
    # Define parameter grid
    param_grid = {
        'short_period': [5, 10, 15, 20],
        'long_period': [20, 30, 40, 50]
    }
    
    # Run optimization
    print("\nRunning parameter optimization...")
    start_time = datetime.now()
    results = optimize_parameters(data, param_grid)
    end_time = datetime.now()
    
    # Print results
    print(f"\nOptimization completed in {(end_time - start_time).total_seconds():.2f} seconds")
    print("\nTop 3 parameter combinations:")
    
    for i, result in enumerate(results[:3]):
        print(f"\n{i+1}. Short MA: {result['short_period']}, Long MA: {result['long_period']}")
        print(f"   Total Return: {result['total_return']:.2%}")
        print(f"   Sharpe Ratio: {result['sharpe_ratio']:.2f}")
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()
