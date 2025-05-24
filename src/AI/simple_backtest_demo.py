#!/usr/bin/env python3
"""
Simple Backtest Demo Script

This script demonstrates the backtesting system with synthetic data
without requiring the full Jamso-AI-Engine dependency structure.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_data(days=100, volatility=0.015, start_price=100.0):
    """Generate synthetic price data for testing."""
    # Generate dates (business days)
    start = datetime.now() - timedelta(days=days)
    dates = pd.date_range(start=start, periods=days, freq='B')
    
    # Generate random returns
    returns = np.random.normal(0, volatility, days)
    
    # Calculate prices
    prices = start_price * (1 + returns).cumprod()
    
    # Create OHLCV data
    df = pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'open': prices * (1 + np.random.normal(0, volatility/3, days)),
        'volume': np.random.lognormal(10, 1, days)
    })
    
    # Generate high/low based on open/close
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
    
    print(f"Generated {len(df)} days of synthetic data")
    return df

def supertrend_strategy(df, atr_len=10, fact=3.0, risk_percent=1.0):
    """Simplified SuperTrend strategy for demonstration."""
    df = df.copy()
    equity = 10000  # Initial capital
    position = 0
    entry_price = 0
    trades = []
    equity_curve = []
    
    # Calculate SuperTrend
    hl2 = (df['high'] + df['low']) / 2
    upper_band = hl2 + fact * df['atr']
    lower_band = hl2 - fact * df['atr']
    supertrend = np.zeros(len(df))
    direction = np.ones(len(df))
    
    for i in range(1, len(df)):
        prev_st = supertrend[i-1] if i > 0 else hl2.iloc[0]
        prev_ub = upper_band.iloc[i-1]
        prev_lb = lower_band.iloc[i-1]
        
        if prev_st == prev_ub:
            direction[i] = -1 if df['close'].iloc[i] > upper_band.iloc[i] else 1
        else:
            direction[i] = 1 if df['close'].iloc[i] < lower_band.iloc[i] else -1
            
        supertrend[i] = lower_band.iloc[i] if direction[i] == -1 else upper_band.iloc[i]
    
    # Trading logic
    for i in range(1, len(df)):
        # Entry signals
        long_signal = direction[i-1] < 0 and direction[i] > 0
        short_signal = direction[i-1] > 0 and direction[i] < 0
        
        # Position sizing
        pos_size = max(1, (equity * risk_percent / 100) / df['close'].iloc[i])
        
        # Entry
        if long_signal and position <= 0:
            # Close any existing short position
            if position < 0:
                pnl = (entry_price - df['close'].iloc[i]) * abs(position)
                equity += pnl
                trades.append({'timestamp': df['timestamp'].iloc[i], 'action': 'CLOSE_SHORT', 'price': df['close'].iloc[i], 'pnl': pnl})
            
            # Open long position
            position = pos_size
            entry_price = df['close'].iloc[i]
            trades.append({'timestamp': df['timestamp'].iloc[i], 'action': 'BUY', 'price': entry_price, 'size': position})
        
        elif short_signal and position >= 0:
            # Close any existing long position
            if position > 0:
                pnl = (df['close'].iloc[i] - entry_price) * position
                equity += pnl
                trades.append({'timestamp': df['timestamp'].iloc[i], 'action': 'CLOSE_LONG', 'price': df['close'].iloc[i], 'pnl': pnl})
            
            # Open short position
            position = -pos_size
            entry_price = df['close'].iloc[i]
            trades.append({'timestamp': df['timestamp'].iloc[i], 'action': 'SELL', 'price': entry_price, 'size': abs(position)})
        
        # Track equity
        equity_curve.append(equity)
    
    # Convert to DataFrames
    trades_df = pd.DataFrame(trades)
    equity_curve = pd.Series(equity_curve, index=df['timestamp'].iloc[1:])
    
    return trades_df, equity_curve

def calculate_metrics(equity_curve, trades):
    """Calculate basic performance metrics."""
    returns = equity_curve.pct_change().dropna()
    
    metrics = {
        'total_return': equity_curve.iloc[-1] / equity_curve.iloc[0] - 1,
        'annualized_return': ((equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (252 / len(equity_curve)) - 1) if len(equity_curve) > 0 else 0,
        'max_drawdown': (equity_curve / equity_curve.cummax() - 1).min(),
        'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else np.nan,
        'num_trades': len(trades),
        'win_rate': (trades['pnl'] > 0).mean() if 'pnl' in trades.columns and len(trades) > 0 else 0
    }
    
    return metrics

def main():
    try:
        with open('/tmp/backtest_demo_log.txt', 'w') as f:
            f.write("Starting backtest demo\n")
        
        print("Jamso AI Engine - Simple Backtest Demo")
        print("======================================")
        
        # Generate sample data
        data = generate_sample_data(days=252)  # One year of data
        
        with open('/tmp/backtest_demo_log.txt', 'a') as f:
            f.write(f"Generated sample data with shape: {data.shape}\n")
        
        print(f"\nRunning SuperTrend backtest...")
        
        # Run backtest
        trades, equity_curve = supertrend_strategy(data, atr_len=14, fact=3.0, risk_percent=1.0)
        
        with open('/tmp/backtest_demo_log.txt', 'a') as f:
            f.write(f"Generated trades: {len(trades)} and equity curve: {len(equity_curve)}\n")
        
        # Calculate metrics
        metrics = calculate_metrics(equity_curve, trades)
        
        with open('/tmp/backtest_demo_log.txt', 'a') as f:
            f.write(f"Calculated metrics: {metrics}\n")
        
        # Display results
        print("\nBacktest Results:")
        print(f"Total Return: {metrics['total_return']:.2%}")
        print(f"Annualized Return: {metrics['annualized_return']:.2%}")
        print(f"Maximum Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Number of Trades: {metrics['num_trades']}")
        print(f"Win Rate: {metrics['win_rate']:.2%}")
        
        print("\nSample Trade Data:")
        if not trades.empty:
            print(trades.head())
        
        print("\nDemo completed successfully!")
        
        with open('/tmp/backtest_demo_log.txt', 'a') as f:
            f.write("Demo completed successfully\n")
            
    except Exception as e:
        with open('/tmp/backtest_demo_log.txt', 'a') as f:
            f.write(f"ERROR: {str(e)}\n")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
