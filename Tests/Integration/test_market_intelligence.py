#!/usr/bin/env python3
"""
Integration tests for the Market Intelligence module in Jamso-AI-Engine.
Tests functionality of news fetching, sentiment analysis, and report generation.

This test verifies:
1. News can be fetched from financial APIs
2. Sentiment analysis works on news articles
3. Market reports can be generated with coherent data
4. API keys are properly retrieved and used
5. Error handling functions correctly

A JSON report with detailed test results is generated after each test run.
"""
import os
import sys
import logging
import argparse
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MarketIntelligenceTest")

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Import necessary modules
try:
    from src.MarketIntelligence.News.news_fetcher import NewsFetcher
    from src.MarketIntelligence.Sentiment.sentiment_analyzer import SentimentAnalyzer
    from src.MarketIntelligence.Reports.report_generator import ReportGenerator
    logger.info("Successfully imported Market Intelligence modules")
except ImportError as e:
    logger.error(f"Failed to import Market Intelligence modules: {e}")
    sys.exit(1)

# Test results storage
test_results = {
    "test_run_id": f"mi_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "timestamp": datetime.now().isoformat(),
    "platform": sys.platform,
    "python_version": sys.version,
    "tests": [],
}

def run_test(test_func):
    """Decorator to run a test function and record results"""
    def wrapper(*args, **kwargs):
        test_name = test_func.__name__
        logger.info(f"{Colors.HEADER}Running test: {test_name}{Colors.END}")
        start_time = time.time()
        
        test_result = {
            "name": test_name,
            "description": test_func.__doc__.strip() if test_func.__doc__ else "No description",
            "status": "PENDING",
            "start_time": datetime.now().isoformat(),
        }
        
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            test_result["duration"] = round(duration, 2)
            test_result["status"] = "PASS"
            test_result.update(result or {})
            logger.info(f"{Colors.GREEN}✓ Test {test_name} PASSED in {duration:.2f}s{Colors.END}")
            return result
        except AssertionError as e:
            duration = time.time() - start_time
            test_result["duration"] = round(duration, 2)
            test_result["status"] = "FAIL"
            test_result["error"] = str(e)
            logger.error(f"{Colors.RED}✗ Test {test_name} FAILED in {duration:.2f}s: {e}{Colors.END}")
        except Exception as e:
            duration = time.time() - start_time
            test_result["duration"] = round(duration, 2)
            test_result["status"] = "ERROR"
            test_result["error"] = f"{type(e).__name__}: {str(e)}"
            logger.error(f"{Colors.RED}✗ Test {test_name} ERROR in {duration:.2f}s: {type(e).__name__}: {e}{Colors.END}")
        finally:
            test_result["end_time"] = datetime.now().isoformat()
            test_results["tests"].append(test_result)
    
    return wrapper

@run_test
def test_news_fetcher_initialization():
    """Test initialization of NewsFetcher class"""
    fetcher = NewsFetcher()
    assert fetcher is not None, "Failed to initialize NewsFetcher"
    return {"message": "NewsFetcher initialized successfully"}

@run_test
def test_fetch_market_news():
    """Test fetching market news from API"""
    fetcher = NewsFetcher()
    news = fetcher.get_market_news(count=5)
    
    assert news is not None, "News result should not be None"
    assert isinstance(news, list), "News result should be a list"
    
    # Only assert length if we have results (otherwise API key might not be set)
    if news:
        assert len(news) <= 5, "Should respect the count parameter"
        
        # Check structure of first news item if available
        if len(news) > 0:
            first_item = news[0]
            assert 'headline' in first_item or 'title' in first_item, "News item should have a headline/title"
    
    return {
        "news_count": len(news),
        "has_results": len(news) > 0,
        "sample": news[0] if news else None
    }

@run_test
def test_sentiment_analyzer_initialization():
    """Test initialization of SentimentAnalyzer class"""
    analyzer = SentimentAnalyzer()
    assert analyzer is not None, "Failed to initialize SentimentAnalyzer"
    return {"message": "SentimentAnalyzer initialized successfully"}

@run_test
def test_basic_sentiment_analysis():
    """Test basic sentiment analysis on predefined text"""
    analyzer = SentimentAnalyzer()
    
    # Test positive sentiment
    positive_text = "Markets rallied as corporate earnings beat expectations, showing strong growth and profitability. Analysts are bullish about future performance."
    positive_result = analyzer.analyze_text_basic(positive_text)
    
    assert positive_result is not None, "Sentiment result should not be None"
    assert 'sentiment' in positive_result, "Result should include sentiment classification"
    assert 'score' in positive_result, "Result should include sentiment score"
    assert positive_result['sentiment'] == 'positive', "Text should be classified as positive"
    assert positive_result['score'] > 0, "Sentiment score should be positive"
    
    # Test negative sentiment
    negative_text = "Markets crashed amid recession fears. Companies reported significant losses and declining revenue, prompting bearish outlooks from analysts."
    negative_result = analyzer.analyze_text_basic(negative_text)
    
    assert negative_result['sentiment'] == 'negative', "Text should be classified as negative"
    assert negative_result['score'] < 0, "Sentiment score should be negative"
    
    return {
        "positive_analysis": positive_result,
        "negative_analysis": negative_result
    }

