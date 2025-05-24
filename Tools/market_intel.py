#!/usr/bin/env python3
"""
Market Intelligence CLI Tool

This tool provides a command-line interface for generating market intelligence reports,
analyzing news sentiment, and monitoring financial markets.

Usage:
    python market_intel.py report [--symbols=SPY,QQQ] [--format=html] [--output=report.html]
    python market_intel.py news [--count=10] [--category=general]
    python market_intel.py sentiment [--symbols=AAPL,MSFT] [--days=7]
    python market_intel.py monitor [--symbols=SPY,QQQ,DIA] [--interval=60]
"""

import os
import sys
import argparse
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MarketIntelCLI")

# ANSI color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Import MarketIntelligence modules
try:
    from src.MarketIntelligence.News.news_fetcher import NewsFetcher
    from src.MarketIntelligence.Sentiment.sentiment_analyzer import SentimentAnalyzer
    from src.MarketIntelligence.Reports.report_generator import ReportGenerator
    print(f"Successfully imported Market Intelligence modules")
except ImportError as e:
    logger.error(f"Failed to import Market Intelligence modules: {e}")
    print(f"{Colors.RED}Error: Failed to import Market Intelligence modules. Make sure the application is properly installed.{Colors.END}")
    print(f"{Colors.RED}Exception details: {e}{Colors.END}")
    sys.exit(1)

def validate_environment():
    """Verify that necessary environment variables are set"""
    required_vars = ['ALPHA_VANTAGE_API_KEY', 'FINNHUB_API_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"{Colors.YELLOW}Warning: The following environment variables are not set:{Colors.END}")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nSome functionality may be limited. Please check your setup.sh and env.sh files.")
        return False
    
    return True

def generate_report(args):
    """
    Generate a market intelligence report
    """
    print(f"{Colors.HEADER}Generating Market Intelligence Report{Colors.END}")
    
    # Parse symbols
    symbols = args.symbols.split(',') if args.symbols else []
    
    # Initialize report generator
    generator = ReportGenerator()
    
    # Generate the report
    print(f"Gathering market data for {len(symbols) if symbols else 'default'} symbols...")
    start_time = time.time()
    report = generator.generate_daily_market_report(symbols=symbols)
    duration = time.time() - start_time
    
    # Show a summary
    print(f"\n{Colors.GREEN}Report generated successfully in {duration:.2f}s{Colors.END}")
    print(f"Overall Market Sentiment: {report['market_sentiment']['overall_sentiment']} (Score: {report['market_sentiment']['overall_score']})")
    print(f"Generated at: {report['generated_at']}")
    
    # Export the report in the requested format
    if args.format.lower() == 'json':
        output_file = args.output or f"market_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved as JSON: {output_file}")
    
    elif args.format.lower() == 'html':
        output_file = args.output or f"market_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html_content = generator.export_report_to_html(report)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\nReport saved as HTML: {output_file}")
    
    elif args.format.lower() == 'csv':
        output_file = args.output or f"market_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        generator._export_report_to_csv(report, output_file)
        print(f"\nReport saved as CSV: {output_file}")
    
    else:
        print(f"{Colors.RED}Error: Unsupported format '{args.format}'{Colors.END}")
        return 1
    
    return 0

def get_news(args):
    """
    Fetch and display market news
    """
    print(f"{Colors.HEADER}Fetching Market News{Colors.END}")
    
    # Initialize news fetcher
    fetcher = NewsFetcher()
    
    # Get news
    print(f"Fetching {args.count} news items from category '{args.category}'...")
    news_items = fetcher.get_market_news(category=args.category, count=args.count)
    
    if not news_items:
        print(f"{Colors.RED}No news items found. Check your API keys and internet connection.{Colors.END}")
        return 1
    
    # Display news items
    print(f"\n{Colors.GREEN}Found {len(news_items)} news items:{Colors.END}\n")
    
    for i, item in enumerate(news_items, 1):
        headline = item.get('headline', '') or item.get('title', '')
        source = item.get('source', '')
        url = item.get('url', '')
        date = item.get('date', '')
        
        print(f"{Colors.BOLD}{i}. {headline}{Colors.END}")
        print(f"   Source: {source} | Date: {date}")
        if args.verbose and 'summary' in item:
            print(f"   Summary: {item['summary']}")
        print(f"   URL: {url}\n")
    
    # Export if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, indent=2)
        print(f"News items saved to {args.output}")
    
    return 0

