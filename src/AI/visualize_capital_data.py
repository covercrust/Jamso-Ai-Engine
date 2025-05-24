#!/usr/bin/env python3
"""
Capital.com Market Data Visualization for Parameter Optimization

This script provides visualization tools for capital.com market data 
and parameter optimization results.

Usage:
    python visualize_capital_data.py --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json
    python visualize_capital_data.py --compare --symbol BTCUSD --timeframe HOUR
"""

import os
import sys
import pandas as pd
import numpy as np
import json
import argparse
import logging
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter, MaxNLocator
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Add parent directory to path to access the standalone optimizer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Import the standalone optimizer functions
from src.AI.standalone_optimizer import (
    supertrend_strategy, 
    calculate_metrics,
    plot_optimization_results
)

# Import the capital data optimizer functions
from src.AI.capital_data_optimizer import (
    fetch_market_data,
    fetch_market_sentiment,
    supertrend_with_sentiment,
    RESOLUTION_MAP
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_strategy_with_parameters(df: pd.DataFrame, params_file: str, use_sentiment: bool = False) -> Optional[dict]:
    """
    Apply the strategy with parameters from a parameter file and return results
    
    Parameters:
    - df: DataFrame with price data
    - params_file: Path to the JSON file with optimized parameters
    - use_sentiment: Whether to use sentiment data in the strategy
    
    Returns:
    - Dictionary with strategy results or None if operation fails
    """
    try:
        with open(params_file, 'r') as f:
            data = json.load(f)
        
        params = data.get('params', {})
        metadata = data.get('metadata', {})
        
        logger.info(f"Loaded parameters from {params_file}")
        logger.info(f"Metadata: {metadata}")
        
        # Apply the strategy with the loaded parameters
        if use_sentiment and metadata.get('use_sentiment'):
            sentiment_weight = metadata.get('sentiment_weight', 0.2)
            result = supertrend_with_sentiment(df, **params, sentiment_weight=sentiment_weight)
        else:
            result = supertrend_strategy(df, **params)
        
        # Calculate metrics
        metrics = calculate_metrics(result)
        logger.info(f"Strategy performance metrics: {metrics}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error applying strategy with parameters: {str(e)}")
        return None

def plot_parameter_importance(params_dir: str, output_file: str = None):
    """
    Plot parameter importance across different optimization objectives
    
    Parameters:
    - params_dir: Directory containing parameter files
    - output_file: Path to save the plot
    """
    # Find all parameter files
    param_files = [
        os.path.join(params_dir, f) 
        for f in os.listdir(params_dir) 
        if f.startswith('capital_com_optimized_params_') and f.endswith('.json')
    ]
    
    if not param_files:
        logger.error(f"No parameter files found in {params_dir}")
        return
    
    # Extract parameters from all files
    param_data = {}
    
    for file_path in param_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            params = data.get('params', {})
            metadata = data.get('metadata', {})
            symbol = metadata.get('symbol', 'unknown')
            timeframe = metadata.get('timeframe', 'unknown')
            objective = metadata.get('objective', 'unknown')
            
            # Create a key for this parameter set
            key = f"{symbol}_{timeframe}_{objective}"
            param_data[key] = params
                
        except Exception as e:
            logger.error(f"Error reading parameter file {file_path}: {str(e)}")
    
    if not param_data:
        logger.error("No valid parameter data found")
        return
    
    # Plot parameter importance
    fig, axes = plt.subplots(len(next(iter(param_data.values()))), 1, figsize=(12, 12))
    
    # For each parameter, show its distribution across different objectives
    for i, param_name in enumerate(next(iter(param_data.values())).keys()):
        param_values = {}
        for key, params in param_data.items():
            objective = key.split('_')[-1]  # Extract objective from key
            if objective not in param_values:
                param_values[objective] = []
            param_values[objective].append(params[param_name])
        
        # Plot this parameter
        ax = axes[i]
        positions = np.arange(len(param_values))
        colors = plt.cm.viridis(np.linspace(0, 1, len(param_values)))
        
        # Create a box plot
        box_data = [values for values in param_values.values()]
        ax.boxplot(box_data, positions=positions, patch_artist=True,
                  boxprops=dict(facecolor='lightblue'))
        
        # Add scatter points for individual values
        for j, (objective, values) in enumerate(param_values.items()):
            ax.scatter([j] * len(values), values, color=colors[j], alpha=0.5)
        
        ax.set_title(f'Parameter: {param_name}')
        ax.set_xticks(positions)
        ax.set_xticklabels(list(param_values.keys()))
        ax.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    # Save the plot if requested
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"Parameter importance plot saved to {output_file}")
    else:
        plt.show()

