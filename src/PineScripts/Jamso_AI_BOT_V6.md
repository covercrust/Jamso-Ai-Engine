# Jamso AI BOT V6 - Enhanced SuperTrend Trading Strategy

![Jamso AI BOT](https://via.placeholder.com/800x400?text=Jamso+AI+BOT+V6)

## Table of Contents

- [Overview](#overview)
- [PineScript V6 Enhancements](#pinescript-v6-enhancements)
- [Installation & Setup](#installation--setup)
- [Strategy Parameters](#strategy-parameters)
- [Trading Logic](#trading-logic)
- [Volatility Clustering](#volatility-clustering)
- [Risk Management](#risk-management)
- [Performance Tracking](#performance-tracking)
- [Alert System](#alert-system)
- [Webhook Integration](#webhook-integration)
- [Memory Optimization](#memory-optimization)
- [Backtesting & Optimization](#backtesting--optimization)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Version History](#version-history)

## Overview

Jamso AI BOT V6 represents a significant upgrade to our trading strategy, leveraging the advanced features available in Pine Script version 6. The strategy combines machine learning-based market regime detection with adaptive technical indicators to provide intelligent trading signals that adapt to changing market conditions.

The V6 implementation includes substantial improvements in performance, memory management, error handling, and user experience compared to previous versions. It's designed for serious traders who need a robust, optimized strategy capable of handling extensive backtesting and live trading across various asset classes.

## PineScript V6 Enhancements

This version takes full advantage of Pine Script V6 capabilities:

- **Improved Error Handling**: Try/catch blocks to prevent script failures during execution
- **String Templates**: f-strings for more readable code and alert message generation
- **Enhanced Array Functions**: Optimized array methods for faster clustering operations
- **Memory Management**: Optimized data structures with periodic cleanup to prevent memory errors
- **Type Declarations**: Explicit type definitions for better script stability
- **Optimized Table Handling**: Conditional table updates to reduce resource usage
- **Enhanced Array Functions**: Using new methods like `array.percentile_nearest_rank` for more accurate calculations

## Installation & Setup

1. **Import the Script**:
   - Copy the Pine Script code from `Jamso_AI_BOT_V6.pine`
   - In TradingView, navigate to Pine Editor (bottom toolbar)
   - Paste the code and click "Save"
   - Click "Add to Chart" to apply the strategy

2. **Initial Configuration**:
   - Configure strategy parameters based on your trading style and risk tolerance
   - Set appropriate alert conditions for trade entries and exits
   - Configure webhook URL in TradingView alerts for integration with external systems

3. **Webhook Integration Setup**:
   - The script generates structured JSON payloads for each trade signal
   - Configure your webhook server to receive and process these payloads
   - Test the connection before live trading

## Strategy Parameters

### Date Range Settings
- **Start/End Year/Month/Day**: Define backtesting period
- **Enable Date Filter**: Toggle date range filtering

### Appearance Settings
- **Transparency 1 & 2**: Control opacity of chart elements
- **Bullish/Bearish Color**: Customize color scheme
- **Custom Table Appearance**: Enhance table visualization
- **Table Positions**: Configure where each information table appears

### SuperTrend Settings
- **ATR Length**: Period for Average True Range calculation (default: 10)
- **SuperTrend Factor**: Multiplier for SuperTrend bands (default: 2.8)
- **Optimize SuperTrend Factor**: Dynamic factor adjustment based on recent volatility

### K-Means Settings
- **Training Data Length**: History length for volatility clustering (default: 100)
- **Initial Volatility Percentile Guesses**: Starting points for clustering algorithm
- **Memory-Efficient Mode**: Reduced computation for better performance

### Risk Management
- **Risk % of Capital**: Capital percentage risked per trade (default: 1%)
- **Maximum Risk %**: Upper limit for adaptive risk (default: 5%)
- **Adaptive Risk**: Dynamically adjust risk based on performance
- **Trading Direction Bias**: Filter for long, short or both directions
- **Stop Loss Configuration**: Choose between fixed percentage or ATR-based stops
- **Position Sizing Method**: Dynamic risk-based or fixed sizing
- **Trailing Stop**: Enable price-following stop loss with customizable step
- **Maximum Drawdown Limit**: Automatically pause trading at specified drawdown level
- **Profit Protection**: Adjust risk based on equity curve

### Alert Configuration
- **Enable Trade Alerts**: Entry and exit notifications
- **Enable Trend Alerts**: SuperTrend crossover notifications
- **Enable Volatility Alerts**: Market regime change notifications
- **Enable Debug Alerts**: Additional diagnostic information

### Table Display
- **Show Tables**: Toggle all information tables
- **Individual Table Toggles**: Control which tables are displayed
- **Memory-Efficient Table Mode**: Simplified displays for performance

## Trading Logic

### Signal Generation

The strategy generates signals based on SuperTrend crossovers with price:

- **Long Entry**: Generated when SuperTrend line crosses below price (direction changes from 1 to -1)
- **Short Entry**: Generated when SuperTrend line crosses above price (direction changes from -1 to 1)

All signals are validated with `barstate.isconfirmed` to prevent false signals on incomplete bars.

### Adaptive Parameters

A key improvement in V6 is the intelligent adaptation of strategy parameters:

1. **Market Regime Detection**: Identifies current volatility conditions as high, medium, or low
2. **SuperTrend Adjustment**: Automatically modifies ATR length and SuperTrend factor
3. **Position Sizing Adjustment**: Reduces size in high volatility, increases in low volatility
4. **Stop/Target Adjustment**: Widens stops in high volatility, tightens in low volatility

### Enhanced Entry/Exit Logic

```pine
// Long Entry Logic
if longCondition and is_in_date_range and not paused_by_drawdown
    // Close existing short position if hedging is disabled
    // Calculate stop loss and take profit levels
    // Apply position sizing based on risk management settings
    // Generate unique trade ID
    // Execute trade with proper risk parameters
    // Send webhook alert with comprehensive trade details
```

## Volatility Clustering

The V6 implementation features an enhanced K-means clustering algorithm for market regime detection:

### Clustering Process

1. **Data Collection**: Gathers ATR values over the specified training period
2. **Centroid Initialization**: Sets initial cluster centers at specified percentiles
3. **Iterative Refinement**: Performs intelligent assignment and recalculation of centroids
4. **Convergence Checking**: Stops iterating when centroids stabilize
5. **Regime Classification**: Identifies current bar's volatility regime based on distance to centroids

### Memory-Optimized Implementation

```pine
// Optimized K-means implementation with limited iterations
for iter = 0 to max_iterations - 1 by 1
    // Initialize clusters
    array.clear(hv)
    array.clear(mv)
    array.clear(lv)
    for i = 0 to array.size(volatility_array) - 1 by 1
        // Assign each data point to nearest centroid
        // ...
    
    // Store old centroid values to check convergence
    // Recalculate centroids for each cluster
    // Check convergence and break if stable
```

### Visual Feedback

The volatility regime is displayed through:
- Background color changes on the chart
- Highlighted rows in the ATR table
- Detailed cluster statistics in the information panel

## Risk Management

The V6 implementation features multi-layered risk management:

### Dynamic Position Sizing

- **Volatility-Based Adjustment**: Reduces position size in high volatility environments
- **Adaptive Risk**: Adjusts risk percentage based on recent win/loss performance
- **Equity-Based Scaling**: Increases position size as account grows
- **Maximum Drawdown Control**: Automatically pauses trading when drawdown exceeds threshold

### Advanced Stop Loss Mechanisms

- **Multiple Stop Types**: Choose between fixed percentage or ATR-multiple stops
- **Trailing Stops**: Dynamically follows price to lock in profits
- **Regime-Adjusted Stops**: Wider stops in volatile markets, tighter in calm markets

### Profit Protection

```pine
// Drawdown monitoring and position size adjustment
if profit_protection and drawdown_percent > 5
    position_size_multiplier := math.max(0.5, 1.0 - drawdown_percent / 100)
else if profit_protection and strategy.equity > strategy.initial_capital * 1.3
    // Increase size when doing well
    position_size_multiplier := math.min(1.5, 1.0 + (strategy.equity - strategy.initial_capital) / strategy.initial_capital * 0.2)
```

### Trading Pause Mechanism

The strategy includes an automatic trading pause feature when drawdown exceeds the user-defined threshold:

```pine
// Implement max drawdown control with hysteresis
if pause_trading_on_drawdown and drawdown_percent >= max_drawdown_limit
    paused_by_drawdown := true
    
// Reset pause when drawdown improves by 20%
if paused_by_drawdown and drawdown_percent < max_drawdown_limit * 0.8
    paused_by_drawdown := false
```

## Performance Tracking

The V6 implementation includes comprehensive performance metrics:

### Real-Time Statistics

- **Equity**: Current account value and percentage change
- **Drawdown**: Maximum peak-to-trough decline percentage
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Sharpe Ratio**: Risk-adjusted return calculation
- **Payoff Ratio**: Average win size divided by average loss size

### Visual Dashboard

Performance metrics are displayed in customizable tables with color-coding:
- Green for strong performance
- Yellow for moderate performance
- Red for weak performance

### Advanced Metrics Calculation

```pine
// Calculate Sharpe Ratio
calculate_sharpe_ratio() =>
    // Calculate daily returns
    daily_returns = strategy.equity / strategy.equity[1] - 1
    
    // Find average daily return and standard deviation
    avg_return = ta.sma(daily_returns, 252)
    std_dev = ta.stdev(daily_returns, 252)
    
    // Sharpe ratio calculation (using 0% as risk-free rate for simplicity)
    std_dev != 0 ? avg_return / std_dev * math.sqrt(252) : 0
```

## Alert System

The V6 implementation features a robust and configurable alert system:

### Alert Categories

- **Trade Alerts**: Entry and exit signals with position details
- **Trend Alerts**: SuperTrend crossovers indicating trend changes
- **Volatility Alerts**: Notifications when market regime changes
- **Debug Alerts**: Additional information for strategy monitoring

### Conditional Alert Function

```pine
// Function to send conditional alerts based on user configuration
send_conditional_alert(message, alert_type) =>
    should_send = switch alert_type
        'trade' => enable_trade_alerts
        'trend' => enable_trend_alerts
        'volatility' => enable_volatility_alerts
        => true // Default to true for other types
    
    if should_send
        alert(message, alert.freq_once_per_bar_close)
```

### Enhanced Alert Messages

Alert messages are now constructed using Pine Script V6's string concatenation for improved readability:

```pine
message = "{\n" +
          "  \"order_id\": \"" + orderId + "\",\n" +
          "  \"ticker\": \"" + ticker + "\",\n" +
          "  \"order_action\": \"" + action + "\",\n" +
          // ... additional fields
          "}"
```

## Webhook Integration

The V6 implementation includes enhanced webhook payloads for seamless integration with external systems:

### Payload Structure

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
  "X-Webhook-Token": "6a87cf683ac94bc7f83bc09ba643dc578538d4eb46c931a60dc4fe3ec3c159cd"
}
```

### Enhanced UUID Generation

The V6 implementation includes an improved unique identifier system:

```pine
// Optimized function using string concatenation
generateTradeId(isLong) =>
    timestamp = str.tostring(math.round(time))
    suffix = str.tostring(math.random(1, 1000))
    id = isLong ? "Long_" + timestamp + "_" + suffix : "Short_" + timestamp + "_" + suffix
    id
```

### Integration Example

To integrate with your trading infrastructure, set up a webhook receiver in your backend:

```python
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    # Get the JSON data from the request
    data = request.json
    
    # Authenticate the request
    token = data.get('X-Webhook-Token')
    if not token or token != "6a87cf683ac94bc7f83bc09ba643dc578538d4eb46c931a60dc4fe3ec3c159cd":
        return jsonify({"status": "error", "message": "Invalid token"}), 401
    
    # Process the trade signal
    order_id = data.get('order_id')
    ticker = data.get('ticker')
    order_action = data.get('order_action')
    market_price = data.get('market_price')
    stop_loss = data.get('stop_loss')
    take_profit = data.get('take_profit')
    position_size = data.get('position_size')
    
    # Execute the trade through your broker API
    # ...
    
    return jsonify({"status": "success", "message": "Order processed", "order_id": order_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Memory Optimization

The V6 implementation includes several memory optimization features:

### Array Management

```pine
// Memory management function
clean_arrays(arr, max_size) =>
    if array.size(arr) > max_size
        while array.size(arr) > max_size
            array.pop(arr)

// Periodic cleanup - called every 50 bars instead of every bar
if bar_index % 50 == 0
    clean_arrays(volatility_array, max_array_size)
    clean_arrays(hv, max_array_size / 3)
    clean_arrays(mv, max_array_size / 3)
    clean_arrays(lv, max_array_size / 3)
```

### Table Optimization

- **Conditional Updates**: Tables are only updated when values change
- **Clear Unused Resources**: Removes unnecessary data from memory
- **Memory-Efficient Mode**: Simplified tables with minimal information

### Reduced Computation

- **Limited K-means Iterations**: Maximum of 3 iterations to prevent excessive computation
- **Periodic Updates**: Heavy calculations are performed periodically rather than on every bar
- **Optimized Loop Structures**: Better for-loop designs to minimize memory usage

## Backtesting & Optimization

### Parameter Optimization Guidelines

- **SuperTrend Factor**: Test between 2.0-3.5 for most markets
- **ATR Length**: Test between 5-14 periods
- **Risk Percentage**: Start with 0.5-1% and increase gradually
- **Volatility Percentiles**: Adjust based on the specific asset's characteristics

### Recommended Testing Methodology

1. **Out-of-Sample Testing**: Optimize on one date range, validate on another
2. **Multi-Market Testing**: Verify performance across different asset classes
3. **Monte Carlo Analysis**: Assess strategy robustness with randomized testing
4. **Walk-Forward Analysis**: Progressive optimization to prevent curve-fitting

### Deep Backtest Mode

The V6 implementation includes a special "Deep Backtest" mode with optimized settings:

```pine
// Apply deep backtest optimizations
if use_deep_settings
    position_size_multiplier := position_size_multiplier * 1.5 // Higher position sizes in deep backtest
    // SuperTrend factor adjustment
    factor_to_use = use_deep_settings ? math.min(fact * 0.8, 2.5) : adjusted_factor
```

## Best Practices

### Strategy Implementation

1. **Start Conservative**: Begin with lower risk percentages (0.5-1%)
2. **Enable Adaptive Parameters**: Allow the strategy to adjust to different market conditions
3. **Setup Proper Alerts**: Configure alerts for all trading actions
4. **Backtest Thoroughly**: Test across multiple timeframes and market conditions
5. **Monitor Memory Usage**: Watch for performance issues during extended backtests

### Performance Optimization

1. **Use Memory-Efficient Mode**: Enable for long backtests or lower-end computers
2. **Reduce Training Data Length**: Lower values require less computation
3. **Disable Unused Tables**: Turn off tables you don't need to view
4. **Set Max Iterations**: Limit K-means iterations to 2-3 for most markets
5. **Periodic Calculations**: Use modulo operations to perform heavy calculations periodically

### Risk Management

1. **Enable Profit Protection**: Protects gains during drawdowns
2. **Set Maximum Drawdown Limit**: Prevents catastrophic losses
3. **Use Trailing Stops**: Helps capture more profit in trending markets
4. **Enable Adaptive Risk**: Scales position size based on performance
5. **Monitor Win Rate**: Adjust parameters if win rate falls below 40%

## Troubleshooting

### Common Issues

#### Memory Problems
- **Error**: "pine_script_runtime: out of memory"
- **Solution**: Enable memory-efficient table mode, reduce training data length, or clean arrays more frequently

#### Alert Issues
- **Problem**: Alerts not firing when expected
- **Solution**: Ensure the correct alert types are enabled in settings and `barstate.isconfirmed` is used

#### Performance Issues
- **Problem**: Strategy runs slowly on charts with extensive history
- **Solution**: Use memory optimization features, reduce table updates, limit iterations

#### Visual Artifacts
- **Problem**: Tables overlap or appear distorted
- **Solution**: Adjust table positions in settings or reduce information density

### Debugging Features

The V6 implementation includes enhanced debugging capabilities:

```pine
// Debugging Helper Function
debug_log(msg, color_code) =>
    if Enable_Debugging
        label.new(bar_index, high, msg, color = color_code, style = label.style_circle)
    else
        na // Return na when not debugging to ensure consistent return type
```

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
- **v2.1.0** - Upgraded to Pine Script v6 with improved memory management
- **v2.2.0** - Enhanced error handling and string template optimization
- **v2.3.0** - Added advanced performance metrics (Sharpe, Payoff Ratio)
- **v2.4.0** - Implemented memory optimization techniques for large datasets
- **v2.5.0** - Added customizable table positions and appearance settings

---

© 2025 Jamso AI BOT | All Rights Reserved
