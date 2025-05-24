# Jamso-AI-Engine Backtesting System

This directory contains tools for backtesting trading strategies, analyzing performance, and optimizing strategy parameters.

## Quick Start

### Running a Backtest

To run a backtest using the SuperTrend strategy:

```bash
python run_backtest.py --strategy supertrend --symbol EURUSD --from 2024-01-01 --to 2024-04-30 --plot
```

If you don't have data in your database, you can use synthetic sample data:

```bash
python run_backtest.py --strategy supertrend --use-sample-data --plot
```

### Optimizing Strategy Parameters

To optimize parameters for better performance:

```bash
python parameter_optimizer.py --strategy supertrend --symbol EURUSD --objective sharpe --max-evals 50 --visualize
```

To use parallel processing for faster optimization:

```bash
python parameter_optimizer.py --strategy supertrend --use-sample-data --parallel --cores 4
```

## Key Components

### 1. Performance Monitor (`performance_monitor.py`)
Core class for running backtests and analyzing trading strategy performance.

### 2. Example Strategies (`example_strategies.py`)
Collection of trading strategies including SuperTrend (Python implementation of Pine Script).

### 3. Backtest Runner (`run_backtest.py`)
Command-line utility for running backtests with various parameters and data sources.

### 4. Parameter Optimizer (`parameter_optimizer.py`)
Advanced tool for finding optimal strategy parameters through grid search.

### 5. Utilities (`backtest_utils.py`)
Helper functions for loading data, saving results, and data preprocessing.

## Data Sources

The backtesting system can use data from multiple sources:

1. **Database**: Loads data from the built-in SQLite database
2. **CSV Files**: Import data from CSV files (see `sample_data_template.csv`)
3. **Synthetic Data**: Generate random price data for testing

## Example Commands

### Basic Backtest
```bash
python run_backtest.py --strategy supertrend --symbol EURUSD --verbose --plot
```

### Parameter Optimization
```bash
python parameter_optimizer.py --strategy supertrend --symbol EURUSD --params '{"fact": [2.0, 2.5, 3.0], "atr_len": [10, 14, 21]}'
```

### Using CSV Data
```bash
python run_backtest.py --strategy supertrend --csv path/to/your/data.csv --plot
```

### Saving & Loading Results
```bash
# Save backtest results
python run_backtest.py --strategy supertrend --use-sample-data --save-results my_backtest

# Load saved results
python run_backtest.py --load-results my_backtest.json --plot
```

## Performance Metrics

The system calculates and reports the following performance metrics:

- Total Return
- Max Drawdown
- Sharpe Ratio
- Win Rate
- Number of Trades

## Adding New Strategies

To add a new trading strategy:

1. Create your strategy function in `example_strategies.py` or a new file
2. Update `STRATEGIES` dictionary in `run_backtest.py` and `parameter_optimizer.py`
3. Add appropriate parameter configurations

## Requirements

- Python 3.7+
- pandas
- numpy
- matplotlib (for visualization)

## Questions and Support

Refer to the main Jamso-AI-Engine documentation for additional details and support.
