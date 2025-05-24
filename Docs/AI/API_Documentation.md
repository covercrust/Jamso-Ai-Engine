# AI Trading Module API Documentation

## Overview

The AI Trading Module provides advanced trading capabilities through volatility regime detection, adaptive position sizing, and risk management. This document describes the API for integrating and extending the AI functionality.

## Core Components

### 1. Volatility Regime Detector

The `VolatilityRegimeDetector` identifies market states based on volatility patterns using K-means clustering.

```python
from src.AI import VolatilityRegimeDetector

# Initialize detector
detector = VolatilityRegimeDetector(
    n_clusters=3,              # Number of regimes to detect
    lookback_days=60,          # Days of historical data to analyze
    db_path='path/to/db.db'    # Database path
)

# Train model for a symbol
regime_id = detector.train('EURUSD')

# Get current regime information
regime_info = detector.get_current_regime('EURUSD')
print(f"Current regime: {regime_info['regime_id']} ({regime_info['volatility_level']})")
```

#### Key Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `train(symbol)` | Train regime detection model | `symbol`: Market symbol | Current regime ID (int) |
| `get_current_regime(symbol)` | Get current volatility regime | `symbol`: Market symbol | Dict with regime info |
| `_fetch_market_data(symbol)` | (Internal) Fetch historical data | `symbol`: Market symbol | DataFrame with market data |

### 2. Adaptive Position Sizer

The `AdaptivePositionSizer` dynamically adjusts position sizes based on market conditions and account metrics.

```python
from src.AI import AdaptivePositionSizer

# Initialize position sizer
position_sizer = AdaptivePositionSizer(
    base_risk_percent=1.0,     # Base risk percentage
    max_position_size=5.0,     # Maximum position size multiplier
    max_risk_percent=2.0,      # Maximum risk percentage
    min_risk_percent=0.5       # Minimum risk percentage
)

# Calculate position size
result = position_sizer.calculate_position_size(
    symbol='EURUSD',
    account_id=1,
    original_size=1.0,
    price=1.2345,
    stop_loss=1.2300
)

print(f"Adjusted size: {result['adjusted_size']}")
print(f"Adjustment factor: {result['total_adjustment_factor']}")
```

#### Key Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `calculate_position_size(symbol, account_id, original_size, price=None, stop_loss=None)` | Calculate adaptive position size | `symbol`: Market symbol<br>`account_id`: Account ID<br>`original_size`: Original position size<br>`price`: Entry price (optional)<br>`stop_loss`: Stop loss price (optional) | Dict with position sizing results |
| `_calculate_regime_adjustment(symbol, base_size)` | (Internal) Calculate regime-based adjustment | `symbol`: Market symbol<br>`base_size`: Base position size | Tuple of adjusted size and info dict |
| `_calculate_performance_adjustment(account_id, symbol, base_size)` | (Internal) Adjust based on recent performance | `account_id`: Account ID<br>`symbol`: Market symbol<br>`base_size`: Base position size | Tuple of adjusted size and info dict |

### 3. Risk Manager

The `RiskManager` provides advanced risk control and management capabilities.

```python
from src.AI import RiskManager

# Initialize risk manager
risk_manager = RiskManager(
    max_daily_risk=5.0,         # Maximum daily risk percentage
    max_drawdown_threshold=20.0, # Maximum allowed drawdown
    correlation_threshold=0.7    # Correlation threshold
)

# Evaluate trade risk
signal_data = {
    'ticker': 'EURUSD',
    'order_action': 'buy',
    'position_size': 1.0,
    'price': 1.2345,
    'stop_loss': 1.2300
}
result = risk_manager.evaluate_trade_risk(signal_data, account_id=1)

if result['status'] == 'APPROVED':
    print("Trade approved")
else:
    print(f"Trade rejected: {result['rejection_reason']}")

# Adjust stop loss for volatility
adjusted_stop = risk_manager.adjust_stop_loss(
    symbol='EURUSD',
    current_price=1.2345,
    stop_loss=1.2300,
    volatility_level='HIGH'
)
```

#### Key Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `evaluate_trade_risk(signal_data, account_id)` | Evaluate risk for a potential trade | `signal_data`: Trade signal dictionary<br>`account_id`: Account ID | Dict with risk evaluation results |
| `adjust_stop_loss(symbol, current_price, stop_loss, volatility_level=None)` | Adjust stop loss based on volatility | `symbol`: Market symbol<br>`current_price`: Current price<br>`stop_loss`: Original stop loss<br>`volatility_level`: Volatility level | Adjusted stop loss price |
| `get_daily_risk_used(account_id)` | Get daily risk already used | `account_id`: Account ID | Daily risk percentage used |

### 4. Market Data Collector

The `MarketDataCollector` gathers and stores market data for AI analysis.

```python
from src.AI import MarketDataCollector, create_default_collector

# Create collector with default symbols
collector = create_default_collector()

# Or specify custom symbols
collector = MarketDataCollector(
    symbols=['EURUSD', 'BTCUSD', 'US500'],
    lookback_days=120
)

# Collect historical data for all symbols
collector.collect_data_for_all_symbols()

# Get data summary
summary = collector.get_data_summary()
print(summary)

# Start scheduled collection
collector.start_scheduled_collection(schedule_time="00:00")
```

#### Key Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `collect_historical_data(symbol, days=None)` | Collect historical data for a symbol | `symbol`: Market symbol<br>`days`: Lookback days (optional) | Success status (bool) |
| `collect_data_for_all_symbols()` | Collect data for all configured symbols | None | None |
| `start_scheduled_collection(schedule_time="00:00")` | Start scheduled data collection | `schedule_time`: Daily collection time | None |
| `get_data_summary()` | Get summary of collected data | None | Dict with data summary |

