#!/usr/bin/env python3
"""
Jamso AI Engine - Parameter Optimizer

This utility provides advanced parameter optimization tools for trading strategies:
- Grid search across parameter spaces
- Hyperparameter tuning using various metrics
- Visualization of parameter sensitivity
- Export of optimal parameter configurations

Features:
- Parallelized optimization for speed
- Adaptive parameter space exploration
- Multiple optimization objectives (return, Sharpe, drawdown, etc.)
- Visualization of parameter impacts
"""

import argparse
import pandas as pd
import numpy as np
import os
import sys
import json
import itertools
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import matplotlib.pyplot as plt
from pathlib import Path

# Import Jamso AI Engine components
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.AI.performance_monitor import PerformanceMonitor
from src.AI.example_strategies import jamso_ai_bot_strategy
from src.AI.backtest_utils import DataLoader, ResultSaver

# Define optimization objectives
OBJECTIVES: Dict[str, Any] = {
    'sharpe': lambda metrics: metrics.get('sharpe_ratio', 0),
    'return': lambda metrics: metrics.get('total_return', 0),
    'calmar': lambda metrics: metrics.get('total_return', 0) / abs(metrics.get('max_drawdown', 1) or 0.0001),
    'win_rate': lambda metrics: metrics.get('win_rate', 0),
    'risk_adjusted': lambda metrics: metrics.get('total_return', 0) / (abs(metrics.get('max_drawdown', 1)) + 0.01),
}

# Strategies available for optimization
STRATEGIES = {
    "supertrend": jamso_ai_bot_strategy,
    # Add more strategies as they become available
}

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Jamso AI Engine Parameter Optimizer')
    
    # Strategy selection
    parser.add_argument('--strategy', type=str, choices=list(STRATEGIES.keys()), 
                      default='supertrend', help='Trading strategy to optimize')
    
    # Data source options
    parser.add_argument('--symbol', type=str, default='EURUSD', 
                      help='Symbol to backtest (e.g., EURUSD, BTCUSD)')
    parser.add_argument('--from', dest='from_date', type=str, 
                      help='Start date in YYYY-MM-DD format')
    parser.add_argument('--to', dest='to_date', type=str, 
                      help='End date in YYYY-MM-DD format')
    parser.add_argument('--csv', type=str, help='Path to CSV file with historical data')
    parser.add_argument('--use-sample-data', action='store_true', 
                      help='Use synthetic sample data')
    
    # Optimization settings
    parser.add_argument('--objective', type=str, choices=list(OBJECTIVES.keys()),
                      default='sharpe', help='Optimization objective')
    parser.add_argument('--params', type=str, 
                      help='JSON string of parameter grid, e.g., \'{"atr_len": [10, 20], "fact": [2.0, 3.0]}\'')
    parser.add_argument('--max-evals', type=int, default=100,
                      help='Maximum number of evaluations')
    parser.add_argument('--parallel', action='store_true',
                      help='Use parallel processing')
    parser.add_argument('--cores', type=int, default=multiprocessing.cpu_count() - 1,
                      help='Number of CPU cores to use')
    
    # Output options
    parser.add_argument('--output', type=str, default='optimization_results.json',
                      help='Output file for optimization results')
    parser.add_argument('--visualize', action='store_true',
                      help='Generate visualizations of parameter impacts')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Show detailed output')
    
    return parser.parse_args()

def load_data(args):
    """Load market data based on command line arguments."""
    # Database path
    db_path = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'
    
    # Load data from CSV if specified
    if args.csv:
        if not os.path.exists(args.csv):
            print(f"Error: CSV file not found: {args.csv}")
            sys.exit(1)
        return DataLoader.load_from_csv(args.csv)
        
    # Use synthetic sample data if requested
    if args.use_sample_data:
        return DataLoader.generate_sample_data(
            symbol=args.symbol, 
            days=365,
            start_date=args.from_date
        )
        
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
            days=365,
            start_date=args.from_date
        )
        
    return data

def get_parameter_grid(args):
    """Get parameter grid to search, either from args or defaults."""
    if args.params:
        try:
            return json.loads(args.params)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in --params argument")
            sys.exit(1)
    
    # Define default parameter grid based on strategy
    if args.strategy == 'supertrend':
        return {
            'atr_len': [5, 10, 14, 21],
            'fact': [1.5, 2.0, 2.5, 3.0, 3.5],
            'sl_percent': [0.3, 0.5, 0.7, 1.0],
            'tp_percent': [1.0, 1.5, 2.0, 2.5]
        }
    
    # Default for other strategies
    return {
        'param1': [1, 2, 3],
        'param2': [0.1, 0.2, 0.3]
    }

def evaluate_params(args_tuple):
    """Evaluate a single parameter set."""
    data, strategy_fn, params, objective_fn = args_tuple
    
    try:
        # Run backtest with these parameters
        monitor = PerformanceMonitor(strategy_fn, data, params)
        result = monitor.run_backtest()
        
        # Calculate score based on objective function
        score = objective_fn(result.metrics)
        
        return {
            'params': params,
            'score': score,
            'metrics': result.metrics
        }
    except Exception as e:
        print(f"Error evaluating parameters {params}: {e}")
        return {
            'params': params,
            'score': float('-inf'),
            'metrics': {'error': str(e)}
        }

