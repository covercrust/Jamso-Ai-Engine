"""
Python translation of Jamso Enhanced Alert SuperTrend (Pine Script)
Template for use with PerformanceMonitor.
"""
import numpy as np
import pandas as pd

def jamso_ai_bot_strategy(df, atr_len=10, fact=2.8, optimize_factor=True, training_data_period=100,
                         highvol=0.75, midvol=0.5, lowvol=0.25, risk_percent=1.0, max_risk_percent=5.0,
                         adaptive_risk=False, direction_bias="Both", sl_type="Fixed Percent", sl_percent=0.5,
                         sl_atr_multiplier=2.0, tp_percent=1.5, max_contracts=28, sizing_method="Dynamic Risk-Based",
                         order_size=1.0, trailing_stop=False, trailing_step=0.2, spread_pips=0.0, use_deep_settings=True,
                         profit_protection=True, max_drawdown_limit=25.0, pause_trading_on_drawdown=True, initial_capital=5000):
    """
    Args:
        df: pandas DataFrame with columns ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        All other args: strategy parameters matching Pine Script inputs
    Returns:
        trades: DataFrame of executed trades
        equity_curve: Series of equity over time
    """
    df = df.copy()
    equity = initial_capital
    position = 0
    entry_price = 0
    trades = []
    equity_curve = []
    peak_equity = initial_capital
    drawdown_percent = 0.0
    win_count = 0
    loss_count = 0
    current_risk = risk_percent
    paused_by_drawdown = False
    # Calculate ATR
    df['atr'] = df['high'].rolling(atr_len).max() - df['low'].rolling(atr_len).min()
    # SuperTrend calculation (simplified)
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
    df['supertrend'] = supertrend
    df['direction'] = direction
    # Volatility regime detection (simple percentile-based)
    df['volatility'] = df['atr']
    hv = df['volatility'].rolling(training_data_period).quantile(highvol)
    mv = df['volatility'].rolling(training_data_period).quantile(midvol)
    lv = df['volatility'].rolling(training_data_period).quantile(lowvol)
    def detect_regime(v, hvv, mvv):
        if v > hvv:
            return 'volatile'
        elif v > mvv:
            return 'medium'
        else:
            return 'calm'
    df['regime'] = [detect_regime(v, hvv, mvv) for v, hvv, mvv in zip(df['volatility'], hv, mv)]
    # Main backtest loop
    for i in range(1, len(df)):
        # Date range filter (optional)
        # ...implement if needed...
        # Drawdown logic
        if equity > peak_equity:
            peak_equity = equity
        if peak_equity > initial_capital:
            drawdown_percent = (peak_equity - equity) / (peak_equity - initial_capital) * 100
        if pause_trading_on_drawdown and drawdown_percent >= max_drawdown_limit:
            paused_by_drawdown = True
        if paused_by_drawdown and drawdown_percent < max_drawdown_limit * 0.8:
            paused_by_drawdown = False
        # Entry/exit logic
        long_signal = direction[i-1] < 0 and direction[i] > 0 and direction_bias != "Short Only"
        short_signal = direction[i-1] > 0 and direction[i] < 0 and direction_bias != "Long Only"
        # Position sizing
        pos_size = order_size if sizing_method == "Fixed Sizing" else max(1, min((equity * current_risk / 100) / (sl_percent / 100 * df['close'].iloc[i]), max_contracts))
        # Profit protection
        pos_size_multiplier = 1.0
        if profit_protection and drawdown_percent > 5:
            pos_size_multiplier = max(0.5, 1.0 - (drawdown_percent / 100))
        elif profit_protection and equity > initial_capital * 1.3:
            pos_size_multiplier = min(1.5, 1.0 + ((equity - initial_capital) / initial_capital) * 0.2)
        if use_deep_settings:
            pos_size_multiplier *= 1.5
        pos_size *= pos_size_multiplier
        # Entry
        if not paused_by_drawdown:
            if long_signal and position <= 0:
                if position < 0:
                    # Close short
                    pnl = (entry_price - df['close'].iloc[i]) * abs(position)
                    equity += pnl
                    trades.append({'timestamp': df['timestamp'].iloc[i], 'action': 'CLOSE_SHORT', 'price': df['close'].iloc[i], 'pnl': pnl, 'size': abs(position)})
                position = pos_size
                entry_price = df['close'].iloc[i]
                trades.append({'timestamp': df['timestamp'].iloc[i], 'action': 'BUY', 'price': entry_price, 'size': position})
            elif short_signal and position >= 0:
                if position > 0:
                    # Close long
                    pnl = (df['close'].iloc[i] - entry_price) * abs(position)
                    equity += pnl
                    trades.append({'timestamp': df['timestamp'].iloc[i], 'action': 'CLOSE_LONG', 'price': df['close'].iloc[i], 'pnl': pnl, 'size': abs(position)})
                position = -pos_size
                entry_price = df['close'].iloc[i]
                trades.append({'timestamp': df['timestamp'].iloc[i], 'action': 'SELL', 'price': entry_price, 'size': abs(position)})
        # Exit logic (TP/SL, trailing, etc. can be added)
        equity_curve.append(equity)
    trades_df = pd.DataFrame(trades)
    equity_curve = pd.Series(equity_curve, index=df['timestamp'].iloc[1:])
    return trades_df, equity_curve