def plot_strategy_performance_comparison(df: pd.DataFrame, param_files: List[str], output_file: str = None):
    """
    Plot strategy performance comparison for different parameter sets
    
    Parameters:
    - df: DataFrame with price data
    - param_files: List of parameter files to compare
    - output_file: Path to save the plot
    """
    if not param_files:
        logger.error("No parameter files provided for comparison")
        return
    
    # Apply each parameter set to the same data
    results = {}
    metrics = {}
    
    for file_path in param_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            params = data.get('params', {})
            metadata = data.get('metadata', {})
            objective = metadata.get('objective', 'unknown')
            
            # Apply the strategy
            if metadata.get('use_sentiment'):
                sentiment_weight = metadata.get('sentiment_weight', 0.2)
                result = supertrend_with_sentiment(df, **params, sentiment_weight=sentiment_weight)
            else:
                result = supertrend_strategy(df, **params)
            
            # Store results
            results[objective] = result
            metrics[objective] = calculate_metrics(result)
                
        except Exception as e:
            logger.error(f"Error processing parameter file {file_path}: {str(e)}")
    
    if not results:
        logger.error("No valid results generated")
        return
        
    # Create a comparison plot
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
    
    # Price chart with equity curves
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(df['timestamp'], df['close'], color='black', alpha=0.5, label='Price')
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
    
    for i, (objective, result) in enumerate(results.items()):
        equity_curve = result.get('equity_curve', [])
        timestamps = df['timestamp'][:len(equity_curve)]
        
        # Normalize equity curve to start at same point as price for visual comparison
        normalized_equity = np.array(equity_curve) / equity_curve[0] * df['close'].iloc[0]
        
        ax1.plot(timestamps, normalized_equity, color=colors[i], 
                label=f"{objective.capitalize()} (Return: {metrics[objective]['total_return']:.2f}%)")
    
    ax1.set_title('Strategy Performance Comparison')
    ax1.legend(loc='best')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Metrics comparison as a table
    ax2 = fig.add_subplot(gs[1])
    ax2.axis('tight')
    ax2.axis('off')
    
    # Prepare table data
    metric_names = ['Total Return (%)', 'Sharpe Ratio', 'Max Drawdown (%)', 
                   'Win Rate (%)', 'Profit Factor', 'Total Trades']
    
    table_data = []
    for objective, m in metrics.items():
        table_data.append([
            f"{m['total_return']:.2f}", 
            f"{m['sharpe_ratio']:.2f}", 
            f"{m['max_drawdown']:.2f}", 
            f"{m['win_rate']:.2f}", 
            f"{m['profit_factor']:.2f}", 
            f"{m['total_trades']}"
        ])
    
    objectives = list(metrics.keys())
    table = ax2.table(cellText=table_data, rowLabels=objectives, 
                     colLabels=metric_names, loc='center', cellLoc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    
    plt.tight_layout()
    
    # Save the plot if requested
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"Strategy performance comparison plot saved to {output_file}")
    else:
        plt.show()

def main():
    """Main function to handle command-line arguments and run visualization tools."""
    parser = argparse.ArgumentParser(description="Capital.com Market Data Visualization")
    parser.add_argument("--params-file", type=str, help="Path to optimized parameters file")
    parser.add_argument("--compare", action="store_true", help="Compare different optimization objectives")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Market symbol for comparison")
    parser.add_argument("--timeframe", type=str, default="HOUR", choices=list(RESOLUTION_MAP.keys()), 
                        help="Timeframe for comparison")
    parser.add_argument("--days", type=int, default=30, help="Days of historical data to fetch")
    parser.add_argument("--importance-plot", action="store_true", 
                       help="Generate parameter importance plot")
    
    args = parser.parse_args()
    
    # Fetch data for visualization
    if args.compare or args.params_file:
        df = fetch_market_data(args.symbol, RESOLUTION_MAP[args.timeframe], args.days)
        
        if df is None or df.empty:
            logger.error("Failed to fetch market data. Exiting.")
            sys.exit(1)
    
    # Visualize a single parameter file
    if args.params_file:
        if not os.path.exists(args.params_file):
            logger.error(f"Parameter file not found: {args.params_file}")
            sys.exit(1)
            
        result = apply_strategy_with_parameters(df, args.params_file)
        
        if result:
            # Generate plot file name from parameter file name
            base_name = os.path.splitext(os.path.basename(args.params_file))[0]
            plot_file = f"{base_name}_visualization.png"
            
            # Use the standalone optimizer's plot function
            plot_optimization_results(df, result.get('params', {}), supertrend_strategy, plot_file)
            logger.info(f"Strategy visualization saved to {plot_file}")
    
    # Compare different optimization objectives
    if args.compare:
        # Find parameter files for this symbol and timeframe
        params_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_pattern = f"capital_com_optimized_params_{args.symbol}_{args.timeframe}"
        
        param_files = [
            os.path.join(params_dir, f) 
            for f in os.listdir(params_dir) 
            if f.startswith(file_pattern) and f.endswith('.json')
        ]
        
        if not param_files:
            logger.error(f"No parameter files found for {args.symbol} {args.timeframe}")
            sys.exit(1)
            
        logger.info(f"Found {len(param_files)} parameter files for comparison")
        
        # Generate comparison plot
        comparison_file = f"{args.symbol}_{args.timeframe}_comparison_chart.png"
        plot_strategy_performance_comparison(df, param_files, comparison_file)
        
        # Generate metrics table
        table_file = f"{args.symbol}_{args.timeframe}_comparison_table.png"
        
        # Generate parameter importance plot
        if args.importance_plot:
            importance_file = f"{args.symbol}_{args.timeframe}_parameter_importance.png"
            plot_parameter_importance(params_dir, importance_file)
    
if __name__ == "__main__":
    main()
