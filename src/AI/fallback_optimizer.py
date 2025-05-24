#!/usr/bin/env python3
"""
Fallback SuperTrend Strategy and Optimization Implementation

This module provides a complete fallback implementation for the SuperTrend strategy
and optimization functions with minimal dependencies.

This file is used when the standard optimization functions fail due to dependency issues.
"""

import pandas as pd
import numpy as np
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
import random
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type annotation helpers for static analysis
def safe_float(val) -> float:
    """Convert value to float safely for static type checking"""
    try:
        if isinstance(val, (int, float)):
            return float(val)
        elif hasattr(val, 'item'):
            # For numpy/pandas values
            return float(val.item())
        else:
            return float(val)
    except (ValueError, TypeError):
        return 0.0  # Return a safe default

# Try to import dotenv for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables may not be loaded properly.")

# Standard optimization objectives
OBJECTIVES: Dict[str, Callable[[Dict[str, float]], float]] = {
    'sharpe': lambda metrics: metrics.get('sharpe_ratio', 0),
    'return': lambda metrics: metrics.get('total_return', 0),
    'calmar': lambda metrics: metrics.get('total_return', 0) / abs(metrics.get('max_drawdown', 1) + 0.0001),
    'win_rate': lambda metrics: metrics.get('win_rate', 0),
    'risk_adjusted': lambda metrics: metrics.get('total_return', 0) / (abs(metrics.get('max_drawdown', 1)) + 0.01),
}

def supertrend_strategy(df: pd.DataFrame, params: Dict[str, Union[int, float]]) -> pd.DataFrame:
    """
    Implement the SuperTrend strategy.
    
    Parameters:
    - df: DataFrame with OHLC data
    - params: Dictionary with strategy parameters
    
    Returns:
    - DataFrame with strategy signals
    """
    # Extract parameters with defaults
    atr_period = int(params.get('atr_period', 14))
    atr_multiplier = params.get('atr_multiplier', 3.0)
    
    # Check that the dataframe has the required columns
    required_columns = ['open', 'high', 'low', 'close']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    df = df.copy()
    
    # Calculate ATR (Average True Range)
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift()),
            abs(df['low'] - df['close'].shift())
        )
    )
    df['atr'] = df['tr'].rolling(atr_period).mean()
    
    # Calculate basic bands
    df['basic_upper'] = (df['high'] + df['low']) / 2 + atr_multiplier * df['atr']
    df['basic_lower'] = (df['high'] + df['low']) / 2 - atr_multiplier * df['atr']
    
    # Initialize SuperTrend columns
    df['trend'] = 0
    df['supertrend'] = 0
    
    # Calculate SuperTrend - using a more type-safe approach
    for i in range(1, len(df)):
        idx = df.index[i]
        prev_idx = df.index[i-1]
        
        # Default values
        curr_trend = df.at[prev_idx, 'trend']
        curr_upper = df.at[idx, 'basic_upper']
        curr_lower = df.at[idx, 'basic_lower']
        
        # Previous SuperTrend values
        prev_upper = df.at[prev_idx, 'basic_upper']
        prev_lower = df.at[prev_idx, 'basic_lower']
        prev_close = df.at[prev_idx, 'close']
        prev_st = df.at[prev_idx, 'supertrend']
        
        # Current price
        curr_close = df.at[idx, 'close']
        
        # Adjust upper band
        if (prev_upper > prev_st) and (prev_close > prev_upper):
            curr_upper = max(curr_upper, prev_upper)
            
        # Adjust lower band
        if (prev_lower < prev_st) and (prev_close < prev_lower):
            curr_lower = min(curr_lower, prev_lower)
            
        # Update trend direction
        if curr_close > prev_upper:
            curr_trend = 1  # Uptrend
        elif curr_close < prev_lower:
            curr_trend = -1  # Downtrend
        else:
            curr_trend = df.at[prev_idx, 'trend']  # Continue previous trend
            
        # Set SuperTrend value based on trend
        if curr_trend == 1:
            curr_st = curr_lower
        else:
            curr_st = curr_upper
            
        # Update DataFrame - using at instead of loc for better type safety
        df.at[idx, 'trend'] = curr_trend
        df.at[idx, 'supertrend'] = curr_st
    
    # Generate signals
    df['signal'] = 0
    
    # Signal is generated when trend changes
    df.loc[df['trend'] != df['trend'].shift(), 'signal'] = df['trend']
    
    # First row signal
    df.loc[df.index[0], 'signal'] = 0
    
    return df


