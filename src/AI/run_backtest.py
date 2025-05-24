#!/usr/bin/env python3
"""
Jamso AI Engine - Backtest Runner

This script provides a command-line interface for backtesting trading strategies
using the Jamso AI Engine's performance monitoring system.

Usage:
    python run_backtest.py --strategy supertrend --symbol EURUSD --from 2024-01-01 --to 2024-04-30
    python run_backtest.py --strategy supertrend --use-sample-data --days 365

Features:
- Run backtests with different strategies and parameters
- Load historical market data from database or CSV files
- Generate synthetic data when needed
- Output detailed performance metrics
- Save and load backtest results
- Parameter optimization
- Comparison with benchmark strategies
"""

import argparse
import pandas as pd
import numpy as np
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import matplotlib.pyplot as plt
from pathlib import Path

# Import Jamso AI Engine components
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.AI.performance_monitor import PerformanceMonitor
from src.AI.example_strategies import jamso_ai_bot_strategy
from src.AI.backtest_utils import DataLoader, ResultSaver

# Available strategies
STRATEGIES = {
    "supertrend": jamso_ai_bot_strategy,
    # Add more strategies as they become available
}

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Jamso AI Engine Backtest Runner')
    
    # Strategy selection
    parser.add_argument('--strategy', type=str, choices=list(STRATEGIES.keys()), 
                      default='supertrend', help='Trading strategy to backtest')
    
    # Data source options
    data_group = parser.add_argument_group('Data Source')
    data_group.add_argument('--symbol', type=str, default='EURUSD', 
                        help='Symbol to backtest (e.g., EURUSD, BTCUSD)')
    data_group.add_argument('--from', dest='from_date', type=str, 
                        help='Start date in YYYY-MM-DD format')
    data_group.add_argument('--to', dest='to_date', type=str, 
                        help='End date in YYYY-MM-DD format')
    data_group.add_argument('--csv', type=str, help='Path to CSV file with historical data')
    data_group.add_argument('--use-sample-data', action='store_true', 
                        help='Use synthetic sample data')
    data_group.add_argument('--days', type=int, default=365, 
                        help='Number of days for sample data')
    
    # Strategy parameters
    param_group = parser.add_argument_group('Strategy Parameters')
    param_group.add_argument('--atr-len', type=int, default=10, 
                         help='ATR length')
    param_group.add_argument('--fact', type=float, default=2.8, 
                         help='SuperTrend factor')
    param_group.add_argument('--risk-percent', type=float, default=1.0, 
                         help='Risk percentage per trade')
    param_group.add_argument('--sl-percent', type=float, default=0.5, 
                         help='Stop-loss percentage')
    param_group.add_argument('--tp-percent', type=float, default=1.5, 
                         help='Take-profit percentage')
    param_group.add_argument('--initial-capital', type=float, default=5000, 
                         help='Initial capital for backtest')
    
    # Performance analysis options
    perf_group = parser.add_argument_group('Performance Analysis')
    perf_group.add_argument('--optimize', action='store_true', 
                        help='Run parameter optimization')
    perf_group.add_argument('--benchmark', action='store_true', 
                        help='Compare with benchmark strategies')
    perf_group.add_argument('--save-results', type=str, 
                        help='Save results to specified JSON file')
    perf_group.add_argument('--load-results', type=str, 
                        help='Load and analyze previously saved results')
    perf_group.add_argument('--plot', action='store_true', 
                        help='Plot equity curve and metrics')
    perf_group.add_argument('--verbose', '-v', action='store_true', 
                        help='Show detailed output')
    
    return parser.parse_args()

def load_data(args):
    """Load market data based on command line arguments."""
    # Database path
    db_path = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'
    
    # Check if we should load previously saved results
    if args.load_results:
        print(f"Loading saved backtest results from {args.load_results}")
        results = ResultSaver.load_results(args.load_results)
        return None, results
        
    # Load data from CSV if specified
    if args.csv:
        if not os.path.exists(args.csv):
            print(f"Error: CSV file not found: {args.csv}")
            sys.exit(1)
        return DataLoader.load_from_csv(args.csv), None
        
    # Use synthetic sample data if requested
    if args.use_sample_data:
        return DataLoader.generate_sample_data(
            symbol=args.symbol, 
            days=args.days,
            start_date=args.from_date
        ), None
        
    # Otherwise load from database (default)
    data = DataLoader.load_from_db(
        db_path=db_path,
        symbol=args.symbol,
        start_date=args.from_date,
        end_date=args.to_date
    )
    
    # If no data in database, generate sample data as fallback
    if data is None or data.empty:
        print(f"No data found in database for {args.symbol}. Generating synthetic data as fallback.")
        data = DataLoader.generate_sample_data(
            symbol=args.symbol, 
            days=args.days,
            start_date=args.from_date
        )
        
    return data, None

