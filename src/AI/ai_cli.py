#!/usr/bin/env python3
"""
AI Module Command Line Interface

This script provides a command line interface for the AI trading module
to run common tasks and access AI functionality directly.

Usage:
    python3 ai_cli.py <command> [options]

Commands:
    setup           - Set up the AI module environment
    collect-data    - Collect market data for analysis
    train-models    - Train volatility regime models
    run-tests       - Run AI module tests
    get-regime      - Get current volatility regime for a symbol
    calculate-size  - Calculate position size for a symbol
    evaluate-risk   - Evaluate trade risk for a signal
    dashboard       - Start the AI dashboard visualization
"""

import argparse
import sys
import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AI Trading Module CLI")
    
    # Main command argument
    parser.add_argument('command', choices=[
        'setup', 'collect-data', 'train-models', 'run-tests',
        'get-regime', 'calculate-size', 'evaluate-risk', 'dashboard'
    ], help="Command to execute")
    
    # Common options
    parser.add_argument('--symbol', type=str, help="Market symbol to operate on")
    parser.add_argument('--symbols', type=str, help="Comma-separated list of market symbols")
    parser.add_argument('--account-id', type=int, default=1, help="Account ID to use")
    parser.add_argument('--days', type=int, help="Number of days for historical data")
    
    # Setup options
    parser.add_argument('--skip-install', action='store_true', help="Skip package installation in setup")
    
    # Training options
    parser.add_argument('--clusters', type=int, default=3, help="Number of clusters for regime detection")
    parser.add_argument('--visualize', action='store_true', help="Generate visualizations in training")
    
    # Testing options
    parser.add_argument('--component', type=str, choices=[
        'all', 'regime_detector', 'position_sizer', 'risk_manager'
    ], default='all', help="Component to test")
    
    # Position sizing options
    parser.add_argument('--size', type=float, help="Original position size")
    parser.add_argument('--price', type=float, help="Current price")
    parser.add_argument('--stop-loss', type=float, help="Stop loss price")
    
    # Risk evaluation options
    parser.add_argument('--signal', type=str, help="JSON string or file path with signal data")
    parser.add_argument('--direction', type=str, choices=['buy', 'sell'], help="Trade direction")
    
    return parser.parse_args()

def execute_setup(args):
    """Execute the setup command."""
    from src.AI.setup_ai_module import main as setup_main
    
    # Set appropriate sys.argv for the setup script
    sys.argv = ['setup_ai_module.py']
    if args.skip_install:
        sys.argv.append('--skip-install')
    if args.symbols:
        sys.argv.append(f'--symbols={args.symbols}')
        
    return setup_main()

def execute_collect_data(args):
    """Execute the collect-data command."""
    from src.AI.scripts.collect_market_data import main as collect_main
    
    # Set appropriate sys.argv for the collect script
    sys.argv = ['collect_market_data.py']
    if args.symbols:
        sys.argv.append(f'--symbols={args.symbols}')
    if args.days:
        sys.argv.append(f'--days={args.days}')
        
    return collect_main()

def execute_train_models(args):
    """Execute the train-models command."""
    from src.AI.scripts.train_regime_models import main as train_main
    
    # Set appropriate sys.argv for the train script
    sys.argv = ['train_regime_models.py']
    if args.symbols:
        sys.argv.append(f'--symbols={args.symbols}')
    if args.clusters:
        sys.argv.append(f'--clusters={args.clusters}')
    if args.days:
        sys.argv.append(f'--days={args.days}')
    if args.visualize:
        sys.argv.append('--visualize')
        
    return train_main()

def execute_run_tests(args):
    """Execute the run-tests command."""
    from src.AI.scripts.test_ai_modules import main as test_main
    
    # Set appropriate sys.argv for the test script
    sys.argv = ['test_ai_modules.py']
    if args.component:
        sys.argv.append(f'--component={args.component}')
    if args.symbols:
        sys.argv.append(f'--symbols={args.symbols}')
        
    return test_main()

