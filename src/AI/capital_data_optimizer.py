#!/usr/bin/env python3
"""
Capital.com API Integration for Parameter Optimizer

This script integrates real market data from Capital.com with the parameter optimization framework from the standalone optimizer.

Usage:
    python capital_data_optimizer.py --symbol BTCUSD --timeframe HOUR --days 30 --objective sharpe --max-evals 20
"""

import os
import sys
import pandas as pd
import numpy as np
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Import and load dotenv first thing to ensure environment variables are available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file if it exists
except ImportError:
    print("python-dotenv not installed. Environment variables may not be loaded properly.")
    # Try to install it
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
        from dotenv import load_dotenv
        load_dotenv()
        print("Installed and loaded python-dotenv successfully.")
    except Exception as e:
        print(f"Failed to install python-dotenv: {e}")
        print("Make sure to run: pip install python-dotenv")

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path to access the standalone optimizer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Define optimization objectives locally
OBJECTIVES = {
    'sharpe': lambda metrics: metrics.get('sharpe_ratio', 0),
    'return': lambda metrics: metrics.get('total_return', 0),
    'calmar': lambda metrics: metrics.get('total_return', 0) / abs(metrics.get('max_drawdown', 1)),
    'win_rate': lambda metrics: metrics.get('win_rate', 0),
    'risk_adjusted': lambda metrics: metrics.get('total_return', 0) / (abs(metrics.get('max_drawdown', 1)) + 0.01),
}

# Import code below might fail if dependencies are missing
# We'll handle each import separately to provide better error messages

# Try to import from standalone optimizer, but provide fallbacks
standalone_imports_successful = False
try:
    from src.AI.standalone_optimizer import (
        supertrend_strategy, 
        calculate_metrics, 
        optimize_parameters, 
        OBJECTIVES
    )
    # Import plot_optimization_results separately to handle possible import issues
    # Define a fallback for plot_optimization_results
    plot_optimization_results = None  # This will be overridden if the import succeeds later
    standalone_imports_successful = True
    logger.info("Successfully imported functions from standalone optimizer")
except ImportError as e:
    logger.warning(f"Could not import from standalone optimizer: {str(e)}")
    logger.warning("Using built-in implementations instead")
    plot_optimization_results = None  # Fallback for static analysis
    # We'll define these functions later if needed

# Try to import Capital.com API
capital_api_imported = False
try:
    from src.Exchanges.capital_com_api.client import Client
    from src.Exchanges.capital_com_api.market_data_manager import MarketDataManager
    from src.Exchanges.capital_com_api.session_manager import SessionManager
    from src.Exchanges.capital_com_api.request_handler import RequestHandler
    logger.info("Successfully imported Capital.com API modules")
    capital_api_imported = True
except ImportError as e:
    logger.warning(f"Failed to import Capital.com API modules: {str(e)}")
    logger.warning("Attempting to use fallback API client...")
    
    # Try to import fallback API client
    try:
        from src.AI.fallback_capital_api import FallbackApiClient
        logger.info("Successfully imported fallback Capital.com API client")
        capital_api_imported = True
    except ImportError as e2:
        logger.error(f"Failed to import fallback API client: {str(e2)}")
        logger.error("Make sure python-dotenv and requests are installed:")
        logger.error("    pip install python-dotenv requests")
        sys.exit(1)

# Resolution mapping from command line args to API parameters
RESOLUTION_MAP = {
    'MINUTE': 'MINUTE',
    'MINUTE_5': 'MINUTE_5',
    'MINUTE_15': 'MINUTE_15',
    'MINUTE_30': 'MINUTE_30',
    'HOUR': 'HOUR',
    'HOUR_4': 'HOUR_4',
    'DAY': 'DAY',
    'WEEK': 'WEEK',
    'MONTH': 'MONTH'
}

