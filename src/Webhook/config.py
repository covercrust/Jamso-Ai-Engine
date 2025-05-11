#!/usr/bin/env python3
import os

BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
WEBHOOK_TOKEN = '6a87cf683ac94bc7f83bc09ba643dc578538d4eb46c931a60dc4fe3ec3c159cd'

class Config:
    """Flask application configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_for_flask_sessions')
    DATABASE = os.path.join(BASE_PATH, 'src/Database/Webhook/trading_signals.db')
    ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = ENV == 'development'
    TESTING = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')