def analyze_sentiment(args):
    """
    Analyze sentiment for specific symbols or recent news
    """
    print(f"{Colors.HEADER}Market Sentiment Analysis{Colors.END}")
    
    # Initialize components
    fetcher = NewsFetcher()
    analyzer = SentimentAnalyzer()
    
    # Parse symbols
    symbols = args.symbols.split(',') if args.symbols else []
    
    # Calculate date range
    to_date = datetime.now().strftime('%Y-%m-%d')
    from_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    all_news = []
    
    # Fetch general market news if no symbols specified
    if not symbols:
        print("Fetching general market news...")
        general_news = fetcher.get_market_news(category='general', count=args.count)
        all_news.extend(general_news)
    
    # Fetch company-specific news for each symbol
    for symbol in symbols:
        print(f"Fetching news for {symbol}...")
        company_news = fetcher.get_company_news(symbol, from_date, to_date)
        # Take only the requested number of items
        company_news = company_news[:args.count]
        all_news.extend(company_news)
    
    if not all_news:
        print(f"{Colors.RED}No news items found. Check your API keys and internet connection.{Colors.END}")
        return 1
    
    # Analyze sentiment
    print(f"Analyzing sentiment for {len(all_news)} news items...")
    analyzed_news = analyzer.analyze_news_batch(all_news)
    
    # Get overall sentiment
    market_sentiment = analyzer.get_market_sentiment_summary(analyzed_news)
    
    # Display results
    print(f"\n{Colors.GREEN}Sentiment Analysis Results:{Colors.END}")
    print(f"Overall Market Sentiment: {market_sentiment['overall_sentiment']} (Score: {market_sentiment['overall_score']})")
    print(f"Confidence: {market_sentiment['confidence']}")
    print(f"Sentiment Counts: {market_sentiment['sentiment_counts']}")
    
    # Display individual news sentiment
    if args.verbose:
        print(f"\n{Colors.BOLD}Individual News Sentiment:{Colors.END}")
        for i, item in enumerate(analyzed_news, 1):
            headline = item.get('headline', '') or item.get('title', '')
            sentiment = item.get('sentiment', {}).get('sentiment', 'neutral')
            score = item.get('sentiment', {}).get('score', 0)
            
            if sentiment == 'positive':
                sentiment_color = Colors.GREEN
            elif sentiment == 'negative':
                sentiment_color = Colors.RED
            else:
                sentiment_color = Colors.YELLOW
                
            print(f"{i}. {headline}")
            print(f"   Sentiment: {sentiment_color}{sentiment.upper()} (Score: {score}){Colors.END}")
    
    # Export if requested
    if args.output:
        output_data = {
            'generated_at': datetime.now().isoformat(),
            'market_sentiment': market_sentiment,
            'analyzed_news': analyzed_news
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nAnalysis saved to {args.output}")
    
    return 0

def monitor_market(args):
    """
    Continuously monitor market data and sentiment
    """
    print(f"{Colors.HEADER}Market Monitoring{Colors.END}")
    
    # Parse symbols
    symbols = args.symbols.split(',') if args.symbols else ['SPY', 'QQQ', 'DIA', 'IWM']
    
    # Initialize components
    fetcher = NewsFetcher()
    
    print(f"Monitoring market data for: {', '.join(symbols)}")
    print(f"Interval: {args.interval} seconds")
    print(f"Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            print(f"\n{Colors.BOLD}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]{Colors.END}")
            
            # Get quotes for each symbol
            for symbol in symbols:
                quote = fetcher.get_global_quote(symbol)
                if quote:
                    price = quote.get('05. price', 'N/A')
                    change = quote.get('09. change', 'N/A')
                    change_pct = quote.get('10. change percent', 'N/A')
                    
                    # Color based on change
                    if change.startswith('-'):
                        color = Colors.RED
                    else:
                        color = Colors.GREEN
                    
                    print(f"{symbol}: {price} {color}{change} ({change_pct}){Colors.END}")
            
            # Get latest news (only one item to avoid clutter)
            latest_news = fetcher.get_market_news(count=1)
            if latest_news:
                headline = latest_news[0].get('headline', '') or latest_news[0].get('title', '')
                print(f"\nLatest News: {headline}")
            
            # Wait for next update
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitoring stopped{Colors.END}")
    
    return 0

def main():
    """Parse arguments and dispatch commands"""
    parser = argparse.ArgumentParser(description='Market Intelligence CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Report generation command
    report_parser = subparsers.add_parser('report', help='Generate a market intelligence report')
    report_parser.add_argument('--symbols', type=str, help='Comma-separated list of symbols to include in the report')
    report_parser.add_argument('--format', type=str, choices=['html', 'json', 'csv'], default='html', help='Output format')
    report_parser.add_argument('--output', type=str, help='Output file path')
    
    # News fetching command
    news_parser = subparsers.add_parser('news', help='Fetch market news')
    news_parser.add_argument('--count', type=int, default=10, help='Number of news items to fetch')
    news_parser.add_argument('--category', type=str, default='general', choices=['general', 'forex', 'crypto', 'merger'], help='News category')
    news_parser.add_argument('--output', type=str, help='Output file path (JSON)')
    news_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    
    # Sentiment analysis command
    sentiment_parser = subparsers.add_parser('sentiment', help='Analyze market sentiment')
    sentiment_parser.add_argument('--symbols', type=str, help='Comma-separated list of symbols to analyze')
    sentiment_parser.add_argument('--days', type=int, default=7, help='Number of days to look back for news')
    sentiment_parser.add_argument('--count', type=int, default=10, help='Number of news items per symbol')
    sentiment_parser.add_argument('--output', type=str, help='Output file path (JSON)')
    sentiment_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    
    # Market monitoring command
    monitor_parser = subparsers.add_parser('monitor', help='Continuously monitor market data')
    monitor_parser.add_argument('--symbols', type=str, help='Comma-separated list of symbols to monitor')
    monitor_parser.add_argument('--interval', type=int, default=60, help='Update interval in seconds')
    
    args = parser.parse_args()
    
    # Check if any command was specified
    if not args.command:
        parser.print_help()
        return 1
    
    # Validate environment
    validate_environment()
    
    # Dispatch command
    if args.command == 'report':
        return generate_report(args)
    elif args.command == 'news':
        return get_news(args)
    elif args.command == 'sentiment':
        return analyze_sentiment(args)
    elif args.command == 'monitor':
        return monitor_market(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