def backtest_strategy(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Backtest the strategy with given parameters.
    
    Parameters:
    - df: DataFrame with price data
    - params: Strategy parameters
    
    Returns:
    - trades_df: DataFrame with trade details
    - equity_curve: Series with equity curve values
    """
    # Apply strategy
    df = supertrend_strategy(df, params)
    
    # Extract parameters with defaults
    stop_loss_pct: float = params.get('stop_loss', 2.0)  # Default 2% stop loss
    take_profit_pct: float = params.get('take_profit', 4.0)  # Default 4% take profit
    position_size: float = params.get('position_size', 1.0)  # Default position size
    
    # Initialize tracking variables
    position = 0
    entry_price = 0
    stop_loss = 0
    take_profit = 0
    equity = 100  # Start with $100
    equity_curve: List[float] = [100.0]  # Type-annotated to ensure it's a list of floats
    trades: List[Dict[str, Any]] = []  # Type-annotated to ensure it's a list of dictionaries
    
    # Simulate trading
    for i in range(1, len(df)):
        # Check for new signals first
        if df.loc[df.index[i], 'signal'] == 1 and position <= 0:
            # Close any short position
            if position < 0:
                # Convert to float to avoid type issues
                close_price = safe_float(df.loc[df.index[i], 'close'])  # type: ignore
                pnl = (safe_float(entry_price) - close_price) * abs(position)
                equity += pnl
                trades.append({
                    'timestamp': df.index[i],
                    'action': 'CLOSE_SHORT',
                    'price': df.loc[df.index[i], 'close'],
                    'pnl': pnl,
                    'size': abs(position)
                })
            
            # Open long position
            position = position_size
            entry_price = df.loc[df.index[i], 'close']
            # Convert to float to avoid type issues
            entry_price_float = safe_float(entry_price)  # type: ignore
            stop_loss = entry_price_float * (1 - stop_loss_pct/100)
            take_profit = entry_price_float * (1 + take_profit_pct/100)
            
            trades.append({
                'timestamp': df.index[i],
                'action': 'BUY',
                'price': entry_price,
                'size': position,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
            
        elif df.loc[df.index[i], 'signal'] == -1 and position >= 0:
            # Close any long position
            if position > 0:
                # Convert to float to avoid type issues
                close_price = safe_float(df.loc[df.index[i], 'close'])  # type: ignore
                pnl = (close_price - safe_float(entry_price)) * position  # type: ignore
                equity += pnl
                trades.append({
                    'timestamp': df.index[i],
                    'action': 'CLOSE_LONG',
                    'price': df.loc[df.index[i], 'close'],
                    'pnl': pnl,
                    'size': position
                })
            
            # Open short position
            position = -position_size
            entry_price = df.loc[df.index[i], 'close']
            # Convert to float to avoid type issues
            entry_price_float = safe_float(entry_price)  # type: ignore
            stop_loss = entry_price_float * (1 + stop_loss_pct/100)
            take_profit = entry_price_float * (1 - take_profit_pct/100)
            
            trades.append({
                'timestamp': df.index[i],
                'action': 'SELL',
                'price': entry_price,
                'size': abs(position),
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
        
        # Check for stop loss and take profit on existing positions
        elif position > 0:  # Long position
            if safe_float(df.loc[df.index[i], 'low']) <= safe_float(stop_loss):  # Stop loss hit  # type: ignore
                pnl = (safe_float(stop_loss) - safe_float(entry_price)) * position  # type: ignore
                equity += pnl
                trades.append({
                    'timestamp': df.index[i],
                    'action': 'STOP_LOSS_LONG',
                    'price': stop_loss,
                    'pnl': pnl,
                    'size': position
                })
                position = 0
                
            elif safe_float(df.loc[df.index[i], 'high']) >= safe_float(take_profit):  # Take profit hit  # type: ignore
                pnl = (safe_float(take_profit) - safe_float(entry_price)) * position  # type: ignore
                equity += pnl
                trades.append({
                    'timestamp': df.index[i],
                    'action': 'TAKE_PROFIT_LONG',
                    'price': take_profit,
                    'pnl': pnl,
                    'size': position
                })
                position = 0
                
        elif position < 0:  # Short position
            if safe_float(df.loc[df.index[i], 'high']) >= safe_float(stop_loss):  # Stop loss hit  # type: ignore
                pnl = (safe_float(entry_price) - safe_float(stop_loss)) * abs(position)  # type: ignore
                equity += pnl
                trades.append({
                    'timestamp': df.index[i],
                    'action': 'STOP_LOSS_SHORT',
                    'price': stop_loss,
                    'pnl': pnl,
                    'size': abs(position)
                })
                position = 0
                
            elif safe_float(df.loc[df.index[i], 'low']) <= safe_float(take_profit):  # Take profit hit  # type: ignore
                pnl = (safe_float(entry_price) - safe_float(take_profit)) * abs(position)  # type: ignore
                equity += pnl
                trades.append({
                    'timestamp': df.index[i],
                    'action': 'TAKE_PROFIT_SHORT',
                    'price': take_profit,
                    'pnl': pnl,
                    'size': abs(position)
                })
                position = 0
        
        # Update equity curve
        # Ensure equity is a number type
        # Convert to float and add to equity curve
        equity_curve.append(float(safe_float(equity)))
    
    # Close any remaining position at the end
    if position != 0:
        final_price = df['close'].iloc[-1]
        if position > 0:  # Long position
            pnl = (final_price - entry_price) * position
            equity += pnl
            trades.append({
                'timestamp': df.index[-1],
                'action': 'CLOSE_FINAL_LONG',
                'price': final_price,
                'pnl': pnl,
                'size': position
            })
        else:  # Short position
            pnl = (entry_price - final_price) * abs(position)
            equity += pnl
            trades.append({
                'timestamp': df.index[-1],
                'action': 'CLOSE_FINAL_SHORT',
                'price': final_price,
                'pnl': pnl,
                'size': abs(position)
            })
    
    # Convert to DataFrame/Series
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    equity_curve = pd.Series(equity_curve, index=df.index)
    
    return trades_df, equity_curve

def calculate_metrics(equity_curve: pd.Series, trades: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate performance metrics for a backtest.
    
    Parameters:
    - equity_curve: Series with equity values
    - trades: DataFrame with trade details
    
    Returns:
    - Dict with performance metrics
    """
    metrics = {}
    
    # Handle empty trades
    if trades.empty or len(equity_curve) < 2:
        return {
            'total_return': 0,
            'annualized_return': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'num_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_trade': 0,
            'avg_winner': 0,
            'avg_loser': 0
        }
    
    # Basic return metrics
    start_equity = equity_curve.iloc[0]
    end_equity = equity_curve.iloc[-1]
    total_return_pct = (end_equity / start_equity - 1) * 100
    
    # Calculate drawdown
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve / rolling_max - 1) * 100
    max_drawdown = abs(drawdown.min())
    
    # Annualized metrics
    try:
        # Check if index is datetime-like and handle accordingly
        try:
            # Use type ignore to handle the static analysis issue
            days = (equity_curve.index[-1] - equity_curve.index[0]).days  # type: ignore
        except (AttributeError, TypeError):
            # If index is not datetime, use length and assume daily data
            days = len(equity_curve) - 1
        if days <= 0:
            days = 1  # Ensure at least one day for backtest period
    except AttributeError:
        # If index is not datetime, use length and assume daily data
        days = len(equity_curve) - 1
        if days <= 0:
            days = 1  # Ensure at least one day
            
    years = days / 365
    if years > 0 and total_return_pct > -100:  # Ensure we don't have negative total returns below -100%
        try:
            annualized_return = ((1 + total_return_pct/100) ** (1/years) - 1) * 100
        except (ValueError, RuntimeWarning):
            # Handle cases where the calculation fails (e.g., negative returns)
            annualized_return = total_return_pct / years  # Simple approximation
    else:
        annualized_return = total_return_pct  # If less than a day, use total return
    
    # Risk metrics
    daily_returns = equity_curve.pct_change().dropna()
    sharpe_ratio = 0
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252)
    
    # Trade metrics
    num_trades = len(trades)
    if 'pnl' in trades.columns and num_trades > 0:
        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] < 0]
        
        win_rate = len(winning_trades) / num_trades if num_trades > 0 else 0
        
        # Calculate profit factor
        gross_profit = winning_trades['pnl'].sum() if not winning_trades.empty else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0 if gross_profit == 0 else float('inf')
        
        # Average trade metrics
        avg_trade = trades['pnl'].mean() if num_trades > 0 else 0
        avg_winner = winning_trades['pnl'].mean() if not winning_trades.empty else 0
        avg_loser = losing_trades['pnl'].mean() if not losing_trades.empty else 0
    else:
        win_rate = 0
        profit_factor = 0
        avg_trade = 0
        avg_winner = 0
        avg_loser = 0
    
    # Compile metrics
    metrics = {
        'total_return': total_return_pct,
        'annualized_return': annualized_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_trade': avg_trade,
        'avg_winner': avg_winner,
        'avg_loser': avg_loser
    }
    
    return metrics

