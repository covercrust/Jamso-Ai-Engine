"""
AI Dashboard Integration Module

This module provides integration points between the AI trading components
and the dashboard for visualization and analytics.
"""

import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

# Configure logger
logger = logging.getLogger(__name__)

class AIDashboardIntegration:
    """
    Provides data and visualization integration for AI components.
    
    Attributes:
        db_path (str): Path to the SQLite database
    """
    
    def __init__(self, db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'):
        """
        Initialize the AI dashboard integration.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
    
    def get_volatility_regime_summary(self, 
                                    symbol: Optional[str] = None, 
                                    days: int = 30) -> List[Dict[str, Any]]:
        """
        Get volatility regime summary for dashboard display.
        
        Args:
            symbol: Specific symbol to get data for (None for all symbols)
            days: Number of days of history to include
            
        Returns:
            List of regime summary dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate the start date
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Build the query based on whether a specific symbol is requested
            if symbol:
                query = """
                SELECT symbol, regime_id, volatility_level, COUNT(*) as days_count,
                       MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
                FROM volatility_regimes
                WHERE symbol = ? AND timestamp >= ?
                GROUP BY symbol, regime_id, volatility_level
                ORDER BY symbol, last_seen DESC
                """
                cursor.execute(query, (symbol, start_date))
            else:
                query = """
                SELECT symbol, regime_id, volatility_level, COUNT(*) as days_count,
                       MIN(timestamp) as first_seen, MAX(timestamp) as last_seen
                FROM volatility_regimes
                WHERE timestamp >= ?
                GROUP BY symbol, regime_id, volatility_level
                ORDER BY symbol, last_seen DESC
                """
                cursor.execute(query, (start_date,))
                
            # Process results
            results = []
            for row in cursor.fetchall():
                symbol, regime_id, vol_level, days_count, first_seen, last_seen = row
                
                results.append({
                    'symbol': symbol,
                    'regime_id': regime_id,
                    'volatility_level': vol_level,
                    'days_count': days_count,
                    'first_seen': first_seen,
                    'last_seen': last_seen,
                    'is_current': self._is_current_regime(symbol or "", regime_id)
                })
                
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting volatility regime summary: {e}")
            return []
            
    def _is_current_regime(self, symbol: str, regime_id: int) -> bool:
        """Check if the given regime is the current regime for the symbol."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT regime_id FROM volatility_regimes
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """, (symbol,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] == regime_id:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking current regime: {e}")
            return False
            
    def get_position_sizing_history(self, 
                                  symbol: Optional[str] = None,
                                  days: int = 30) -> List[Dict[str, Any]]:
        """
        Get position sizing history for dashboard display.
        
        Args:
            symbol: Specific symbol to get data for (None for all symbols)
            days: Number of days of history to include
            
        Returns:
            List of position sizing history dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate the start date
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Build the query based on whether a specific symbol is requested
            if symbol:
                query = """
                SELECT timestamp, symbol, original_size, adjusted_size, 
                       risk_percent, volatility_regime, volatility_level, 
                       risk_adjustment_factor
                FROM position_sizing
                WHERE symbol = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                """
                cursor.execute(query, (symbol, start_date))
            else:
                query = """
                SELECT timestamp, symbol, original_size, adjusted_size, 
                       risk_percent, volatility_regime, volatility_level, 
                       risk_adjustment_factor
                FROM position_sizing
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                """
                cursor.execute(query, (start_date,))
                
            # Process results
            results = []
            for row in cursor.fetchall():
                timestamp, symbol, orig_size, adj_size, risk_pct, \
                    vol_regime, vol_level, adj_factor = row
                
                results.append({
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'original_size': orig_size,
                    'adjusted_size': adj_size,
                    'adjustment_ratio': adj_size / orig_size if orig_size else 1.0,
                    'risk_percent': risk_pct,
                    'volatility_regime': vol_regime,
                    'volatility_level': vol_level,
                    'adjustment_factor': adj_factor
                })
                
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting position sizing history: {e}")
            return []
            
    def get_risk_metrics_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get risk metrics history for dashboard display.
        
        Args:
            days: Number of days of history to include
            
        Returns:
            List of risk metrics history dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate the start date
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT timestamp, account_id, daily_risk_used, open_risk,
                   drawdown_percent, max_correlated_exposure, risk_status
            FROM risk_metrics
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """
            cursor.execute(query, (start_date,))
                
            # Process results
            results = []
            for row in cursor.fetchall():
                timestamp, acct_id, daily_risk, open_risk, \
                    drawdown_pct, corr_exposure, risk_status = row
                
                results.append({
                    'timestamp': timestamp,
                    'account_id': acct_id,
                    'daily_risk_used': daily_risk,
                    'open_risk': open_risk,
                    'drawdown_percent': drawdown_pct,
                    'max_correlated_exposure': corr_exposure,
                    'risk_status': risk_status
                })
                
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting risk metrics history: {e}")
            return []
    
    def get_volatility_chart_data(self, 
                               symbol: str, 
                               days: int = 90) -> Dict[str, Any]:
        """
        Get volatility chart data for a symbol.
        
        Args:
            symbol: Market symbol to get data for
            days: Number of days of history to include
            
        Returns:
            Dictionary with volatility chart data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate the start date
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Get market volatility data
            market_query = """
            SELECT timestamp, close, volatility, atr
            FROM market_volatility
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            """
            cursor.execute(market_query, (symbol, start_date))
            market_rows = cursor.fetchall()
            
            # Get regime data
            regime_query = """
            SELECT timestamp, regime_id, volatility_level
            FROM volatility_regimes
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            """
            cursor.execute(regime_query, (symbol, start_date))
            regime_rows = cursor.fetchall()
            
            conn.close()
            
            # Process data for chart
            dates = [row[0] for row in market_rows]
            prices = [row[1] for row in market_rows]
            volatilities = [row[2] for row in market_rows]
            atrs = [row[3] for row in market_rows]
            
            # Create regime bands
            regime_dates = [row[0] for row in regime_rows]
            regime_ids = [row[1] for row in regime_rows]
            regime_levels = [row[2] for row in regime_rows]
            
            # Format for charting library
            chart_data = {
                'symbol': symbol,
                'dates': dates,
                'prices': prices,
                'volatilities': volatilities,
                'atrs': atrs,
                'regime_dates': regime_dates,
                'regime_ids': regime_ids,
                'regime_levels': regime_levels
            }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error getting volatility chart data: {e}")
            return {
                'symbol': symbol,
                'error': str(e)
            }
    
    def get_account_performance_metrics(self, 
                                     account_id: int,
                                     days: int = 30) -> Dict[str, Any]:
        """
        Get account performance metrics for dashboard display.
        
        Args:
            account_id: Account ID to get data for
            days: Number of days of history to include
            
        Returns:
            Dictionary with account performance metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate the start date
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Get account balance history
            query = """
            SELECT timestamp, balance, equity, peak_balance, max_drawdown, drawdown_percent
            FROM account_balances
            WHERE account_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            """
            cursor.execute(query, (account_id, start_date))
            rows = cursor.fetchall()
            
            conn.close()
            
            if not rows:
                return {
                    'account_id': account_id,
                    'error': 'No account data available'
                }
            
            # Process data for metrics
            dates = [row[0] for row in rows]
            balances = [row[1] for row in rows]
            equities = [row[2] for row in rows]
            peak_balances = [row[3] for row in rows]
            max_drawdowns = [row[4] for row in rows]
            drawdown_percents = [row[5] for row in rows]
            
            # Calculate performance metrics
            start_balance = balances[0] if balances else 0
            end_balance = balances[-1] if balances else 0
            gain_loss = end_balance - start_balance
            gain_loss_percent = (gain_loss / start_balance) * 100 if start_balance else 0
            
            max_drawdown = max(max_drawdowns) if max_drawdowns else 0
            max_drawdown_percent = max(drawdown_percents) if drawdown_percents else 0
            
            # Format for dashboard
            performance_metrics = {
                'account_id': account_id,
                'date_range': f"{dates[0]} to {dates[-1]}" if dates else 'None',
                'starting_balance': start_balance,
                'ending_balance': end_balance,
                'gain_loss': gain_loss,
                'gain_loss_percent': gain_loss_percent,
                'max_drawdown': max_drawdown,
                'max_drawdown_percent': max_drawdown_percent,
                'chart_data': {
                    'dates': dates,
                    'balances': balances,
                    'equities': equities,
                    'drawdowns': drawdown_percents
                }
            }
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Error getting account performance metrics: {e}")
            return {
                'account_id': account_id,
                'error': str(e)
            }