def fetch_market_data(symbol: str, resolution: str = 'HOUR', days: int = 30) -> pd.DataFrame:
    """
    Fetch historical price data from Capital.com API
    
    Parameters:
    - symbol: Market symbol/epic (e.g., 'BTCUSD', 'EURUSD')
    - resolution: Timeframe ('MINUTE', 'HOUR', 'DAY', etc.)
    - days: Number of days of data to fetch
    
    Returns:
    - DataFrame with OHLCV data
    """
    logger.info(f"Fetching {days} days of {resolution} data for {symbol}")
    
    # Calculate number of candles based on resolution and days
    # We need to consider trading hours and weekends for some resolutions
    candle_multiplier = {
        'MINUTE': 24 * 60,    # Minutes per day
        'MINUTE_5': 24 * 12,  # 5-minute candles per day
        'MINUTE_15': 24 * 4,  # 15-minute candles per day
        'MINUTE_30': 24 * 2,  # 30-minute candles per day
        'HOUR': 24,           # Hours per day
        'HOUR_4': 6,          # 4-hour candles per day
        'DAY': 1,             # Days per day
        'WEEK': 1/7,          # Weeks per day
        'MONTH': 1/30         # Months per day (approximate)
    }
    
    # Calculate max parameter for API (max candles to retrieve)
    max_candles = int(days * candle_multiplier.get(resolution, 1))
    
    # Cap at 1000 which is usually the API limit
    if max_candles > 1000:
        logger.warning(f"Requested {max_candles} candles, capping at 1000 (API limit)")
        max_candles = 1000
    
    try:
        candles = []
        # First try using the standard API client
        try:
            if 'Client' in globals():
                # Initialize the Capital.com API client
                client = Client()
                
                # Fetch historical price data
                price_data = client.market_data_manager.prices(
                    epic=symbol,
                    resolution=resolution,
                    max=max_candles
                )
                
                # Extract price data from the response
                candles = price_data.get('prices', [])
                logger.info(f"Successfully fetched data using standard API client: {len(candles)} candles")
        except Exception as e:
            logger.warning(f"Error using standard API: {str(e)}")
            logger.warning("Attempting to use fallback API client...")
            
            # If standard client fails, try the fallback client
            try:
                if 'FallbackApiClient' in globals():
                    fallback_client = FallbackApiClient()
                    candles = fallback_client.get_historical_prices(
                        symbol=symbol,
                        resolution=resolution,
                        days=days,
                        max_candles=max_candles
                    ) or []
                    
                    if candles:
                        logger.info(f"Successfully fetched data using fallback API client: {len(candles)} candles")
                    else:
                        logger.error("Fallback API client returned no data")
            except Exception as e2:
                logger.error(f"Error using fallback API: {str(e2)}")
        
        if not candles:
            logger.error(f"No price data returned for {symbol} from either API client")
            return pd.DataFrame()
        
        # Convert to pandas DataFrame
        data = []
        for candle in candles:
            # Extract OHLCV data
            timestamp = candle.get('snapshotTimeUTC')
            # Handle differences between standard and fallback API responses
            open_price = high_price = low_price = close_price = None
            if 'openPrice' in candle and isinstance(candle['openPrice'], dict):
                open_price = candle.get('openPrice', {}).get('bid')
                high_price = candle.get('highPrice', {}).get('bid')
                low_price = candle.get('lowPrice', {}).get('bid')
                close_price = candle.get('closePrice', {}).get('bid')
            else:
                open_price = candle.get('openPrice') or candle.get('open')
                high_price = candle.get('highPrice') or candle.get('high')
                low_price = candle.get('lowPrice') or candle.get('low')
                close_price = candle.get('closePrice') or candle.get('close')
            volume = candle.get('lastTradedVolume', 0) or candle.get('volume', 0)
            # Skip incomplete candles
            if not all([timestamp, open_price, high_price, low_price, close_price]):
                continue
            # Explicit type guards for static analysis
            if open_price is None or high_price is None or low_price is None or close_price is None:
                continue
            data.append({
                'timestamp': timestamp,
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'close': float(close_price),
                'volume': float(volume)
            })
        
        # Create DataFrame and sort by timestamp
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate ATR (Average True Range)
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            df['atr'] = df['tr'].rolling(window=14).mean().fillna(df['tr'])
            
            # Clean up temporary columns
            df = df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1)
            
            logger.info(f"Fetched {len(df)} candles from {df['timestamp'].min()} to {df['timestamp'].max()}")
            return df
        else:
            logger.error("Failed to create DataFrame from candle data")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return pd.DataFrame()

