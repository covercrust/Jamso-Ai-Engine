# AI Trading Module

This directory contains the AI-driven trading module for the Jamso-AI-Engine. The module provides advanced trading capabilities through volatility regime detection, adaptive position sizing, and risk management.

## Directory Structure

```
src/AI/
├── __init__.py                # Module exports
├── regime_detector.py         # Volatility regime detection using K-means clustering
├── position_sizer.py          # Adaptive position sizing based on market conditions
├── risk_manager.py            # Advanced risk management with drawdown protection
├── data_collector.py          # Market data collection for AI analysis
├── dashboard_integration.py   # Dashboard integration for visualization
├── setup_ai_module.py         # Setup script for the AI module
├── models/                    # Machine learning models
├── indicators/                # Technical indicators for market analysis
├── utils/                     # Utility functions and classes
│   ├── __init__.py
│   └── cache.py               # Caching system for performance optimization
└── scripts/                   # Automation scripts
    ├── collect_market_data.py # Script for collecting market data
    ├── train_regime_models.py # Script for training volatility regime models
    └── test_ai_modules.py     # Testing framework for AI components
```

## Key Components

1. **VolatilityRegimeDetector**: Identifies market states using K-means clustering
2. **AdaptivePositionSizer**: Dynamically adjusts position sizes based on market conditions
3. **RiskManager**: Controls trading risk with various risk metrics
4. **MarketDataCollector**: Gathers and stores market data for analysis

## Getting Started

1. **Setup the module**:
   ```bash
   python3 src/AI/setup_ai_module.py
   ```

2. **Collect market data**:
   ```bash
   python3 src/AI/scripts/collect_market_data.py
   ```

3. **Train regime models**:
   ```bash
   python3 src/AI/scripts/train_regime_models.py
   ```

4. **Run tests**:
   ```bash
   python3 src/AI/scripts/test_ai_modules.py
   ```

5. **Setup scheduled tasks**:
   ```bash
   bash Tools/setup_ai_cron.sh
   ```

## Documentation

For detailed documentation, refer to:

- [API Documentation](/Docs/AI/API_Documentation.md)
- [Developer Guide](/Docs/AI/Developer_Guide.md)
- [Risk Parameters Guide](/Docs/AI/Risk_Parameters_Guide.md)
- [Documentation Index](/Docs/AI/README.md)

## Integration

The AI module integrates with the trading webhook flow via the `apply_ai_trading_logic()` function in `src/Webhook/utils.py`. This function applies AI-driven trading enhancements to incoming trading signals.

## Dependencies

- scikit-learn
- numpy
- pandas
- matplotlib
- schedule (for scheduled data collection)
- sqlite3 (included in Python standard library)

These dependencies are included in the project's `requirements.txt` file.