def execute_get_regime(args):
    """Execute the get-regime command."""
    if not args.symbol:
        logger.error("Symbol is required for get-regime command")
        return 1
        
    from src.AI import VolatilityRegimeDetector
    
    try:
        detector = VolatilityRegimeDetector()
        regime_info = detector.get_current_regime(args.symbol)
        
        print(json.dumps(regime_info, indent=2))
        
        logger.info(f"Current regime for {args.symbol}: "
                   f"{regime_info['regime_id']} ({regime_info['volatility_level']})")
        return 0
    except Exception as e:
        logger.error(f"Error getting regime for {args.symbol}: {e}")
        return 1

def execute_calculate_size(args):
    """Execute the calculate-size command."""
    if not args.symbol:
        logger.error("Symbol is required for calculate-size command")
        return 1
    if not args.size:
        logger.error("Position size is required for calculate-size command")
        return 1
        
    from src.AI import AdaptivePositionSizer
    
    try:
        position_sizer = AdaptivePositionSizer()
        kwargs = {
            'symbol': args.symbol,
            'account_id': args.account_id,
            'original_size': args.size,
        }
        
        if args.price:
            kwargs['price'] = args.price
        if args.stop_loss:
            kwargs['stop_loss'] = args.stop_loss
            
        result = position_sizer.calculate_position_size(**kwargs)
        
        print(json.dumps(result, indent=2))
        
        logger.info(f"Position size for {args.symbol}: {args.size} -> {result['adjusted_size']} "
                   f"(adjustment: {result['total_adjustment_factor']:.2f}x)")
        return 0
    except Exception as e:
        logger.error(f"Error calculating position size for {args.symbol}: {e}")
        return 1

def execute_evaluate_risk(args):
    """Execute the evaluate-risk command."""
    if not args.symbol and not args.signal:
        logger.error("Symbol or signal data is required for evaluate-risk command")
        return 1
        
    from src.AI import RiskManager
    
    try:
        risk_manager = RiskManager()
        
        # Get signal data from arguments or file
        if args.signal:
            if os.path.isfile(args.signal):
                with open(args.signal, 'r') as f:
                    signal_data = json.load(f)
            else:
                signal_data = json.loads(args.signal)
        else:
            # Build signal from arguments
            signal_data = {
                'ticker': args.symbol,
                'order_action': args.direction or 'buy',
                'position_size': args.size or 1.0
            }
            
            if args.price:
                signal_data['price'] = args.price
            if args.stop_loss:
                signal_data['stop_loss'] = args.stop_loss
        
        result = risk_manager.evaluate_trade_risk(signal_data, args.account_id)
        
        print(json.dumps(result, indent=2))
        
        if result['status'] == 'APPROVED':
            logger.info(f"Trade approved with risk level: {result.get('risk_level', 'MEDIUM')}")
        else:
            logger.info(f"Trade rejected: {result.get('rejection_reason', 'Unknown reason')}")
            
        return 0
    except Exception as e:
        logger.error(f"Error evaluating trade risk: {e}")
        return 1

def execute_dashboard(args):
    """Execute the dashboard command."""
    logger.info("Dashboard visualization is not yet implemented in CLI")
    logger.info("Please access the dashboard through the web interface")
    return 0

def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    try:
        # Execute the requested command
        if args.command == 'setup':
            return execute_setup(args)
        elif args.command == 'collect-data':
            return execute_collect_data(args)
        elif args.command == 'train-models':
            return execute_train_models(args)
        elif args.command == 'run-tests':
            return execute_run_tests(args)
        elif args.command == 'get-regime':
            return execute_get_regime(args)
        elif args.command == 'calculate-size':
            return execute_calculate_size(args)
        elif args.command == 'evaluate-risk':
            return execute_evaluate_risk(args)
        elif args.command == 'dashboard':
            return execute_dashboard(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
    except Exception as e:
        logger.error(f"Error executing command {args.command}: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
