#!/usr/bin/env python3
"""
Out-of-Sample Testing for Optimized Trading Parameters

This script tests optimized trading parameters on out-of-sample data to evaluate 
their robustness and prevent overfitting. It can use both historical data from
Capital.com API and synthetic data for testing.

Usage:
    python test_optimized_params.py --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json --days 30 --mode historical
"""

import os
import sys
import pandas as pd
import numpy as np
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Import the standalone optimizer functions
from src.AI.standalone_optimizer import (
    supertrend_strategy, 
    calculate_metrics,
    generate_sample_data
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

def load_parameters(params_file: str) -> Tuple[dict, dict]:
    """
    Load parameters and metadata from a JSON file
    
    Parameters:
    - params_file: Path to the parameter file
    
    Returns:
    - Tuple of (parameters dict, metadata dict)
    """
    try:
        with open(params_file, 'r') as f:
            data = json.load(f)
        
        params = data.get('params', {})
        metadata = data.get('metadata', {})
        
        logger.info(f"Loaded parameters from {params_file}")
        return params, metadata
    except Exception as e:
        logger.error(f"Error loading parameters from {params_file}: {str(e)}")
        return {}, {}

def split_data_for_testing(df: pd.DataFrame, train_ratio: float = 0.7) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into training and testing sets
    
    Parameters:
    - df: DataFrame with price data
    - train_ratio: Ratio of data to use for training (default: 0.7)
    
    Returns:
    - Tuple of (training DataFrame, testing DataFrame)
    """
    split_idx = int(len(df) * train_ratio)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    
    logger.info(f"Split data: {len(train_df)} training rows, {len(test_df)} testing rows")
    return train_df, test_df

def test_strategy_on_unseen_data(df: pd.DataFrame, params: dict, use_sentiment: bool = False, 
                                sentiment_weight: float = 0.2) -> dict:
    """
    Test a strategy on unseen data
    
    Parameters:
    - df: DataFrame with price data
    - params: Strategy parameters
    - use_sentiment: Whether to use sentiment data
    - sentiment_weight: Weight of sentiment data
    
    Returns:
    - Dictionary with strategy results and metrics
    """
    try:
        # Apply the strategy
        if use_sentiment:
            result = supertrend_with_sentiment(df, **params, sentiment_weight=sentiment_weight)
            # Extract trades and equity curve from result dictionary
            trades = result.get('trades', pd.DataFrame())
            equity_curve = result.get('equity_curve', pd.Series())
        else:
            # Standalone optimizer returns a tuple of (trades_df, equity_curve)
            trades, equity_curve = supertrend_strategy(df, **params)
        
        # Calculate metrics
        metrics = calculate_metrics(equity_curve, trades)
        
        return {
            'result': {'trades': trades, 'equity_curve': equity_curve},
            'metrics': metrics
        }
    except Exception as e:
        logger.error(f"Error testing strategy: {str(e)}")
        return {
            'result': {'trades': pd.DataFrame(), 'equity_curve': pd.Series()},
            'metrics': {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'expectancy': 0,
                'total_trades': 0
            }
        }

def perform_monte_carlo_simulation(df: pd.DataFrame, params: dict, use_sentiment: bool = False,
                                 sentiment_weight: float = 0.2, n_simulations: int = 100) -> dict:
    """
    Perform Monte Carlo simulation to test strategy robustness
    
    Parameters:
    - df: DataFrame with price data
    - params: Strategy parameters
    - use_sentiment: Whether to use sentiment data
    - sentiment_weight: Weight of sentiment data
    - n_simulations: Number of simulations to run
    
    Returns:
    - Dictionary with simulation results
    """
    try:
        returns = []
        sharpe_ratios = []
        drawdowns = []
        win_rates = []
        
        # Run simulations
        for i in range(n_simulations):
            # Generate synthetic data with similar properties to the original data
            synthetic_df = generate_monte_carlo_data(df)
            
            # Apply the strategy
            if use_sentiment:
                result = supertrend_with_sentiment(synthetic_df, **params, sentiment_weight=sentiment_weight)
                # Extract trades and equity curve from result dictionary
                trades = result.get('trades', pd.DataFrame())
                equity_curve = result.get('equity_curve', pd.Series())
            else:
                # Standalone optimizer returns a tuple of (trades_df, equity_curve)
                trades, equity_curve = supertrend_strategy(synthetic_df, **params)
            
            # Calculate metrics
            metrics = calculate_metrics(equity_curve, trades)
            
            # Store results
            returns.append(metrics['total_return'])
            sharpe_ratios.append(metrics['sharpe_ratio'])
            drawdowns.append(metrics['max_drawdown'])
            win_rates.append(metrics['win_rate'])
            
            if i % 10 == 0:
                logger.info(f"Completed {i}/{n_simulations} simulations")
        
        # Calculate statistics
        results = {
            'returns': {
                'mean': np.mean(returns),
                'median': np.median(returns),
                'std': np.std(returns),
                'min': np.min(returns),
                'max': np.max(returns),
                'samples': returns
            },
            'sharpe_ratios': {
                'mean': np.mean(sharpe_ratios),
                'median': np.median(sharpe_ratios),
                'std': np.std(sharpe_ratios),
                'min': np.min(sharpe_ratios),
                'max': np.max(sharpe_ratios),
                'samples': sharpe_ratios
            },
            'drawdowns': {
                'mean': np.mean(drawdowns),
                'median': np.median(drawdowns),
                'std': np.std(drawdowns),
                'min': np.min(drawdowns),
                'max': np.max(drawdowns),
                'samples': drawdowns
            },
            'win_rates': {
                'mean': np.mean(win_rates),
                'median': np.median(win_rates),
                'std': np.std(win_rates),
                'min': np.min(win_rates),
                'max': np.max(win_rates),
                'samples': win_rates
            }
        }
        
        return results
    except Exception as e:
        logger.error(f"Error running Monte Carlo simulation: {str(e)}")
        # Return empty dict with the expected structure
        return {
            'returns': {'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0, 'samples': []},
            'sharpe_ratios': {'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0, 'samples': []},
            'drawdowns': {'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0, 'samples': []},
            'win_rates': {'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0, 'samples': []}
        }

def generate_monte_carlo_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic data for Monte Carlo simulation based on original data statistics
    
    Parameters:
    - df: Original DataFrame with price data
    
    Returns:
    - Synthetic DataFrame with price data
    """
    # Copy the DataFrame to preserve timestamps
    synthetic_df = df.copy()
    
    # Calculate log returns (pandas Series has dropna method)
    log_returns = np.log(df['close'] / df['close'].shift(1))
    log_returns = log_returns[~np.isnan(log_returns)]  # Remove NaN values
    
    # Calculate statistics
    mean_return = log_returns.mean()
    std_return = log_returns.std()
    
    # Generate random returns
    random_returns = np.random.normal(mean_return, std_return, len(df))
    
    # Generate synthetic prices
    start_price = df['close'].iloc[0]
    synthetic_prices = start_price * np.exp(np.cumsum(random_returns))
    
    # Replace close prices
    synthetic_df['close'] = synthetic_prices
    
    # Generate OHLC based on close
    daily_range = np.mean(df['high'] / df['low'] - 1)
    synthetic_df['high'] = synthetic_df['close'] * (1 + daily_range * np.random.rand(len(synthetic_df)) * 0.5)
    synthetic_df['low'] = synthetic_df['close'] * (1 - daily_range * np.random.rand(len(synthetic_df)) * 0.5)
    synthetic_df['open'] = synthetic_df['close'].shift(1)
    # Correctly set the first row's open price
    idx = 0
    col = 'open'
    synthetic_df.loc[synthetic_df.index[idx], col] = synthetic_df['close'].iloc[0]
    
    return synthetic_df

def plot_comparative_results(train_results: dict, test_results: dict, mc_results: dict, 
                           output_file: str = ""):
    """
    Plot comparative results of in-sample vs out-of-sample testing
    
    Parameters:
    - train_results: Results on training data
    - test_results: Results on testing data
    - mc_results: Monte Carlo simulation results
    - output_file: Path to save plot
    """
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(15, 12))
    
    # Grid layout - import GridSpec from matplotlib.gridspec instead of plt
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(3, 2, figure=fig)
    
    # Return comparison
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.bar(['Training', 'Testing'], 
           [train_results['metrics']['total_return'], test_results['metrics']['total_return']],
           color=['blue', 'green'])
    ax1.set_title('Total Return Comparison')
    ax1.set_ylabel('Return (%)')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Sharpe ratio comparison
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.bar(['Training', 'Testing'], 
           [train_results['metrics']['sharpe_ratio'], test_results['metrics']['sharpe_ratio']],
           color=['blue', 'green'])
    ax2.set_title('Sharpe Ratio Comparison')
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # Other metrics comparison
    metrics = ['win_rate', 'max_drawdown', 'profit_factor', 'expectancy']
    labels = ['Win Rate (%)', 'Max Drawdown (%)', 'Profit Factor', 'Expectancy']
    
    ax3 = fig.add_subplot(gs[1, :])
    x = np.arange(len(metrics))
    width = 0.35
    
    train_values = [train_results['metrics'][m] for m in metrics]
    test_values = [test_results['metrics'][m] for m in metrics]
    
    ax3.bar(x - width/2, train_values, width, label='Training')
    ax3.bar(x + width/2, test_values, width, label='Testing')
    
    ax3.set_title('Strategy Metrics Comparison')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels)
    ax3.legend()
    ax3.grid(True, linestyle='--', alpha=0.7)
    
    # Monte Carlo simulation results
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.hist(mc_results['returns']['samples'], bins=20, alpha=0.7)
    ax4.axvline(mc_results['returns']['mean'], color='r', linestyle='--')
    ax4.axvline(test_results['metrics']['total_return'], color='g', linestyle='-')
    ax4.set_title('Monte Carlo Returns Distribution')
    ax4.set_xlabel('Return (%)')
    ax4.set_ylabel('Frequency')
    ax4.grid(True, linestyle='--', alpha=0.7)
    
    # Monte Carlo drawdown results
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.hist(mc_results['drawdowns']['samples'], bins=20, alpha=0.7)
    ax5.axvline(mc_results['drawdowns']['mean'], color='r', linestyle='--')
    ax5.axvline(test_results['metrics']['max_drawdown'], color='g', linestyle='-')
    ax5.set_title('Monte Carlo Drawdown Distribution')
    ax5.set_xlabel('Drawdown (%)')
    ax5.set_ylabel('Frequency')
    ax5.grid(True, linestyle='--', alpha=0.7)
    
    # Add a text box with statistics
    textbox = (
        f"Mean MC Return: {mc_results['returns']['mean']:.2f}%\n"
        f"Testing Return: {test_results['metrics']['total_return']:.2f}%\n\n"
        f"Mean MC Sharpe: {mc_results['sharpe_ratios']['mean']:.2f}\n"
        f"Testing Sharpe: {test_results['metrics']['sharpe_ratio']:.2f}\n\n"
        f"Out-of-Sample Performance: "
        f"{100 * test_results['metrics']['total_return'] / train_results['metrics']['total_return']:.1f}% "
        f"of In-Sample"
    )
    
    fig.text(0.5, 0.01, textbox, ha='center', va='bottom', 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout(rect=(0, 0.05, 1, 1))
    
    if output_file and output_file != "":
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"Comparative results saved to {output_file}")
    else:
        plt.show()