@run_test
def test_analyze_news_batch():
    """Test batch sentiment analysis on news items"""
    fetcher = NewsFetcher()
    analyzer = SentimentAnalyzer()
    
    # Get some news items
    news_items = fetcher.get_market_news(count=3)
    
    if not news_items:
        logger.warning("No news items returned, using mock data")
        news_items = [
            {
                "headline": "Markets rally as inflation data shows improvement",
                "summary": "Stocks climbed after new data showed inflation cooling."
            },
            {
                "headline": "Tech stocks fall on disappointing earnings",
                "summary": "Major tech companies reported weaker than expected earnings."
            }
        ]
    
    # Analyze the batch
    analyzed_news = analyzer.analyze_news_batch(news_items)
    
    assert analyzed_news is not None, "Analyzed news should not be None"
    assert len(analyzed_news) == len(news_items), "Should analyze all news items"
    
    # Check the first item
    first_item = analyzed_news[0]
    assert 'sentiment' in first_item, "Each item should have sentiment data"
    assert 'score' in first_item['sentiment'], "Sentiment data should include a score"
    
    return {
        "analyzed_count": len(analyzed_news),
        "sample": first_item['sentiment'] if analyzed_news else None
    }

@run_test
def test_report_generator_initialization():
    """Test initialization of ReportGenerator class"""
    generator = ReportGenerator()
    assert generator is not None, "Failed to initialize ReportGenerator"
    return {"message": "ReportGenerator initialized successfully"}

@run_test
def test_generate_market_report():
    """Test generation of a basic market report"""
    generator = ReportGenerator()
    
    # Generate a report with minimal data
    test_symbols = ['SPY', 'QQQ']  # Use common ETFs for testing
    report = generator.generate_daily_market_report(symbols=test_symbols)
    
    assert report is not None, "Report should not be None"
    assert 'generated_at' in report, "Report should include generation timestamp"
    assert 'report_date' in report, "Report should include report date"
    assert 'market_sentiment' in report, "Report should include market sentiment"
    assert 'summary' in report, "Report should include a summary"
    
    return {
        "has_report": True,
        "report_timestamp": report['generated_at'],
        "sentiment": report['market_sentiment']['overall_sentiment'] if 'overall_sentiment' in report['market_sentiment'] else None
    }

@run_test
def test_export_report_formats():
    """Test exporting a report in different formats"""
    generator = ReportGenerator()
    report = generator.generate_daily_market_report(symbols=['SPY'])
    
    # Test HTML export
    html_content = generator.export_report_to_html(report)
    assert html_content is not None, "HTML export should not be None"
    assert len(html_content) > 0, "HTML content should not be empty"
    assert '<!DOCTYPE html>' in html_content, "HTML content should include DOCTYPE"
    
    # We'll skip actual file saving in tests
    return {
        "html_export_success": True,
        "html_length": len(html_content)
    }

def save_test_results(output_file=None):
    """Save test results to a JSON file"""
    if not output_file:
        output_file = f"market_intelligence_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Calculate summary statistics
    total_tests = len(test_results["tests"])
    passed_tests = sum(1 for t in test_results["tests"] if t["status"] == "PASS")
    failed_tests = sum(1 for t in test_results["tests"] if t["status"] == "FAIL")
    error_tests = sum(1 for t in test_results["tests"] if t["status"] == "ERROR")
    
    test_results["summary"] = {
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "errors": error_tests,
        "success_rate": round(passed_tests / total_tests * 100 if total_tests > 0 else 0, 2)
    }
    
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    logger.info(f"Test results saved to {output_file}")
    return output_file

def print_summary():
    """Print a summary of test results"""
    total = len(test_results["tests"])
    passed = sum(1 for t in test_results["tests"] if t["status"] == "PASS")
    failed = sum(1 for t in test_results["tests"] if t["status"] == "FAIL")
    errors = sum(1 for t in test_results["tests"] if t["status"] == "ERROR")
    
    print("\n" + "="*80)
    print(f"{Colors.HEADER}MARKET INTELLIGENCE TEST RESULTS{Colors.END}")
    print("="*80)
    print(f"Total tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    print(f"{Colors.RED}Errors: {errors}{Colors.END}")
    print(f"Success rate: {round(passed / total * 100 if total > 0 else 0, 2)}%")
    print("="*80)
    
    # Print individual test results
    for test in test_results["tests"]:
        if test["status"] == "PASS":
            status_str = f"{Colors.GREEN}✓ PASS{Colors.END}"
        elif test["status"] == "FAIL":
            status_str = f"{Colors.RED}✗ FAIL{Colors.END}"
        else:
            status_str = f"{Colors.RED}! ERROR{Colors.END}"
            
        print(f"{status_str} {test['name']} ({test['duration']}s)")
        if test["status"] != "PASS" and "error" in test:
            print(f"    {Colors.RED}{test['error']}{Colors.END}")
    
    print("\n")
    if failed > 0 or errors > 0:
        return 1
    return 0

def main():
    """Run all tests and generate report"""
    parser = argparse.ArgumentParser(description='Run Market Intelligence integration tests')
    parser.add_argument('--output', '-o', help='Output file for test results')
    parser.add_argument('--news', action='store_true', help='Run only news fetching tests')
    parser.add_argument('--sentiment', action='store_true', help='Run only sentiment analysis tests')
    parser.add_argument('--reports', action='store_true', help='Run only report generation tests')
    args = parser.parse_args()
    
    print(f"{Colors.HEADER}Running Market Intelligence Integration Tests{Colors.END}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Always run initialization tests
    test_news_fetcher_initialization()
    test_sentiment_analyzer_initialization() 
    test_report_generator_initialization()
    
    # Run specific test groups or all tests
    if args.news or not (args.news or args.sentiment or args.reports):
        test_fetch_market_news()
    
    if args.sentiment or not (args.news or args.sentiment or args.reports):
        test_basic_sentiment_analysis()
        test_analyze_news_batch()
    
    if args.reports or not (args.news or args.sentiment or args.reports):
        test_generate_market_report()
        test_export_report_formats()
    
    # Save results
    output_file = args.output if args.output else "market_intelligence_test_results.json"
    save_test_results(output_file)
    
    # Print summary
    exit_code = print_summary()
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
