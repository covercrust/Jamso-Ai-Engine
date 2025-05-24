# Market Intelligence User Guide

This guide provides detailed instructions for using the Market Intelligence module in the Jamso AI Engine.

## Prerequisites

Before using the Market Intelligence features, ensure you have:

1. Set up API keys (see `/home/jamso-ai-server/Jamso-Ai-Engine/Docs/API_Keys_Setup.md`)
2. Sourced the environment file: `source src/Credentials/env.sh`

## Using the CLI Tool

The Market Intelligence module includes a powerful command-line interface (CLI) tool for quick access to its features.

### Command Structure

```
python Tools/market_intel.py <command> [options]
```

### Available Commands

1. **Report Generation**

   Generate comprehensive market intelligence reports:

   ```bash
   python Tools/market_intel.py report --symbols=AAPL,MSFT,GOOG --format=html --output=report.html
   ```

   Options:
   - `--symbols`: Comma-separated list of stock symbols to analyze (optional)
   - `--format`: Output format - html, json, or csv (default: html)
   - `--output`: Output file path (optional)

2. **News Fetching**

   Fetch the latest market news:

   ```bash
   python Tools/market_intel.py news --count=10 --category=general
   ```

   Options:
   - `--count`: Number of news items to retrieve (default: 10)
   - `--category`: News category - general, forex, crypto, or merger (default: general)
   - `--output`: Output file path for JSON export (optional)
   - `--verbose`: Show detailed information

3. **Sentiment Analysis**

   Analyze sentiment for specific symbols:

   ```bash
   python Tools/market_intel.py sentiment --symbols=AAPL,MSFT --days=7
   ```

   Options:
   - `--symbols`: Comma-separated list of stock symbols
   - `--days`: Number of days to look back for news (default: 7)
   - `--count`: Number of news items per symbol (default: 10)
   - `--output`: Output file path for JSON export (optional)
   - `--verbose`: Show detailed information

4. **Market Monitoring**

   Continuously monitor market data:

   ```bash
   python Tools/market_intel.py monitor --symbols=SPY,QQQ,DIA --interval=60
   ```

   Options:
   - `--symbols`: Comma-separated list of stock symbols to monitor (default: SPY, QQQ, DIA, IWM)
   - `--interval`: Update interval in seconds (default: 60)

## Using the Module in Python Code

You can also import and use the Market Intelligence module in your Python code:

```python
from src.MarketIntelligence.News.news_fetcher import NewsFetcher
from src.MarketIntelligence.Sentiment.sentiment_analyzer import SentimentAnalyzer
from src.MarketIntelligence.Reports.report_generator import ReportGenerator

# Fetch news
fetcher = NewsFetcher()
news = fetcher.get_market_news(count=5)

# Analyze sentiment
analyzer = SentimentAnalyzer()
sentiment = analyzer.analyze_text_basic("Markets rallied as earnings beat expectations")

# Generate a report
generator = ReportGenerator()
report = generator.generate_daily_market_report(symbols=["AAPL", "MSFT"])
```

## Troubleshooting

### API Key Issues

If you see errors like "401 Client Error: Unauthorized", check your API keys:

1. Verify you have valid keys in your `src/Credentials/env.sh` file
2. Make sure you've sourced the environment file: `source src/Credentials/env.sh`
3. Check if your API usage limits have been exceeded

### OpenAI API Issues

If you see errors related to OpenAI API:

1. Verify your OpenAI API key is valid
2. Check if you have sufficient credit in your OpenAI account
3. The module will fall back to basic sentiment analysis if OpenAI is unavailable

## Running Tests

To verify the Market Intelligence module is working correctly:

```bash
# Run all tests
python Tests/Integration/test_market_intelligence.py

# Run specific test groups
python Tests/Integration/test_market_intelligence.py --news
python Tests/Integration/test_market_intelligence.py --sentiment
python Tests/Integration/test_market_intelligence.py --reports
```
