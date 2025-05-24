# OpenAI API Integration Guide

This guide explains how to work with the OpenAI API in the Jamso AI Engine's Market Intelligence module.

## Current Implementation

The Market Intelligence module currently uses OpenAI API version 0.28.0, which uses the legacy API format. This document provides information on how to update to newer OpenAI client versions if needed.

## Compatibility Notes

- **Current Version:** 0.28.0 (Legacy API)
- **Latest Version:** 1.x+ (New API format)

## Updating to the Latest OpenAI Client (If Needed)

If you need to update to the newer OpenAI client (1.x+), you'll need to modify the API calls. Here's how:

### 1. Update the OpenAI Package

```bash
pip install openai --upgrade
```

### 2. Update the API Client Initialization

**Old Format (0.28.0):**
```python
import openai
openai.api_key = "your_api_key"
```

**New Format (1.x+):**
```python
from openai import OpenAI
client = OpenAI(api_key="your_api_key")
```

### 3. Update API Calls

#### Sentiment Analysis Call

**Old Format (0.28.0):**
```python
response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a financial sentiment analysis assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=500
)

result_text = response['choices'][0]['message']['content']
```

**New Format (1.x+):**
```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a financial sentiment analysis assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=500
)

result_text = response.choices[0].message.content
```

### 4. Files to Update

The following files need to be updated when upgrading:

1. `/home/jamso-ai-server/Jamso-Ai-Engine/src/MarketIntelligence/Sentiment/sentiment_analyzer.py` 
   - Update the API initialization and calls in `analyze_text_openai` method

2. `/home/jamso-ai-server/Jamso-Ai-Engine/src/MarketIntelligence/Reports/report_generator.py`
   - Update any OpenAI API calls

### 5. Testing the Updates

After updating the code, run the tests to verify everything works correctly:

```bash
python Tests/Integration/test_market_intelligence.py --sentiment
```

## Version Decision

For now, we're keeping the legacy version (0.28.0) as it's working well with our implementation. If we decide to upgrade, follow the guidelines above.

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference/introduction)
- [OpenAI Python Library GitHub](https://github.com/openai/openai-python)