def fetch_market_sentiment(symbol: str) -> dict:
    """
    Fetch market sentiment data from Capital.com API
    
    Parameters:
    - symbol: Market symbol/epic (e.g., 'BTCUSD', 'EURUSD')
    
    Returns:
    - Dictionary with sentiment data
    """
    try:
        # Initialize the Capital.com API client
        client = Client()
        
        # Fetch sentiment data
        sentiment_data = client.market_data_manager.client_sentiment(symbol)
        
        # Extract relevant information
        if sentiment_data:
            return {
                'long_position_percentage': sentiment_data.get('longPositionPercentage', 50),
                'short_position_percentage': sentiment_data.get('shortPositionPercentage', 50)
            }
        else:
            logger.warning(f"No sentiment data returned for {symbol}")
            return {'long_position_percentage': 50, 'short_position_percentage': 50}
            
    except Exception as e:
        logger.error(f"Error fetching market sentiment: {str(e)}")
        return {'long_position_percentage': 50, 'short_position_percentage': 50}

def supertrend_with_sentiment(df: pd.DataFrame, atr_len=10, fact=3.0, risk_percent=1.0, sl_percent=0.5,
                            tp_percent=1.5, initial_capital=10000, direction_bias="Both",
                            sentiment_weight=0.2, symbol=None, timeframe=None):
    """
    Enhanced SuperTrend strategy with sentiment analysis integration.
    
    Parameters:
    - df: DataFrame with price data
    - atr_len, fact, etc.: Standard SuperTrend parameters
    - sentiment_weight: How much to weigh sentiment data (0-1 range)
    """
    # Make a copy of the DataFrame
    df = df.copy()
    
    # Get sentiment data if available using our new sentiment integration module
    if 'sentiment' not in df.columns:
        try:
            # Try to import the sentiment integration module
            from src.AI.sentiment_integration import SentimentIntegration
            
            # Calculate date range for sentiment data
            start_date = df['timestamp'].min().strftime('%Y-%m-%d')
            end_date = df['timestamp'].max().strftime('%Y-%m-%d')
            
            # Get sentiment data for the symbol and timeframe
            sentiment = SentimentIntegration()
            sentiment_series = sentiment.get_combined_sentiment_series(
                symbol or "UNKNOWN",
                timeframe or "HOUR",
                start_date=start_date, 
                end_date=end_date
            )
            
            # Convert sentiment from -1/+1 scale to 0-1 scale
            sentiment_series = (sentiment_series + 1) / 2
            
            # Merge with dataframe using timestamp as index
            df.set_index('timestamp', inplace=True)
            df['sentiment'] = sentiment_series
            df.reset_index(inplace=True)
            
            # Fill any missing values with neutral sentiment
            df['sentiment'] = df['sentiment'].fillna(0.5)
            
            logger.info(f"Successfully integrated sentiment data with price data")
        except Exception as e:
            logger.warning(f"Failed to load sentiment data: {e}")
            df['sentiment'] = 0.5  # Default to neutral sentiment
    
    # Run the standard SuperTrend strategy to get baseline signals
    result = supertrend_strategy(df, atr_len, fact, risk_percent, sl_percent, 
                               tp_percent, initial_capital, direction_bias)
    
    # Enhance with sentiment data
    if sentiment_weight > 0 and 'sentiment' in df.columns:
        # Apply sentiment adjustment to position sizing or entry/exit timing
        # This is a simple implementation - you can make it more sophisticated
        
        # Example: Adjust position size based on sentiment aligned with trend
        trades = result.get('trades', [])
        for i, trade in enumerate(trades):
            # Get sentiment at trade entry time
            entry_time = trade['entry_time']
            entry_idx = df[df['timestamp'] == entry_time].index
            
            if len(entry_idx) > 0:
                sentiment_value = df.iloc[entry_idx[0]]['sentiment']
                
                # Adjust position size based on sentiment alignment with trade direction
                if trade['direction'] == 'long' and sentiment_value > 0.5:
                    # Bullish sentiment for long trade - increase position
                    trade['position_size'] *= (1 + (sentiment_value - 0.5) * sentiment_weight)
                elif trade['direction'] == 'short' and sentiment_value < 0.5:
                    # Bearish sentiment for short trade - increase position
                    trade['position_size'] *= (1 + (0.5 - sentiment_value) * sentiment_weight)
                else:
                    # Sentiment against trade direction - reduce position
                    trade['position_size'] *= (1 - abs(sentiment_value - 0.5) * sentiment_weight)
                
                # Update trade profit/loss based on adjusted position size
                trade['profit'] = trade['profit_pct'] * trade['position_size'] * initial_capital / 100
                
                # Update the trades list
                trades[i] = trade
        
        # Update the result with adjusted trades
        result['trades'] = trades
        
        # Recalculate metrics based on adjusted trades
        total_profit = sum(trade['profit'] for trade in trades)
        result['total_return'] = total_profit / initial_capital * 100
        
    return result

