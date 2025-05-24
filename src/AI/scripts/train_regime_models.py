#!/usr/bin/env python3
"""
Volatility Regime Detection Training Script

This script trains volatility regime detection models for specified market symbols.
It can be run manually or scheduled to retrain models with updated market data.

Usage:
    python3 train_regime_models.py [--symbols SYMBOL1,SYMBOL2,...] [--clusters CLUSTERS] [--days DAYS]

Example:
    python3 train_regime_models.py --symbols EURUSD,BTCUSD,US500 --clusters 4 --days 120
"""

import argparse
import logging
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Any

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the regime detector
from src.AI.regime_detector import VolatilityRegimeDetector
from src.AI.data_collector import create_default_collector

# Configure logging
log_file = os.path.join(os.path.dirname(__file__), '../../Logs/regime_detection_training.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Train volatility regime detection models')
    
    parser.add_argument('--symbols', type=str, default='',
                       help='Comma-separated list of symbols to train models for')
    
    parser.add_argument('--clusters', type=int, default=3,
                       help='Number of volatility regimes (clusters) to detect')
    
    parser.add_argument('--days', type=int, default=120,
                       help='Number of days of historical data to use for training')
    
    parser.add_argument('--visualize', action='store_true',
                       help='Generate visualization of the regimes')
    
    return parser.parse_args()

def visualize_regimes(detector: VolatilityRegimeDetector, symbol: str):
    """Generate visualization of detected regimes."""
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np
        
        # Visualize the regimes with historical data
        conn = sqlite3.connect(detector.db_path)
        
        # Get market data with regime labels
        query = """
        SELECT 
            m.timestamp, 
            m.close, 
            m.volatility,
            m.atr,
            COALESCE(r.regime_id, -1) as regime_id,
            COALESCE(r.volatility_level, 'UNKNOWN') as volatility_level
        FROM market_volatility m
        LEFT JOIN volatility_regimes r ON m.symbol = r.symbol AND m.timestamp = r.timestamp
        WHERE m.symbol = ?
        ORDER BY m.timestamp ASC
        """
        
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        
        if len(df) < 10:
            logger.warning(f"Insufficient data for visualization of {symbol}")
            return
        
        # Create plots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # Plot 1: Price chart with regime coloring
        ax1.set_title(f"Volatility Regimes for {symbol}")
        
        # Define colors for different regimes
        colors = ['blue', 'orange', 'red', 'green', 'purple']
        
        for regime in sorted(df['regime_id'].unique()):
            if regime == -1:
                continue
            regime_data = df[df['regime_id'] == regime]
            color = colors[regime % len(colors)]
            ax1.plot(regime_data['timestamp'], regime_data['close'], 'o-', 
                     color=color, label=f"Regime {regime}")
        
        ax1.legend()
        ax1.set_ylabel('Price')
        
        # Plot 2: Volatility chart
        ax2.plot(df['timestamp'], df['volatility'], 'b-')
        ax2.set_ylabel('Volatility (annualized)')
        
        # Plot 3: ATR chart
        ax3.plot(df['timestamp'], df['atr'], 'g-')
        ax3.set_ylabel('ATR')
        ax3.set_xlabel('Date')
        
        # Adjust layout and save
        plt.tight_layout()
        
        # Create visualizations directory if it doesn't exist
        viz_dir = os.path.join(os.path.dirname(__file__), '../../Logs/visualizations')
        os.makedirs(viz_dir, exist_ok=True)
        
        # Save the plot
        plt.savefig(os.path.join(viz_dir, f"{symbol}_volatility_regimes.png"))
        logger.info(f"Saved visualization to {viz_dir}/{symbol}_volatility_regimes.png")
        
    except Exception as e:
        logger.error(f"Error generating visualization for {symbol}: {e}")

def main():
    """Main function to train regime detection models."""
    args = parse_args()
    
    # Get symbols from arguments or available data
    symbols = args.symbols.split(',') if args.symbols else None
    
    if not symbols:
        # Use data collector to get available symbols
        collector = create_default_collector()
        symbols = collector.get_available_symbols()
        
        if not symbols:
            logger.error("No symbols specified and no data available")
            return 1
    
    # Log start of training
    logger.info(f"Starting volatility regime detection training for {symbols}")
    start_time = time.time()
    
    # Create regime detector with specified parameters
    detector = VolatilityRegimeDetector(
        n_clusters=args.clusters,
        lookback_days=args.days
    )
    
    results = {}
    
    # Train models for each symbol
    for symbol in symbols:
        try:
            logger.info(f"Training regime detection model for {symbol}")
            
            # Train the model
            regime_id = detector.train(symbol)
            
            if regime_id >= 0:
                # Get regime characteristics
                regime_info = detector.get_current_regime(symbol)
                
                # Store result
                results[symbol] = {
                    'current_regime': regime_id,
                    'volatility_level': regime_info.get('volatility_level', 'UNKNOWN'),
                    'training_success': True
                }
                
                logger.info(f"Successfully trained regime model for {symbol}. " +
                           f"Current regime: {regime_id} ({regime_info.get('volatility_level', 'UNKNOWN')})")
                
                # Generate visualization if requested
                if args.visualize:
                    visualize_regimes(detector, symbol)
            else:
                results[symbol] = {
                    'training_success': False,
                    'error': 'Training failed'
                }
                logger.warning(f"Failed to train regime model for {symbol}")
                
        except Exception as e:
            results[symbol] = {
                'training_success': False,
                'error': str(e)
            }
            logger.error(f"Error training regime model for {symbol}: {e}")
    
    # Log summary
    success_count = sum(1 for r in results.values() if r.get('training_success', False))
    logger.info(f"Training completed for {success_count}/{len(symbols)} symbols")
    
    # Save results to a JSON file
    results_file = os.path.join(os.path.dirname(__file__), 
                              f'../../Logs/regime_training_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {results_file}")
    
    # Log completion time
    elapsed_time = time.time() - start_time
    logger.info(f"Training completed in {elapsed_time:.2f} seconds")
    return 0

if __name__ == "__main__":
    import sqlite3  # Import here for visualize_regimes function
    sys.exit(main())
