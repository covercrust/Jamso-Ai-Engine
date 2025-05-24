#!/usr/bin/env python3
"""
AI Module Testing Script

This module runs tests on the AI trading components, including:
- Regime detection accuracy
- Position sizing performance
- Risk management evaluations

Usage:
    python3 test_ai_modules.py [--component COMPONENT] [--symbols SYMBOL1,SYMBOL2,...]

Example:
    python3 test_ai_modules.py --component regime_detector --symbols EURUSD,BTCUSD
"""

import argparse
import logging
import os
import sys
import time
import json
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import AI modules
from src.AI.regime_detector import VolatilityRegimeDetector
from src.AI.position_sizer import AdaptivePositionSizer
from src.AI.risk_manager import RiskManager
from src.AI.data_collector import create_default_collector

# Configure logging
log_file = os.path.join(os.path.dirname(__file__), '../../Logs/ai_module_tests.log')
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

class RegimeDetectorTests(unittest.TestCase):
    """Tests for the VolatilityRegimeDetector class."""
    
    def __init__(self, *args, symbols=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbols = symbols or ['EURUSD', 'BTCUSD']
        self.detector = VolatilityRegimeDetector(n_clusters=3)
        
    def setUp(self):
        # Ensure we have test data
        collector = create_default_collector(self.symbols)
        for symbol in self.symbols:
            if not collector.collect_historical_data(symbol):
                self.skipTest(f"Insufficient data for {symbol}")
    
    def test_regime_detection(self):
        """Test that regimes can be detected for each symbol."""
        for symbol in self.symbols:
            regime_id = self.detector.train(symbol)
            self.assertGreaterEqual(regime_id, 0, f"Failed to detect regime for {symbol}")
            
            # Get and validate regime info
            regime_info = self.detector.get_current_regime(symbol)
            self.assertIsNotNone(regime_info, f"No regime info returned for {symbol}")
            self.assertIn('volatility_level', regime_info, f"Missing volatility level for {symbol}")
            
            logger.info(f"Detected regime {regime_id} ({regime_info.get('volatility_level')}) for {symbol}")
            
    def test_regime_stability(self):
        """Test that regimes are stable across multiple runs."""
        for symbol in self.symbols:
            # Run detection twice
            regime1 = self.detector.train(symbol)
            time.sleep(1)  # Short delay
            regime2 = self.detector.train(symbol)
            
            self.assertEqual(regime1, regime2, f"Regime detection unstable for {symbol}")
            
    def test_regime_characteristics(self):
        """Test that regime characteristics are meaningful."""
        for symbol in self.symbols:
            self.detector.train(symbol)
            characteristics = self.detector.regime_characteristics.get(symbol, {})
            
            self.assertGreater(len(characteristics), 0, 
                              f"No regime characteristics found for {symbol}")
            
            # Check that regimes have distinct volatility levels
            volatility_levels = set()
            for regime_id, data in characteristics.items():
                vol_level = data.get('volatility_level')
                self.assertIsNotNone(vol_level, f"Missing volatility level for regime {regime_id}")
                volatility_levels.add(vol_level)
            
            # Should have at least 2 different volatility levels
            self.assertGreaterEqual(len(volatility_levels), 2, 
                                   f"Not enough distinct volatility levels for {symbol}")

class PositionSizerTests(unittest.TestCase):
    """Tests for the AdaptivePositionSizer class."""
    
    def __init__(self, *args, symbols=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbols = symbols or ['EURUSD', 'BTCUSD']
        self.position_sizer = AdaptivePositionSizer()
    
    def test_position_sizing(self):
        """Test position sizing calculations."""
        for symbol in self.symbols:
            # Test with different account balances and position sizes
            test_cases = [
                {'balance': 10000, 'size': 1.0},
                {'balance': 10000, 'size': 5.0},
                {'balance': 1000, 'size': 1.0},
                {'balance': 100000, 'size': 10.0}
            ]
            
            for case in test_cases:
                original_size = case['size']
                
                # Mock account balance
                account_id = 1
                self._mock_account_balance(account_id, case['balance'])
                
                # Calculate position size
                result = self.position_sizer.calculate_position_size(
                    symbol=symbol,
                    account_id=account_id,
                    original_size=original_size
                )
                
                adjusted_size = result.get('adjusted_size')
                self.assertIsNotNone(adjusted_size, "No position size returned")
                
                # Check that the adjustment is within bounds
                self.assertLessEqual(adjusted_size, 
                                    original_size * 2,  
                                    "Position size increased too much")
                                    
                self.assertGreaterEqual(adjusted_size, 
                                       original_size * 0.2,  
                                       "Position size reduced too much")
                
                logger.info(f"{symbol} position sizing with {case['balance']} balance: " +
                           f"{original_size} -> {adjusted_size} " +
                           f"({result.get('total_adjustment_factor', 1.0):.2f}x)")
    
    def _mock_account_balance(self, account_id, balance):
        """Mock account balance in the database for testing."""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect(self.position_sizer.db_path)
            cursor = conn.cursor()
            
            # Check if account exists
            cursor.execute("SELECT COUNT(*) FROM account_balances WHERE account_id = ?", 
                          (account_id,))
            exists = cursor.fetchone()[0] > 0
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if exists:
                # Update existing account
                cursor.execute("""
                UPDATE account_balances 
                SET balance = ?, equity = ?, timestamp = ?
                WHERE account_id = ?
                """, (balance, balance, timestamp, account_id))
            else:
                # Insert new account record
                cursor.execute("""
                INSERT INTO account_balances 
                (account_id, balance, equity, timestamp, peak_balance, max_drawdown, drawdown_percent, source)
                VALUES (?, ?, ?, ?, ?, 0, 0, 'TEST')
                """, (account_id, balance, balance, timestamp, balance))
                
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error mocking account balance: {e}")
            raise

class RiskManagerTests(unittest.TestCase):
    """Tests for the RiskManager class."""
    
    def __init__(self, *args, symbols=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbols = symbols or ['EURUSD', 'BTCUSD']
        self.risk_manager = RiskManager()
    
    def test_risk_evaluation(self):
        """Test risk evaluation logic."""
        for symbol in self.symbols:
            # Create test signal data
            signal_data = {
                'ticker': symbol,
                'order_action': 'buy',
                'position_size': 1.0,
                'price': 100.0,
                'stop_loss': 95.0,
                'account_id': 1
            }
            
            # Mock account balance
            self._mock_account_balance(signal_data['account_id'], 10000)
            
            # Test risk evaluation
            result = self.risk_manager.evaluate_trade_risk(signal_data, signal_data['account_id'])
            
            self.assertIsNotNone(result, f"No risk evaluation returned for {symbol}")
            self.assertIn('status', result, f"Missing status in risk evaluation for {symbol}")
            
            logger.info(f"Risk evaluation for {symbol}: {result.get('status')} " +
                       f"(Risk: {result.get('risk_amount', 0):.2f}, " +
                       f"{result.get('risk_percent', 0):.2f}%)")
    
    def test_stop_loss_adjustment(self):
        """Test stop loss adjustment logic."""
        for symbol in self.symbols:
            current_price = 100.0
            initial_stop = 95.0
            
            # Test with different volatility levels
            for vol_level in ['LOW', 'MEDIUM', 'HIGH']:
                adjusted_stop = self.risk_manager.adjust_stop_loss(
                    symbol=symbol,
                    current_price=current_price,
                    stop_loss=initial_stop,
                    volatility_level=vol_level
                )
                
                self.assertIsNotNone(adjusted_stop, f"No stop loss returned for {vol_level}")
                
                # Check that stop is adjusted in the correct direction
                if vol_level == 'HIGH':
                    self.assertLess(adjusted_stop, initial_stop, 
                                   "High volatility should widen stop loss")
                elif vol_level == 'LOW':
                    self.assertGreaterEqual(adjusted_stop, initial_stop, 
                                          "Low volatility should tighten stop loss")
                
                logger.info(f"{symbol} stop loss adjustment for {vol_level} volatility: " +
                           f"{initial_stop:.2f} -> {adjusted_stop:.2f} " +
                           f"({(current_price - adjusted_stop):.2f} points)")
    
    def _mock_account_balance(self, account_id, balance):
        """Mock account balance in the database for testing."""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect(self.risk_manager.db_path)
            cursor = conn.cursor()
            
            # Check if account exists
            cursor.execute("SELECT COUNT(*) FROM account_balances WHERE account_id = ?", 
                          (account_id,))
            exists = cursor.fetchone()[0] > 0
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if exists:
                # Update existing account
                cursor.execute("""
                UPDATE account_balances 
                SET balance = ?, equity = ?, timestamp = ?
                WHERE account_id = ?
                """, (balance, balance, timestamp, account_id))
            else:
                # Insert new account record
                cursor.execute("""
                INSERT INTO account_balances 
                (account_id, balance, equity, timestamp, peak_balance, max_drawdown, drawdown_percent, source)
                VALUES (?, ?, ?, ?, ?, 0, 0, 'TEST')
                """, (account_id, balance, balance, timestamp, balance))
                
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error mocking account balance: {e}")
            raise

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test AI trading modules')
    
    parser.add_argument('--component', type=str, default='all',
                       choices=['all', 'regime_detector', 'position_sizer', 'risk_manager'],
                       help='Component to test')
    
    parser.add_argument('--symbols', type=str, default='EURUSD,BTCUSD',
                       help='Comma-separated list of symbols to test with')
    
    return parser.parse_args()

def main():
    """Main function to run tests."""
    args = parse_args()
    
    # Get symbols from arguments
    symbols = args.symbols.split(',')
    
    # Set up test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases based on component
    if args.component in ['all', 'regime_detector']:
        test_suite.addTest(RegimeDetectorTests('test_regime_detection', symbols=symbols))
        test_suite.addTest(RegimeDetectorTests('test_regime_stability', symbols=symbols))
        test_suite.addTest(RegimeDetectorTests('test_regime_characteristics', symbols=symbols))
        
    if args.component in ['all', 'position_sizer']:
        test_suite.addTest(PositionSizerTests('test_position_sizing', symbols=symbols))
        
    if args.component in ['all', 'risk_manager']:
        test_suite.addTest(RiskManagerTests('test_risk_evaluation', symbols=symbols))
        test_suite.addTest(RiskManagerTests('test_stop_loss_adjustment', symbols=symbols))
    
    # Run tests
    logger.info(f"Starting AI module tests for component: {args.component}")
    start_time = time.time()
    
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Log completion time
    elapsed_time = time.time() - start_time
    logger.info(f"Tests completed in {elapsed_time:.2f} seconds")
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    import sqlite3  # Import here for database operations
    sys.exit(main())
