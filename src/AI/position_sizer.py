"""
Adaptive Position Sizer Module

This module provides dynamic position sizing based on market conditions,
volatility regimes, account equity, and risk parameters.
"""

import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, Tuple

from src.AI.regime_detector import VolatilityRegimeDetector

# Configure logger
logger = logging.getLogger(__name__)

class AdaptivePositionSizer:
    """
    Adaptive position sizer that adjusts position size based on:
    - Current volatility regime
    - Account balance
    - Risk parameters
    - Market conditions
    - Recent trading performance
    
    Attributes:
        base_risk_percent (float): Base risk percentage per trade
        max_position_size (float): Maximum allowed position size
        db_path (str): Path to the SQLite database
        regime_detector (VolatilityRegimeDetector): Volatility regime detector
    """
    
    def __init__(self, 
                base_risk_percent: float = 1.0, 
                max_position_size: float = 5.0,
                max_risk_percent: float = 2.0,
                min_risk_percent: float = 0.5, 
                db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'):
        """
        Initialize the adaptive position sizer.
        
        Args:
            base_risk_percent: Base percentage of account to risk per trade (default: 1.0%)
            max_position_size: Maximum allowable position size (default: 5.0)
            max_risk_percent: Maximum percentage of account to risk per trade (default: 2.0%)
            min_risk_percent: Minimum percentage of account to risk per trade (default: 0.5%)
            db_path: Path to the SQLite database
        """
        self.base_risk_percent = base_risk_percent
        self.max_risk_percent = max_risk_percent
        self.min_risk_percent = min_risk_percent
        self.max_position_size = max_position_size
        self.db_path = db_path
        
        # Initialize regime detector
        self.regime_detector = VolatilityRegimeDetector(db_path=db_path)
        
        # Create performance tracking table if it doesn't exist
        self._create_tables()
        
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create position_sizing table to track sizing decisions
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS position_sizing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                signal_id INTEGER,
                symbol TEXT,
                original_size REAL,
                adjusted_size REAL,
                account_balance REAL,
                risk_amount REAL,
                risk_percent REAL,
                volatility_regime INTEGER,
                volatility_level TEXT,
                recent_performance REAL,
                risk_adjustment_factor REAL,
                sizing_data TEXT,
                FOREIGN KEY(signal_id) REFERENCES signals(id)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Position sizing tables created successfully")
        except Exception as e:
            logger.error(f"Error creating position sizing tables: {e}")
        
    def _calculate_regime_adjustment(self, 
                                    symbol: str, 
                                    base_size: float) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate position size adjustment based on current volatility regime.
        
        Args:
            symbol: Market symbol
            base_size: Base position size
            
        Returns:
            Tuple of (adjusted size, regime info)
        """
        # Get current regime
        regime_info = self.regime_detector.get_current_regime(symbol)
        
        # Default adjustment factor
        adjustment_factor = 1.0
        
        # Adjust based on volatility level
        vol_level = regime_info.get('volatility_level', 'MEDIUM')
        
        if vol_level == 'HIGH':
            # Reduce position size in high volatility
            adjustment_factor = 0.7  # 30% reduction
        elif vol_level == 'LOW':
            # Increase position size in low volatility
            adjustment_factor = 1.2  # 20% increase
        
        # Apply adjustment, but ensure within limits
        adjusted_size = base_size * adjustment_factor
        
        return adjusted_size, regime_info
        
    def _calculate_performance_adjustment(self, 
                                         symbol: str, 
                                         days: int = 7) -> float:
        """
        Calculate position size adjustment based on recent trading performance.
        
        Args:
            symbol: Market symbol
            days: Lookback period in days
            
        Returns:
            Performance adjustment factor
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate win rate over the last N days
            query = """
            SELECT 
                COUNT(CASE WHEN profit_loss > 0 THEN 1 END) AS wins,
                COUNT(CASE WHEN profit_loss < 0 THEN 1 END) AS losses,
                SUM(profit_loss) AS total_pnl
            FROM positions
            WHERE 
                symbol = ? AND 
                timestamp >= date('now', ?) AND
                exit_timestamp IS NOT NULL
            """
            
            cursor = conn.execute(query, (symbol, f'-{days} days'))
            row = cursor.fetchone()
            conn.close()
            
            if row is None or (row[0] + row[1]) == 0:
                # No trading data available
                return 1.0
                
            wins, losses, total_pnl = row[0] or 0, row[1] or 0, row[2] or 0
            total_trades = wins + losses
            
            if total_trades < 5:
                # Not enough trades for reliable assessment
                return 1.0
                
            # Calculate win rate
            win_rate = wins / total_trades if total_trades > 0 else 0
            
            # Calculate adjustment factor
            if win_rate > 0.7:  # Very good performance
                return 1.2
            elif win_rate > 0.5:  # Good performance
                return 1.1
            elif win_rate < 0.3:  # Poor performance
                return 0.7
            else:  # Average performance
                return 1.0
                
        except Exception as e:
            logger.error(f"Error calculating performance adjustment: {e}")
            return 1.0
    
    def _calculate_drawdown_adjustment(self, account_id: int) -> float:
        """
        Calculate position size adjustment based on current drawdown.
        
        Args:
            account_id: Account ID to check
            
        Returns:
            Drawdown adjustment factor
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get account history for drawdown calculation
            query = """
            SELECT balance, peak_balance
            FROM account_balances
            WHERE account_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            cursor = conn.execute(query, (account_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row is None:
                return 1.0
                
            balance, peak_balance = row
            
            # No peak balance recorded or invalid data
            if peak_balance is None or peak_balance <= 0:
                return 1.0
                
            # Calculate current drawdown percentage
            drawdown_percent = (peak_balance - balance) / peak_balance * 100
            
            # Apply progressive reduction based on drawdown
            if drawdown_percent > 20:  # Severe drawdown
                return 0.5  # 50% reduction
            elif drawdown_percent > 15:
                return 0.7  # 30% reduction
            elif drawdown_percent > 10:
                return 0.8  # 20% reduction
            elif drawdown_percent > 5:
                return 0.9  # 10% reduction
            else:
                return 1.0  # No reduction
                
        except Exception as e:
            logger.error(f"Error calculating drawdown adjustment: {e}")
            return 1.0
            
    def _get_account_balance(self, account_id: int) -> float:
        """
        Get current account balance.
        
        Args:
            account_id: Account ID
            
        Returns:
            Current account balance or default value
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT balance 
            FROM account_balances
            WHERE account_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            cursor = conn.execute(query, (account_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row is None or row[0] is None:
                logger.warning(f"No account balance found for account {account_id}, using default")
                return 10000.0  # Default balance if not found
                
            return float(row[0])
            
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return 10000.0  # Default balance in case of error
            
    def calculate_position_size(self, 
                               symbol: str, 
                               account_id: int, 
                               original_size: float,
                               signal_id: Optional[int] = None,
                               price: Optional[float] = None,
                               stop_loss: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate optimal position size based on current market conditions and account state.
        
        Args:
            symbol: Market symbol
            account_id: Account ID
            original_size: Original position size from the signal
            signal_id: Signal ID (optional)
            price: Entry price (optional)
            stop_loss: Stop loss level (optional)
            
        Returns:
            Dictionary with position sizing information
        """
        try:
            # Step 1: Get account balance
            account_balance = self._get_account_balance(account_id)
            
            # Step 2: Calculate risk amount based on base risk percentage
            risk_amount = account_balance * (self.base_risk_percent / 100)
            
            # Step 3: Get adjustments based on volatility regime
            base_size = original_size
            regime_adjusted_size, regime_info = self._calculate_regime_adjustment(symbol, base_size)
            
            # Step 4: Apply performance adjustment
            performance_factor = self._calculate_performance_adjustment(symbol)
            performance_adjusted_size = regime_adjusted_size * performance_factor
            
            # Step 5: Apply drawdown protection adjustment
            drawdown_factor = self._calculate_drawdown_adjustment(account_id)
            drawdown_adjusted_size = performance_adjusted_size * drawdown_factor
            
            # Step 6: Calculate actual risk percentage based on stop loss if provided
            risk_percent = self.base_risk_percent
            if price is not None and stop_loss is not None:
                risk_per_unit = abs(price - stop_loss)
                if risk_per_unit > 0:
                    # Calculate how many units we can trade with our risk amount
                    units_for_risk = risk_amount / risk_per_unit
                    # Convert to position size (depends on your position sizing conventions)
                    risk_based_size = units_for_risk * 0.01  # Assuming 0.01 units = 1 position size
                    # Apply this as another adjustment factor
                    drawdown_adjusted_size = min(drawdown_adjusted_size, risk_based_size)
            
            # Step 7: Ensure within limits
            final_size = min(drawdown_adjusted_size, self.max_position_size)
            final_size = max(final_size, 0.1)  # Minimum size
            
            # Round to 2 decimal places for practical use
            final_size = round(final_size, 2)
            
            # Calculate cumulative adjustment factor
            total_adjustment = final_size / original_size if original_size > 0 else 1.0
            
            # Prepare result
            result = {
                'original_size': original_size,
                'adjusted_size': final_size,
                'account_balance': account_balance,
                'risk_amount': risk_amount,
                'risk_percent': risk_percent,
                'regime_id': regime_info.get('regime_id', -1),
                'volatility_level': regime_info.get('volatility_level', 'UNKNOWN'),
                'performance_factor': performance_factor,
                'drawdown_factor': drawdown_factor,
                'total_adjustment_factor': total_adjustment,
                'max_position_size': self.max_position_size,
                'signal_id': signal_id
            }
            
            # Save sizing decision to database if signal_id provided
            if signal_id:
                self._save_sizing_decision(symbol, result)
                
            return result
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            # Return original size in case of error
            return {
                'original_size': original_size,
                'adjusted_size': original_size,
                'error': str(e)
            }
            
    def _save_sizing_decision(self, symbol: str, sizing_data: Dict[str, Any]):
        """
        Save position sizing decision to database.
        
        Args:
            symbol: Market symbol
            sizing_data: Position sizing data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO position_sizing (
                timestamp, signal_id, symbol, original_size, adjusted_size, 
                account_balance, risk_amount, risk_percent, volatility_regime,
                volatility_level, risk_adjustment_factor, sizing_data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                sizing_data.get('signal_id'),
                symbol,
                sizing_data.get('original_size'),
                sizing_data.get('adjusted_size'),
                sizing_data.get('account_balance'),
                sizing_data.get('risk_amount'),
                sizing_data.get('risk_percent'),
                sizing_data.get('regime_id'),
                sizing_data.get('volatility_level'),
                sizing_data.get('total_adjustment_factor'),
                json.dumps(sizing_data)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving position sizing decision: {e}")
