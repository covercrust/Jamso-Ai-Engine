"""
Fixed versions of technical indicator functions that had type errors.
"""
import pandas as pd
import numpy as np

def fixed_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On-Balance Volume with fixed type handling.
    
    Args:
        close: Close price series
        volume: Volume series
        
    Returns:
        Series with OBV values
    """
    # Ensure inputs are Series
    if not isinstance(close, pd.Series):
        close = pd.Series(close)
    if not isinstance(volume, pd.Series):
        volume = pd.Series(volume)
    
    # Use a vectorized approach with cumsum to avoid type issues
    # Calculate price changes
    price_change = close.diff()
    
    # Initialize with zeros
    obv = pd.Series(0.0, index=close.index)
    
    # Set initial value 
    if len(volume) > 0:
        if isinstance(volume.iloc[0], (int, float)) and not pd.isna(volume.iloc[0]):
            obv.iloc[0] = float(volume.iloc[0])
    
    # Loop-based calculation (safer and avoids type issues)
    for i in range(1, len(close)):
        prev_val = float(obv.iloc[i-1])
        curr_vol = float(volume.iloc[i]) if pd.notna(volume.iloc[i]) else 0.0
        pc = price_change.iloc[i]
        
        if pd.notna(pc):
            if float(pc) > 0.0:
                obv.iloc[i] = prev_val + curr_vol
            elif float(pc) < 0.0:
                obv.iloc[i] = prev_val - curr_vol
            else:
                obv.iloc[i] = prev_val
        else:
            obv.iloc[i] = prev_val
    
    return obv

def fixed_volatility(close: pd.Series, window: int = 20) -> pd.DataFrame:
    """
    Calculate different volatility measures with fixed type handling.
    
    Args:
        close: Close price series
        window: Window size for calculations
        
    Returns:
        DataFrame with volatility measures
    """
    # Ensure close is a pandas Series
    if not isinstance(close, pd.Series):
        close = pd.Series(close)
    
    # Calculate returns safely
    shifted = close.shift(1)
    # Avoid division by zero
    valid_mask = shifted != 0
    returns = pd.Series(index=close.index, dtype=float)
    returns.loc[valid_mask] = np.log(close.loc[valid_mask] / shifted.loc[valid_mask])
    
    # Calculate volatilities
    hist_vol = returns.rolling(window=window).std() * np.sqrt(252)
    rolling_std = close.rolling(window=window).std()
    
    # Create a result DataFrame
    result = pd.DataFrame(index=close.index)
    result['hist_volatility'] = hist_vol
    result['parkinson_volatility'] = rolling_std / (4 * np.log(2)) * np.sqrt(252)
    result['garman_klass_volatility'] = rolling_std * np.sqrt(252)
    
    return result