def extract_strategy_params(args):
    """Extract strategy parameters from command line arguments."""
    # For SuperTrend strategy
    if args.strategy == 'supertrend':
        return {
            'atr_len': args.atr_len,
            'fact': args.fact,
            'risk_percent': args.risk_percent,
            'sl_percent': args.sl_percent,
            'tp_percent': args.tp_percent,
            'initial_capital': args.initial_capital,
            # Additional parameters with default values
            'direction_bias': "Both",
            'max_contracts': 28,
            'spread_pips': 0.0,
            'trailing_stop': False
        }
    
    # For other strategies
    return {}

def run_optimization(monitor, data, strategy_fn, base_params):
    """Run parameter optimization."""
    print("\n--- Running Parameter Optimization ---")
    
    # Define parameter grid based on strategy
    param_grid = {
        'atr_len': [5, 10, 14, 21],
        'fact': [1.5, 2.0, 2.5, 3.0, 3.5],
        'sl_percent': [0.3, 0.5, 0.7, 1.0],
        'tp_percent': [1.0, 1.5, 2.0, 2.5]
    }
    
    print(f"Testing {len(param_grid['atr_len']) * len(param_grid['fact']) * len(param_grid['sl_percent']) * len(param_grid['tp_percent'])} parameter combinations")
    print("This may take a while...")
    
    # Create new monitor for optimization
    opt_monitor = PerformanceMonitor(strategy_fn, data, base_params)
    best_params = opt_monitor.optimize_parameters(param_grid, max_evals=20)
    
    print("\nOptimal Parameters Found:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")
        
    # Run backtest with optimal parameters
    print("\nRunning backtest with optimal parameters...")
    opt_monitor = PerformanceMonitor(strategy_fn, data, best_params)
    results = opt_monitor.run_backtest()
    
    print("\nPerformance with Optimal Parameters:")
    for metric, value in results.metrics.items():
        print(f"  {metric}: {value:.4f}" if isinstance(value, float) else f"  {metric}: {value}")
        
    return best_params, results

def run_benchmark_comparison(data, strategy_fn, params):
    """Compare strategy with benchmarks."""
    print("\n--- Benchmark Comparison ---")
    
    # Create benchmark strategies with different parameters
    benchmark_params = [
        # Conservative
        {**params, 'fact': 3.5, 'risk_percent': 0.5, 'sl_percent': 1.0},
        # Aggressive
        {**params, 'fact': 2.0, 'risk_percent': 2.0, 'sl_percent': 0.3},
        # Balanced
        {**params, 'fact': 3.0, 'risk_percent': 1.0, 'sl_percent': 0.5}
    ]
    
    benchmark_names = ['Conservative', 'Aggressive', 'Balanced']
    benchmark_results = []
    
    # Run benchmarks
    for i, bp in enumerate(benchmark_params):
        print(f"\nRunning {benchmark_names[i]} benchmark...")
        monitor = PerformanceMonitor(strategy_fn, data, bp)
        result = monitor.run_backtest()
        benchmark_results.append(result)
        
        print(f"{benchmark_names[i]} Performance:")
        for metric, value in result.metrics.items():
            print(f"  {metric}: {value:.4f}" if isinstance(value, float) else f"  {metric}: {value}")
    
    # Compare results
    monitor = PerformanceMonitor(strategy_fn, data, params)
    monitor.run_backtest()
    comparison = monitor.benchmark(benchmark_results)
    
    print("\nStrategy Comparison:")
    pd.set_option('display.float_format', '{:.4f}'.format)
    print(comparison)
    
    return benchmark_results, comparison

