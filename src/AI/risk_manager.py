"""
Risk Manager Module

This module provides advanced risk management functionality, including:
- Drawdown protection
- Dynamic stop-loss adjustment
- Trading session risk limits
- Correlation-based risk management
"""

import logging
import sqlite3
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple

# Configure logger
logger = logging.getLogger(__name__)

class RiskManager:
    """
    Advanced risk management system for controlling trading risk.
    
    Attributes:
        max_daily_risk (float): Maximum daily risk as percentage of account
        max_drawdown_threshold (float): Maximum drawdown threshold as percentage
        correlation_threshold (float): Correlation threshold for correlated risk
        db_path (str): Path to the SQLite database
    """
    
    def __init__(self, 
                max_daily_risk: float = 5.0, 
                max_drawdown_threshold: float = 20.0,
                correlation_threshold: float = 0.7,
                db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'):
        """
        Initialize the risk manager.
        
        Args:
            max_daily_risk: Maximum daily risk as percentage of account (default: 5%)
            max_drawdown_threshold: Maximum drawdown threshold as percentage (default: 20%)
            correlation_threshold: Correlation threshold for correlated risk (default: 0.7)
            db_path: Path to the SQLite database
        """
        self.max_daily_risk = max_daily_risk
        self.max_drawdown_threshold = max_drawdown_threshold
        self.correlation_threshold = correlation_threshold
        self.db_path = db_path
        
        # Create risk management tables if they don't exist
        self._create_tables()
        
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create risk_metrics table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                account_id INTEGER,
                daily_risk_used REAL DEFAULT 0.0,
                open_risk REAL DEFAULT 0.0,
                drawdown_percent REAL DEFAULT 0.0,
                max_correlated_exposure REAL DEFAULT 0.0,
                risk_status TEXT DEFAULT 'NORMAL',
                risk_data TEXT
            )
            ''')
            
            # Create market_correlations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol1 TEXT NOT NULL,
                symbol2 TEXT NOT NULL,
                correlation_90d REAL,
                correlation_30d REAL,
                correlation_7d REAL,
                UNIQUE(symbol1, symbol2)
            )
            ''')
            
            # Create account_balances table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                account_id INTEGER NOT NULL,
                balance REAL NOT NULL,
                equity REAL NOT NULL,
                margin_used REAL,
                peak_balance REAL,
                max_drawdown REAL,
                drawdown_percent REAL,
                source TEXT DEFAULT 'API'
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Risk management tables created successfully")
        except Exception as e:
            logger.error(f"Error creating risk management tables: {e}")
    
    def check_daily_risk_limit(self, account_id: int) -> Dict[str, Any]:
        """
        Check if daily risk limit has been reached.
        
        Args:
            account_id: Account ID to check
            
        Returns:
            Dictionary with risk status and information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Query for today's risk usage
            query = """
            SELECT 
                SUM(CASE WHEN exit_timestamp IS NULL THEN ABS(size * entry_price * 0.01) ELSE 0 END) AS open_risk,
                SUM(CASE WHEN exit_timestamp IS NOT NULL AND DATE(timestamp) = ? THEN ABS(profit_loss) ELSE 0 END) AS closed_risk
            FROM positions
            WHERE account_id = ?
            """
            
            cursor = conn.execute(query, (today, account_id))
            row = cursor.fetchone()
            
            if row is None or (row[0] is None and row[1] is None):
                logger.warning(f"No risk data found for account {account_id}")
                return {"status": "NORMAL", "used_risk": 0, "remaining_risk": self.max_daily_risk}
            
            open_risk = float(row[0]) if row[0] is not None else 0.0
            closed_risk = float(row[1]) if row[1] is not None else 0.0
            
            # Get account balance
            query = """
            SELECT balance
            FROM account_balances
            WHERE account_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            cursor = conn.execute(query, (account_id,))
            balance_row = cursor.fetchone()
            conn.close()
            
            balance = float(balance_row[0]) if balance_row and balance_row[0] is not None else 10000.0
            
            # Calculate risk percentage
            open_risk_percent = (open_risk / balance) * 100
            closed_risk_percent = (closed_risk / balance) * 100
            total_risk_percent = open_risk_percent + closed_risk_percent
            
            # Determine risk status
            risk_status = "NORMAL"
            if total_risk_percent >= self.max_daily_risk:
                risk_status = "DAILY_LIMIT_REACHED"
            elif total_risk_percent >= (self.max_daily_risk * 0.8):
                risk_status = "DAILY_LIMIT_WARNING"
                
            return {
                "status": risk_status,
                "used_risk_percent": total_risk_percent,
                "remaining_risk_percent": max(0, self.max_daily_risk - total_risk_percent),
                "open_risk_percent": open_risk_percent,
                "closed_risk_percent": closed_risk_percent,
                "account_balance": balance,
                "max_daily_risk_percent": self.max_daily_risk
            }
            
        except Exception as e:
            logger.error(f"Error checking daily risk limit: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def check_drawdown(self, account_id: int) -> Dict[str, Any]:
        """
        Check current drawdown and apply risk measures if needed.
        
        Args:
            account_id: Account ID to check
            
        Returns:
            Dictionary with drawdown status and information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get current account info
            query = """
            SELECT 
                balance, 
                peak_balance, 
                drawdown_percent
            FROM account_balances
            WHERE account_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            cursor = conn.execute(query, (account_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row is None:
                return {
                    "status": "UNKNOWN", 
                    "drawdown_percent": 0, 
                    "max_threshold": self.max_drawdown_threshold
                }
                
            balance, peak_balance, drawdown_percent = row
            
            # Calculate drawdown if it's not in the database
            if drawdown_percent is None and peak_balance is not None and peak_balance > 0:
                drawdown_percent = ((peak_balance - balance) / peak_balance) * 100
            elif drawdown_percent is None:
                drawdown_percent = 0
            
            # Determine drawdown status
            if drawdown_percent >= self.max_drawdown_threshold:
                status = "CRITICAL"
                action = "HALT_TRADING"
            elif drawdown_percent >= (self.max_drawdown_threshold * 0.8):
                status = "WARNING"
                action = "REDUCE_SIZE"
            elif drawdown_percent >= (self.max_drawdown_threshold * 0.5):
                status = "CAUTION"
                action = "MONITOR"
            else:
                status = "NORMAL"
                action = "NONE"
                
            return {
                "status": status,
                "action": action,
                "drawdown_percent": drawdown_percent,
                "max_threshold": self.max_drawdown_threshold,
                "balance": balance,
                "peak_balance": peak_balance
            }
            
        except Exception as e:
            logger.error(f"Error checking drawdown: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def get_position_correlations(self, symbol: str, account_id: int) -> Dict[str, Any]:
        """
        Calculate correlation risk for a potential new position.
        
        Args:
            symbol: Market symbol for potential new position
            account_id: Account ID
            
        Returns:
            Dictionary with correlation risk information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get open positions
            query = """
            SELECT symbol, direction, size
            FROM positions
            WHERE 
                account_id = ? AND
                exit_timestamp IS NULL
            """
            
            cursor = conn.execute(query, (account_id,))
            open_positions = cursor.fetchall()
            
            if not open_positions:
                return {"status": "NO_POSITIONS", "correlation_risk": 0}
                
            # Get correlations for the symbol with existing positions
            correlated_positions = []
            total_correlated_exposure = 0
            
            for pos_symbol, direction, size in open_positions:
                # Skip self-correlation
                if pos_symbol == symbol:
                    continue
                    
                # Get correlation data
                query = """
                SELECT correlation_30d
                FROM market_correlations
                WHERE 
                    (symbol1 = ? AND symbol2 = ?) OR
                    (symbol1 = ? AND symbol2 = ?)
                ORDER BY timestamp DESC
                LIMIT 1
                """
                
                cursor.execute(query, (symbol, pos_symbol, pos_symbol, symbol))
                corr_row = cursor.fetchone()
                
                if corr_row is not None and corr_row[0] is not None:
                    correlation = float(corr_row[0])
                    
                    # Account for direction (positive correlation with opposite directions cancels out)
                    effective_correlation = correlation
                    
                    # If correlation is high enough to be considered a risk
                    if abs(effective_correlation) > self.correlation_threshold:
                        correlated_positions.append({
                            "symbol": pos_symbol,
                            "correlation": correlation,
                            "effective_correlation": effective_correlation,
                            "size": size
                        })
                        
                        # Add to total exposure (weighted by correlation and size)
                        total_correlated_exposure += abs(effective_correlation * size)
            
            conn.close()
            
            # Determine correlation risk status
            if total_correlated_exposure > 5:  # Arbitrary threshold for high correlated exposure
                status = "HIGH"
                action = "REDUCE_SIZE"
            elif total_correlated_exposure > 3:
                status = "MEDIUM"
                action = "CAUTION"
            else:
                status = "LOW"
                action = "NONE"
                
            return {
                "status": status,
                "action": action,
                "correlation_risk": total_correlated_exposure,
                "correlated_positions": correlated_positions,
                "correlation_threshold": self.correlation_threshold
            }
            
        except Exception as e:
            logger.error(f"Error calculating position correlations: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def update_account_balance(self, account_id: int, balance: float, equity: float, 
                              margin_used: Optional[float] = None, source: str = "API"):
        """
        Update account balance information and calculate drawdown.
        
        Args:
            account_id: Account ID
            balance: Current account balance
            equity: Current account equity
            margin_used: Current margin used (optional)
            source: Source of the update
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get previous peak balance
            query = """
            SELECT peak_balance
            FROM account_balances
            WHERE account_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            cursor.execute(query, (account_id,))
            row = cursor.fetchone()
            
            previous_peak = None
            if row is not None and row[0] is not None:
                previous_peak = float(row[0])
            
            # Determine new peak balance
            peak_balance = balance
            if previous_peak is not None and previous_peak > balance:
                peak_balance = previous_peak
            
            # Calculate drawdown
            drawdown_amount = 0
            drawdown_percent = 0
            if peak_balance > 0:
                drawdown_amount = peak_balance - balance
                drawdown_percent = (drawdown_amount / peak_balance) * 100
            
            # Insert new balance record
            cursor.execute('''
            INSERT INTO account_balances
            (account_id, balance, equity, margin_used, peak_balance, max_drawdown, drawdown_percent, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account_id,
                balance,
                equity,
                margin_used,
                peak_balance,
                drawdown_amount,
                drawdown_percent,
                source
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
    
    def update_market_correlation(self, symbol1: str, symbol2: str, correlation_90d: float, 
                                correlation_30d: float, correlation_7d: float):
        """
        Update market correlation data.
        
        Args:
            symbol1: First market symbol
            symbol2: Second market symbol
            correlation_90d: 90-day correlation
            correlation_30d: 30-day correlation
            correlation_7d: 7-day correlation
        """
        try:
            # Ensure symbols are in consistent order (alphabetical)
            if symbol1 > symbol2:
                symbol1, symbol2 = symbol2, symbol1
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO market_correlations
            (symbol1, symbol2, correlation_90d, correlation_30d, correlation_7d)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                symbol1,
                symbol2,
                correlation_90d,
                correlation_30d,
                correlation_7d
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating market correlation: {e}")
    
    def adjust_stop_loss(self, symbol: str, current_price: float, original_stop: float, 
                         position_direction: str, volatility_level: str) -> float:
        """
        Adjust stop loss based on volatility level and market conditions.
        
        Args:
            symbol: Market symbol
            current_price: Current market price
            original_stop: Original stop loss price
            position_direction: Position direction ('BUY' or 'SELL')
            volatility_level: Current volatility level
            
        Returns:
            Adjusted stop loss price
        """
        try:
            # Calculate price distance
            price_distance = abs(current_price - original_stop)
            
            # Base buffer percentage by volatility
            if volatility_level == "HIGH":
                buffer_percent = 0.05  # 5% buffer for high volatility
            elif volatility_level == "MEDIUM":
                buffer_percent = 0.03  # 3% buffer for medium volatility
            else:
                buffer_percent = 0.02  # 2% buffer for low volatility
                
            # Calculate buffer amount
            buffer_amount = price_distance * buffer_percent
            
            # Apply buffer to stop loss (widen it)
            if position_direction == "BUY":  # Long position
                adjusted_stop = original_stop - buffer_amount
            else:  # Short position
                adjusted_stop = original_stop + buffer_amount
                
            logger.info(f"Adjusted stop loss for {symbol} from {original_stop} to {adjusted_stop} (volatility: {volatility_level})")
            return adjusted_stop
            
        except Exception as e:
            logger.error(f"Error adjusting stop loss: {e}")
            return original_stop  # Return original if error
    
    def evaluate_trade_risk(self, signal_data: Dict[str, Any], account_id: int) -> Dict[str, Any]:
        """
        Comprehensive trade risk evaluation for a potential trade.
        
        Args:
            signal_data: Trading signal data
            account_id: Account ID
            
        Returns:
            Dictionary with risk evaluation results
        """
        try:
            symbol = signal_data.get('ticker') or signal_data.get('symbol')
            direction = signal_data.get('order_action') or signal_data.get('direction')
            size = float(signal_data.get('position_size') or signal_data.get('quantity') or 0)
            
            if not symbol or not direction or size <= 0:
                return {"status": "REJECTED", "reason": "Invalid signal data"}
            
            # Check daily risk limit
            daily_risk = self.check_daily_risk_limit(account_id)
            
            # Check drawdown
            drawdown = self.check_drawdown(account_id)
            
            # Check correlation risk
            correlation = self.get_position_correlations(symbol, account_id)
            
            # Determine overall risk status
            risk_status = "ACCEPTABLE"
            rejection_reason = None
            size_adjustment = 1.0
            
            # Stop trading if daily risk limit reached
            if daily_risk["status"] == "DAILY_LIMIT_REACHED":
                risk_status = "REJECTED"
                rejection_reason = "Daily risk limit reached"
                
            # Stop trading if in critical drawdown
            elif drawdown["status"] == "CRITICAL":
                risk_status = "REJECTED"
                rejection_reason = "Maximum drawdown threshold exceeded"
                
            # Reduce size if in warning drawdown or high correlation risk
            elif drawdown["status"] == "WARNING":
                risk_status = "ADJUST_SIZE"
                size_adjustment = 0.5  # 50% size reduction
                
            elif correlation["status"] == "HIGH":
                risk_status = "ADJUST_SIZE"
                size_adjustment = 0.7  # 30% size reduction
                
            # Calculate adjusted position size
            adjusted_size = size * size_adjustment
            if adjusted_size < 0.1:  # Minimum practical position size
                adjusted_size = 0
                risk_status = "REJECTED"
                rejection_reason = "Adjusted size too small"
                
            # Prepare response
            result = {
                "status": risk_status,
                "rejection_reason": rejection_reason,
                "original_size": size,
                "adjusted_size": round(adjusted_size, 2),
                "size_adjustment_factor": size_adjustment,
                "daily_risk": daily_risk,
                "drawdown": drawdown,
                "correlation_risk": correlation,
                "symbol": symbol,
                "direction": direction,
                "account_id": account_id,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save risk evaluation result
            self._save_risk_evaluation(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating trade risk: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }
            
    def _save_risk_evaluation(self, risk_data: Dict[str, Any]):
        """
        Save risk evaluation data to database.
        
        Args:
            risk_data: Risk evaluation data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract relevant data
            account_id = risk_data.get('account_id')
            daily_risk = risk_data.get('daily_risk', {})
            drawdown = risk_data.get('drawdown', {})
            
            cursor.execute('''
            INSERT INTO risk_metrics
            (account_id, daily_risk_used, open_risk, drawdown_percent, risk_status, risk_data)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                account_id,
                daily_risk.get('used_risk_percent', 0),
                daily_risk.get('open_risk_percent', 0),
                drawdown.get('drawdown_percent', 0),
                risk_data.get('status'),
                json.dumps(risk_data)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving risk evaluation: {e}")
