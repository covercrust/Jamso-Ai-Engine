#!/usr/bin/env python3
"""
Test script to verify fixes to the optimizer
"""
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_calculate_metrics():
    """Test if the calculate_metrics function works correctly with different index types"""
    from src.AI.fallback_optimizer import calculate_metrics
    
    # Test with datetime index
    index = pd.date_range('2025-01-01', periods=100, freq='D')
    equity_curve = pd.Series(np.linspace(100, 150, 100), index=index)
    trades = pd.DataFrame({'timestamp': index[1:20:2], 'pnl': [10]*10})
    
    logger.info("Testing calculate_metrics with datetime index...")
    metrics = calculate_metrics(equity_curve, trades)
    logger.info(f"Metrics with datetime index: {metrics}")
    
    # Test with numeric index
    equity_curve2 = pd.Series(np.linspace(100, 150, 100))
    trades2 = pd.DataFrame({'timestamp': range(10), 'pnl': [10]*10})
    
    logger.info("Testing calculate_metrics with numeric index...")
    metrics2 = calculate_metrics(equity_curve2, trades2)
    logger.info(f"Metrics with numeric index: {metrics2}")
    
    # Test with empty trades
    trades_empty = pd.DataFrame()
    logger.info("Testing calculate_metrics with empty trades...")
    metrics_empty = calculate_metrics(equity_curve, trades_empty)
    logger.info(f"Metrics with empty trades: {metrics_empty}")
    
    return True

def test_optimization_flow():
    """Test the optimization flow with default parameters"""
    from src.AI.fallback_optimizer import (
        supertrend_strategy,
        optimize_parameters,
        generate_param_set,
        backtest_strategy
    )
    
    # Create sample data
    dates = pd.date_range('2025-01-01', periods=100, freq='D')
    data = {
        'open': np.random.normal(100, 5, 100),
        'high': np.random.normal(105, 5, 100),
        'low': np.random.normal(95, 5, 100), 
        'close': np.random.normal(100, 5, 100),
    }
    df = pd.DataFrame(data, index=dates)
    
    # Make sure high > low
    df['high'] = df[['high', 'open', 'close']].max(axis=1) + 1
    df['low'] = df[['low', 'open', 'close']].min(axis=1) - 1
    
    logger.info("Testing optimization with minimal search space...")
    search_space = {
        'atr_period': [10, 20],
        'atr_multiplier': [2.0, 4.0],
        'stop_loss': [1.0, 3.0],
        'take_profit': [2.0, 5.0]
    }
    
    # Run optimizer with limited evaluations
    best_params, best_value, results = optimize_parameters(
        df,
        supertrend_strategy,
        search_space,
        objective_name='sharpe',
        num_evals=5
    )
    
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best value: {best_value}")
    
    # Test default parameter handling
    if best_params is None:
        logger.info("Testing fallback to default parameters")
        default_params = {
            'atr_period': 14,
            'atr_multiplier': 3.0,
            'stop_loss': 2.0,
            'take_profit': 4.0
        }
        
        result = supertrend_strategy(df, default_params)
        logger.info(f"Strategy with default params returned DataFrame with shape: {result.shape}")
    
    return True

if __name__ == "__main__":
    success = True
    
    try:
        logger.info("===== Testing calculate_metrics function =====")
        success &= test_calculate_metrics()
    except Exception as e:
        logger.error(f"Test calculate_metrics failed: {str(e)}")
        success = False
    
    try:
        logger.info("===== Testing optimization flow =====")
        success &= test_optimization_flow()
    except Exception as e:
        logger.error(f"Test optimization flow failed: {str(e)}")
        success = False
    
    if success:
        logger.info("✅ All tests passed! The fixes should work.")
    else:
        logger.error("❌ Some tests failed. Further investigation needed.")
