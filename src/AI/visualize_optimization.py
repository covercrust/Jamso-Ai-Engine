#!/usr/bin/env python3
"""
Visualize SuperTrend Optimization Results

This script visualizes the optimization results from the standalone_optimizer.py script.
It generates charts showing the price data, SuperTrend indicator, and trade signals.

Usage:
    python visualize_optimization.py [--params-file supertrend_optimized_params_sharpe.json]
"""

import pandas as pd
import numpy as np
import json
import argparse
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Import functionality from standalone optimizer
try:
    from standalone_optimizer import generate_sample_data, supertrend_strategy
except ImportError:
    print("Error: Could not import from standalone_optimizer.py")
    print("Make sure it's in the same directory as this script.")
    exit(1)

def load_parameters(params_file) -> Tuple[Optional[dict], Optional[dict], Optional[str]]:
    """
    Load optimized parameters from JSON file
    
    Parameters:
    - params_file: Path to the JSON file with optimization results
    
    Returns:
    - Tuple containing (best_params, metrics, objective) or (None, None, None) if error occurs
    """
    try:
        with open(params_file, 'r') as f:
            data = json.load(f)
            return data['best_params'], data['metrics'], data['objective']
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading parameters file: {e}")
        return None, None, None

def visualize_strategy(data, params):
    """
    Visualize the SuperTrend strategy with the given parameters
    """
    # Run backtest with the optimized parameters to get trades and signals
    trades_df, equity_curve = supertrend_strategy(data, **params)
    
    # Calculate SuperTrend for visualization
    atr_len = params.get('atr_len', 14)
    fact = params.get('fact', 3.0)
    
    # Calculate ATR
    df = data.copy()
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['close'].shift(1))
    df['tr3'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr'] = df['tr'].rolling(window=atr_len).mean().fillna(df['tr'])
    
    # Calculate SuperTrend
    hl2 = (df['high'] + df['low']) / 2
    df['upperband'] = hl2 + fact * df['atr']
    df['lowerband'] = hl2 - fact * df['atr']
    
    # Initialize SuperTrend values
    df['supertrend'] = 0.0
    df['uptrend'] = True
    
    # First value initialization
    df.loc[0, 'supertrend'] = df.loc[0, 'upperband']
    df.loc[0, 'uptrend'] = False
    
    # Calculate SuperTrend and uptrend status
    for i in range(1, len(df)):
        curr_close = df.loc[i, 'close']
        prev_supertrend = df.loc[i-1, 'supertrend']
        curr_upperband = df.loc[i, 'upperband']
        curr_lowerband = df.loc[i, 'lowerband']
        prev_uptrend = df.loc[i-1, 'uptrend']
        
        # Determine trend
        if prev_supertrend <= curr_upperband and prev_uptrend:
            curr_supertrend = max(curr_lowerband, prev_supertrend)
            curr_uptrend = True
        elif prev_supertrend <= curr_upperband and not prev_uptrend:
            curr_supertrend = curr_lowerband
            curr_uptrend = True if curr_close > prev_supertrend else False
        elif prev_supertrend >= curr_lowerband and prev_uptrend:
            curr_supertrend = curr_upperband
            curr_uptrend = False if curr_close < prev_supertrend else True
        else:  # prev_supertrend >= curr_lowerband and not prev_uptrend
            curr_supertrend = min(curr_upperband, prev_supertrend)
            curr_uptrend = False
            
        # Assign to dataframe
        df.loc[i, 'supertrend'] = curr_supertrend
        df.loc[i, 'uptrend'] = curr_uptrend
    
    # Add signals to dataframe
    df['signal'] = 0
    for i in range(1, len(df)):
        # Buy signal - trend changes from down to up
        if not df.loc[i-1, 'uptrend'] and df.loc[i, 'uptrend']:
            df.loc[i, 'signal'] = 1
        # Sell signal - trend changes from up to down
        elif df.loc[i-1, 'uptrend'] and not df.loc[i, 'uptrend']:
            df.loc[i, 'signal'] = -1
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot price and SuperTrend
    ax1.plot(df['timestamp'], df['close'], label='Price', color='black')
    
    # Plot SuperTrend with appropriate colors
    for i in range(1, len(df)):
        if df.loc[i, 'uptrend']:
            ax1.plot([df.loc[i-1, 'timestamp'], df.loc[i, 'timestamp']], 
                     [df.loc[i-1, 'supertrend'], df.loc[i, 'supertrend']], 
                     color='green', linewidth=1.5)
        else:
            ax1.plot([df.loc[i-1, 'timestamp'], df.loc[i, 'timestamp']], 
                     [df.loc[i-1, 'supertrend'], df.loc[i, 'supertrend']], 
                     color='red', linewidth=1.5)
    
    # Plot buy and sell signals
    if not trades_df.empty:
        buy_signals = trades_df[trades_df['action'] == 'BUY']
        if not buy_signals.empty:
            ax1.scatter(buy_signals['timestamp'], buy_signals['price'], 
                        marker='^', color='green', s=100, label='Buy Signal')
        
        sell_signals = trades_df[trades_df['action'] == 'SELL']
        if not sell_signals.empty:
            ax1.scatter(sell_signals['timestamp'], sell_signals['price'], 
                        marker='v', color='red', s=100, label='Sell Signal')
        
        # Plot take profit and stop loss signals
        tp_long = trades_df[trades_df['action'] == 'TAKE_PROFIT_LONG']
        if not tp_long.empty:
            ax1.scatter(tp_long['timestamp'], tp_long['price'], 
                        marker='*', color='cyan', s=100, label='TP Long')
        
        sl_long = trades_df[trades_df['action'] == 'STOP_LOSS_LONG']
        if not sl_long.empty:
            ax1.scatter(sl_long['timestamp'], sl_long['price'], 
                        marker='x', color='magenta', s=100, label='SL Long')
        
        tp_short = trades_df[trades_df['action'] == 'TAKE_PROFIT_SHORT']
        if not tp_short.empty:
            ax1.scatter(tp_short['timestamp'], tp_short['price'], 
                        marker='*', color='blue', s=100, label='TP Short')
        
        sl_short = trades_df[trades_df['action'] == 'STOP_LOSS_SHORT']
        if not sl_short.empty:
            ax1.scatter(sl_short['timestamp'], sl_short['price'], 
                        marker='x', color='yellow', s=100, label='SL Short')
    
    # Set title and labels
    params_str = ', '.join([f"{k}={v}" for k, v in params.items() 
                           if k in ('atr_len', 'fact', 'risk_percent', 'sl_percent', 'tp_percent')])
    ax1.set_title(f'SuperTrend Strategy with {params_str}', fontsize=14)
    ax1.set_ylabel('Price')
    ax1.grid(True)
    ax1.legend(loc='upper left')
    
    # Format dates on x-axis
    date_format = DateFormatter("%Y-%m-%d")
    ax1.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()
    
    # Plot equity curve
    ax2.plot(equity_curve.index, equity_curve, color='blue', label='Equity Curve')
    ax2.set_title('Equity Curve', fontsize=12)
    ax2.set_ylabel('Equity')
    ax2.grid(True)
    ax2.legend(loc='upper left')
    
    # Add metrics text
    metrics_text = []
    if trades_df is not None:
        metrics_text.append(f"Total Return: {(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1):.2%}")
        metrics_text.append(f"Number of Trades: {len(trades_df)}")
        
        if 'pnl' in trades_df.columns:
            win_rate = (trades_df['pnl'] > 0).mean() if len(trades_df) > 0 else 0
            metrics_text.append(f"Win Rate: {win_rate:.2%}")
    
    if metrics_text:
        ax1.text(0.01, 0.01, '\n'.join(metrics_text), transform=ax1.transAxes, 
                 fontsize=10, verticalalignment='bottom', 
                 bbox={'facecolor': 'white', 'alpha': 0.6, 'pad': 10})
    
    plt.tight_layout()
    return fig

def visualize_parameter_comparison(params_files) -> tuple:
    """
    Compare results from different optimization objectives
    
    Parameters:
    - params_files: List of parameter files to compare
    
    Returns:
    - Tuple of (comparison chart figure, parameter table figure)
      Both elements can be None if no valid parameters are found
    """
    results = []
    
    for params_file in params_files:
        try:
            with open(params_file, 'r') as f:
                data = json.load(f)
                objective = data['objective']
                params = {k: v for k, v in data['best_params'].items() 
                        if k in ('atr_len', 'fact', 'risk_percent', 'sl_percent', 'tp_percent')}
                metrics = data['metrics']
                results.append({
                    'objective': objective,
                    'params': params,
                    'metrics': metrics
                })
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading parameters file {params_file}: {e}")
    
    if not results:
        print("No valid parameter files found")
        return None, None
    
    # Create a comparison chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    
    # Prepare data for charts
    objectives = [r['objective'] for r in results]
    returns = [r['metrics'].get('total_return', 0) * 100 for r in results]
    sharpes = [r['metrics'].get('sharpe_ratio', 0) for r in results]
    win_rates = [r['metrics'].get('win_rate', 0) * 100 for r in results]
    drawdowns = [abs(r['metrics'].get('max_drawdown', 0)) * 100 for r in results]
    
    # Returns and drawdowns
    x = range(len(objectives))
    width = 0.35
    ax1.bar([i - width/2 for i in x], returns, width, label='Return (%)', color='green')
    ax1.bar([i + width/2 for i in x], drawdowns, width, label='Max Drawdown (%)', color='red')
    ax1.set_ylabel('Percentage')
    ax1.set_title('Returns vs Drawdowns by Objective')
    ax1.set_xticks(x)
    ax1.set_xticklabels(objectives)
    ax1.legend()
    
    # Sharpe and win rate
    ax2.bar([i - width/2 for i in x], sharpes, width, label='Sharpe Ratio', color='blue')
    ax2.bar([i + width/2 for i in x], win_rates, width, label='Win Rate (%)', color='orange')
    ax2.set_ylabel('Value')
    ax2.set_title('Sharpe Ratio and Win Rate by Objective')
    ax2.set_xticks(x)
    ax2.set_xticklabels(objectives)
    ax2.legend()
    
    plt.tight_layout()
    
    # Create table with parameter values
    param_keys = sorted(list(set(key for r in results for key in r['params'].keys())))
    param_table = []
    for r in results:
        row = [r['objective']] + [str(r['params'].get(key, '-')) for key in param_keys]
        param_table.append(row)
    
    header = ['Objective'] + param_keys
    
    # Plot parameter table
    fig_table = plt.figure(figsize=(10, len(results) + 1))
    ax_table = fig_table.add_subplot(111)
    ax_table.axis('tight')
    ax_table.axis('off')
    table = ax_table.table(cellText=param_table, colLabels=header, 
                           loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 1.5)
    ax_table.set_title("Parameter Values by Optimization Objective", fontsize=14)
    
    return fig, fig_table

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Visualize SuperTrend Optimization Results')
    parser.add_argument('--params-file', type=str, default='supertrend_optimized_params_sharpe.json',
                      help='JSON file with optimized parameters')
    parser.add_argument('--compare', action='store_true',
                      help='Compare results from different optimization objectives')
    parser.add_argument('--days', type=int, default=100,
                      help='Number of days of data to generate')
    parser.add_argument('--trends', type=int, default=3,
                      help='Number of trend cycles to generate')
    parser.add_argument('--volatility', type=float, default=0.02,
                      help='Daily volatility for synthetic data')
    parser.add_argument('--output', type=str, default='optimization_results.png',
                      help='Output filename for the chart')
    args = parser.parse_args()
    
    print(f"Visualizing SuperTrend Strategy Optimization Results")
    print(f"=============================================")
    
    if args.compare:
        # Look for optimization results files
        import glob
        params_files = glob.glob('supertrend_optimized_params_*.json')
        
        if params_files:
            print(f"Found {len(params_files)} parameter files for comparison")
            for f in params_files:
                print(f"  - {f}")
                
            fig, fig_table = visualize_parameter_comparison(params_files)
            # Check if fig is not None and is a valid matplotlib Figure
            if fig is not None and hasattr(fig, 'savefig'):
                fig.savefig(f"comparison_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                print(f"Saved comparison chart to comparison_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            # Check if fig_table is not None and is a valid matplotlib Figure
            if fig_table is not None and hasattr(fig_table, 'savefig'):
                fig_table.savefig(f"comparison_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                print(f"Saved comparison table to comparison_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        else:
            print("No parameter files found for comparison. Run standalone_optimizer.py first.")
            return
    else:
        # Load optimized parameters
        best_params, metrics, objective = load_parameters(args.params_file)
        if not best_params:
            print(f"Could not load parameters from {args.params_file}")
            return
        
        print(f"Loaded parameters optimized for {objective}")
        for k, v in best_params.items():
            if k in ('atr_len', 'fact', 'risk_percent', 'sl_percent', 'tp_percent'):
                print(f"  {k}: {v}")
        
        # Generate sample data
        data = generate_sample_data(
            days=args.days,
            trend_cycles=args.trends,
            volatility=args.volatility
        )
        
        # Visualize strategy with optimized parameters
        print("Generating visualization...")
        fig = visualize_strategy(data, best_params)
        
        # Save chart
        output_filename = f"strategy_visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_filename)
        print(f"Saved visualization to {output_filename}")

if __name__ == "__main__":
    main()
