"""
Market report generator for creating comprehensive market analysis reports.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import csv
import matplotlib.pyplot as plt
import io
import base64

# Optional OpenAI integration if API key is available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.Logging import get_logger
from src.MarketIntelligence.News.news_fetcher import NewsFetcher
from src.MarketIntelligence.Sentiment.sentiment_analyzer import SentimentAnalyzer

logger = get_logger(__name__)

class ReportGenerator:
    """Class for generating comprehensive market analysis reports."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.news_fetcher = NewsFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        # Set up OpenAI if available
        if self.openai_api_key and OPENAI_AVAILABLE:
            openai.api_key = self.openai_api_key
            logger.info("OpenAI API integration enabled for report generation")
        else:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI Python package not installed")
            else:
                logger.warning("OpenAI API key not found in environment variables")
    
    def generate_daily_market_report(self, symbols: List[str] = None) -> Dict:
        """
        Generate a comprehensive daily market report.
        
        Args:
            symbols: List of symbols to include in the report (optional)
            
        Returns:
            Dictionary with report data
        """
        # Use default symbols if none provided
        if not symbols:
            symbols = ['SPY', 'QQQ', 'DIA', 'IWM', 'VIX']
            
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Fetch market news
        market_news = self.news_fetcher.get_market_news(category='general', count=10)
        
        # Analyze sentiment of news
        analyzed_news = self.sentiment_analyzer.analyze_news_batch(market_news)
        
        # Get market sentiment summary
        market_sentiment = self.sentiment_analyzer.get_market_sentiment_summary(analyzed_news)
        
        # Get economic calendar events
        economic_events = self.news_fetcher.get_economic_calendar(
            from_date=today, 
            to_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        )
        
        # Get quotes for each symbol
        quotes = {}
        for symbol in symbols:
            quote = self.news_fetcher.get_global_quote(symbol)
            if quote:
                quotes[symbol] = quote
        
        # Prepare report data
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'report_date': today,
            'market_sentiment': market_sentiment,
            'analyzed_news': analyzed_news[:5],  # Include top 5 analyzed news items
            'economic_events': economic_events[:10],  # Include top 10 upcoming economic events
            'quotes': quotes
        }
        
        # Generate report summary using OpenAI if available
        if self.openai_api_key and OPENAI_AVAILABLE:
            report_data['summary'] = self._generate_report_summary(report_data)
        else:
            report_data['summary'] = self._generate_basic_summary(report_data)
        
        return report_data
    
    def _generate_report_summary(self, report_data: Dict) -> Dict:
        """
        Generate a detailed report summary using OpenAI.
        
        Args:
            report_data: The full report data
            
        Returns:
            Dictionary with summary text and key points
        """
        try:
            # Prepare the input data for OpenAI
            input_text = f"""
            Generate a comprehensive market report summary based on the following data:
            
            Market Sentiment: {json.dumps(report_data['market_sentiment'])}
            
            Recent News Headlines:
            {self._format_news_for_prompt(report_data['analyzed_news'])}
            
            Upcoming Economic Events:
            {self._format_events_for_prompt(report_data['economic_events'][:5])}
            
            Latest Market Quotes:
            {self._format_quotes_for_prompt(report_data['quotes'])}
            
            Format your response as JSON with the following structure:
            {{
                "summary": "A detailed 2-paragraph summary of market conditions",
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "market_outlook": "bullish/bearish/neutral with brief explanation",
                "trading_ideas": ["Idea 1", "Idea 2"]
            }}
            """
            
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Use an appropriate model
                messages=[
                    {"role": "system", "content": "You are a professional financial market analyst."},
                    {"role": "user", "content": input_text}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            # Extract the response
            result_text = response['choices'][0]['message']['content']
            
            # Parse the JSON response
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                # If parsing fails, use the raw text
                logger.warning("Failed to parse OpenAI report summary as JSON")
                return {
                    "summary": result_text,
                    "key_points": [],
                    "market_outlook": "neutral",
                    "trading_ideas": []
                }
                
        except Exception as e:
            logger.error(f"Error generating report summary with OpenAI: {e}")
            # Fall back to basic summary
            return self._generate_basic_summary(report_data)
    
    def _format_news_for_prompt(self, news_items: List[Dict]) -> str:
        """Format news items for the OpenAI prompt."""
        result = ""
        for item in news_items:
            headline = item.get('headline', '')
            sentiment = item.get('sentiment', {}).get('sentiment', 'neutral')
            score = item.get('sentiment', {}).get('score', 0)
            result += f"- {headline} (Sentiment: {sentiment}, Score: {score})\n"
        return result
    
    def _format_events_for_prompt(self, events: List[Dict]) -> str:
        """Format economic events for the OpenAI prompt."""
        result = ""
        for event in events:
            event_name = event.get('event', '')
            country = event.get('country', '')
            date = event.get('date', '')
            impact = event.get('impact', '')
            result += f"- {date}: {event_name} ({country}, Impact: {impact})\n"
        return result
    
    def _format_quotes_for_prompt(self, quotes: Dict) -> str:
        """Format quotes for the OpenAI prompt."""
        result = ""
        for symbol, quote in quotes.items():
            price = quote.get('05. price', 'N/A')
            change_percent = quote.get('10. change percent', 'N/A')
            result += f"- {symbol}: {price} ({change_percent})\n"
        return result
    
    def _generate_basic_summary(self, report_data: Dict) -> Dict:
        """
        Generate a basic report summary without using OpenAI.
        
        Args:
            report_data: The full report data
            
        Returns:
            Dictionary with summary text and key points
        """
        sentiment = report_data['market_sentiment']['overall_sentiment']
        score = report_data['market_sentiment']['overall_score']
        
        # Generate a simple summary based on sentiment
        if sentiment == 'positive':
            summary = (f"Market sentiment is positive (score: {score}). The news suggests an optimistic "
                      "outlook with potential upside in the near term. Investors may consider looking "
                      "for buying opportunities while maintaining risk management strategies.")
            outlook = "bullish"
        elif sentiment == 'negative':
            summary = (f"Market sentiment is negative (score: {score}). Recent news indicates caution "
                      "is warranted. Investors may want to reduce risk exposure and focus on "
                      "defensive positions until clearer market direction emerges.")
            outlook = "bearish"
        else:
            summary = (f"Market sentiment is neutral (score: {score}). The market appears balanced "
                      "with mixed signals. Investors may want to maintain current positions while "
                      "watching for a clearer directional move before making significant changes.")
            outlook = "neutral"
            
        # Generate key points based on available data
        key_points = []
        
        # Add point about market sentiment
        key_points.append(f"Overall market sentiment is {sentiment} with a score of {score}")
        
        # Add point about economic events if available
        if report_data['economic_events']:
            events_count = len(report_data['economic_events'])
            key_points.append(f"{events_count} upcoming economic events may impact market direction")
        
        # Add point about notable quotes if available
        if report_data['quotes']:
            symbols = list(report_data['quotes'].keys())
            key_points.append(f"Key symbols to watch: {', '.join(symbols)}")
        
        return {
            "summary": summary,
            "key_points": key_points,
            "market_outlook": outlook,
            "trading_ideas": ["Monitor market volatility indicators", 
                             "Watch economic data releases for market direction"]
        }
    
    def export_report_to_html(self, report_data: Dict, filename: str = None) -> str:
        """
        Export report data to HTML format.
        
        Args:
            report_data: The report data to export
            filename: Optional filename to save the HTML to
            
        Returns:
            HTML content as string
        """
        # Generate the HTML content
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Market Report {report_data['report_date']}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .header {{
                    border-bottom: 2px solid #3498db;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                }}
                .summary {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-left: 4px solid #3498db;
                    margin-bottom: 20px;
                }}
                .sentiment {{
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                .positive {{
                    background-color: #2ecc71;
                    color: white;
                }}
                .negative {{
                    background-color: #e74c3c;
                    color: white;
                }}
                .neutral {{
                    background-color: #f39c12;
                    color: white;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .news-item {{
                    margin-bottom: 15px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #eee;
                }}
                .key-points {{
                    background-color: #f0f8ff;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .trading-ideas {{
                    background-color: #fffaf0;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Market Intelligence Report</h1>
                <p>Generated: {report_data['generated_at']}</p>
                <p>Report Date: {report_data['report_date']}</p>
            </div>
            
            <div class="summary">
                <h2>Market Summary</h2>
                <p>{report_data.get('summary', {}).get('summary', 'No summary available.')}</p>
                
                <h3>Current Market Sentiment</h3>
                <p>Overall Sentiment: 
                    <span class="sentiment {report_data['market_sentiment']['overall_sentiment']}">
                        {report_data['market_sentiment']['overall_sentiment'].upper()}
                    </span>
                    (Score: {report_data['market_sentiment']['overall_score']})
                </p>
                
                <h3>Key Points</h3>
                <ul class="key-points">
        """
        
        # Add key points if available
        for point in report_data.get('summary', {}).get('key_points', []):
            html += f"<li>{point}</li>"
        
        # Add market outlook
        html += f"""
                </ul>
                
                <h3>Market Outlook</h3>
                <p>{report_data.get('summary', {}).get('market_outlook', 'No outlook available.')}</p>
            </div>
            
            <h2>Market Quotes</h2>
            <table>
                <tr>
                    <th>Symbol</th>
                    <th>Price</th>
                    <th>Change</th>
                    <th>Change %</th>
                    <th>Volume</th>
                </tr>
        """
        
        # Add quotes
        for symbol, quote in report_data['quotes'].items():
            price = quote.get('05. price', 'N/A')
            change = quote.get('09. change', 'N/A')
            change_pct = quote.get('10. change percent', 'N/A')
            volume = quote.get('06. volume', 'N/A')
            
            html += f"""
                <tr>
                    <td>{symbol}</td>
                    <td>{price}</td>
                    <td>{change}</td>
                    <td>{change_pct}</td>
                    <td>{volume}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Recent News Analysis</h2>
        """
        
        # Add news items
        for item in report_data['analyzed_news']:
            headline = item.get('headline', 'No headline')
            summary = item.get('summary', 'No summary available')
            sentiment = item.get('sentiment', {}).get('sentiment', 'neutral')
            score = item.get('sentiment', {}).get('score', 0)
            source = item.get('source', 'Unknown source')
            url = item.get('url', '#')
            
            html += f"""
            <div class="news-item">
                <h3><a href="{url}" target="_blank">{headline}</a></h3>
                <p>{summary}</p>
                <p>Source: {source} | Sentiment: 
                    <span class="sentiment {sentiment}">{sentiment.upper()}</span> 
                    (Score: {score})
                </p>
            </div>
            """
        
        html += """
            <h2>Upcoming Economic Events</h2>
            <table>
                <tr>
                    <th>Date</th>
                    <th>Event</th>
                    <th>Country</th>
                    <th>Impact</th>
                    <th>Forecast</th>
                </tr>
        """
        
        # Add economic events
        for event in report_data['economic_events'][:10]:  # Show top 10 events
            date = event.get('date', 'N/A')
            event_name = event.get('event', 'N/A')
            country = event.get('country', 'N/A')
            impact = event.get('impact', 'N/A')
            forecast = event.get('forecast', 'N/A')
            
            html += f"""
                <tr>
                    <td>{date}</td>
                    <td>{event_name}</td>
                    <td>{country}</td>
                    <td>{impact}</td>
                    <td>{forecast}</td>
                </tr>
            """
        
        # Add trading ideas section
        html += """
            </table>
            
            <div class="trading-ideas">
                <h2>Trading Ideas</h2>
                <ul>
        """
        
        for idea in report_data.get('summary', {}).get('trading_ideas', ['No trading ideas available']):
            html += f"<li>{idea}</li>"
        
        html += """
                </ul>
            </div>
            
            <div class="footer">
                <p>Generated by Jamso AI Engine. This report is for informational purposes only and does not constitute financial advice.</p>
            </div>
        </body>
        </html>
        """
        
        # Save to file if filename provided
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
                
        return html
        
    def save_report(self, report_data: Dict, format: str = 'json', directory: str = None) -> str:
        """
        Save the report to a file.
        
        Args:
            report_data: The report data to save
            format: Output format ('json', 'html', 'csv')
            directory: Directory to save the report in (default: Data/Reports)
            
        Returns:
            Path to the saved file
        """
        # Setup directory
        if directory is None:
            directory = os.path.join(os.environ.get('ROOT_DIR', '.'), 'Data', 'Reports')
            
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"market_report_{timestamp}"
        
        if format.lower() == 'json':
            filename = os.path.join(directory, f"{base_filename}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
                
        elif format.lower() == 'html':
            filename = os.path.join(directory, f"{base_filename}.html")
            html_content = self.export_report_to_html(report_data, filename)
            
        elif format.lower() == 'csv':
            filename = os.path.join(directory, f"{base_filename}.csv")
            self._export_report_to_csv(report_data, filename)
            
        else:
            logger.error(f"Unsupported report format: {format}")
            return None
            
        logger.info(f"Report saved to {filename}")
        return filename
        
    def _export_report_to_csv(self, report_data: Dict, filename: str) -> None:
        """Export report data to CSV format."""
        # Export news items
        news_csv = os.path.join(os.path.dirname(filename), 
                               f"{os.path.splitext(os.path.basename(filename))[0]}_news.csv")
        with open(news_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Headline', 'Summary', 'Source', 'Date', 'Sentiment', 'Score', 'URL'])
            
            for item in report_data['analyzed_news']:
                writer.writerow([
                    item.get('headline', ''),
                    item.get('summary', ''),
                    item.get('source', ''),
                    item.get('date', ''),
                    item.get('sentiment', {}).get('sentiment', 'neutral'),
                    item.get('sentiment', {}).get('score', 0),
                    item.get('url', '')
                ])
                
        # Export economic events
        events_csv = os.path.join(os.path.dirname(filename), 
                                f"{os.path.splitext(os.path.basename(filename))[0]}_events.csv")
        with open(events_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Event', 'Country', 'Impact', 'Previous', 'Forecast', 'Actual'])
            
            for event in report_data['economic_events']:
                writer.writerow([
                    event.get('date', ''),
                    event.get('event', ''),
                    event.get('country', ''),
                    event.get('impact', ''),
                    event.get('prev', ''),
                    event.get('forecast', ''),
                    event.get('actual', '')
                ])
                
        # Export quotes
        quotes_csv = os.path.join(os.path.dirname(filename), 
                                f"{os.path.splitext(os.path.basename(filename))[0]}_quotes.csv")
        with open(quotes_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Symbol', 'Price', 'Change', 'Change %', 'Volume', 'Latest Trading Day'])
            
            for symbol, quote in report_data['quotes'].items():
                writer.writerow([
                    symbol,
                    quote.get('05. price', ''),
                    quote.get('09. change', ''),
                    quote.get('10. change percent', ''),
                    quote.get('06. volume', ''),
                    quote.get('07. latest trading day', '')
                ])
                
        # Create main CSV with summary
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Report Date', 'Generated At', 'Overall Sentiment', 'Sentiment Score'])
            writer.writerow([
                report_data['report_date'],
                report_data['generated_at'],
                report_data['market_sentiment']['overall_sentiment'],
                report_data['market_sentiment']['overall_score']
            ])
            
            writer.writerow([])
            writer.writerow(['Summary'])
            writer.writerow([report_data.get('summary', {}).get('summary', 'No summary available')])
            
            writer.writerow([])
            writer.writerow(['Key Points'])
            for point in report_data.get('summary', {}).get('key_points', []):
                writer.writerow([point])
                
            writer.writerow([])
            writer.writerow(['Market Outlook'])
            writer.writerow([report_data.get('summary', {}).get('market_outlook', 'No outlook available')])
            
            writer.writerow([])
            writer.writerow(['Related Files'])
            writer.writerow([f"News: {os.path.basename(news_csv)}"])
            writer.writerow([f"Economic Events: {os.path.basename(events_csv)}"])
            writer.writerow([f"Market Quotes: {os.path.basename(quotes_csv)}"])
