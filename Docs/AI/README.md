# AI Trading Module Documentation

Welcome to the Jamso-AI-Engine AI Trading Module documentation. This module provides advanced AI-driven trading capabilities including volatility regime detection, adaptive position sizing, and risk management.

## Documentation Index

### Getting Started

- [API Documentation](API_Documentation.md) - Complete API reference for all AI components
- [Developer Guide](Developer_Guide.md) - Guide for extending and customizing the AI module
- [Risk Parameters Guide](Risk_Parameters_Guide.md) - Detailed configuration guide for risk management

### Architecture & Design

- [System Architecture Overview](../Architecture/System_Architecture.md) - Overall system architecture
- [AI Component Integration](../Architecture/Component_Diagram.md) - How AI components integrate with the system

### Tutorials & Examples

- [Basic Usage Example](#basic-usage-example)
- [Configuration Example](#configuration-example)

---

## Quick Start

### Installation

The AI module is included in the Jamso-AI-Engine. To ensure all dependencies are installed:

```bash
cd /home/jamso-ai-server/Jamso-Ai-Engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Setup

Run the setup script to initialize the AI environment:

```bash
python3 src/AI/setup_ai_module.py
```

### Data Collection

Start collecting market data for AI analysis:

```bash
python3 src/AI/scripts/collect_market_data.py
```

### Scheduled Tasks

Set up daily data collection and model training:

```bash
bash Tools/setup_ai_cron.sh
```

## Basic Usage Example

```python
from src.AI import VolatilityRegimeDetector, AdaptivePositionSizer, RiskManager

# 1. Detect volatility regime
detector = VolatilityRegimeDetector()
regime_info = detector.get_current_regime('EURUSD')
print(f"Current regime: {regime_info['regime_id']} ({regime_info['volatility_level']})")

# 2. Calculate position size
position_sizer = AdaptivePositionSizer()
sizing_result = position_sizer.calculate_position_size(
    symbol='EURUSD',
    account_id=1,
    original_size=1.0
)
print(f"Adjusted size: {sizing_result['adjusted_size']}")

# 3. Evaluate trade risk
risk_manager = RiskManager()
signal_data = {
    'ticker': 'EURUSD',
    'order_action': 'buy',
    'position_size': sizing_result['adjusted_size'],
    'price': 1.2345,
    'stop_loss': 1.2300
}
risk_result = risk_manager.evaluate_trade_risk(signal_data, account_id=1)

if risk_result['status'] == 'APPROVED':
    print("Trade approved")
else:
    print(f"Trade rejected: {risk_result['rejection_reason']}")
```

## Configuration Example

```json
{
  "risk_manager": {
    "max_daily_risk": 3.0,
    "max_drawdown_threshold": 15.0,
    "correlation_threshold": 0.6
  },
  "position_sizer": {
    "base_risk_percent": 0.8,
    "max_risk_percent": 1.5,
    "min_risk_percent": 0.4,
    "max_position_size": 4.0
  },
  "regime_detector": {
    "n_clusters": 3,
    "lookback_days": 60
  }
}
```

Save this as `config.json` and load it with:

```python
from src.AI.utils.config import AIConfigManager

config = AIConfigManager('config.json')
```

## Advanced Backtesting & Performance Optimization

### Comprehensive Backtesting System

The Jamso AI Engine now includes a powerful backtesting system for strategy evaluation and optimization:

```bash
# Run basic backtest
python src/AI/run_backtest.py --strategy supertrend --symbol EURUSD --plot

# Use synthetic data when real data unavailable
python src/AI/run_backtest.py --use-sample-data --days 365

# Find optimal parameters
python src/AI/parameter_optimizer.py --strategy supertrend --objective sharpe

# Run multiple strategy comparisons
./src/AI/scripts/run_comparison_backtests.sh
```

For detailed instructions, see the [Backtesting README](/home/jamso-ai-server/Jamso-Ai-Engine/src/AI/BACKTEST_README.md).

### Parameter Optimization

The new parameter optimization utilities help find the best strategy settings:

- Grid search across parameter spaces
- Multiple optimization objectives (Sharpe, return, drawdown, etc.)
- Visualization of parameter sensitivity
- Parallel processing for faster results

### Dashboard Integration

The dashboard and analytics pipeline can display advanced backtest and benchmarking results:

- Use the `/dashboard/api/advanced_backtest` endpoint to run and visualize strategy backtests
- Display metrics such as Sharpe ratio, drawdown, win rate, and parameter optimization results
- See `src/AI/performance_monitor.py` for details on available metrics and payload format

To add new visualizations, extend the analytics frontend to consume the new API and display the returned metrics and equity curves.

## Support

For issues or questions about the AI trading module, please contact the development team or open an issue in the project repository.
