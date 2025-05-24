"""
Sentiment analyzer for market news and reports.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
import requests
import re
from collections import Counter
from datetime import datetime

# Optional OpenAI integration if API key is available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.Logging import get_logger

logger = get_logger(__name__)

class SentimentAnalyzer:
    """Class for analyzing sentiment of market news and reports."""
    
    def __init__(self):
        """Initialize the sentiment analyzer."""
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        if self.openai_api_key and OPENAI_AVAILABLE:
            openai.api_key = self.openai_api_key
            logger.info("OpenAI API integration enabled for sentiment analysis")
        else:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI Python package not installed")
            else:
                logger.warning("OpenAI API key not found in environment variables")
                
        # Sentiment word dictionaries for basic analysis
        self.positive_words = set([
            'bullish', 'uptrend', 'gain', 'positive', 'increase', 'growth', 'rise', 'upside',
            'outperform', 'beat', 'exceed', 'surpass', 'strong', 'opportunity', 'profit',
            'upgrade', 'recovers', 'recovery', 'rally', 'success', 'successful'
        ])
        
        self.negative_words = set([
            'bearish', 'downtrend', 'loss', 'negative', 'decrease', 'decline', 'fall', 'downside',
            'underperform', 'miss', 'below', 'weak', 'risk', 'lose', 'downgrade', 'slowdown',
            'slump', 'crash', 'crisis', 'concern', 'warning', 'recession', 'inflation'
        ])
        
        self.neutral_words = set([
            'hold', 'stable', 'unchanged', 'flat', 'steady', 'neutral', 'mixed', 'balanced'
        ])
        
    def analyze_text_basic(self, text: str) -> Dict:
        """
        Perform basic sentiment analysis on a text using keyword counting.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing sentiment scores and metrics
        """
        if not text:
            return {'sentiment': 'neutral', 'score': 0, 'confidence': 0}
        
        # Convert to lowercase and tokenize
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Count sentiment words
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        neutral_count = sum(1 for word in words if word in self.neutral_words)
        
        # Calculate raw sentiment score (-1 to 1)
        total = positive_count + negative_count + neutral_count
        if total == 0:
            return {'sentiment': 'neutral', 'score': 0, 'confidence': 0}
            
        score = (positive_count - negative_count) / total
        
        # Determine sentiment label
        if score > 0.2:
            sentiment = 'positive'
        elif score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
            
        # Calculate confidence based on how many sentiment words were found
        word_count = len(words)
        confidence = min(1.0, total / (word_count * 0.25)) if word_count > 0 else 0
        
        return {
            'sentiment': sentiment,
            'score': round(score, 2),
            'confidence': round(confidence, 2),
            'details': {
                'positive_words': positive_count,
                'negative_words': negative_count,
                'neutral_words': neutral_count,
                'total_words': word_count
            }
        }
        
    def analyze_text_openai(self, text: str) -> Dict:
        """
        Perform sentiment analysis using OpenAI API.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not self.openai_api_key or not OPENAI_AVAILABLE:
            logger.warning("OpenAI sentiment analysis unavailable - falling back to basic analysis")
            return self.analyze_text_basic(text)
            
        try:
            # Prepare prompt for sentiment analysis
            prompt = f"""Analyze the sentiment of this financial news text. 
            Provide a sentiment score from -1 (very negative) to 1 (very positive).
            Also extract key entities (companies, markets, currencies mentioned) and key topics.
            Format your response as JSON with the following structure:
            {{
                "sentiment": "positive/negative/neutral",
                "score": 0.7, 
                "confidence": 0.8,
                "key_entities": ["Apple", "NASDAQ"],
                "key_topics": ["earnings report", "market growth"],
                "brief_summary": "One sentence summary"
            }}

            Text to analyze:
            {text[:4000]}  # Limit to 4000 chars to stay within token limits
            """
            
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Use an appropriate model
                messages=[
                    {"role": "system", "content": "You are a financial sentiment analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Extract and parse the JSON response
            result_text = response['choices'][0]['message']['content']
            # Find JSON data in the response
            json_match = re.search(r'({.*})', result_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                    # Add timestamp
                    result['timestamp'] = datetime.now().isoformat()
                    return result
                except json.JSONDecodeError:
                    logger.error("Failed to parse OpenAI response as JSON")
            
            # If parsing fails, fall back to basic analysis
            logger.warning("OpenAI response format unexpected - falling back to basic analysis")
            return self.analyze_text_basic(text)
            
        except Exception as e:
            logger.error(f"Error using OpenAI for sentiment analysis: {e}")
            # Fall back to basic analysis on error
            return self.analyze_text_basic(text)
    
    def analyze_news_item(self, news_item: Dict) -> Dict:
        """
        Analyze sentiment of a news item.
        
        Args:
            news_item: Dictionary containing news item data
            
        Returns:
            News item with sentiment analysis added
        """
        # Create a copy to avoid modifying the original
        result = dict(news_item)
        
        # Concatenate headline and summary for analysis
        text_to_analyze = ""
        if 'headline' in news_item:
            text_to_analyze += news_item['headline'] + " "
        if 'summary' in news_item:
            text_to_analyze += news_item['summary']
        
        # Use OpenAI if available, otherwise fall back to basic analysis
        if self.openai_api_key and OPENAI_AVAILABLE:
            sentiment_data = self.analyze_text_openai(text_to_analyze)
        else:
            sentiment_data = self.analyze_text_basic(text_to_analyze)
            
        # Add sentiment data to the result
        result['sentiment'] = sentiment_data
        
        return result
        
    def analyze_news_batch(self, news_items: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for a batch of news items.
        
        Args:
            news_items: List of news item dictionaries
            
        Returns:
            List of news items with sentiment analysis added
        """
        return [self.analyze_news_item(item) for item in news_items]
        
    def get_market_sentiment_summary(self, analyzed_news: List[Dict]) -> Dict:
        """
        Generate an overall market sentiment summary from analyzed news.
        
        Args:
            analyzed_news: List of news items with sentiment analysis
            
        Returns:
            Dictionary with market sentiment summary
        """
        if not analyzed_news:
            return {
                'overall_sentiment': 'neutral',
                'overall_score': 0,
                'sentiment_counts': {'positive': 0, 'negative': 0, 'neutral': 0},
                'confidence': 0,
                'timestamp': datetime.now().isoformat()
            }
            
        # Aggregate sentiment data
        sentiments = []
        scores = []
        confidences = []
        
        for item in analyzed_news:
            if 'sentiment' in item and isinstance(item['sentiment'], dict):
                sentiment_data = item['sentiment']
                sentiments.append(sentiment_data.get('sentiment', 'neutral'))
                scores.append(sentiment_data.get('score', 0))
                confidences.append(sentiment_data.get('confidence', 0))
        
        # Calculate overall sentiment
        sentiment_counts = Counter(sentiments)
        
        # Calculate weighted average score based on confidence
        total_weight = sum(confidences)
        if total_weight > 0:
            overall_score = sum(score * conf for score, conf in zip(scores, confidences)) / total_weight
        else:
            overall_score = sum(scores) / len(scores) if scores else 0
            
        # Determine overall sentiment
        if overall_score > 0.2:
            overall_sentiment = 'positive'
        elif overall_score < -0.2:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
            
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'overall_sentiment': overall_sentiment,
            'overall_score': round(overall_score, 2),
            'sentiment_counts': dict(sentiment_counts),
            'confidence': round(avg_confidence, 2),
            'timestamp': datetime.now().isoformat()
        }