def run_grid_search(data, strategy_fn, param_grid, objective_fn, max_evals, use_parallel=False, cores=None):
    """Run grid search optimization."""
    # Generate all parameter combinations
    param_keys = list(param_grid.keys())
    param_values = list(param_grid.values())
    
    # Calculate total combinations
    total_combos = 1
    for values in param_values:
        total_combos *= len(values)
    
    print(f"Parameter space has {total_combos} combinations")
    print(f"Running up to {max_evals} evaluations")
    
    # Generate parameter combinations
    all_combos = list(itertools.product(*param_values))
    np.random.shuffle(all_combos)  # Randomize order
    
    # Limit by max_evals
    if max_evals < len(all_combos):
        all_combos = all_combos[:max_evals]
    
    # Prepare parameter dictionaries
    param_dicts = [dict(zip(param_keys, combo)) for combo in all_combos]
    
    # Add other fixed parameters
    for p in param_dicts:
        p['initial_capital'] = 5000
        p['direction_bias'] = "Both"
    
    results = []
    
    if use_parallel and cores:
        # Use parallel processing
        print(f"Using {cores} CPU cores for parallel processing")
        args_list = [(data, strategy_fn, p, objective_fn) for p in param_dicts]
        
        with multiprocessing.Pool(processes=cores) as pool:
            results = pool.map(evaluate_params, args_list)
    else:
        # Sequential processing
        for i, params in enumerate(param_dicts):
            print(f"Evaluating parameter set {i+1}/{len(param_dicts)}")
            result = evaluate_params((data, strategy_fn, params, objective_fn))
            results.append(result)
            
            # Print progress
            if (i+1) % 10 == 0 or i+1 == len(param_dicts):
                print(f"Completed {i+1}/{len(param_dicts)} evaluations")
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results

def visualize_parameter_impacts(results, param_grid):
    """Create visualizations of parameter impacts on performance."""
    # Convert results to DataFrame for analysis
    results_df = pd.DataFrame([
        {**r['params'], 'score': r['score'], **r['metrics']}
        for r in results
    ])
    
    # Create parameter impact plots
    plt.figure(figsize=(15, 10))
    
    for i, param in enumerate(param_grid.keys()):
        if len(param_grid[param]) > 1:  # Only visualize parameters with multiple values
            plt.subplot(2, 2, i % 4 + 1)
            
            # Group by this parameter and get mean score
            grouped = results_df.groupby(param)['score'].mean().reset_index()
            plt.bar(grouped[param].astype(str), grouped['score'])
            
            plt.title(f"Impact of {param}")
            plt.xlabel(param)
            plt.ylabel("Performance Score")
            plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("parameter_impacts.png")
    plt.close()
    
    # Create scatter plots for pairs of parameters
    params = list(param_grid.keys())
    if len(params) >= 2:
        for i in range(min(6, len(params))):
            for j in range(i+1, min(6, len(params))):
                plt.figure(figsize=(10, 8))
                
                scatter = plt.scatter(
                    results_df[params[i]], 
                    results_df[params[j]],
                    c=results_df['score'],
                    cmap='viridis',
                    alpha=0.7,
                    s=100
                )
                
                plt.colorbar(scatter, label='Performance Score')
                plt.title(f"Parameter Interaction: {params[i]} vs {params[j]}")
                plt.xlabel(params[i])
                plt.ylabel(params[j])
                plt.grid(True, alpha=0.3)
                
                plt.savefig(f"param_interaction_{params[i]}_{params[j]}.png")
                plt.close()
    
    print("Visualizations saved as PNG files")

def main():
    """Main function."""
    args = parse_args()
    
    print(f"\nJamso AI Engine - Parameter Optimizer")
    print(f"===================================")
    
    # Load the data
    data = load_data(args)
    
    # Show data summary
    print(f"\nData Summary:")
    print(f"  Symbol: {args.symbol}")
    print(f"  Period: {data['timestamp'].min().date()} to {data['timestamp'].max().date()}")
    print(f"  Data Points: {len(data)}")
    
    # Get strategy function
    strategy_fn = STRATEGIES[args.strategy]
    
    # Get parameter grid
    param_grid = get_parameter_grid(args)
    print("\nParameter Grid:")
    for param, values in param_grid.items():
        print(f"  {param}: {values}")
    
    # Get objective function
    objective_fn = OBJECTIVES[args.objective]
    print(f"Optimization Objective: {args.objective}")
    
    # Run grid search
    print("\nStarting parameter optimization...")
    results = run_grid_search(
        data=data,
        strategy_fn=strategy_fn,
        param_grid=param_grid,
        objective_fn=objective_fn,
        max_evals=args.max_evals,
        use_parallel=args.parallel,
        cores=args.cores if args.parallel else None
    )
    
    # Print top results
    print("\nTop 5 Parameter Combinations:")
    for i, result in enumerate(results[:5]):
        print(f"\n{i+1}. Score: {result['score']:.4f}")
        
        # Print parameters
        for param, value in result['params'].items():
            if param in param_grid:  # Only show optimized parameters
                print(f"   {param}: {value}")
        
        # Print key metrics
        metrics = result['metrics']
        print(f"   Total Return: {metrics.get('total_return', 0):.2%}")
        print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
        print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"   Win Rate: {metrics.get('win_rate', 0):.2%}")
    
    # Save results
    output_file = args.output
    if not output_file.endswith('.json'):
        output_file += '.json'
        
    output_data = {
        'strategy': args.strategy,
        'symbol': args.symbol,
        'objective': args.objective,
        'param_grid': param_grid,
        'results': results[:20],  # Save top 20 results
        'best_params': results[0]['params'],
        'timestamp': datetime.now().isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"\nOptimization results saved to {output_file}")
    
    # Generate visualizations
    if args.visualize:
        print("\nGenerating parameter impact visualizations...")
        visualize_parameter_impacts(results, param_grid)

if __name__ == "__main__":
    main()