def generate_param_set(search_space: Dict[str, List[Any]]) -> Dict[str, Any]:
    """
    Generate a random parameter set from the search space.
    
    Parameters:
    - search_space: Dictionary with parameter ranges
    
    Returns:
    - Dictionary with parameter values
    """
    params = {}
    for param_name, param_range in search_space.items():
        if isinstance(param_range, list):
            if all(isinstance(x, int) for x in param_range):
                # Integer parameter
                params[param_name] = random.randint(min(param_range), max(param_range))
            elif all(isinstance(x, float) for x in param_range):
                # Float parameter
                params[param_name] = random.uniform(min(param_range), max(param_range))
            else:
                # Categorical parameter
                params[param_name] = random.choice(param_range)
        else:
            # Use the value directly
            params[param_name] = param_range
    
    return params

def optimize_parameters(
    df: pd.DataFrame, 
    strategy_func: Callable, 
    search_space: Dict[str, List], 
    objective_name: str = 'sharpe', 
    num_evals: int = 50
) -> Tuple[Dict[str, Any], float, List[Dict]]:
    """
    Optimize strategy parameters using random search.
    
    Parameters:
    - df: DataFrame with price data
    - strategy_func: Function that implements the strategy
    - search_space: Dictionary with parameter ranges
    - objective_name: Name of the objective to optimize
    - num_evals: Number of parameter sets to evaluate
    
    Returns:
    - best_params: Dictionary with best parameters
    - best_value: Best objective value
    - results: List of all evaluation results
    """
    logger.info(f"Starting parameter optimization with {num_evals} evaluations")
    
    # Get the objective function
    objective_fn = OBJECTIVES.get(objective_name, OBJECTIVES['sharpe'])
    
    # Initialize results
    best_params: Dict[str, Any] = {}  # Initialize as empty dict instead of None
    best_value = float('-inf')  # For maximizing objectives
    results = []
    
    # Test each parameter set
    for i in range(num_evals):
        # Generate random parameter set
        params = generate_param_set(search_space)
        
        try:
            # Run backtest with these parameters
            trades_df, equity_curve = backtest_strategy(df, params)
            
            # Calculate performance metrics
            metrics = calculate_metrics(equity_curve, trades_df)
            
            # Evaluate objective
            obj_value = objective_fn(metrics)
            
            # Track result
            result = {
                'params': params,
                'metrics': metrics,
                'objective_value': obj_value
            }
            results.append(result)
            
            # Update best if improved
            if obj_value > best_value:
                best_value = obj_value
                best_params = params.copy()
                
            # Log progress
            if (i+1) % 5 == 0 or i == 0:
                logger.info(f"Evaluated {i+1}/{num_evals} parameter sets. Current best {objective_name}: {best_value:.4f}")
                
        except Exception as e:
            logger.warning(f"Error evaluating parameter set {params}: {str(e)}")
    
    # Log final results
    if best_params:
        logger.info(f"Optimization completed. Best {objective_name}: {best_value:.4f}")
        logger.info(f"Best parameters: {best_params}")
    else:
        logger.error("Optimization failed. No valid parameter set found.")
    
    return best_params, best_value, results

