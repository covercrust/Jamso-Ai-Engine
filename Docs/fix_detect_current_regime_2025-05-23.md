# Implemented Fixes for Missing detect_current_regime Method

## Overview

In the Jamso-AI-Engine codebase, we identified an issue where the `detect_current_regime` method was being called in `realtime_analytics.py` but wasn't actually implemented in the `VolatilityRegimeDetector` class in `regime_detector.py`.

## The Issue

The `realtime_analytics.py` file on line 240 calls `self.regime_detector.detect_current_regime(symbol)` but this method did not exist in the `VolatilityRegimeDetector` class. 

## The Solution

We implemented the missing `detect_current_regime` method in the `VolatilityRegimeDetector` class in `regime_detector.py`. The implemented method leverages the existing `get_current_regime` method and extracts just the regime_id from the comprehensive regime information.

```python
def detect_current_regime(self, symbol: str) -> int:
    """
    Detect the current volatility regime ID for the given symbol.
    
    Args:
        symbol: The market symbol
        
    Returns:
        Current regime ID (int) or -1 if detection failed
    """
    try:
        # Get the full regime information
        regime_info = self.get_current_regime(symbol)
        
        # Check if regime_info is valid and contains regime_id
        if not regime_info or 'regime_id' not in regime_info:
            logger.warning(f"No valid regime information found for {symbol}")
            return -1
            
        # Extract and return just the regime ID
        return regime_info.get('regime_id', -1)
        
    except Exception as e:
        logger.error(f"Error detecting current regime for {symbol}: {e}")
        return -1
```

## Implementation Notes

1. The method safely handles different error conditions:
   - Returns -1 if no regime information is available
   - Returns -1 if the regime_id is missing from the regime information
   - Returns -1 if any exceptions occur during processing
   - Returns the correct regime_id (which can be 0, 1, 2, etc.) when available

2. The implementation follows the existing pattern in the codebase by:
   - Using similar error handling
   - Adhering to the established logging pattern
   - Maintaining consistent return types

## Testing

The implementation was tested with various scenarios including:
- Valid regime_id values (2, 1, 0)
- Missing regime_id in the return data
- Null/None return values
- Exception handling

## Affected Files

- `/home/jamso-ai-server/Jamso-Ai-Engine/src/AI/regime_detector.py` - Added the new method
- `/home/jamso-ai-server/Jamso-Ai-Engine/src/AI/realtime_analytics.py` - No changes needed as this now works with the new method
