#!/bin/bash
# Environment variables for Jamso AI Engine
# Generated from env.sh.template

# API Credentials
export CAPITAL_API_KEY="GLvPQvsyZ8n8BlOU"
export CAPITAL_API_PASSWORD="Jamso@colopio@2025"
export CAPITAL_API_IDENTIFIER=""

# Database Configuration
export DB_USER="db_username"
export DB_PASSWORD="db_password" 
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="jamso_db"

# Web Service Settings
export FLASK_SECRET_KEY="generate_a_random_key_here"
export WEBHOOK_TOKEN="your_webhook_token"

# Paths
export PROJECT_ROOT="/home/jamso-ai-server/Jamso-Ai-Engine"
export FLASK_APP="src.Webhook.app"

# Logging
export LOG_LEVEL="DEBUG"

# Status indication
export ENV_VARIABLES_LOADED="true"
export CREDENTIALS_SOURCE="env.sh"

# Echo success message when sourced
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    echo "Jamso-AI-Engine environment variables loaded successfully"
fi

# DO NOT COMMIT THIS FILE WITH REAL CREDENTIALS

# Capital.com API Login
export CAPITAL_API_LOGIN="james.philippi@gmail.com"

# Telegram credentials  
export TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"

# OpenAI API credentials
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY" # DO NOT COMMIT ACTUAL API KEYS

# Market Intelligence API keys
export ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_API_KEY"
export FINNHUB_API_KEY="YOUR_FINNHUB_API_KEY"

# Feature flags
export ENABLE_AI_ANALYSIS="true"
export ENABLE_NEWS_SENTIMENT="true"
export ENABLE_TELEGRAM_NOTIFICATIONS="true"
