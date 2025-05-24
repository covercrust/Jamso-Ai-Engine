#!/usr/bin/env python3
"""
Simple test script for the detect_current_regime method in VolatilityRegimeDetector.
"""

import sys
import os
import logging
import traceback
from unittest import mock

# Enable console output for debugging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the detector
from src.AI.regime_detector import VolatilityRegimeDetector

def test_detect_current_regime():
    """Test the detect_current_regime method"""
    
    print("Starting test_detect_current_regime")
    
    try:
        # Create a detector instance
        print("Creating VolatilityRegimeDetector instance...")
        detector = VolatilityRegimeDetector(db_path=':memory:')
        print("Successfully created detector instance")
    
    # Test case 1: Valid regime_id = 2
    with mock.patch.object(detector, 'get_current_regime', return_value={'regime_id': 2, 'description': 'High'}):
        result = detector.detect_current_regime('BTCUSD')
        assert result == 2, f"Expected regime_id 2, got {result}"
        print("✓ Test 1 passed: Returns correct regime_id when present")
    
    # Test case 2: Valid regime_id = 0 
    with mock.patch.object(detector, 'get_current_regime', return_value={'regime_id': 0, 'description': 'Low'}):
        result = detector.detect_current_regime('EURUSD')
        assert result == 0, f"Expected regime_id 0, got {result}"
        print("✓ Test 2 passed: Returns correct regime_id when it's zero")
    
    # Test case 3: Missing regime_id
    with mock.patch.object(detector, 'get_current_regime', return_value={'description': 'Unknown'}):
        result = detector.detect_current_regime('AAPL')
        assert result == -1, f"Expected -1 for missing regime_id, got {result}"
        print("✓ Test 3 passed: Returns -1 when regime_id is missing")
    
    # Test case 4: None return value
    with mock.patch.object(detector, 'get_current_regime', return_value=None):
        result = detector.detect_current_regime('unknown')
        assert result == -1, f"Expected -1 for None return value, got {result}"
        print("✓ Test 4 passed: Returns -1 when get_current_regime returns None")
    
    # Test case 5: Exception handling
    with mock.patch.object(detector, 'get_current_regime', side_effect=Exception("Test error")):
        result = detector.detect_current_regime('error')
        assert result == -1, f"Expected -1 for exception, got {result}"
        print("✓ Test 5 passed: Returns -1 when get_current_regime raises an exception")
    
    print("\nAll tests passed! The detect_current_regime method is working correctly.")

if __name__ == '__main__':
    try:
        print("Starting test script...")
        test_detect_current_regime()
    except Exception as e:
        print(f"ERROR: Test failed with exception: {str(e)}")
        traceback.print_exc()
