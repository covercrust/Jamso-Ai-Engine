#!/usr/bin/env python3
"""
Essential SuperTrend strategy and optimization functions

This module provides standalone implementations of the SuperTrend strategy
and optimization functions that don't rely on other project dependencies.

This is a self-contained implementation that can be used when the main API
integration fails due to dependency issues.
"""

# Import dotenv for loading environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file if it exists
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables may not be loaded properly.")

import pandas as pd
import numpy as np
import time
import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

# Try to import hyperopt, if it's not available we'll provide a simpler optimizer
try:
    from hyperopt import fmin, tpe, hp, Trials, STATUS_OK
    HYPEROPT_AVAILABLE = True
except ImportError:
    HYPEROPT_AVAILABLE = False
    print("Hyperopt not available. Using simple grid search instead.")

# Configure logging
logger = logging.getLogger(__name__)

# Define optimization objectives
OBJECTIVES = {
    'sharpe': lambda metrics: metrics.get('sharpe_ratio', 0),
    'return': lambda metrics: metrics.get('total_return', 0),
    'calmar': lambda metrics: metrics.get('total_return', 0) / abs(metrics.get('max_drawdown', 1)),
    'win_rate': lambda metrics: metrics.get('win_rate', 0),
    'risk_adjusted': lambda metrics: metrics.get('total_return', 0) / (abs(metrics.get('max_drawdown', 1)) + 0.01),
}

# Define environment variable helper functions
def get_env_var(name, default=None):
    """Get environment variable with fallback to default value"""
    return os.environ.get(name, default)

def create_env_file_if_missing():
    """Create a .env file if it doesn't exist"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if not os.path.exists(env_path):
        try:
            with open(env_path, 'w') as f:
                f.write("""# Capital.com API Credentials
CAPITAL_API_KEY=
CAPITAL_API_LOGIN=
CAPITAL_API_PASSWORD=

