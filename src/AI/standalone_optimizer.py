#!/usr/bin/env python3
"""
Standalone Parameter Optimizer for SuperTrend Strategy

This script provides a parameter optimization utility for the SuperTrend trading strategy
without requiring the full Jamso-AI-Engine dependency structure.

Usage:
    python standalone_optimizer.py [--objective sharpe|return|calmar|win_rate] [--params '{"fact":[2,3], "atr_len":[10,14]}']
"""

import pandas as pd
import numpy as np
import json
import time
import argparse
import itertools
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Define optimization objectives
OBJECTIVES = {
    'sharpe': lambda metrics: metrics.get('sharpe_ratio', 0),
    'return': lambda metrics: metrics.get('total_return', 0),
    'calmar': lambda metrics: metrics.get('total_return', 0) / abs(metrics.get('max_drawdown', 1)),
    'win_rate': lambda metrics: metrics.get('win_rate', 0),
    'risk_adjusted': lambda metrics: metrics.get('total_return', 0) / (abs(metrics.get('max_drawdown', 1)) + 0.01),
}

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
        
        # Position sizing based on current equity
        pos_size = max(1, (equity * risk_percent / 100) / (sl_percent / 100 * df.loc[i, 'close']))
        
        # Long signal
        if signal == 1 and (direction_bias == "Both" or direction_bias == "Long Only"):
            # Close any existing short position
            if position < 0:
                pnl = (entry_price - df.loc[i, 'close']) * abs(position)
                equity += pnl
                trades.append({
                    'timestamp': df.loc[i, 'timestamp'],
                    'action': 'CLOSE_SHORT',
                    'price': df.loc[i, 'close'],
                    'pnl': pnl,
                    'size': abs(position)
                })
            
            # Open long position
            position = pos_size
            entry_price = df.loc[i, 'close']
            stop_loss = entry_price * (1 - sl_percent/100)
            take_profit = entry_price * (1 + tp_percent/100)
            
            trades.append({
                'timestamp': df.loc[i, 'timestamp'],
                'action': 'BUY',
                'price': entry_price,
                'size': position,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
            print(f"BUY at {entry_price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}")
        
        # Short signal
        elif signal == -1 and (direction_bias == "Both" or direction_bias == "Short Only"):
            # Close any existing long position
            if position > 0:
                pnl = (df.loc[i, 'close'] - entry_price) * position
                equity += pnl
                trades.append({
                    'timestamp': df.loc[i, 'timestamp'],
                    'action': 'CLOSE_LONG',
                    'price': df.loc[i, 'close'],
                    'pnl': pnl,
                    'size': position
                })
            
            # Open short position
            position = -pos_size
            entry_price = df.loc[i, 'close']
            stop_loss = entry_price * (1 + sl_percent/100)
            take_profit = entry_price * (1 - tp_percent/100)
            
            trades.append({
                'timestamp': df.loc[i, 'timestamp'],
                'action': 'SELL',
                'price': entry_price,
                'size': abs(position),
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
            print(f"SELL at {entry_price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}")
        
        # Handle existing positions - check for stop loss and take profit
        elif position > 0:  # Long position
            if df.loc[i, 'low'] <= stop_loss:  # Stop loss hit
                pnl = (stop_loss - entry_price) * position
                equity += pnl
                trades.append({
                    'timestamp': df.loc[i, 'timestamp'],
                    'action': 'STOP_LOSS_LONG',
                    'price': stop_loss,
                    'pnl': pnl,
                    'size': position
                })
                position = 0
                print(f"STOP LOSS on LONG at {stop_loss:.2f}, PNL: {pnl:.2f}")
                
            elif df.loc[i, 'high'] >= take_profit:  # Take profit hit
                pnl = (take_profit - entry_price) * position
                equity += pnl
                trades.append({
                    'timestamp': df.loc[i, 'timestamp'],
                    'action': 'TAKE_PROFIT_LONG',
                    'price': take_profit,
                    'pnl': pnl,
                    'size': position
                })
                position = 0
                print(f"TAKE PROFIT on LONG at {take_profit:.2f}, PNL: {pnl:.2f}")
        
        elif position < 0:  # Short position
            if df.loc[i, 'high'] >= stop_loss:  # Stop loss hit
                pnl = (entry_price - stop_loss) * abs(position)
                equity += pnl
                trades.append({
                    'timestamp': df.loc[i, 'timestamp'],
                    'action': 'STOP_LOSS_SHORT',
                    'price': stop_loss,
                    'pnl': pnl,
                    'size': abs(position)
                })
                position = 0
                print(f"STOP LOSS on SHORT at {stop_loss:.2f}, PNL: {pnl:.2f}")
                
            elif df.loc[i, 'low'] <= take_profit:  # Take profit hit
                pnl = (entry_price - take_profit) * abs(position)
                equity += pnl
                trades.append({
                    'timestamp': df.loc[i, 'timestamp'],
                    'action': 'TAKE_PROFIT_SHORT',
                    'price': take_profit,
                    'pnl': pnl,
                    'size': abs(position)
                })
                position = 0
                print(f"TAKE PROFIT on SHORT at {take_profit:.2f}, PNL: {pnl:.2f}")
        
        # Update equity curve
        equity_curve.append(equity)
    
    # Debug - print number of signals
    num_buy_signals = sum(df['signal'] == 1)
    num_sell_signals = sum(df['signal'] == -1)
    print(f"Generated {num_buy_signals} buy signals and {num_sell_signals} sell signals")
    
    # Close any remaining position at the end
    if position != 0:
        final_price = df['close'].iloc[-1]
        if position > 0:  # Long position
            pnl = (final_price - entry_price) * position
            equity += pnl
            trades.append({
                'timestamp': df['timestamp'].iloc[-1], 
                'action': 'CLOSE_FINAL_LONG', 
                'price': final_price, 
                'pnl': pnl,
                'size': position
            })
            print(f"CLOSE FINAL LONG at {final_price:.2f}, PNL: {pnl:.2f}")
        else:  # Short position
            pnl = (entry_price - final_price) * abs(position)
            equity += pnl
            trades.append({
                'timestamp': df['timestamp'].iloc[-1], 
                'action': 'CLOSE_FINAL_SHORT', 
                'price': final_price, 
                'pnl': pnl,
                'size': abs(position)
            })
            print(f"CLOSE FINAL SHORT at {final_price:.2f}, PNL: {pnl:.2f}")
    
    # Convert to DataFrame/Series
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    
    # Make sure we have timestamps for the equity curve
    if len(equity_curve) > len(df['timestamp']):
        equity_curve = equity_curve[1:]  # Drop the initial value if needed
        
    equity_curve = pd.Series(equity_curve, index=df['timestamp'])
    
    # Debug - print number of trades
    print(f"Generated {len(trades_df)} trades")
    if len(trades_df) > 0:
        profitable_trades = trades_df[trades_df['pnl'] > 0] if 'pnl' in trades_df.columns else pd.DataFrame()
        print(f"Profitable trades: {len(profitable_trades)}")
    
    return trades_df, equity_curve

def calculate_metrics(equity_curve, trades):
    """Calculate performance metrics for the backtest."""
    if trades.empty:
        return {
            'total_return': 0,
            'annualized_return': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'num_trades': 0,
            'win_rate': 0,
        }
    
    # Check if we actually have any trades
    if len(trades) == 0:
        return {
            'total_return': 0,
            'annualized_return': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'num_trades': 0,
            'win_rate': 0,
        }
    
    # Daily returns
    daily_returns = equity_curve.pct_change().dropna()
    
    # Calculate metrics
    metrics = {
        'total_return': float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1),
        'annualized_return': ((equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (252 / len(equity_curve)) - 1) if len(equity_curve) > 0 else 0,
        'max_drawdown': float((equity_curve / equity_curve.cummax() - 1).min()),
        'sharpe_ratio': float(daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0,
        'num_trades': len(trades),
        'win_rate': float((trades['pnl'] > 0).mean()) if 'pnl' in trades.columns and len(trades) > 0 else 0
    }
    
    return metrics

def optimize_parameters(data, param_grid, objective_fn, max_evals=20, verbose=True):
    """
    Run grid search optimization for strategy parameters.
    """
    # Generate all parameter combinations
    param_keys = list(param_grid.keys())
    param_values = list(param_grid.values())
    all_combos = list(itertools.product(*param_values))
    
    # Calculate total combinations
    total_combos = len(all_combos)
    print(f"Parameter space has {total_combos} combinations")
    print(f"Running up to {min(max_evals, total_combos)} evaluations")
    
    # Limit by max_evals
    np.random.shuffle(all_combos)
    if max_evals < total_combos:
        all_combos = all_combos[:max_evals]
    
    # Redirect print statements if not verbose
    import sys
    import io
    original_stdout = sys.stdout
    
    # Run evaluations
    results = []
    for i, combo in enumerate(all_combos):
        # Create parameter dictionary
        params = dict(zip(param_keys, combo))
        print(f"Evaluating parameter set {i+1}/{len(all_combos)}: {params}")
        
        # Add default parameters
        params['initial_capital'] = 10000
        params['direction_bias'] = "Both"
        
        # Run backtest (capture or suppress output based on verbose setting)
        if not verbose:
            sys.stdout = io.StringIO()  # Redirect stdout
            
        try:
            trades, equity_curve = supertrend_strategy(data, **params)
            metrics = calculate_metrics(equity_curve, trades)
            score = objective_fn(metrics)
            
            result = {
                'params': params,
                'score': score,
                'metrics': metrics,
                'trades': len(trades),
                'win_count': sum(1 for t in trades['pnl'] if t > 0) if 'pnl' in trades.columns and len(trades) > 0 else 0
            }
            results.append(result)
            
        except Exception as e:
            print(f"  Error with params {params}: {str(e)}")
            continue
        finally:
            if not verbose:
                sys.stdout = original_stdout  # Restore stdout
        
        print(f"  Score: {result['score']:.4f}, Return: {result['metrics']['total_return']:.2%}, " +
              f"Sharpe: {result['metrics']['sharpe_ratio']:.2f}, Win Rate: {result['metrics']['win_rate']:.2%}, " +
              f"Trades: {result.get('trades', 0)}")
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Parameter Optimizer for SuperTrend Strategy')
    parser.add_argument('--objective', type=str, choices=list(OBJECTIVES.keys()), 
                      default='sharpe', help='Optimization objective')
    parser.add_argument('--params', type=str, 
                      help='JSON string of parameter grid, e.g., \'{"atr_len": [10, 20], "fact": [2.0, 3.0]}\'')
    parser.add_argument('--max-evals', type=int, default=20,
                      help='Maximum number of evaluations')
    parser.add_argument('--days', type=int, default=252,
                      help='Number of days of data to generate')
    parser.add_argument('--trends', type=int, default=3,
                      help='Number of trend cycles to generate')
    parser.add_argument('--volatility', type=float, default=0.015,
                      help='Daily volatility for synthetic data')
    parser.add_argument('--verbose', action='store_true', 
                      help='Enable verbose output')
    parser.add_argument('--save-plot', action='store_true',
                      help='Save equity curve plot')
    args = parser.parse_args()
    
    print(f"SuperTrend Strategy - Parameter Optimizer")
    print(f"========================================")
    
    # Generate sample data with enhanced trend patterns
    data = generate_sample_data(
        days=args.days, 
        trend_cycles=args.trends,
        volatility=args.volatility
    )
    
    # Plot price data if matplotlib is available and save-plot flag is set
    if args.save_plot:
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(12, 6))
            plt.plot(data['timestamp'], data['close'])
            plt.title('Synthetic Price Data for Optimization')
            plt.savefig('price_data.png')
            print(f"Saved price chart to price_data.png")
        except ImportError:
            print("Matplotlib not installed, skipping chart generation")
            print("Install with: pip install matplotlib")
    
    # Get parameter grid
    if args.params:
        try:
            param_grid = json.loads(args.params)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in --params argument")
            return
    else:
        # Default parameter grid
        param_grid = {
            'atr_len': [5, 10, 14, 21],
            'fact': [1.5, 2.0, 2.5, 3.0, 3.5],
            'risk_percent': [0.5, 1.0, 1.5],
            'sl_percent': [0.3, 0.5, 0.7],
            'tp_percent': [1.0, 1.5, 2.0]
        }
    
    # Get objective function
    objective_fn = OBJECTIVES[args.objective]
    print(f"Optimization Objective: {args.objective}")
    
    # Run optimization
    print(f"\nStarting parameter optimization...")
    start_time = time.time()
    results = optimize_parameters(
        data=data,
        param_grid=param_grid,
        objective_fn=objective_fn,
        max_evals=args.max_evals,
        verbose=args.verbose
    )
    end_time = time.time()
    
    # Print results
    print(f"\nOptimization completed in {end_time - start_time:.2f} seconds")
    
    # Analyze the optimization results
    scores = [r['score'] for r in results]
    returns = [r['metrics']['total_return'] for r in results]
    
    print(f"\nOptimization Statistics:")
    print(f"  Total evaluations: {len(results)}")
    print(f"  Score range: [{min(scores):.4f}, {max(scores):.4f}]")
    print(f"  Return range: [{min(returns):.2%}, {max(returns):.2%}]")
    
    # Print parameter importance (basic analysis)
    param_keys = list(param_grid.keys())
    for param in param_keys:
        param_values = sorted(set([r['params'][param] for r in results]))
        param_scores = {}
        for value in param_values:
            matching_results = [r for r in results if r['params'][param] == value]
            avg_score = sum(r['score'] for r in matching_results) / len(matching_results)
            param_scores[value] = avg_score
            
        best_value = max(param_scores.items(), key=lambda x: x[1])[0]
        print(f"  Best {param}: {best_value} (avg score: {param_scores[best_value]:.4f})")
    
    print("\nTop 5 Parameter Combinations:")
    for i, result in enumerate(results[:5]):
        print(f"\n{i+1}. Score: {result['score']:.4f}")
        
        # Print parameters
        for param, value in result['params'].items():
            if param in param_grid:  # Only show optimized parameters
                print(f"   {param}: {value}")
        
        # Print key metrics
        metrics = result['metrics']
        print(f"   Total Return: {metrics['total_return']:.2%}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Win Rate: {metrics['win_rate']:.2%}")
        print(f"   Number of Trades: {metrics['num_trades']}")
        print(f"   Annualized Return: {metrics['annualized_return']:.2%}")
    
    # Save best parameters to a file
    output_data = {
        'best_params': results[0]['params'],
        'metrics': results[0]['metrics'],
        'timestamp': datetime.now().isoformat(),
        'objective': args.objective
    }
    
    output_file = f"supertrend_optimized_params_{args.objective}.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
        
    print(f"\nBest parameters saved to {output_file}")

if __name__ == "__main__":
    main()
