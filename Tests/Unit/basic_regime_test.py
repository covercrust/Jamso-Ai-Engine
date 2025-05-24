#!/usr/bin/env python3
"""
Simple test for the detect_current_regime method
"""

import sys
import os

print("Starting test script...")

try:
    # Add the project root to the Python path for proper imports
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    sys.path.insert(0, project_root)
    print(f"Added project root to Python path: {project_root}")

    # Try to import the regime_detector module
    print("Importing VolatilityRegimeDetector...")
    from src.AI.regime_detector import VolatilityRegimeDetector
    print("Successfully imported VolatilityRegimeDetector")

    # Create an instance
    print("Creating detector instance...")
    detector = VolatilityRegimeDetector(db_path=':memory:')
    print("Successfully created detector instance")
    
    # Verify that detect_current_regime exists
    print("Checking if detect_current_regime method exists...")
    if hasattr(detector, 'detect_current_regime') and callable(getattr(detector, 'detect_current_regime')):
        print("✓ detect_current_regime method exists")
    else:
        print("✗ detect_current_regime method does NOT exist!")
        sys.exit(1)
    
    # Manual test case
    print("\nTesting with hardcoded values...")
    
    # Replace get_current_regime with our own version for testing
    original_get_current_regime = detector.get_current_regime
    
    def test_get_current_regime(symbol):
        print(f"Mock get_current_regime called with symbol: {symbol}")
        if symbol == "BTCUSD":
            return {"regime_id": 2, "description": "High Volatility"}
        elif symbol == "EURUSD":
            return {"regime_id": 0, "description": "Low Volatility"}
        elif symbol == "AAPL":
            return {"description": "Missing ID"}  # No regime_id
        elif symbol == "NONE":
            return None
        else:
            raise Exception("Test exception")
    
    # Replace the method
    detector.get_current_regime = test_get_current_regime
    
    # Test case 1: Valid regime_id = 2
    try:
        print("\nTest case 1: Valid regime_id = 2")
        result = detector.detect_current_regime("BTCUSD")
        print(f"Result: {result}")
        assert result == 2, f"Expected 2, got {result}"
        print("✓ Test case 1 passed")
    except Exception as e:
        print(f"✗ Test case 1 failed: {str(e)}")
    
    # Test case 2: Valid regime_id = 0
    try:
        print("\nTest case 2: Valid regime_id = 0")
        result = detector.detect_current_regime("EURUSD")
        print(f"Result: {result}")
        assert result == 0, f"Expected 0, got {result}"
        print("✓ Test case 2 passed")
    except Exception as e:
        print(f"✗ Test case 2 failed: {str(e)}")
    
    # Test case 3: Missing regime_id
    try:
        print("\nTest case 3: Missing regime_id")
        result = detector.detect_current_regime("AAPL")
        print(f"Result: {result}")
        assert result == -1, f"Expected -1, got {result}"
        print("✓ Test case 3 passed")
    except Exception as e:
        print(f"✗ Test case 3 failed: {str(e)}")
    
    # Test case 4: None return value
    try:
        print("\nTest case 4: None return value")
        result = detector.detect_current_regime("NONE")
        print(f"Result: {result}")
        assert result == -1, f"Expected -1, got {result}"
        print("✓ Test case 4 passed")
    except Exception as e:
        print(f"✗ Test case 4 failed: {str(e)}")
    
    # Test case 5: Exception handling
    try:
        print("\nTest case 5: Exception handling")
        result = detector.detect_current_regime("ERROR")
        print(f"Result: {result}")
        assert result == -1, f"Expected -1, got {result}"
        print("✓ Test case 5 passed")
    except Exception as e:
        print(f"✗ Test case 5 failed: {str(e)}")
    
    # Restore original method
    detector.get_current_regime = original_get_current_regime
    print("\nAll tests completed.")

except Exception as e:
    import traceback
    print(f"ERROR: {str(e)}")
    traceback.print_exc()