# You need to fill in these values with your actual Capital.com API credentials
# For security, do not commit this file to version control
# This file should be included in your .gitignore
""")
            print(f"Created .env file at {env_path}")
            print("Please edit this file to add your Capital.com API credentials")
        except Exception as e:
            print(f"Error creating .env file: {e}")

# Call function to ensure .env file exists
create_env_file_if_missing()

def generate_sample_data(days=252, volatility=0.015, start_price=100.0, trend_cycles=3):
    """
    Generate synthetic price data for testing with trending behaviors.
    
    Parameters:
    - days: Number of trading days
    - volatility: Daily volatility
    - start_price: Initial price
    - trend_cycles: Number of bullish/bearish cycles to generate
    """
    # Generate dates
    start = datetime.now() - timedelta(days=days)
    dates = pd.date_range(start=start, periods=days, freq='B')
    
    # Create trend components - sine wave with multiple cycles
    cycle_period = days / trend_cycles
    trend = np.sin(np.linspace(0, trend_cycles * 2 * np.pi, days)) * 0.2
    
    # Add random walk component
    random_walk = np.random.normal(0, volatility, days).cumsum() * 0.3
    
    # Create price series with trend and random component
    price_changes = trend + random_walk
    prices = start_price * np.exp(price_changes)
    
    # Create OHLCV data
    df = pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'open': prices * (1 + np.random.normal(0, volatility/3, days)),
        'volume': np.random.lognormal(10, 1, days)
    })
    
    # Generate high/low based on open/close with intraday volatility
    daily_range = prices * volatility * np.random.uniform(0.5, 2.0, days)
    df['high'] = np.maximum(df['open'], df['close']) + daily_range / 2
    df['low'] = np.minimum(df['open'], df['close']) - daily_range / 2
    
    # Calculate ATR (Average True Range)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['close'].shift(1))
    df['tr3'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr'] = df['tr'].rolling(window=14).mean().fillna(df['tr'])
    
    # Clean up temporary columns
    df = df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1)
    
    print(f"Generated {len(df)} days of synthetic data with {trend_cycles} trend cycles")
    return df

def supertrend_strategy(df, atr_len=10, fact=3.0, risk_percent=1.0, sl_percent=0.5, 
                       tp_percent=1.5, initial_capital=10000, direction_bias="Both"):
    """SuperTrend trading strategy implementation."""
    df = df.copy()
    equity = initial_capital
    position = 0
    entry_price = 0
    trades = []
    equity_curve = [initial_capital]  # Start with initial capital
    
    # Calculate ATR if not already calculated or recalculate with specific length
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
    
    # Add signals to dataframe - signal is 1 for buy, -1 for sell, 0 for no action
    df['signal'] = 0
    
    # Generate signals at trend change
    for i in range(1, len(df)):
        # Buy signal - trend changes from down to up
        if not df.loc[i-1, 'uptrend'] and df.loc[i, 'uptrend']:
            df.loc[i, 'signal'] = 1
        # Sell signal - trend changes from up to down
        elif df.loc[i-1, 'uptrend'] and not df.loc[i, 'uptrend']:
            df.loc[i, 'signal'] = -1
    
    # Trading logic
    for i in range(1, len(df)):
        # Get signal from our indicator
        signal = df.loc[i, 'signal']
        price = df.loc[i, 'close']
        timestamp = df.loc[i, 'timestamp']
        
        # Check if we have a new signal
        if signal != 0:
            # Apply direction bias if specified
            if direction_bias != "Both":
                if (direction_bias == "Long" and signal < 0) or (direction_bias == "Short" and signal > 0):
                    continue
            
            # If we have an existing position, close it
            if position != 0:
                # Calculate position value
                position_value = abs(entry_price - price) / entry_price * position_size
                
                # Determine if profit or loss
                if (position > 0 and price > entry_price) or (position < 0 and price < entry_price):
                    profit = position_value
                else:
                    profit = -position_value
                
                # Update equity
                equity += profit
                
                # Record the trade
                trades.append({
                    'entry_time': entry_timestamp,
                    'exit_time': timestamp,
                    'entry_price': entry_price,
                    'exit_price': price,
                    'direction': 'long' if position > 0 else 'short',
                    'profit': profit,
                    'profit_pct': profit / position_size * 100,
                    'position_size': position_size
                })
                
                # Reset position
                position = 0
                entry_price = 0
                
            # Enter new position based on signal
            if signal != 0:
                # Calculate position size based on risk percentage
                position_size = equity * risk_percent / 100
                entry_price = price
                entry_timestamp = timestamp
                position = 1 if signal > 0 else -1
        
        # Update equity curve whether we have a trade or not
        equity_curve.append(equity)
    
    # Close any open position at the end
    if position != 0:
        # Calculate position value
        last_price = df.iloc[-1]['close']
        position_value = abs(entry_price - last_price) / entry_price * position_size
        
        # Determine if profit or loss
        if (position > 0 and last_price > entry_price) or (position < 0 and last_price < entry_price):
            profit = position_value
        else:
            profit = -position_value
        
        # Update equity
        equity += profit
        
        # Record the trade
        trades.append({
            'entry_time': entry_timestamp,
            'exit_time': df.iloc[-1]['timestamp'],
            'entry_price': entry_price,
            'exit_price': last_price,
            'direction': 'long' if position > 0 else 'short',
            'profit': profit,
            'profit_pct': profit / position_size * 100,
            'position_size': position_size
        })
        
        # Update the last value in equity curve
        equity_curve[-1] = equity
    
    return {
        'trades': trades,
        'equity_curve': equity_curve,
        'final_equity': equity,
        'params': {
            'atr_len': atr_len,
            'fact': fact,
            'risk_percent': risk_percent,
            'sl_percent': sl_percent,
            'tp_percent': tp_percent
        }
    }

def calculate_metrics(result):
    """Calculate performance metrics for the trading strategy."""
    trades = result.get('trades', [])
    equity_curve = result.get('equity_curve', [])
    initial_capital = equity_curve[0]
    final_equity = equity_curve[-1]
    
    # Calculate returns
    returns = np.diff(equity_curve) / np.array(equity_curve[:-1])
    
    # Basic metrics
    total_return = (final_equity - initial_capital) / initial_capital * 100
    
    # Handle case with no trades
    if not trades:
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'expectancy': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_winner': 0,
            'avg_loser': 0,
            'largest_winner': 0,
            'largest_loser': 0
        }
    
    # Calculate profits/losses for metrics
    profits = [trade['profit'] for trade in trades if trade['profit'] > 0]
    losses = [abs(trade['profit']) for trade in trades if trade['profit'] <= 0]
    
    # Win rate
    total_trades = len(trades)
    winning_trades = len(profits)
    losing_trades = len(losses)
    win_rate = winning_trades / total_trades * 100 if total_trades else 0
    
    # Profit factor
    gross_profits = sum(profits) if profits else 0
    gross_losses = sum(losses) if losses else 0
    profit_factor = gross_profits / gross_losses if gross_losses else float('inf')
    
    # Averages
    avg_winner = np.mean(profits) if profits else 0
    avg_loser = np.mean(losses) if losses else 0
    
    # Largest trades
    largest_winner = max(profits) if profits else 0
    largest_loser = max(losses) if losses else 0
    
    # Expectancy
    expectancy = win_rate / 100 * avg_winner - (1 - win_rate / 100) * avg_loser
    
    # Calculate maximum drawdown
    peak = initial_capital
    max_dd = 0
    
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        max_dd = max(max_dd, dd)
    
    # Calculate Sharpe ratio
    # Assuming risk-free rate of 0 and annualizing by multiplying by sqrt(252)
    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'expectancy': expectancy,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'largest_winner': largest_winner,
        'largest_loser': largest_loser
    }

def optimize_parameters(df, strategy_func, search_space, objective_name='sharpe', num_evals=50):
    """
    Optimize strategy parameters using either hyperopt or grid search.
    
    Parameters:
    - df: DataFrame with price data
    - strategy_func: Strategy function to optimize
    - search_space: Dictionary with parameter ranges, e.g., {'atr_len': (5, 20)}
    - objective_name: Name of the objective function to maximize ('sharpe', 'return', etc.)
    - num_evals: Number of parameter combinations to evaluate
    
    Returns:
    - Tuple of (best parameters, best objective value, all results)
    """
    objective_func = OBJECTIVES.get(objective_name, OBJECTIVES['sharpe'])
    results = []
    
    if HYPEROPT_AVAILABLE:
        # Create hyperopt search space
        hspace = {}
        for param, value_range in search_space.items():
            if isinstance(value_range, tuple) and len(value_range) == 2:
                # For numeric ranges, create uniform distribution
                if isinstance(value_range[0], int) and isinstance(value_range[1], int):
                    hspace[param] = hp.quniform(param, value_range[0], value_range[1], 1)
                else:
                    hspace[param] = hp.uniform(param, value_range[0], value_range[1])
            elif isinstance(value_range, list):
                # For discrete values, create choice
                hspace[param] = hp.choice(param, value_range)
        
        # Define the objective function to minimize
        def objective(params):
            # Convert int parameters from float (hyperopt returns float values)
            for k, v in params.items():
                if k in ['atr_len'] and isinstance(v, float):
                    params[k] = int(v)
            
            # Run strategy with these parameters
            result = strategy_func(df, **params)
            metrics = calculate_metrics(result)
            
            # Calculate objective value
            obj_value = objective_func(metrics)
            
            # Save all results for later analysis
            results.append({
                'params': params.copy(),
                'metrics': metrics,
                'objective': obj_value
            })
            
            # Hyperopt minimizes, so negate for maximization objectives
            return {'loss': -obj_value, 'status': STATUS_OK}
        
        # Run optimization
        trials = Trials()
        best = fmin(
            fn=objective,
            space=hspace,
            algo=tpe.suggest,
            max_evals=num_evals,
            trials=trials
        )
        
        # Convert best parameters back to proper types
        best_params = {}
        for k, v in best.items():
            if k in ['atr_len']:
                best_params[k] = int(v)
            else:
                best_params[k] = v
        
        # Find best objective value
        best_idx = np.argmin([t['result']['loss'] for t in trials.trials])
        best_value = -trials.trials[best_idx]['result']['loss']
        
    else:
        # Simple grid search if hyperopt is not available
        # Generate parameter combinations
        param_grid = []
        for param, value_range in search_space.items():
            if isinstance(value_range, tuple) and len(value_range) == 2:
                if isinstance(value_range[0], int) and isinstance(value_range[1], int):
                    # For integer parameters
                    values = np.linspace(value_range[0], value_range[1], min(10, num_evals), dtype=int)
                else:
                    # For float parameters
                    values = np.linspace(value_range[0], value_range[1], min(10, num_evals))
                param_grid.append((param, values))
            elif isinstance(value_range, list):
                # For discrete values
                param_grid.append((param, value_range))
        
        # Generate all combinations
        import itertools
        param_names = [p[0] for p in param_grid]
        param_values = [p[1] for p in param_grid]
        combinations = list(itertools.product(*param_values))
        
        # Limit to num_evals
        if len(combinations) > num_evals:
            combinations = np.random.choice(combinations, num_evals, replace=False)
        
        # Evaluate each combination
        best_value = float('-inf')
        best_params = None
        
        for combo in combinations:
            params = dict(zip(param_names, combo))
            
            # Convert int parameters
            for k, v in params.items():
                if k in ['atr_len'] and isinstance(v, float):
                    params[k] = int(v)
            
            # Run strategy
            result = strategy_func(df, **params)
            metrics = calculate_metrics(result)
            obj_value = objective_func(metrics)
            
            # Save result
            results.append({
                'params': params.copy(),
                'metrics': metrics,
                'objective': obj_value
            })
            
            # Update best if better
            if obj_value > best_value:
                best_value = obj_value
                best_params = params.copy()
    
    return best_params, best_value, results

def plot_optimization_results(df, best_params, strategy_func, output_file=None):
    """
    Plot optimization results including price chart, SuperTrend, and equity curve.
    
    Parameters:
    - df: DataFrame with price data
    - best_params: Best parameters found by optimization
    - strategy_func: Strategy function to run with best parameters
    - output_file: Path to save the plot (None for display)
    
    Returns:
    - None (displays or saves plot)
    """
    # Run strategy with best parameters
    result = strategy_func(df, **best_params)
    trades = result.get('trades', [])
    equity_curve = result.get('equity_curve', [])
    metrics = calculate_metrics(result)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(14, 10))
    gs = plt.GridSpec(3, 1, height_ratios=[2, 1, 1])
    
    # Price chart with SuperTrend
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(df['timestamp'], df['close'], label='Close Price', color='black', alpha=0.5)
    ax1.plot(df['timestamp'], df['supertrend'], label='SuperTrend', color='blue', linewidth=1)
    
    # Add buy/sell markers based on trades
    for trade in trades:
        if trade['direction'] == 'long':
            ax1.scatter(trade['entry_time'], trade['entry_price'], marker='^', color='green', s=100)
            ax1.scatter(trade['exit_time'], trade['exit_price'], marker='v', color='red', s=100)
        else:
            ax1.scatter(trade['entry_time'], trade['entry_price'], marker='v', color='red', s=100)
            ax1.scatter(trade['exit_time'], trade['exit_price'], marker='^', color='green', s=100)
    
    ax1.set_title('Price Chart with SuperTrend')
    ax1.set_ylabel('Price')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Equity curve
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(df['timestamp'][:len(equity_curve)], equity_curve, label='Equity Curve', color='green')
    ax2.set_title('Equity Curve')
    ax2.set_ylabel('Equity')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add metrics as text
    ax3 = fig.add_subplot(gs[2])
    ax3.axis('off')
    
    params_text = f"Params: ATR={best_params.get('atr_len', 'N/A')}, Factor={best_params.get('fact', 'N/A'):.2f}, Risk={best_params.get('risk_percent', 'N/A'):.2f}%"
    metrics_text = (
        f"Return: {metrics['total_return']:.2f}% | Sharpe: {metrics['sharpe_ratio']:.2f} | "
        f"Max DD: {metrics['max_drawdown']:.2f}% | Win Rate: {metrics['win_rate']:.2f}% | "
        f"Trades: {metrics['total_trades']} | Profit Factor: {metrics['profit_factor']:.2f}"
    )
    
    ax3.text(0.5, 0.6, params_text, ha='center', fontsize=12)
    ax3.text(0.5, 0.3, metrics_text, ha='center', fontsize=12)
    
    plt.tight_layout()
    
    # Save or display the plot
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    else:
        plt.show()
