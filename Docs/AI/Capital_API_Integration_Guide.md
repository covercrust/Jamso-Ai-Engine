# Advanced Parameter Optimization Process (APOP) with Capital.com Integration

## Overview

The Advanced Parameter Optimization Process (APOP) integrates with Capital.com's API to provide real-time market data for optimizing trading strategy parameters. This document explains how to use the APOP system with Capital.com data, including setup, configuration, running optimizations, and interpreting results.

## Key Features

- **Real Market Data**: Uses Capital.com API to fetch historical price data for optimization
- **Sentiment Analysis**: Incorporates market sentiment data into the optimization process
- **Robust Evaluation**: Includes out-of-sample testing and Monte Carlo simulations
- **Scheduled Optimization**: Automatically updates parameters on a regular schedule
- **Performance Monitoring**: Tracks parameter performance over time and alerts on degradation
- **Visual Analytics**: Provides visualization tools for strategy performance

## Setup Instructions

### Prerequisites

1. Valid Capital.com API credentials
2. Python 3.8+ with required packages

### Configuration

1. Ensure your Capital.com API credentials are set up in the credentials manager
2. Configure optimization settings in `src/AI/config/capital_api_config.json`

### Installation

If not already installed, run:

```bash
pip install pandas numpy matplotlib hyperopt scikit-learn tabulate
```

## Using the System

### Running a Single Optimization

To optimize parameters for a specific market:

```bash
python src/AI/capital_data_optimizer.py --symbol BTCUSD --timeframe HOUR --objective sharpe --days 30 --max-evals 20 --use-sentiment
```

Parameters:
- `--symbol`: Market symbol (e.g., BTCUSD, EURUSD)
- `--timeframe`: Candle timeframe (MINUTE, HOUR, DAY, etc.)
- `--objective`: Optimization objective (sharpe, return, risk_adjusted, win_rate)
- `--days`: Number of days of historical data to use
- `--max-evals`: Maximum number of parameter combinations to evaluate
- `--use-sentiment`: Include market sentiment data in optimization
- `--sentiment-weight`: Weight of sentiment data (0-1 range, default: 0.2)
- `--save-plot`: Save a visualization of the strategy performance
- `--output`: Custom output file path for the results

### Visualizing Optimization Results

To visualize results for an optimization:

```bash
python src/AI/visualize_capital_data.py --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json
```

For comparing multiple optimizations:

```bash
python src/AI/visualize_capital_data.py --compare --symbol BTCUSD --timeframe HOUR
```

### Out-of-Sample Testing

To test the robustness of optimized parameters:

```bash
python src/AI/test_optimized_params.py --params-file capital_com_optimized_params_BTCUSD_HOUR_sharpe.json --days 60
```

### Scheduled Optimization

To set up automated optimization that runs on a schedule:

```bash
python src/AI/scheduled_optimization.py --interval 24 --symbols BTCUSD,EURUSD --timeframes HOUR,DAY
```

To run as a background process:

```bash
nohup python src/AI/scheduled_optimization.py --daemon > optimization_log.txt 2>&1 &
```

## Understanding the Results

### Parameter Files

Optimization results are saved as JSON files with the following structure:

```json
{
    "params": {
        "fact": 3.2,
        "atr_len": 14,
        "risk_percent": 1.5,
        "sl_percent": 0.8,
        "tp_percent": 2.1
    },
    "metrics": {
        "total_return": 42.8,
        "sharpe_ratio": 2.1,
        "max_drawdown": 12.5,
        "win_rate": 65.2,
        "profit_factor": 2.4,
        "total_trades": 48
    },
    "metadata": {
        "symbol": "BTCUSD",
        "timeframe": "HOUR",
        "days": 30,
        "objective": "sharpe",
        "use_sentiment": true,
        "sentiment_weight": 0.2,
        "date": "2025-05-19 12:30:45",
        "max_evals": 20
    }
}
```

### Optimization Objectives

- **sharpe**: Maximizes Sharpe ratio (return adjusted for risk)
- **return**: Maximizes total return percentage
- **risk_adjusted**: Maximizes return divided by maximum drawdown
- **win_rate**: Maximizes percentage of winning trades
- **calmar**: Maximizes Calmar ratio (annualized return divided by maximum drawdown)

### Performance Metrics

- **Total Return**: Percentage profit/loss over the tested period
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Max Drawdown**: Maximum percentage decline from peak (lower is better)
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit divided by gross loss (higher is better)
- **Expectancy**: Average profit/loss per trade

### Robustness Assessment

Out-of-sample testing evaluates how well the strategy performs on unseen data:

- **Excellent**: Out-of-sample performance is 70%+ of in-sample
- **Good**: Out-of-sample performance is 30-70% of in-sample
- **Fair**: Out-of-sample performance is 0-30% of in-sample
- **Poor**: Out-of-sample performance is negative

Monte Carlo simulations test performance across many different market scenarios.

## Dashboard

The system generates a performance dashboard that helps track optimization results over time. To access it:

1. Generate the dashboard: `python src/AI/scheduled_optimization.py --dashboard-only`
2. Open the HTML file in `/home/jamso-ai-server/Jamso-Ai-Engine/dashboard/index.html`

## Troubleshooting

### API Connection Issues

If you encounter connection issues with Capital.com API:

1. Verify your API credentials are correct
2. Check your internet connection
3. Ensure you're not exceeding API rate limits
4. Try increasing the request timeout in configuration

### Optimization Problems

If optimization results are poor:

1. Try increasing `max-evals` for more thorough search
2. Use more historical data with `--days` parameter
3. Test different objectives to find what works for your market
4. Check if the market has enough volatility for the strategy

## Advanced Configuration

The system can be further customized by modifying:

- SuperTrend strategy implementation in `capital_data_optimizer.py`
- Sentiment integration weights and methods
- Monte Carlo simulation parameters
- Alert thresholds for parameter degradation

## Future Enhancements

Planned enhancements include:

1. Support for additional technical indicators
2. Integration with more data sources
3. Machine learning-based parameter prediction
4. Enhanced visualization dashboard
5. Real-time strategy monitoring

## Support

For issues or questions, please contact the Jamso-AI-Engine development team.