def main():
    """Main function to handle command-line arguments and run out-of-sample testing."""
    parser = argparse.ArgumentParser(description="Out-of-Sample Testing for Optimized Parameters")
    parser.add_argument("--params-file", type=str, required=True, 
                       help="Path to optimized parameters file")
    parser.add_argument("--days", type=int, default=60, 
                       help="Number of days of data to use (for historical mode)")
    parser.add_argument("--mode", type=str, choices=['historical', 'synthetic'], default='historical',
                       help="Testing mode - historical uses Capital.com data, synthetic generates data")
    parser.add_argument("--train-ratio", type=float, default=0.7,
                       help="Ratio of data to use for training (default: 0.7)")
    parser.add_argument("--mc-simulations", type=int, default=100,
                       help="Number of Monte Carlo simulations to run")
    parser.add_argument("--output", type=str, default=None,
                       help="Output file path for visualization")
    
    args = parser.parse_args()
    
    # Load parameters
    params, metadata = load_parameters(args.params_file)
    
    if not params or not metadata:
        logger.error("Failed to load parameters. Exiting.")
        sys.exit(1)
    
    # Extract metadata
    symbol = metadata.get('symbol', 'BTCUSD')
    timeframe = metadata.get('timeframe', 'HOUR')
    use_sentiment = metadata.get('use_sentiment', False)
    sentiment_weight = metadata.get('sentiment_weight', 0.2) if use_sentiment else 0
    
    # Get data based on mode
    if args.mode == 'historical':
        # Fetch historical data from Capital.com
        df = fetch_market_data(symbol, RESOLUTION_MAP[timeframe], args.days)
        
        if df is None or df.empty:
            logger.error("Failed to fetch market data. Exiting.")
            sys.exit(1)
    else:
        # Generate synthetic data
        df = generate_sample_data(days=args.days, trend_cycles=3)
    
    # Split data into training and testing sets
    train_df, test_df = split_data_for_testing(df, args.train_ratio)
    
    # Test strategy on training data (in-sample)
    train_results = test_strategy_on_unseen_data(
        train_df, params, use_sentiment, sentiment_weight
    )
    
    # Test strategy on testing data (out-of-sample)
    test_results = test_strategy_on_unseen_data(
        test_df, params, use_sentiment, sentiment_weight
    )
    
    # Display comparison
    logger.info("--- In-Sample vs Out-of-Sample Performance ---")
    logger.info(f"In-Sample (Training) Return: {train_results['metrics']['total_return']:.2f}%")
    logger.info(f"In-Sample (Training) Sharpe: {train_results['metrics']['sharpe_ratio']:.2f}")
    logger.info(f"Out-of-Sample (Testing) Return: {test_results['metrics']['total_return']:.2f}%")
    logger.info(f"Out-of-Sample (Testing) Sharpe: {test_results['metrics']['sharpe_ratio']:.2f}")
    
    # Calculate robustness ratio
    robustness_ratio = test_results['metrics']['total_return'] / train_results['metrics']['total_return']
    logger.info(f"Robustness Ratio: {robustness_ratio:.2f} ({100 * robustness_ratio:.1f}% of in-sample performance)")
    
    # Define robustness categories
    if robustness_ratio >= 0.7:
        robustness = "EXCELLENT"
    elif robustness_ratio >= 0.3:
        robustness = "GOOD"
    elif robustness_ratio > 0:
        robustness = "FAIR"
    elif robustness_ratio <= 0:
        robustness = "POOR"
    
    logger.info(f"Robustness Assessment: {robustness}")
    
    # Run Monte Carlo simulations if requested
    if args.mc_simulations > 0:
        logger.info(f"Running {args.mc_simulations} Monte Carlo simulations...")
        
        mc_results = perform_monte_carlo_simulation(
            df, params, use_sentiment, sentiment_weight, args.mc_simulations
        )
        
        logger.info("--- Monte Carlo Simulation Results ---")
        logger.info(f"Mean Return: {mc_results['returns']['mean']:.2f}% (Std: {mc_results['returns']['std']:.2f}%)")
        logger.info(f"Mean Sharpe: {mc_results['sharpe_ratios']['mean']:.2f} (Std: {mc_results['sharpe_ratios']['std']:.2f})")
        logger.info(f"Mean Drawdown: {mc_results['drawdowns']['mean']:.2f}% (Std: {mc_results['drawdowns']['std']:.2f}%)")
        logger.info(f"Mean Win Rate: {mc_results['win_rates']['mean']:.2f}% (Std: {mc_results['win_rates']['std']:.2f}%)")
        
        # Check if out-of-sample performance is within Monte Carlo distribution
        returns = mc_results['returns']['samples']
        percentile = sum(1 for x in returns if x < test_results['metrics']['total_return']) / len(returns) * 100
        logger.info(f"Out-of-Sample Return is at the {percentile:.1f}th percentile of the Monte Carlo distribution")
        
        # Plot comparative results
        output_file = args.output
        if output_file is None or output_file == "":
            base_name = os.path.splitext(os.path.basename(args.params_file))[0]
            output_file = f"{base_name}_out_of_sample_test.png"
        
        plot_comparative_results(train_results, test_results, mc_results, output_file)
    
    # Save detailed results to file
    results_file = f"{os.path.splitext(args.params_file)[0]}_validation.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'params': params,
            'metadata': metadata,
            'in_sample': {
                'return': train_results['metrics']['total_return'],
                'sharpe': train_results['metrics']['sharpe_ratio'],
                'drawdown': train_results['metrics']['max_drawdown'],
                'win_rate': train_results['metrics']['win_rate'],
                'trades': train_results['metrics']['total_trades']
            },
            'out_of_sample': {
                'return': test_results['metrics']['total_return'],
                'sharpe': test_results['metrics']['sharpe_ratio'],
                'drawdown': test_results['metrics']['max_drawdown'],
                'win_rate': test_results['metrics']['win_rate'],
                'trades': test_results['metrics']['total_trades']
            },
            'robustness': {
                'ratio': robustness_ratio,
                'assessment': robustness
            },
            'monte_carlo': mc_results if args.mc_simulations > 0 else None
        }, f, indent=4)
    
    logger.info(f"Validation results saved to {results_file}")

if __name__ == "__main__":
    main()