def plot_results(results, title="Backtest Results"):
    """Plot equity curve and performance metrics."""
    try:
        plt.figure(figsize=(12, 8))
        
        # Plot equity curve
        plt.subplot(2, 1, 1)
        plt.plot(results.equity_curve.index, results.equity_curve.values)
        plt.title(f"{title} - Equity Curve")
        plt.xlabel("Date")
        plt.ylabel("Account Value")
        plt.grid(True)
        
        # Calculate drawdowns
        peak = results.equity_curve.cummax()
        drawdown = (results.equity_curve - peak) / peak * 100
        
        # Plot drawdowns
        plt.subplot(2, 1, 2)
        plt.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
        plt.title("Drawdown %")
        plt.xlabel("Date")
        plt.ylabel("Drawdown %")
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"Error plotting results: {e}")

def print_metrics_table(metrics):
    """Print metrics in a formatted table."""
    print("\n--- Performance Metrics ---")
    print("-" * 40)
    
    # Handle various metric types with appropriate formatting
    for key, value in metrics.items():
        if isinstance(value, float):
            if 'percent' in key.lower() or 'rate' in key.lower():
                print(f"{key.replace('_', ' ').title():25}: {value*100:.2f}%")
            else:
                print(f"{key.replace('_', ' ').title():25}: {value:.4f}")
        else:
            print(f"{key.replace('_', ' ').title():25}: {value}")
    print("-" * 40)

def main():
    """Main function to run the backtest."""
    args = parse_args()
    
    print(f"\nJamso AI Engine - Backtest Runner")
    print(f"================================")
    
    # Load the data
    data, saved_results = load_data(args)
    
    # If we're just analyzing saved results
    if saved_results:
        print("\nAnalyzing saved backtest results:")
        print_metrics_table(saved_results.get('metrics', {}))
        
        if args.plot and 'equity_curve' in saved_results:
            plot_results(saved_results, title=f"Saved Results")
        return
    
    # Show data summary
    print(f"\nData Summary:")
    print(f"  Symbol: {args.symbol}")
    print(f"  Period: {data['timestamp'].min().date()} to {data['timestamp'].max().date()}")
    print(f"  Data Points: {len(data)}")
    
    # Get strategy function
    strategy_fn = STRATEGIES[args.strategy]
    params = extract_strategy_params(args)
    
    # Show strategy and parameters
    print(f"\nStrategy: {args.strategy}")
    print("Parameters:")
    for param, value in params.items():
        print(f"  {param}: {value}")
    
    # Run parameter optimization if requested
    if args.optimize:
        best_params, opt_results = run_optimization(None, data, strategy_fn, params)
        # Update params with optimized values
        params = best_params
    
    # Run the backtest
    print("\nRunning backtest...")
    monitor = PerformanceMonitor(strategy_fn, data, params)
    results = monitor.run_backtest()
    
    # Print results
    print("\nBacktest completed!")
    print_metrics_table(results.metrics)
    
    # Run benchmark comparison if requested
    if args.benchmark:
        benchmark_results, comparison = run_benchmark_comparison(data, strategy_fn, params)
    
    # Save results if requested
    if args.save_results:
        output_file = args.save_results
        if not output_file.endswith('.json'):
            output_file += '.json'
            
        # Prepare results
        save_data = {
            'strategy': args.strategy,
            'symbol': args.symbol,
            'params': params,
            'metrics': results.metrics,
            'equity_curve': results.equity_curve,
            'trades': results.trades,
            'timestamp': datetime.now().isoformat()
        }
        
        ResultSaver.save_results(save_data, output_file)
    
    # Plot if requested
    if args.plot:
        plot_results(results, title=f"{args.strategy.upper()} on {args.symbol}")
    
    # Print detailed trades if verbose
    if args.verbose and not results.trades.empty:
        print("\nTrade Summary:")
        print(f"Total Trades: {len(results.trades)}")
        winning_trades = results.trades[results.trades['pnl'] > 0]
        losing_trades = results.trades[results.trades['pnl'] < 0]
        print(f"Winning Trades: {len(winning_trades)} ({len(winning_trades)/len(results.trades)*100:.1f}%)")
        print(f"Losing Trades: {len(losing_trades)} ({len(losing_trades)/len(results.trades)*100:.1f}%)")
        
        if len(results.trades) > 10:
            print("\nFirst 5 trades:")
            print(results.trades.head(5))
            print("\nLast 5 trades:")
            print(results.trades.tail(5))
        else:
            print("\nAll trades:")
            print(results.trades)

if __name__ == "__main__":
    main()
