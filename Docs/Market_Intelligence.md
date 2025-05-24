# Market Intelligence Module

## Overview

The Market Intelligence module adds powerful financial data analysis capabilities to the Jamso AI Engine. It provides tools for fetching and analyzing market news, performing sentiment analysis, and generating comprehensive market reports.

## Features

- **News Fetching**: Retrieve the latest financial news from multiple sources
- **Sentiment Analysis**: Analyze the sentiment of market news using NLP and AI
- **Report Generation**: Create comprehensive market intelligence reports
- **Market Monitoring**: Real-time monitoring of market data and sentiment

## Installation

The Market Intelligence module is included in the main Jamso AI Engine installation. Make sure you have the following environment variables set in your `src/Credentials/env.sh` file:

```bash
# Market data API credentials
export ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_API_KEY"
export FINNHUB_API_KEY="YOUR_FINNHUB_API_KEY"

# OpenAI API credentials (for advanced sentiment analysis)
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

You'll need to sign up for free API keys at:
- [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- [Finnhub](https://finnhub.io/register)
- [OpenAI](https://platform.openai.com/signup) (optional, for advanced sentiment analysis)

## Usage

### From the Start Menu

You can access the Market Intelligence tools from the main start menu by selecting option 7.

```
./start.sh
```

Then select option 7 to access the Market Intelligence Tools submenu.

### Using the CLI Tool

The Market Intelligence module includes a command-line tool for generating reports and analyzing market data.

```bash
# Generate a market report
python Tools/market_intel.py report --symbols=SPY,QQQ,AAPL --format=html

# Get the latest market news
python Tools/market_intel.py news --count=10 --category=general --verbose

# Analyze market sentiment
python Tools/market_intel.py sentiment --symbols=TSLA,NVDA --days=5 --verbose

# Monitor the market in real-time
python Tools/market_intel.py monitor --symbols=SPY,DIA,QQQ --interval=30
```

### Using the Python API

You can also use the Market Intelligence modules directly in your Python code:

```python
from src.MarketIntelligence.News.news_fetcher import NewsFetcher
from src.MarketIntelligence.Sentiment.sentiment_analyzer import SentimentAnalyzer
from src.MarketIntelligence.Reports.report_generator import ReportGenerator

# Get market news
news_fetcher = NewsFetcher()
market_news = news_fetcher.get_market_news(category='general', count=10)

# Analyze sentiment
sentiment_analyzer = SentimentAnalyzer()
analyzed_news = sentiment_analyzer.analyze_news_batch(market_news)
market_sentiment = sentiment_analyzer.get_market_sentiment_summary(analyzed_news)

# Generate a report
report_generator = ReportGenerator()
report = report_generator.generate_daily_market_report(symbols=['SPY', 'QQQ'])
report_generator.export_report_to_html(report, filename='market_report.html')
```

## Testing

To run tests for the Market Intelligence module, use:

```bash
python Tests/Integration/test_market_intelligence.py
```

Or from the start menu, select option 6 (Run Tests), then option 3 (Market Intelligence tests).

## Configuration

The Market Intelligence module can be configured through environment variables:

- `ALPHA_VANTAGE_API_KEY`: API key for Alpha Vantage (required for some features)
- `FINNHUB_API_KEY`: API key for Finnhub (required for news features)
- `OPENAI_API_KEY`: API key for OpenAI (optional, enhances sentiment analysis)
- `ENABLE_AI_ANALYSIS`: Set to "true" to enable AI-powered analysis (default: true)
- `ENABLE_NEWS_SENTIMENT`: Set to "true" to enable news sentiment analysis (default: true)
