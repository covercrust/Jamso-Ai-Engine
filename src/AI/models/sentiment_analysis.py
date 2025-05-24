"""
News Sentiment Analysis Module

This module provides sentiment analysis functionality for financial news
to enhance trading decisions with market sentiment data.
"""

import pandas as pd
import numpy as np
import logging
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
import spacy
from typing import Dict, List, Any, Optional, Union, Tuple
import sqlite3
from datetime import datetime, timedelta
import os
import re
import json
import requests
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

# Configure logger
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Financial news sentiment analyzer for market analysis.
    
    Attributes:
        model_type (str): Type of model to use ('vader', 'textblob', 'transformers', or 'ensemble')
        db_path (str): Path to the SQLite database
        sentiment_model: The sentiment analysis model
    """
    
    def __init__(self, 
                model_type: str = 'ensemble',
                db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'):
        """
        Initialize the sentiment analyzer.
        
        Args:
            model_type: Type of model ('vader', 'textblob', 'transformers', or 'ensemble')
            db_path: Path to the SQLite database
        """
        self.model_type = model_type.lower()
        self.db_path = db_path
        self.sentiment_model = None
        self.nlp = None
        
        # Initialize NLTK data if needed
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            logger.info("Downloading NLTK Vader lexicon")
            nltk.download('vader_lexicon')
        
        # Initialize the appropriate sentiment model
        if self.model_type == 'vader':
            self.sentiment_model = SentimentIntensityAnalyzer()
            logger.info("Initialized VADER sentiment analyzer")
            
        elif self.model_type == 'textblob':
            # TextBlob doesn't need explicit initialization
            logger.info("Initialized TextBlob sentiment analyzer")
            
        elif self.model_type == 'transformers':
            try:
                # Initialize a financial sentiment analysis pipeline
                model_name = "yiyanghkust/finbert-tone"
                self.sentiment_model = pipeline(
                    "sentiment-analysis", 
                    model=model_name,
                    tokenizer=model_name
                )
                logger.info(f"Initialized transformers sentiment analyzer with {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize transformers model: {str(e)}")
                logger.info("Falling back to VADER sentiment analyzer")
                self.model_type = 'vader'
                self.sentiment_model = SentimentIntensityAnalyzer()
                
        elif self.model_type == 'ensemble':
            # Initialize all models for ensemble approach
            self.vader_model = SentimentIntensityAnalyzer()
            try:
                model_name = "yiyanghkust/finbert-tone"
                self.transformer_model = pipeline(
                    "sentiment-analysis", 
                    model=model_name,
                    tokenizer=model_name
                )
            except Exception as e:
                logger.error(f"Failed to initialize transformers model: {str(e)}")
                self.transformer_model = None
                
            logger.info("Initialized ensemble sentiment analyzer")
            
        else:
            logger.error(f"Unsupported model type: {self.model_type}")
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        # Initialize spaCy for entity recognition (if available)
        try:
            # Load smaller model for efficiency
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Initialized spaCy for entity recognition")
        except:
            logger.warning("spaCy model not available. Entity recognition will be limited.")
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for sentiment analysis.
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_vader_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using VADER.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        preprocessed_text = self._preprocess_text(text)
        scores = self.vader_model.polarity_scores(preprocessed_text)
        
        return {
            'sentiment': scores['compound'],
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu']
        }
    
    def analyze_textblob_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using TextBlob.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        preprocessed_text = self._preprocess_text(text)
        blob = TextBlob(preprocessed_text)
        
        # Get polarity (-1 to 1) and subjectivity (0 to 1)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Map polarity to positive/negative/neutral
        if polarity > 0:
            positive = polarity
            negative = 0
            neutral = 1 - positive
        elif polarity < 0:
            positive = 0
            negative = abs(polarity)
            neutral = 1 - negative
        else:
            positive = 0
            negative = 0
            neutral = 1
        
        return {
            'sentiment': polarity,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'subjectivity': subjectivity
        }
    
    def analyze_transformer_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using transformer models.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        preprocessed_text = self._preprocess_text(text)
        
        # Truncate text if too long for transformer model
        max_length = 512
        if len(preprocessed_text.split()) > max_length:
            words = preprocessed_text.split()
            preprocessed_text = " ".join(words[:max_length])
        
        # Run prediction
        try:
            results = self.transformer_model(preprocessed_text)
            
            if isinstance(results, list) and len(results) > 0:
                result = results[0]
                label = result['label']
                score = result['score']
                
                # Map FinBERT labels to sentiment scores
                if label.lower() == 'positive':
                    sentiment = score
                elif label.lower() == 'negative':
                    sentiment = -score
                else:  # neutral
                    sentiment = 0.0
                
                # Calculate positive/negative/neutral scores
                if sentiment > 0:
                    positive = sentiment
                    negative = 0
                    neutral = 1 - positive
                elif sentiment < 0:
                    positive = 0
                    negative = abs(sentiment)
                    neutral = 1 - negative
                else:
                    positive = 0
                    negative = 0
                    neutral = 1
                    
                return {
                    'sentiment': sentiment,
                    'positive': positive,
                    'negative': negative,
                    'neutral': neutral,
                    'model_label': label
                }
            else:
                logger.warning(f"Unexpected transformer result format: {results}")
                return self.analyze_vader_sentiment(text)
        except Exception as e:
            logger.error(f"Transformer model prediction failed: {str(e)}")
            return self.analyze_vader_sentiment(text)
    
    def analyze_ensemble_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using an ensemble of models.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with ensemble sentiment scores
        """
        # Get sentiment from VADER
        vader_scores = self.analyze_vader_sentiment(text)
        
        # Get sentiment from TextBlob
        textblob_scores = self.analyze_textblob_sentiment(text)
        
        # Get sentiment from transformer model if available
        if self.transformer_model:
            transformer_scores = self.analyze_transformer_sentiment(text)
            
            # Weighted ensemble (give more weight to transformer model)
            sentiment = (
                0.2 * vader_scores['sentiment'] + 
                0.2 * textblob_scores['sentiment'] + 
                0.6 * transformer_scores['sentiment']
            )
            
            positive = (
                0.2 * vader_scores['positive'] + 
                0.2 * textblob_scores['positive'] + 
                0.6 * transformer_scores['positive']
            )
            
            negative = (
                0.2 * vader_scores['negative'] + 
                0.2 * textblob_scores['negative'] + 
                0.6 * transformer_scores['negative']
            )
            
            neutral = (
                0.2 * vader_scores['neutral'] + 
                0.2 * textblob_scores['neutral'] + 
                0.6 * transformer_scores['neutral']
            )
        else:
            # Just average VADER and TextBlob if transformer not available
            sentiment = (vader_scores['sentiment'] + textblob_scores['sentiment']) / 2
            positive = (vader_scores['positive'] + textblob_scores['positive']) / 2
            negative = (vader_scores['negative'] + textblob_scores['negative']) / 2
            neutral = (vader_scores['neutral'] + textblob_scores['neutral']) / 2
        
        return {
            'sentiment': sentiment,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'vader_sentiment': vader_scores['sentiment'],
            'textblob_sentiment': textblob_scores['sentiment'],
            'transformer_sentiment': transformer_scores['sentiment'] if self.transformer_model else None
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a text based on the selected model.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        if self.model_type == 'vader':
            return self.analyze_vader_sentiment(text)
        elif self.model_type == 'textblob':
            return self.analyze_textblob_sentiment(text)
        elif self.model_type == 'transformers':
            return self.analyze_transformer_sentiment(text)
        elif self.model_type == 'ensemble':
            return self.analyze_ensemble_sentiment(text)
        else:
            logger.error(f"Unsupported model type: {self.model_type}")
            # Default to VADER
            return self.analyze_vader_sentiment(text)
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of dictionaries with entity information
        """
        if self.nlp is None:
            return []
            
        doc = self.nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
            
        return entities
    
    def analyze_news_batch(self, news_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Analyze a batch of news articles.
        
        Args:
            news_data: List of news article dictionaries with 'title' and 'content' keys
            
        Returns:
            List of dictionaries with sentiment analysis results
        """
        results = []
        
        for news_item in news_data:
            title = news_item.get('title', '')
            content = news_item.get('content', '')
            
            # Analyze title and content separately, with more weight on title
            title_sentiment = self.analyze_sentiment(title) if title else None
            content_sentiment = self.analyze_sentiment(content) if content else None
            
            if title_sentiment and content_sentiment:
                # Combine title and content sentiment with more weight on title
                sentiment = title_sentiment['sentiment'] * 0.7 + content_sentiment['sentiment'] * 0.3
                positive = title_sentiment['positive'] * 0.7 + content_sentiment['positive'] * 0.3
                negative = title_sentiment['negative'] * 0.7 + content_sentiment['negative'] * 0.3
                neutral = title_sentiment['neutral'] * 0.7 + content_sentiment['neutral'] * 0.3
            elif title_sentiment:
                sentiment = title_sentiment['sentiment']
                positive = title_sentiment['positive']
                negative = title_sentiment['negative']
                neutral = title_sentiment['neutral']
            elif content_sentiment:
                sentiment = content_sentiment['sentiment']
                positive = content_sentiment['positive']
                negative = content_sentiment['negative']
                neutral = content_sentiment['neutral']
            else:
                sentiment = 0.0
                positive = 0.0
                negative = 0.0
                neutral = 1.0
            
            # Extract entities from content
            entities = self.extract_entities(content)
            
            result = {
                'id': news_item.get('id'),
                'title': title,
                'sentiment': sentiment,
                'positive': positive,
                'negative': negative,
                'neutral': neutral,
                'entities': entities
            }
            
            results.append(result)
        
        return results
    
    def store_sentiment_data(self, symbol: str, sentiment_data: Dict[str, Any]) -> bool:
        """
        Store sentiment analysis data in the database.
        
        Args:
            symbol: Market symbol
            sentiment_data: Dictionary with sentiment data
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create the sentiment table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    sentiment_score REAL,
                    positive_score REAL,
                    negative_score REAL,
                    neutral_score REAL,
                    news_count INTEGER,
                    date TEXT,
                    timestamp INTEGER,
                    source TEXT,
                    raw_data TEXT
                )
            ''')
            
            # Insert sentiment data
            cursor.execute('''
                INSERT INTO market_sentiment (
                    symbol, sentiment_score, positive_score, negative_score, neutral_score, 
                    news_count, date, timestamp, source, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                sentiment_data.get('sentiment', 0),
                sentiment_data.get('positive', 0),
                sentiment_data.get('negative', 0),
                sentiment_data.get('neutral', 0),
                sentiment_data.get('news_count', 0),
                datetime.now().strftime('%Y-%m-%d'),
                int(datetime.now().timestamp()),
                sentiment_data.get('source', self.model_type),
                json.dumps(sentiment_data.get('raw_data', {}))
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored sentiment data for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store sentiment data: {str(e)}")
            return False
    
    def get_sentiment_history(self, 
                           symbol: str = None, 
                           days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical sentiment data from the database.
        
        Args:
            symbol: Market symbol (None for all symbols)
            days: Number of days of history to retrieve
            
        Returns:
            List of sentiment data dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate the start date
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Query parameters
            params = [start_date]
            symbol_filter = ""
            
            if symbol:
                symbol_filter = "AND symbol = ?"
                params.append(symbol)
            
            # Fetch sentiment data
            query = f'''
                SELECT symbol, date, sentiment_score, positive_score, negative_score, 
                       neutral_score, news_count, source
                FROM market_sentiment
                WHERE date >= ?
                {symbol_filter}
                ORDER BY date ASC
            '''
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    'symbol': row[0],
                    'date': row[1],
                    'sentiment': row[2],
                    'positive': row[3],
                    'negative': row[4],
                    'neutral': row[5],
                    'news_count': row[6],
                    'source': row[7]
                })
            
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Failed to get sentiment history: {str(e)}")
            return []


class NewsCollector:
    """
    Financial news collector for sentiment analysis.
    
    Attributes:
        db_path (str): Path to the SQLite database
        api_key (str): News API key
        sentiment_analyzer (SentimentAnalyzer): Sentiment analyzer
    """
    
    def __init__(self, 
                db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db',
                api_key: str = None):
        """
        Initialize the news collector.
        
        Args:
            db_path: Path to the SQLite database
            api_key: News API key (optional)
        """
        self.db_path = db_path
        self.api_key = api_key
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentAnalyzer(model_type='ensemble', db_path=db_path)
        
        # Create necessary tables
        self._create_tables()
        
        logger.info("Initialized financial news collector")
    
    def _create_tables(self) -> None:
        """
        Create database tables for news storage.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create news articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    url TEXT UNIQUE,
                    published_at TEXT,
                    timestamp INTEGER,
                    symbols TEXT,
                    sentiment_score REAL,
                    positive_score REAL,
                    negative_score REAL,
                    neutral_score REAL,
                    entities TEXT
                )
            ''')
            
            # Create news symbols mapping table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    news_id INTEGER,
                    symbol TEXT,
                    FOREIGN KEY (news_id) REFERENCES news_articles (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create news tables: {str(e)}")
    
    def collect_news_from_api(self, 
                            symbols: List[str] = None, 
                            days: int = 1) -> List[Dict[str, Any]]:
        """
        Collect news from external API.
        
        Args:
            symbols: List of market symbols to collect news for
            days: Number of days of news to collect
            
        Returns:
            List of collected news dictionaries
        """
        if not self.api_key:
            logger.warning("No API key provided for news collection")
            return []
            
        collected_news = []
        
        # Use symbols or default list
        target_symbols = symbols or ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        for symbol in target_symbols:
            try:
                # Calculate date range
                to_date = datetime.now().strftime('%Y-%m-%d')
                from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                # News API request
                url = f"https://newsapi.org/v2/everything"
                params = {
                    'q': symbol,
                    'from': from_date,
                    'to': to_date,
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'apiKey': self.api_key
                }
                
                response = requests.get(url, params=params)
                data = response.json()
                
                if data.get('status') == 'ok':
                    articles = data.get('articles', [])
                    
                    for article in articles:
                        news_item = {
                            'title': article.get('title', ''),
                            'content': article.get('content', '') or article.get('description', ''),
                            'source': article.get('source', {}).get('name', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('publishedAt', ''),
                            'timestamp': int(datetime.now().timestamp()),
                            'symbols': [symbol]
                        }
                        
                        collected_news.append(news_item)
                        
                    logger.info(f"Collected {len(articles)} news articles for {symbol}")
                else:
                    logger.warning(f"News API error: {data.get('message', 'Unknown error')}")
                
                # Respect API rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to collect news for {symbol}: {str(e)}")
        
        return collected_news
    
    def analyze_and_store_news(self, news_data: List[Dict[str, Any]]) -> bool:
        """
        Analyze sentiment for collected news and store in database.
        
        Args:
            news_data: List of news dictionaries
            
        Returns:
            True if successful
        """
        if not news_data:
            logger.warning("No news data to analyze")
            return False
            
        try:
            # Analyze sentiment for each news item
            analyzed_news = self.sentiment_analyzer.analyze_news_batch(news_data)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for news in analyzed_news:
                # Skip if no title or content
                if not news.get('title'):
                    continue
                    
                # Check if article already exists
                url = news_data[analyzed_news.index(news)].get('url', '')
                if url:
                    cursor.execute('SELECT id FROM news_articles WHERE url = ?', (url,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        continue
                
                # Insert news article
                cursor.execute('''
                    INSERT INTO news_articles (
                        title, content, source, url, published_at, timestamp,
                        symbols, sentiment_score, positive_score, negative_score, neutral_score, entities
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    news.get('title', ''),
                    news_data[analyzed_news.index(news)].get('content', ''),
                    news_data[analyzed_news.index(news)].get('source', ''),
                    url,
                    news_data[analyzed_news.index(news)].get('published_at', ''),
                    int(datetime.now().timestamp()),
                    ','.join(news_data[analyzed_news.index(news)].get('symbols', [])),
                    news.get('sentiment', 0),
                    news.get('positive', 0),
                    news.get('negative', 0),
                    news.get('neutral', 0),
                    json.dumps(news.get('entities', []))
                ))
                
                # Get the new article ID
                news_id = cursor.lastrowid
                
                # Insert symbol mappings
                for symbol in news_data[analyzed_news.index(news)].get('symbols', []):
                    cursor.execute('''
                        INSERT INTO news_symbols (news_id, symbol) VALUES (?, ?)
                    ''', (news_id, symbol))
                    
                # Update aggregate sentiment for each symbol
                for symbol in news_data[analyzed_news.index(news)].get('symbols', []):
                    # Get existing sentiment data for today
                    today = datetime.now().strftime('%Y-%m-%d')
                    cursor.execute('''
                        SELECT id, sentiment_score, positive_score, negative_score, neutral_score, news_count
                        FROM market_sentiment
                        WHERE symbol = ? AND date = ?
                    ''', (symbol, today))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        # Update existing sentiment
                        sentiment_id, sentiment_score, positive_score, negative_score, neutral_score, news_count = row
                        
                        # Calculate new averages
                        new_count = news_count + 1
                        new_sentiment = (sentiment_score * news_count + news.get('sentiment', 0)) / new_count
                        new_positive = (positive_score * news_count + news.get('positive', 0)) / new_count
                        new_negative = (negative_score * news_count + news.get('negative', 0)) / new_count
                        new_neutral = (neutral_score * news_count + news.get('neutral', 0)) / new_count
                        
                        cursor.execute('''
                            UPDATE market_sentiment
                            SET sentiment_score = ?, positive_score = ?, negative_score = ?,
                                neutral_score = ?, news_count = ?
                            WHERE id = ?
                        ''', (new_sentiment, new_positive, new_negative, new_neutral, new_count, sentiment_id))
                    else:
                        # Insert new sentiment
                        self.sentiment_analyzer.store_sentiment_data(symbol, {
                            'sentiment': news.get('sentiment', 0),
                            'positive': news.get('positive', 0),
                            'negative': news.get('negative', 0),
                            'neutral': news.get('neutral', 0),
                            'news_count': 1,
                            'source': 'news_api',
                            'raw_data': news
                        })
            
            conn.commit()
            conn.close()
            
            logger.info(f"Analyzed and stored {len(analyzed_news)} news articles")
            return True
            
        except Exception as e:
            logger.error(f"Failed to analyze and store news: {str(e)}")
            return False
    
    def get_sentiment_for_symbol(self, 
                              symbol: str, 
                              days: int = 7) -> Dict[str, Any]:
        """
        Get aggregated sentiment data for a specific symbol.
        
        Args:
            symbol: Market symbol
            days: Number of days of data to include
            
        Returns:
            Dictionary with aggregated sentiment data
        """
        sentiment_history = self.sentiment_analyzer.get_sentiment_history(symbol, days)
        
        if not sentiment_history:
            return {
                'symbol': symbol,
                'sentiment': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'news_count': 0,
                'trend': 'neutral',
                'history': []
            }
            
        # Calculate overall sentiment metrics
        total_sentiment = 0
        total_positive = 0
        total_negative = 0
        total_neutral = 0
        total_news = 0
        
        for entry in sentiment_history:
            total_sentiment += entry.get('sentiment', 0)
            total_positive += entry.get('positive', 0)
            total_negative += entry.get('negative', 0)
            total_neutral += entry.get('neutral', 0)
            total_news += entry.get('news_count', 0)
            
        # Calculate averages
        count = len(sentiment_history) or 1
        avg_sentiment = total_sentiment / count
        avg_positive = total_positive / count
        avg_negative = total_negative / count
        avg_neutral = total_neutral / count
        
        # Determine trend
        if len(sentiment_history) >= 2:
            recent_sentiment = sentiment_history[-1].get('sentiment', 0)
            previous_sentiment = sentiment_history[-2].get('sentiment', 0)
            
            if recent_sentiment > previous_sentiment:
                trend = 'improving'
            elif recent_sentiment < previous_sentiment:
                trend = 'deteriorating'
            else:
                trend = 'stable'
        else:
            trend = 'neutral'
            
        return {
            'symbol': symbol,
            'sentiment': avg_sentiment,
            'positive': avg_positive,
            'negative': avg_negative,
            'neutral': avg_neutral,
            'news_count': total_news,
            'trend': trend,
            'history': sentiment_history
        }
