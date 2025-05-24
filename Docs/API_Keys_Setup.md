# API Keys Setup Guide for Market Intelligence Module

The Market Intelligence module requires valid API keys from several external services to function properly. This document explains how to obtain these keys and set them up correctly.

## Required API Keys

### 1. Alpha Vantage
Alpha Vantage provides market data and financial indicators API.

**How to Obtain:**
1. Visit [Alpha Vantage API Key Registration](https://www.alphavantage.co/support/#api-key)
2. Fill out the form to receive a free API key
3. Copy the API key

### 2. Finnhub
Finnhub provides real-time RESTful APIs for stocks, forex, and cryptocurrency.

**How to Obtain:**
1. Visit [Finnhub Registration Page](https://finnhub.io/register)
2. Create a free account
3. Navigate to your dashboard to get your API key

### 3. OpenAI
OpenAI API is used for advanced sentiment analysis and report generation.

**How to Obtain:**
1. Visit [OpenAI Platform](https://platform.openai.com/signup)
2. Create an account (if you don't already have one)
3. Navigate to the [API Keys section](https://platform.openai.com/account/api-keys)
4. Create a new secret key

## Setting Up API Keys

Once you have obtained the necessary API keys, you need to add them to your environment configuration:

1. Edit the `src/Credentials/env.sh` file:

```bash
# Market Intelligence API keys
export ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_KEY"
export FINNHUB_API_KEY="YOUR_FINNHUB_KEY"

# OpenAI API for advanced sentiment analysis
export OPENAI_API_KEY="YOUR_OPENAI_KEY"

# Feature flags
export ENABLE_AI_ANALYSIS="true"
export ENABLE_NEWS_SENTIMENT="true"
export ENABLE_TELEGRAM_NOTIFICATIONS="true"
```

2. Source the updated environment file:

```bash
source src/Credentials/env.sh
```

## API Key Limits and Usage Notes

### Alpha Vantage
- Free tier: 5 API requests per minute, 500 requests per day
- Consider upgrading for production use

### Finnhub
- Free tier: 60 API calls per minute
- More data available with premium subscriptions

### OpenAI
- Pay-as-you-go model based on tokens used
- Set up usage limits in OpenAI dashboard to control costs
- Different models have different pricing (gpt-3.5-turbo is more cost-effective than gpt-4)

## Verifying API Key Setup

To verify your API keys are configured correctly:

```bash
# Run the news fetching test
python Tests/Integration/test_market_intelligence.py --news

# Run the sentiment analysis test
python Tests/Integration/test_market_intelligence.py --sentiment
```

If the tests pass without API errors, your keys are correctly configured.
