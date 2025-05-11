# Jamso AI BOT - Enhanced SuperTrend Trading Strategy

![Jamso AI BOT](https://via.placeholder.com/800x400?text=Jamso+AI+BOT)

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Strategy Parameters](#strategy-parameters)
- [Trading Logic](#trading-logic)
- [Volatility Clustering](#volatility-clustering)
- [Risk Management](#risk-management)
- [Performance Tracking](#performance-tracking)
- [Alert System](#alert-system)
- [Webhook Integration](#webhook-integration)
- [API Implementation](#api-implementation)
- [Backtesting & Optimization](#backtesting--optimization)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Version History](#version-history)

## Overview

Jamso AI BOT is an advanced trading strategy implemented in Pine Script for TradingView. It combines machine learning techniques with traditional technical analysis to provide adaptive trading signals based on market volatility regimes. The core of the strategy is an enhanced SuperTrend indicator that dynamically adjusts its parameters based on market conditions.

The strategy features K-means clustering to identify market volatility regimes, adaptive risk management, and comprehensive performance tracking. It's designed to work across multiple asset classes including forex, crypto, stocks, and futures.

## Key Features

- **Enhanced SuperTrend Algorithm**: Adapts to changing market conditions
- **K-Means Clustering**: Identifies high, medium, and low volatility regimes
- **Adaptive Risk Management**: Dynamically adjusts position sizing based on performance
- **Profit Protection**: Reduces risk during drawdowns and increases during profitable periods
- **Multiple Asset Support**: Works on forex, crypto, stocks, commodities, and futures
- **Visual Dashboard**: Real-time performance metrics and trade information
- **Comprehensive Alerts**: Webhook integration for automated trading
- **Backtesting Framework**: Integrates with TradingView's strategy tester

## How It Works

The Jamso AI BOT operates through several key components:

1. **Market Regime Detection**: Uses K-means clustering to categorize market conditions into high, medium, or low volatility regimes
2. **Adaptive SuperTrend**: Adjusts factor and ATR length based on the detected market regime
3. **Entry/Exit Signals**: Generates signals based on SuperTrend crossovers
4. **Dynamic Risk Management**: Calculates position size based on account equity, market volatility, and historical performance
5. **Performance Tracking**: Monitors win rate, drawdown, and profit factor to inform risk management

The strategy also features unique trade identifiers (UUIDs) for each position, enabling accurate tracking and management of trades across multiple timeframes and assets.

## Installation

1. Copy the Pine Script code from `Jamso_AI_BOT.pine`
2. In TradingView, open a chart and click on "Pine Editor" (bottom toolbar)
3. Paste the code and click "Save" 
4. Click "Add to Chart" to apply the strategy
5. Configure parameters in the strategy settings

## Strategy Parameters

### Date Range Settings
- **Start/End Year/Month/Day**: Define the backtesting period
- **Enable Date Filter**: Toggle backtesting period filter

### Appearance Settings
- **Transparency 1 & 2**: Control the transparency of chart elements
- **Bullish/Bearish Color**: Customize colors for long and short signals

### SuperTrend Settings
- **ATR Length**: Lookback period for ATR calculation (default: 10)
- **SuperTrend Factor**: Multiplier for SuperTrend bands (default: 2.8)
- **Optimize SuperTrend Factor**: Enable dynamic factor adjustment
- **Adaptive Parameters**: When enabled, automatically adjusts parameters based on volatility regime

### K-Means Settings
- **Training Data Length**: Number of bars for clustering (default: 100)
- **Initial Volatility Percentile Guesses**: Starting points for clustering
- **Regime Change Threshold**: Minimum confidence required to switch regimes (prevents rapid switching)

### Risk Management
- **Risk % of Capital**: Percentage of capital risked per trade (default: 1%)
- **Maximum Risk %**: Upper limit for adaptive risk (default: 5%)
- **Trading Direction Bias**: Filter for long, short, or both directions
- **Stop Loss Type**: Choose between fixed percentage or ATR-based stops
- **Stop Loss %**: Define exit level as percentage of entry (for fixed mode)
- **Stop Loss ATR Multiplier**: Define stop loss distance in ATR units (for ATR mode)
- **Take Profit %**: Define profit target as percentage of entry
- **Maximum Contracts**: Limit position size regardless of account size
- **Sizing Method**: Choose between risk-based or fixed position sizing
- **Trailing Stop**: Enable dynamic stop loss that follows price
- **Profit Protection**: Reduce risk during drawdowns

### Alert Configuration
- **Enable Trade Alerts**: Toggle alerts for entries and exits
- **Enable Trend Alerts**: Toggle alerts for trend changes (SuperTrend crosses)
- **Enable Volatility Alerts**: Toggle alerts for volatility regime changes
- **Enable Debug Alerts**: Add additional information to alert messages

### Table Display
- **Show Tables**: Master switch to enable/disable all tables
- **Show Performance Table**: Toggle the performance metrics table
- **Show Trades Table**: Toggle the active trades table
- **Show ATR Table**: Toggle the volatility clustering table
- **Memory-Efficient Table Mode**: Simplified tables with less information

## Trading Logic

### Entry Conditions
- **Long Entry**: When SuperTrend line crosses below price (dir changes from 1 to -1)
- **Short Entry**: When SuperTrend line crosses above price (dir changes from -1 to 1)

Entry signals are validated with `barstate.isconfirmed` to avoid false signals on incomplete bars.

### Exit Conditions
- **Take Profit**: Fixed percentage from entry (adjusts with market volatility)
- **Stop Loss Options**:
  - **Fixed Percentage**: Traditional stop loss at a set percentage from entry
  - **ATR-Based**: Dynamic stop distance based on market volatility (ATR)
  - Both stop types adjust automatically with market volatility regimes
- **Trailing Stop**: Optional moving stop that follows price at a defined distance

### Signal Confirmation
- **Volume Filter**: Optional filter to confirm signals with above-average volume
- **RSI Filter**: Optional confirmation using RSI divergence or extreme values
- **Time-of-Day Filter**: Option to avoid trading during specific market sessions
- **News Filter**: Option to avoid trading around major economic releases

## Volatility Clustering

The strategy employs K-means clustering to categorize market conditions:

1. Collects ATR values for the specified training period
2. Initializes cluster centroids at defined percentiles (high, medium, low)
3. Assigns each ATR value to the nearest centroid
4. Recalculates centroids based on cluster members
5. Repeats until convergence or maximum iterations
6. Classifies current market conditions based on distance to each centroid

The identified regime then influences:
- SuperTrend parameters (automatically adjusts ATR length and factor)
- Risk management decisions (smaller position sizes in high volatility)
- Stop loss and take profit distances (wider in high volatility)
- Trailing stop parameters (looser in high volatility)

### Volatility Regimes Explained

- **Low Volatility Regime**:
  - Tighter SuperTrend parameters (lower factor, shorter ATR)
  - Smaller stop loss distances
  - Higher position sizes
  - Closer take profit targets
  - Best for ranging or slow-trending markets

- **Medium Volatility Regime**:
  - Balanced SuperTrend parameters
  - Moderate stop loss distances
  - Standard position sizes
  - Standard take profit targets
  - Suitable for most market conditions

- **High Volatility Regime**:
  - Looser SuperTrend parameters (higher factor, longer ATR)
  - Wider stop loss distances
  - Smaller position sizes
  - Further take profit targets
  - Designed for choppy or news-driven markets

### Regime Transition Management
To prevent excessive regime switching, the strategy implements:
- Confidence thresholds that must be met before switching regimes
- Transition periods where parameters gradually adjust between regimes
- Historical regime tracking to identify patterns and predict transitions

## Risk Management

The strategy implements several layers of risk management:

### Position Sizing
- Calculates position size as a percentage of equity based on risk tolerance
- Adjusts position size based on market volatility (smaller in high volatility)
- Limits maximum position size based on account leverage and max contracts setting

### Adaptive Risk
- Tracks win/loss performance
- Increases risk percentage after consecutive wins
- Decreases risk percentage after consecutive losses
- Maintains risk within defined minimum and maximum bounds

### Profit Protection
- Reduces position size during drawdowns to protect capital
- Increases position size during profitable periods to maximize returns
- Adjusts allocation based on equity curve gradient

### Advanced Risk Controls

- **Maximum Drawdown Limit**: Automatically pauses trading when a specific drawdown percentage is reached
- **Safety Pause**: Stops opening new positions during severe market conditions
- **Drawdown Recovery**: Automatically resumes trading when drawdown improves by 20%
- **Position Size Scaling**: Reduces trade size during drawdowns to preserve capital
- **Maximum Open Positions**: Limits the number of concurrent trades
- **Correlation Control**: Avoids excessive exposure to correlated assets

## Performance Tracking

The strategy provides comprehensive performance metrics through an on-chart table:

- **Equity**: Current account value and percentage change
- **Drawdown**: Maximum peak-to-trough decline percentage
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Sharpe Ratio**: Risk-adjusted return (with higher values indicating better risk-adjusted performance)
- **Payoff Ratio**: Average win size divided by average loss size
- **Expectancy**: Average profit/loss per trade, considering win rate and payoff ratio
- **MAE/MFE Analysis**: Maximum adverse/favorable excursion statistics

Performance metrics are color-coded (green/yellow/red) for quick assessment.

## Alert System

The strategy includes comprehensive alerting capabilities with flexible configuration:

### Alert Categories
- **Trade Alerts**: Entry and exit signals with position details
- **Trend Alerts**: SuperTrend crossovers indicating trend changes
- **Volatility Alerts**: Notifications when market regime changes
- **Debug Alerts**: Additional information for system monitoring

### Alert Configuration
- **Frequency Control**: Limit alert frequency to prevent notification fatigue
- **Priority Settings**: Assign importance levels to different alert types
- **Customizable Messages**: Edit alert messages to include specific information

## Webhook Integration

Jamso AI BOT supports webhook integration for automated trading, sending detailed JSON payloads to external systems:

### Webhook Setup
1. In TradingView alert settings, enable "Webhook URL" option
2. Enter your server URL (e.g., `https://your-server.com/webhook`)
3. Configure alert conditions based on strategy signals
4. Set alert message format to "JSON"

### Webhook Payload Structure

```json
{
  "order_id": "Long_1687426800000_457",
  "ticker": "BTCUSD",
  "order_action": "BUY",
  "market_price": 30500.25,
  "stop_loss": 29475.50,
  "take_profit": 32550.75,
  "position_size": 0.5,
  "price": 30500.25,
  "spread_estimate": 0.12,
  "trailing_stop": true,
  "trailing_step_percent": 0.2,
  "trailing_offset": 61.0,
  "hedging_enabled": false,
  "volatility_regime": "medium",
  "X-Webhook-Token": "your_auth_token_here"
}
```

### Field Descriptions

- **order_id**: Unique identifier for the trade (format: Direction_Timestamp_Random)
- **ticker**: Trading instrument symbol (should match broker symbol)
- **order_action**: Type of order (BUY, SELL, CLOSE_BUY, CLOSE_SELL)
- **market_price**: Current price when signal generated
- **stop_loss**: Calculated stop loss level
- **take_profit**: Calculated take profit level
- **position_size**: Suggested position size based on risk parameters
- **price**: Entry price used for calculations
- **spread_estimate**: Current spread as percentage of price
- **trailing_stop**: Boolean indicating if trailing stop should be used
- **trailing_step_percent**: Percentage for trailing stop movement
- **trailing_offset**: Initial distance for trailing stop in points
- **hedging_enabled**: Whether hedging mode should be used
- **volatility_regime**: Current market regime (low, medium, high)
- **X-Webhook-Token**: Authentication token for webhook security

### Error Handling
The webhook system includes several safeguards:
- Automatic retry mechanism for failed webhooks
- Rate limiting to prevent excessive requests
- Failure logging for troubleshooting
- Alternative alert delivery methods as backup

## API Implementation

To implement Jamso AI BOT with your trading infrastructure:

### Basic Implementation Steps
1. Set up a webhook receiver endpoint in your backend
2. Authenticate incoming webhooks using the token
3. Parse the JSON payload
4. Validate trade parameters
5. Execute orders through your broker's API
6. Log transactions and maintain state

### Security Considerations
- Use HTTPS for all webhook communications
- Implement proper authentication and token validation
- Set up IP whitelisting for TradingView's servers
- Implement rate limiting to prevent abuse

### Sample Backend Implementation (Python Flask)

```python
from flask import Flask, request, jsonify
import json
import hmac
import hashlib

app = Flask(__name__)

# Your webhook token for authentication
WEBHOOK_TOKEN = "your_auth_token_here"

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    # Get the JSON data from the request
    data = request.json
    
    # Authenticate the request
    token = data.get('X-Webhook-Token')
    if not token or token != WEBHOOK_TOKEN:
        return jsonify({"status": "error", "message": "Invalid token"}), 401
    
    # Extract trading parameters
    order_id = data.get('order_id')
    ticker = data.get('ticker')
    order_action = data.get('order_action')
    position_size = data.get('position_size')
    stop_loss = data.get('stop_loss')
    take_profit = data.get('take_profit')
    trailing_stop = data.get('trailing_stop', False)
    
    # Execute trade through your broker API
    # broker_api.place_order(...)
    
    # Log the transaction
    # log_transaction(...)
    
    return jsonify({"status": "success", "message": "Order received", "order_id": order_id})

if __name__ == '__main__':
    app.run(ssl_context='adhoc', host='0.0.0.0', port=5000)
```

## Backtesting & Optimization

### Effective Backtesting Methodology

1. **Multiple Timeframes**: Test strategy on different timeframes to ensure robustness
2. **Multiple Assets**: Verify performance across different asset classes
3. **Out-of-Sample Testing**: Use different date ranges for optimization and validation
4. **Monte Carlo Simulation**: Assess strategy robustness through randomized sampling
5. **Walk-Forward Analysis**: Progressive optimization through time to reduce curve-fitting

### Parameter Optimization

- **SuperTrend Factors**: Recommended ranges
  - Low volatility: 1.5-2.5
  - Medium volatility: 2.5-3.5
  - High volatility: 3.5-4.5

- **ATR Length**: Recommended ranges
  - Low volatility: 5-10
  - Medium volatility: 10-14
  - High volatility: 14-20

- **Risk Percentage**: Recommended to start low (0.5-1%) and gradually increase based on performance

### Performance Metrics

Focus optimization on these key metrics:
- **Risk-Adjusted Return** (Sharpe Ratio ≥ 1.0)
- **Maximum Drawdown** (≤ 20% ideally)
- **Win Rate** (Target ≥ 50%)
- **Profit Factor** (Target ≥ 1.5)
- **Expectancy** (Target ≥ 0.2R per trade)

## Best Practices

### Strategy Implementation
1. **Start Conservative**: Begin with lower risk percentages (0.5-1%) until familiar with strategy behavior
2. **Timeframe Selection**: Works best on 1h, 4h, and daily timeframes for most assets
3. **Asset Selection**: Choose liquid markets with reasonable spreads
4. **Adaptive Parameters**: Enable automatic parameter adjustments to handle different market conditions
5. **Use Multiple Instances**: Deploy across uncorrelated assets to improve overall performance

### Money Management
1. **Risk Consistency**: Maintain consistent risk per trade rather than position size
2. **Pyramiding**: Consider adding to winning positions in strong trends
3. **Scaling Out**: Take partial profits at different levels to secure gains
4. **Drawdown Management**: Have clear rules for reducing size during losing streaks
5. **Compounding**: Periodically adjust your capital base to account for profits

### Technical Implementation
1. **Alert Redundancy**: Set up multiple alert methods as backup
2. **Data Verification**: Implement checks to verify data accuracy
3. **Network Reliability**: Ensure your webhook server has high uptime
4. **Error Recovery**: Implement mechanisms to handle and recover from failures

## Troubleshooting

### Common Issues

#### Webhook Problems
- **Missing Alerts**: Verify TradingView alert settings and internet connection
- **Authentication Errors**: Check webhook token in alert message
- **Payload Parsing Issues**: Verify JSON format is correct

#### Strategy Issues
- **No Signals**: Ensure SuperTrend factor isn't too high for the asset's volatility
- **Excessive Trading**: Try increasing SuperTrend factor or ATR length
- **Poor Performance**: Check if the strategy is suitable for current market conditions
- **Table Not Visible**: Adjust chart size or move tables to different positions

#### Optimization Problems
- **Overfitting**: Too many parameters optimized for a specific period
- **Inconsistent Results**: Strategy may not be robust across different conditions
- **Resource Limitations**: Reduce complexity for better performance

### Solutions to Common Problems

- **Signals Occur Late**: Decrease the ATR length and SuperTrend factor
- **Too Many False Signals**: Increase the ATR length and SuperTrend factor
- **Stop Losses Too Tight**: Increase the stop loss percentage or ATR multiplier
- **Stop Losses Too Wide**: Decrease the stop loss percentage or ATR multiplier
- **Performance Degradation**: Re-optimize for current market conditions
- **Memory/CPU Issues**: Enable memory-efficient mode or reduce history length

## Version History

- **v1.0.0** - Initial release
- **v1.1.0** - Added K-means clustering for volatility regimes
- **v1.2.0** - Implemented adaptive risk management
- **v1.3.0** - Added performance visualization tables
- **v1.4.0** - Enhanced webhook alert system with UUIDs
- **v1.5.0** - Improved visibility of data tables and UI elements
- **v1.6.0** - Added ATR-based stop losses and enhanced UUID generation
- **v1.7.0** - Implemented configurable alerts and memory-efficient table modes
- **v1.8.0** - Added correlation control and maximum drawdown protection
- **v1.9.0** - Improved regime transition with confidence thresholds
- **v2.0.0** - Complete overhaul with enhanced backtesting capabilities

---

© 2023 Jamso AI BOT | All Rights Reserved