# Capital.com API Integration for Parameter Optimization

This module implements the Advanced Parameter Optimization Process (APOP) with Capital.com API integration for the Jamso-AI-Engine trading system. It enables backtesting, benchmarking, and parameter optimization for trading strategies using real market data.

## Features

- **Live Market Data**: Fetch real-time and historical data from Capital.com API
- **Sentiment Analysis**: Incorporate market sentiment into your trading strategies
- **Parameter Optimization**: Optimize strategy parameters using multiple objectives
- **Out-of-Sample Testing**: Validate optimization results on unseen data
- **Monte Carlo Simulations**: Test strategy robustness across different market conditions
- **Performance Dashboard**: Track optimization performance over time
- **Scheduled Optimization**: Automatically update parameters on a regular schedule
- **Degradation Monitoring**: Get alerts when parameter performance degrades

## Quick Start

1. **Set Up Environment Variables**

Create a `.env` file in the project root directory with your Capital.com API credentials:
```
# Capital.com API Credentials
CAPITAL_API_KEY=your_api_key
CAPITAL_API_LOGIN=your_login
CAPITAL_API_PASSWORD=your_password
```

2. **Install Dependencies**

```bash
# Run the setup script to install all required dependencies
./Tools/setup_capital_optimization.sh
```

3. **Optimize Parameters**

```bash
# Run optimization for BTCUSD on hourly timeframe
./Tools/run_capital_optimization.sh optimize --symbol BTCUSD --timeframe HOUR
```

3. **Visualize Results**

```bash
# Visualize the optimization results
./Tools/run_capital_optimization.sh visualize --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json
```

4. **Test Robustness**

```bash
# Test parameters on out-of-sample data
./Tools/run_capital_optimization.sh test --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json
```

## Available Scripts

The integration includes several Python scripts:

- **capital_data_optimizer.py**: Main optimization script with Capital.com data
- **visualize_capital_data.py**: Visualization tools for optimization results
- **test_optimized_params.py**: Out-of-sample testing and Monte Carlo simulations
- **scheduled_optimization.py**: Automated optimization scheduler
- **capital_api_utils.py**: Utility functions for working with Capital.com API

## Command Line Tool

The `run_capital_optimization.sh` script provides a simple command-line interface:

```
Usage: ./Tools/run_capital_optimization.sh [command] [options]

Commands:
  optimize         Run parameter optimization for a market
  visualize        Visualize optimization results
  test             Test optimized parameters on out-of-sample data
  schedule         Schedule regular optimization tasks
  dashboard        Generate a performance dashboard
  fetch-data       Fetch and save market data to CSV
  list-markets     List available market symbols
  help             Show this help information
```

## Configuration

The system can be configured by editing:

```
src/AI/config/capital_api_config.json
```

For email alerts, copy and edit:

```
src/Credentials/email_config.json.sample
```

## Documentation

For more detailed information, see:

- [Capital API Integration Guide](../../Docs/AI/Capital_API_Integration_Guide.md)

## Requirements

- Python 3.8+
- pandas, numpy, matplotlib
- hyperopt, scikit-learn
- Valid Capital.com API credentials

## License

This project is licensed under the terms of the license included with Jamso-AI-Engine.

## Troubleshooting

If you encounter issues with the Capital.com API integration, try the following solutions:

1. **Run the test script** to verify your installation:
   ```bash
   ./Tools/test_capital_integration.sh
   ```

2. **Check environment variable loading**:
   ```bash
   python src/AI/test_env_loading.py
   ```

3. **Manual dependency installation**:
   ```bash
   pip install python-dotenv requests pandas numpy matplotlib hyperopt scikit-learn tabulate
   ```

4. **Use fallback solutions**:
   - The system includes a simplified API client (`fallback_capital_api.py`) that works without complex dependencies
   - A standalone parameter optimizer (`optimizer_essentials.py`) that doesn't rely on other project components
   
5. **Check logs** for detailed error messages:
   ```bash
   tail -n 50 Logs/capital_optimization.log
   ```

## Fallback Solutions

The system includes multiple fallback mechanisms:

1. **Fallback API Client**: A simplified Capital.com API client that works without complex dependencies
2. **Essential Optimizer**: A standalone parameter optimizer that doesn't rely on other project components
3. **Automatic dotenv Installation**: The system attempts to install missing dependencies when possible
