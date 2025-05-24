# AI Risk Parameters Configuration Guide

## Overview

This document provides detailed information on configuring the risk management parameters in the AI trading module. Proper configuration of these parameters is crucial for controlling trading risk and optimizing performance.

## Risk Manager Parameters

The `RiskManager` class accepts several parameters that control different aspects of risk management:

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `max_daily_risk` | 5.0 | Maximum percentage of account that can be risked in a single trading day | Higher values allow more trades but increase potential daily losses |
| `max_drawdown_threshold` | 20.0 | Maximum acceptable drawdown percentage before risk reduction is applied | Lower values provide stricter drawdown protection but may limit opportunities |
| `correlation_threshold` | 0.7 | Correlation coefficient threshold above which markets are considered correlated | Lower values reduce correlation risk but may limit diversification |

### Configuration Examples

#### Conservative Risk Profile

```python
risk_manager = RiskManager(
    max_daily_risk=3.0,            # Lower daily risk limit
    max_drawdown_threshold=10.0,   # Stricter drawdown protection
    correlation_threshold=0.5      # Stricter correlation threshold
)
```

#### Balanced Risk Profile

```python
risk_manager = RiskManager(
    max_daily_risk=5.0,            # Default daily risk
    max_drawdown_threshold=20.0,   # Default drawdown protection
    correlation_threshold=0.7      # Default correlation threshold
)
```

#### Aggressive Risk Profile

```python
risk_manager = RiskManager(
    max_daily_risk=8.0,            # Higher daily risk limit
    max_drawdown_threshold=30.0,   # More relaxed drawdown protection
    correlation_threshold=0.8      # More relaxed correlation threshold
)
```

## Position Sizer Parameters

The `AdaptivePositionSizer` class accepts parameters that control how position sizes are calculated:

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `base_risk_percent` | 1.0 | Base percentage of account to risk per trade | Higher values increase position sizes and potential profit/loss |
| `max_risk_percent` | 2.0 | Maximum percentage of account to risk per trade | Acts as a hard limit on position sizing |
| `min_risk_percent` | 0.5 | Minimum percentage of account to risk per trade | Ensures positions aren't sized too small |
| `max_position_size` | 5.0 | Maximum multiplier for position size | Prevents excessive position sizing in favorable conditions |

### Configuration Examples

#### Conservative Position Sizing

```python
position_sizer = AdaptivePositionSizer(
    base_risk_percent=0.5,     # Lower base risk
    max_risk_percent=1.0,      # Lower maximum risk
    min_risk_percent=0.25,     # Lower minimum risk
    max_position_size=3.0      # Lower maximum position size
)
```

#### Balanced Position Sizing

```python
position_sizer = AdaptivePositionSizer(
    base_risk_percent=1.0,     # Default base risk
    max_risk_percent=2.0,      # Default maximum risk
    min_risk_percent=0.5,      # Default minimum risk
    max_position_size=5.0      # Default maximum position size
)
```

#### Aggressive Position Sizing

```python
position_sizer = AdaptivePositionSizer(
    base_risk_percent=1.5,     # Higher base risk
    max_risk_percent=3.0,      # Higher maximum risk
    min_risk_percent=0.75,     # Higher minimum risk
    max_position_size=7.0      # Higher maximum position size
)
```

## Volatility Regime Detector Parameters

The `VolatilityRegimeDetector` class accepts parameters that control volatility regime detection:

| Parameter | Default | Description | Impact |
|-----------|---------|-------------|--------|
| `n_clusters` | 3 | Number of volatility regimes to detect | More clusters can capture more nuanced regimes but may be less stable |
| `lookback_days` | 60 | Number of days of historical data to analyze | Longer periods provide more stable regimes but slower adaptation |

### Configuration Examples

#### Short-Term Adaptive Configuration

```python
regime_detector = VolatilityRegimeDetector(
    n_clusters=4,          # More granular regime detection
    lookback_days=30       # Shorter lookback for faster adaptation
)
```

#### Balanced Configuration

```python
regime_detector = VolatilityRegimeDetector(
    n_clusters=3,          # Default number of regimes
    lookback_days=60       # Default lookback period
)
```

#### Long-Term Stable Configuration

```python
regime_detector = VolatilityRegimeDetector(
    n_clusters=2,          # Fewer regimes for stability
    lookback_days=90       # Longer lookback for more stability
)
```

## Environment Variables

All risk parameters can be configured using environment variables:

```bash
# Risk Manager parameters
export JAMSO_AI_RISK_MANAGER_MAX_DAILY_RISK=5.0
export JAMSO_AI_RISK_MANAGER_MAX_DRAWDOWN_THRESHOLD=20.0
export JAMSO_AI_RISK_MANAGER_CORRELATION_THRESHOLD=0.7

# Position Sizer parameters
export JAMSO_AI_POSITION_SIZER_BASE_RISK_PERCENT=1.0
export JAMSO_AI_POSITION_SIZER_MAX_RISK_PERCENT=2.0
export JAMSO_AI_POSITION_SIZER_MIN_RISK_PERCENT=0.5
export JAMSO_AI_POSITION_SIZER_MAX_POSITION_SIZE=5.0

# Regime Detector parameters
export JAMSO_AI_REGIME_DETECTOR_N_CLUSTERS=3
export JAMSO_AI_REGIME_DETECTOR_LOOKBACK_DAYS=60
```

## Configuration File

You can also configure parameters using a JSON configuration file:

```json
{
  "risk_manager": {
    "max_daily_risk": 5.0,
    "max_drawdown_threshold": 20.0,
    "correlation_threshold": 0.7
  },
  "position_sizer": {
    "base_risk_percent": 1.0,
    "max_risk_percent": 2.0,
    "min_risk_percent": 0.5,
    "max_position_size": 5.0
  },
  "regime_detector": {
    "n_clusters": 3,
    "lookback_days": 60
  }
}
```