def plot_optimization_results(
    df: pd.DataFrame, 
    best_params: Dict[str, Any], 
    results: List[Dict], 
    save_path: Optional[str] = None
) -> None:
    """
    Plot optimization results.
    
    Parameters:
    - df: DataFrame with price data
    - best_params: Dictionary with best parameters
    - results: List of all evaluation results
    - save_path: Optional path to save the plot
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec
        
        # Run backtest with best parameters
        trades, equity_curve = backtest_strategy(df, best_params)
        metrics = calculate_metrics(equity_curve, trades)
        
        # Create figure
        plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 2)
        
        # Plot price with SuperTrend
        ax1 = plt.subplot(gs[0, :])
        strategy_df = supertrend_strategy(df, best_params)
        ax1.plot(strategy_df.index, strategy_df['close'], label='Close Price')
        ax1.plot(strategy_df.index, strategy_df['supertrend'], 'r--', label='SuperTrend')
        
        # Plot buy/sell signals
        buys = strategy_df[strategy_df['signal'] == 1]
        sells = strategy_df[strategy_df['signal'] == -1]
        ax1.scatter(buys.index, buys['close'], marker='^', color='g', s=100, label='Buy')
        ax1.scatter(sells.index, sells['close'], marker='v', color='r', s=100, label='Sell')
        
        ax1.set_title('Price Chart with SuperTrend')
        ax1.legend()
        ax1.grid(True)
        
        # Plot equity curve
        ax2 = plt.subplot(gs[1, :])
        ax2.plot(equity_curve.index, equity_curve, 'b')
        ax2.set_title(f'Equity Curve (Total Return: {metrics["total_return"]:.2f}%, Max DD: {metrics["max_drawdown"]:.2f}%)')
        ax2.grid(True)
        
        # Plot parameter distributions
        ax3 = plt.subplot(gs[2, 0])
        if results and isinstance(results, list) and len(results) > 0 and 'params' in results[0]:
            # Plot distribution of objective values
            values = [r['objective_value'] for r in results if 'objective_value' in r]
            if values:
                ax3.hist(values, bins=min(20, len(values)))
                ax3.set_title('Distribution of Objective Values')
                ax3.grid(True)
            else:
                ax3.text(0.5, 0.5, 'No valid objective values', horizontalalignment='center',
                      verticalalignment='center', transform=ax3.transAxes)
        else:
            ax3.text(0.5, 0.5, 'No results data available', horizontalalignment='center',
                   verticalalignment='center', transform=ax3.transAxes)
        
        # Plot metrics
        ax4 = plt.subplot(gs[2, 1])
        if metrics:
            metrics_to_display = {
                'Total Return (%)': metrics.get('total_return', 0),
                'Sharpe Ratio': metrics.get('sharpe_ratio', 0),
                'Max Drawdown (%)': metrics.get('max_drawdown', 0),
                'Win Rate (%)': metrics.get('win_rate', 0) * 100,
                'Trades': metrics.get('num_trades', 0)
            }
            
            y_pos = np.arange(len(metrics_to_display))
            values = list(metrics_to_display.values())
            
            ax4.barh(y_pos, values)
            ax4.set_yticks(y_pos)
            ax4.set_yticklabels(list(metrics_to_display.keys()))
            ax4.set_title('Performance Metrics')
            ax4.grid(True)
        
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()
            
    except ImportError:
        logger.warning("Matplotlib not available. Skipping plot generation.")
    except Exception as e:
        logger.error(f"Error plotting results: {str(e)}")

# Main execution for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fallback SuperTrend Strategy Optimizer")
    parser.add_argument("--data", type=str, help="Path to CSV data file")
    parser.add_argument("--objective", type=str, default="sharpe", choices=list(OBJECTIVES.keys()), help="Optimization objective")
    parser.add_argument("--evals", type=int, default=50, help="Number of parameter sets to evaluate")
    parser.add_argument("--save-plot", type=str, help="Path to save the plot")
    
    args = parser.parse_args()
    
    if args.data:
        # Load data
        df = pd.read_csv(args.data, parse_dates=True, index_col=0)
        
        # Define search space
        search_space = {
            'atr_period': list(range(10, 30)),
            'atr_multiplier': [x / 10 for x in range(15, 50)],
            'stop_loss': [x / 10 for x in range(10, 40)],
            'take_profit': [x / 10 for x in range(20, 80)]
        }
        
        # Run optimization
        best_params, best_value, results = optimize_parameters(
            df, 
            supertrend_strategy, 
            search_space, 
            objective_name=args.objective,
            num_evals=args.evals
        )
        
        # Plot results
        plot_optimization_results(df, best_params, results, args.save_plot)