def main():
    """Main function to handle command-line arguments and run the optimizer."""
    parser = argparse.ArgumentParser(description="Capital.com Data Parameter Optimizer")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Market symbol/epic")
    parser.add_argument("--timeframe", type=str, default="HOUR", choices=list(RESOLUTION_MAP.keys()), 
                       help="Timeframe to fetch data for")
    parser.add_argument("--days", type=int, default=30, help="Number of days of data to fetch")
    parser.add_argument("--objective", type=str, choices=list(OBJECTIVES.keys()), 
                        default="sharpe", help="Optimization objective")
    parser.add_argument("--max-evals", type=int, default=10, help="Maximum evaluations for optimization")
    parser.add_argument("--save-plot", action="store_true", help="Save optimization results plot")
    parser.add_argument("--save-params", action="store_true", help="Save optimized parameters to JSON file")
    parser.add_argument("--use-sentiment", action="store_true", help="Include sentiment data in optimization")
    parser.add_argument("--sentiment-weight", type=float, default=0.2, 
                       help="Weight to assign to sentiment data (0-1)")
    parser.add_argument("--output", type=str, default=None, 
                       help="Output file path for optimized parameters")
    
    args = parser.parse_args()
    
    # Fetch data from Capital.com API
    df = fetch_market_data(args.symbol, RESOLUTION_MAP[args.timeframe], args.days)
    
    if df is None or df.empty:
        logger.error("Failed to fetch market data. Exiting.")
        sys.exit(1)
    
    # Fetch sentiment data if requested
    if args.use_sentiment:
        try:
            # Try to import the sentiment integration module
            from src.AI.sentiment_integration import SentimentIntegration
            
            logger.info("Using advanced sentiment integration module")
            
            # Fetch historical sentiment data
            sentiment = SentimentIntegration()
            
            # Calculate date range for sentiment data
            start_date = df['timestamp'].min().strftime('%Y-%m-%d')
            end_date = df['timestamp'].max().strftime('%Y-%m-%d')
            
            # Get sentiment data for the symbol and timeframe
            sentiment_series = sentiment.get_combined_sentiment_series(
                args.symbol,
                args.timeframe,
                start_date=start_date, 
                end_date=end_date
            )
            
            if not sentiment_series.empty:
                # Convert sentiment from -1/+1 scale to 0-1 scale
                sentiment_series = (sentiment_series + 1) / 2
                
                # Merge with dataframe using timestamp as index
                df.set_index('timestamp', inplace=True)
                df['sentiment'] = sentiment_series
                df.reset_index(inplace=True)
                
                # Fill any missing values with neutral sentiment
                df['sentiment'] = df['sentiment'].fillna(0.5)
                
                logger.info(f"Successfully integrated historical sentiment data with {len(sentiment_series)} data points")
            else:
                # Fallback to fetching current sentiment if historical data not available
                sentiment_data = fetch_market_sentiment(args.symbol)
                logger.info(f"Using current market sentiment data: {sentiment_data}")
                
                # Add sentiment data to DataFrame as constant value
                sentiment_value = sentiment_data.get('long_position_percentage', 50) / 100
                df['sentiment'] = sentiment_value
                logger.info(f"Using constant sentiment value: {sentiment_value}")
        except Exception as e:
            logger.warning(f"Failed to load advanced sentiment data: {str(e)}")
            
            # Fallback to simple sentiment
            sentiment_data = fetch_market_sentiment(args.symbol)
            logger.info(f"Falling back to current market sentiment data: {sentiment_data}")
            
            # Add sentiment data to DataFrame
            sentiment_value = sentiment_data.get('long_position_percentage', 50) / 100
            df['sentiment'] = sentiment_value
            logger.info(f"Using constant sentiment value: {sentiment_value}")
        
    # Define the parameter search space
    search_space = {
        'atr_period': list(range(10, 30)),  # ATR period
        'atr_multiplier': [x / 10 for x in range(15, 50)],  # SuperTrend multiplier
        'stop_loss': [x / 10 for x in range(10, 40)],  # Stop loss percentage
        'take_profit': [x / 10 for x in range(20, 80)]  # Take profit percentage
    }
    
    # Set up the optimization function based on whether to use sentiment
    if args.use_sentiment:
        # When using sentiment, wrap the standard optimizer function to include sentiment
        def strategy_func(df, params):
            return supertrend_with_sentiment(df, **params, sentiment_weight=args.sentiment_weight, 
                                           symbol=args.symbol, timeframe=args.timeframe)
    else:
        # Use the standard strategy function, wrapped to match (df, params)
        strategy_func = lambda df, params: supertrend_strategy(df, **params)
    
    # Run the optimizer with real market data
    start_time = time.time()
    
    # Different optimize_parameters functions have different parameter names
    # Let's try to handle both formats
    try:
        # First try with the format from optimizer_essentials.py
        best_params, best_value, results = optimize_parameters(
            df, 
            strategy_func,
            search_space,
            objective_name=args.objective,  # type: ignore
            num_evals=args.max_evals  # type: ignore
        )
    except Exception as e1:
        logger.warning(f"First optimization attempt failed: {str(e1)}")
        try:
            # Then try with the format from standalone_optimizer.py
            objective_fn = OBJECTIVES[args.objective]
            best_params, best_value, results = optimize_parameters(
                df, 
                strategy_func,
                search_space, 
                objective_fn,
                max_evals=args.max_evals  # type: ignore
            )
        except Exception as e2:
            logger.warning(f"Second optimization attempt failed: {str(e2)}")
            
            # Try the fallback optimizer as a last resort
            try:
                logger.info("Attempting to use fallback optimizer...")
                # Import the fallback optimizer
                from src.AI.fallback_optimizer import (
                    optimize_parameters as fallback_optimize,
                    supertrend_strategy as fallback_strategy,
                    plot_optimization_results as fallback_plot
                )
                
                # Use the fallback optimizer
                best_params, best_value, results = fallback_optimize(
                    df,
                    fallback_strategy,
                    search_space,
                    objective_name=args.objective,
                    num_evals=args.max_evals
                )
                
                # Update strategy_func to use fallback
                strategy_func = fallback_strategy
                
                # Override the plot_optimization_results function
                plot_optimization_results = fallback_plot
                
                logger.info("Successfully used fallback optimizer")
            except Exception as e3:
                logger.error(f"All optimization attempts failed: {str(e3)}")
                logger.error("Could not optimize parameters. Check your dependencies.")
                sys.exit(1)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Optimization completed in {elapsed_time:.2f} seconds")
    
    # Print optimization results
    logger.info(f"Best parameters found: {best_params}")
    logger.info(f"Best {args.objective} value: {best_value}")
    
    # Run the strategy with best parameters
    if best_params is not None:
        # In fallback_optimizer, backtest_strategy returns (trades_df, equity_curve)
        # While strategy_func just returns a DataFrame with signals
        result_df = strategy_func(df, best_params)
        
        # Run backtest to get trades and equity curve
        try:
            from src.AI.fallback_optimizer import backtest_strategy
            trades_df, equity_curve = backtest_strategy(df, best_params)
            metrics = calculate_metrics(equity_curve, trades_df)
            
            # Display key metrics
            logger.info(f"--- Performance with optimized parameters ---")
            logger.info(f"Total Return: {metrics['total_return']:.2f}%")
            logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            logger.info(f"Win Rate: {metrics['win_rate']:.2f}%")
            logger.info(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        except Exception as e:
            logger.error(f"Error running backtest with optimized parameters: {str(e)}")
            logger.info("Using default metrics instead")
            metrics = {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'max_drawdown': 0.0
            }
        
        # Save parameters to JSON file if applicable
        if args.save_params:
            save_path = f"supertrend_optimized_params_{args.objective}.json"
            logger.info(f"Saving parameters to {save_path}")
            with open(save_path, 'w') as f:
                json.dump(best_params, f, indent=4)
        
        # Plot and save results if applicable
        if args.save_plot and plot_optimization_results is not None and callable(plot_optimization_results):
            plot_path = f"strategy_visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            logger.info(f"Saving strategy visualization to {plot_path}")
            try:
                plot_optimization_results(df, best_params, results, plot_path)  # type: ignore
            except Exception as e:
                logger.error(f"Error calling plot_optimization_results: {e}")
    else:
        logger.error("Optimization failed: No valid parameters found")
        logger.info("Using default parameters as fallback")
        default_params = {
            'atr_period': 14,
            'atr_multiplier': 3.0,
            'stop_loss': 2.0,
            'take_profit': 4.0
        }
        logger.info(f"Default parameters: {default_params}")
        
        # Run with default parameters
        try:
            result_df = strategy_func(df, default_params)
            
            # Run backtest to get trades and equity curve
            from src.AI.fallback_optimizer import backtest_strategy
            trades_df, equity_curve = backtest_strategy(df, default_params)
            metrics = calculate_metrics(equity_curve, trades_df)
            
            # Display key metrics
            logger.info(f"--- Performance with default parameters ---")
            logger.info(f"Total Return: {metrics['total_return']:.2f}%")
            logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            logger.info(f"Win Rate: {metrics['win_rate']:.2f}%")
            logger.info(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        except Exception as e:
            logger.error(f"Error running backtest with default parameters: {str(e)}")
            metrics = {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'max_drawdown': 0.0
            }
    
    # Save results to file
    output_file = args.output
    if output_file is None:
        output_file = f"capital_com_optimized_params_{args.symbol}_{args.timeframe}_{args.objective}.json"
    
    # Save with a timestamp and metadata
    results_data = {
        "params": best_params,
        "metrics": metrics,
        "metadata": {
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "days": args.days,
            "objective": args.objective,
            "use_sentiment": args.use_sentiment,
            "sentiment_weight": args.sentiment_weight if args.use_sentiment else None,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "max_evals": args.max_evals
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=4)
    
    logger.info(f"Optimized parameters saved to {output_file}")
    
    # Plot results if requested
    if args.save_plot and plot_optimization_results is not None and callable(plot_optimization_results):
        plot_file = f"capital_com_strategy_{args.symbol}_{args.timeframe}_{args.objective}.png"
        try:
            plot_optimization_results(df, best_params, results, plot_file)  # type: ignore
            logger.info(f"Strategy plot saved to {plot_file}")
        except Exception as e:
            logger.error(f"Error calling plot_optimization_results: {e}")

if __name__ == "__main__":
    main()