To use this configuration:

```python
from src.AI.utils.config import AIConfigManager

# Initialize with configuration file
config = AIConfigManager('/path/to/config.json')

# Get risk manager configuration
risk_config = config.get('risk_manager')
risk_manager = RiskManager(
    max_daily_risk=risk_config.get('max_daily_risk', 5.0),
    max_drawdown_threshold=risk_config.get('max_drawdown_threshold', 20.0),
    correlation_threshold=risk_config.get('correlation_threshold', 0.7)
)
```

## Risk Parameter Optimization

For optimal results, risk parameters should be adjusted based on:

1. **Account size**: Smaller accounts may need more conservative settings
2. **Market conditions**: More volatile markets may require lower risk settings
3. **Trading strategy**: Some strategies perform better with different risk profiles
4. **Historical performance**: Parameters should be optimized based on backtesting results

### Parameter Optimization Process

1. Start with default parameters
2. Run backtests on historical data
3. Analyze performance metrics (Sharpe ratio, maximum drawdown, etc.)
4. Adjust parameters to optimize performance
5. Validate with out-of-sample testing
6. Monitor live performance and adjust as needed

## Parameter Optimization and Monitoring

### Using the Parameter Optimizer

The Jamso AI Engine now includes a dedicated parameter optimization tool that automates the search for optimal strategy parameters:

```bash
# Basic optimization
python src/AI/parameter_optimizer.py --strategy supertrend --symbol EURUSD

# Optimize for risk-adjusted returns
python src/AI/parameter_optimizer.py --objective risk_adjusted --symbol EURUSD

# Custom parameter search grid
python src/AI/parameter_optimizer.py --params '{"fact": [2.0, 2.5, 3.0], "sl_percent": [0.3, 0.5, 0.7]}'

# Parallel processing for faster optimization
python src/AI/parameter_optimizer.py --parallel --cores 4
```

### Optimization Objectives

The parameter optimizer supports multiple optimization objectives:

| Objective | Description | Use Case |
|-----------|-------------|----------|
| `sharpe` | Sharpe Ratio | Balanced risk/reward |
| `return` | Total Return | Maximum profitability |
| `calmar` | Return/Max Drawdown | Capital preservation |
| `win_rate` | Winning Trade Percentage | Psychological comfort |
| `risk_adjusted` | Custom risk-adjusted score | Conservative approach |

### Integration with Risk Management

- Use the `PerformanceMonitor` class to automate parameter optimization based on backtest results.
- Integrate optimization results into your risk management review process.
- Monitor live and historical performance using the dashboard analytics integration.
- Save optimization results to track parameter evolution over time.

### Validation Best Practices

1. Always validate optimized parameters on out-of-sample data
2. Compare performance across multiple market regimes
3. Use walk-forward testing to prevent overfitting
4. Start with small position sizes when deploying new parameters

See the API documentation for details on running optimizations and using the dashboard API.

## Market-Specific Risk Parameters

You can configure different risk parameters for different markets:

```python
# Example of market-specific risk settings
market_risk_settings = {
    'EURUSD': {
        'max_daily_risk': 3.0,  # More conservative for forex
        'correlation_threshold': 0.6
    },
    'BTCUSD': {
        'max_daily_risk': 2.0,  # Even more conservative for crypto
        'max_drawdown_threshold': 15.0
    },
    'US500': {
        'max_daily_risk': 4.0,  # Moderate for indices
        'correlation_threshold': 0.75
    }
}

# Apply market-specific settings in your trading logic
def get_risk_manager(symbol):
    """Get a risk manager with market-specific settings."""
    settings = market_risk_settings.get(symbol, {})
    return RiskManager(
        max_daily_risk=settings.get('max_daily_risk', 5.0),
        max_drawdown_threshold=settings.get('max_drawdown_threshold', 20.0),
        correlation_threshold=settings.get('correlation_threshold', 0.7)
    )
```

## Special Considerations

### High-Volatility Markets

For highly volatile markets like cryptocurrencies:

- Use lower `base_risk_percent` (0.5% or less)
- Lower `max_position_size` (3.0 or less)
- Use stricter `max_drawdown_threshold` (15% or less)
- Consider increasing `n_clusters` in regime detection (4 or 5)

### Low-Volatility Markets

For stable markets like major forex pairs or blue-chip stocks:

- Risk settings can be more relaxed
- Consider fewer regime clusters for stability
- Longer lookback periods may provide better results

### Correlation Management

- The `correlation_threshold` is particularly important for portfolios with similar instruments
- Lower thresholds are recommended when trading multiple pairs in the same asset class
- Higher thresholds can be used for truly diversified instruments

## Monitoring and Adjustment

Risk parameters should be reviewed and potentially adjusted:

1. After significant market regime changes
2. When account size changes significantly
3. After periods of unusual performance (good or bad)
4. At least quarterly as part of regular strategy review

### Key Monitoring Metrics

| Metric | Target | Action if Exceeded |
|--------|--------|-------------------|
| Daily loss | < `max_daily_risk` | Reduce position sizes or pause trading |
| Drawdown | < `max_drawdown_threshold` | Implement drawdown recovery plan |
| Correlation of open positions | < `correlation_threshold` | Reduce exposure to correlated markets |
| Position size vs. account | Within reasonable ratios | Adjust `base_risk_percent` |

## Conclusion

Proper configuration of risk parameters is essential for balancing trading opportunities with risk management. Start with conservative settings and gradually optimize based on performance data and trading goals. Regular monitoring and adjustment will ensure the AI trading system adapts to changing market conditions.