### 5. AI Dashboard Integration 

The `AIDashboardIntegration` provides visualization and analytics for the AI components.

```python
from src.AI import AIDashboardIntegration

# Initialize dashboard integration
dashboard = AIDashboardIntegration()

# Get volatility regime summary
regimes = dashboard.get_volatility_regime_summary(symbol='EURUSD', days=30)

# Get position sizing history
sizing_history = dashboard.get_position_sizing_history(symbol='EURUSD', days=30)

# Get volatility chart data
chart_data = dashboard.get_volatility_chart_data('EURUSD', days=90)

# Get account performance metrics
performance = dashboard.get_account_performance_metrics(account_id=1, days=30)
```

#### Key Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `get_volatility_regime_summary(symbol=None, days=30)` | Get volatility regime summary | `symbol`: Market symbol (optional)<br>`days`: History days | List of regime summaries |
| `get_position_sizing_history(symbol=None, days=30)` | Get position sizing history | `symbol`: Market symbol (optional)<br>`days`: History days | List of position sizing records |
| `get_volatility_chart_data(symbol, days=90)` | Get volatility chart data | `symbol`: Market symbol<br>`days`: History days | Dict with chart data |
| `get_account_performance_metrics(account_id, days=30)` | Get account performance metrics | `account_id`: Account ID<br>`days`: History days | Dict with performance metrics |

## Advanced Performance Monitoring

### Automated Backtesting, Benchmarking, and Parameter Optimization

The AI module now includes advanced performance monitoring via the `PerformanceMonitor` class:

- **Automated Backtesting**: Run historical simulations of trading strategies and collect detailed metrics (Sharpe ratio, drawdown, win rate, etc.).
- **Benchmarking**: Compare multiple strategies or parameter sets side-by-side.
- **Parameter Optimization**: Search for optimal strategy parameters using grid/random search.
- **Dashboard Integration**: Results can be sent to the dashboard via the `/api/advanced_backtest` endpoint for real-time and historical analytics.

#### Example Usage

```python
from src.AI import PerformanceMonitor

def my_strategy(data, param1, param2):
    # ... implement strategy logic ...
    return trades_df, equity_curve_series

monitor = PerformanceMonitor(my_strategy, data, {'param1': 10, 'param2': 0.5})
result = monitor.run_backtest()
print(result.metrics)

# For dashboard integration:
payload = monitor.to_dashboard_payload()
```

#### API Endpoint

- `POST /dashboard/api/advanced_backtest`
  - Request JSON: `{ "strategy": "example_strategy", "params": {...}, "data": ... }`
  - Response: `{ "success": true, "result": { ...metrics and equity curve... } }`

See the Developer Guide for details on adding new strategies and using the benchmarking/optimization features.

## Utilities

### Caching

The AI module includes a caching system to improve performance for frequently called methods.

```python
from src.AI.utils.cache import cached, regime_cache

# Use the cached decorator with a cache instance
@cached(regime_cache, key_prefix='my_function')
def my_expensive_function(param1, param2):
    # Expensive computation
    return result
```

### Scripts

The AI module provides several scripts for automation:

1. **Data Collection**: `src/AI/scripts/collect_market_data.py`
   ```bash
   python3 src/AI/scripts/collect_market_data.py --symbols EURUSD,BTCUSD --days 60
   ```

2. **Regime Training**: `src/AI/scripts/train_regime_models.py`
   ```bash
   python3 src/AI/scripts/train_regime_models.py --symbols EURUSD,BTCUSD --clusters 4
   ```

3. **AI Module Testing**: `src/AI/scripts/test_ai_modules.py`
   ```bash
   python3 src/AI/scripts/test_ai_modules.py --component regime_detector
   ```

4. **Setup Script**: `src/AI/setup_ai_module.py`
   ```bash
   python3 src/AI/setup_ai_module.py --symbols EURUSD,BTCUSD,US500
   ```

## Database Schema

The AI module uses several tables in the SQLite database:

1. **market_volatility** - Stores market data for volatility analysis
2. **volatility_regimes** - Stores detected volatility regimes
3. **position_sizing** - Tracks position sizing adjustments
4. **risk_metrics** - Monitors risk levels across accounts
5. **market_correlations** - Tracks correlations between markets
6. **account_balances** - Monitors account equity and drawdowns

## Integration Example

Example of integrating with trading signals:

```python
from src.AI import VolatilityRegimeDetector, AdaptivePositionSizer, RiskManager

def process_trading_signal(signal_data, account_id):
    # 1. Detect volatility regime
    detector = VolatilityRegimeDetector()
    regime_info = detector.get_current_regime(signal_data['ticker'])
    
    # 2. Apply position sizing
    position_sizer = AdaptivePositionSizer()
    sizing_result = position_sizer.calculate_position_size(
        symbol=signal_data['ticker'],
        account_id=account_id,
        original_size=signal_data['position_size']
    )
    
    # 3. Apply risk management
    risk_manager = RiskManager()
    risk_evaluation = risk_manager.evaluate_trade_risk(signal_data, account_id)
    
    if risk_evaluation['status'] == 'REJECTED':
        return {
            'status': 'rejected',
            'reason': risk_evaluation['rejection_reason']
        }
        
    # 4. Update the trade signal with AI enhancements
    signal_data['position_size'] = sizing_result['adjusted_size']
    
    return {
        'status': 'approved',
        'enhanced_signal': signal_data,
        'regime_info': regime_info,
        'sizing_info': sizing_result
    }
```
