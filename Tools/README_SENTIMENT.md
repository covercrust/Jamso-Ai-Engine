# Sentiment Data Tools for Jamso AI Engine

This directory contains tools to generate and manage sentiment data for cryptocurrency pairs used by the Jamso AI Engine trading strategies.

## Available Scripts

### 1. `capital_sentiment_import.py`

Imports sentiment data from the Capital.com API and combines it with model-generated historical data.

```bash
python3 capital_sentiment_import.py [options]
```

Options:
- `--symbols SYMBOLS`: Comma-separated list of symbols (default: BTCUSD,ETHUSD)
- `--days DAYS`: Number of days for historical data backfill (default: 90)
- `--output OUTPUT`: Output file path (default: src/Database/Sentiment/sentiment_data.json)
- `--verbose`: Enable verbose output
- `--model-only`: Use only the model without trying to connect to Capital.com API
- `--credentials-db PATH`: Path to credentials database (optional)
- `--force`: Force overwrite of existing sentiment data

### 2. `btcusd_sentiment.py`

Creates realistic sentiment data for cryptocurrency pairs based on a model with configurable parameters.

```bash
python3 btcusd_sentiment.py
```

### 3. `update_sentiment_daily.sh`

A shell script designed to be run from a cron job that updates sentiment data daily.

```bash
# Add to crontab to run daily at 1:00 AM
0 1 * * * /home/jamso-ai-server/Jamso-Ai-Engine/Tools/update_sentiment_daily.sh
```

## Data Format

The sentiment data is stored in JSON format with the following structure:

```json
{
  "BTCUSD": {
    "2025-05-20 12:00:00": 0.25,
    "2025-05-20 13:00:00": 0.27,
    ...
  },
  "ETHUSD": {
    "2025-05-20 12:00:00": 0.31,
    "2025-05-20 13:00:00": 0.29,
    ...
  }
}
```

Each symbol has a dictionary mapping timestamp strings to sentiment values. Sentiment values range from -1.0 (extremely bearish) to +1.0 (extremely bullish), with 0.0 being neutral.

## Integration with Trading Strategies

The sentiment data is used by the Capital.com API optimizer in the Jamso AI Engine to enhance trading decisions. When sentiment data is available, the optimizer can:

1. Filter or qualify trades based on market sentiment
2. Adjust position sizing based on sentiment strength
3. Modify entry and exit parameters in trending markets

## Troubleshooting

If you encounter issues with the Capital.com API credentials:

1. Ensure the credentials are properly stored in the credentials database
2. Check that your API key has the necessary permissions
3. Use the `--model-only` flag to generate data without accessing the API
4. Check the logs in `Logs/sentiment_updates.log` for error messages

For any persistent issues, contact the system administrator.
