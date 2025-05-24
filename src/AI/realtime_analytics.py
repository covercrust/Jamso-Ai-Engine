"""
Real-time Analytics Module

This module provides real-time analytics capabilities for the AI trading system:
- Real-time volatility regime monitoring
- Live position risk tracking
- Market correlation alerts
- Performance metrics streaming
"""

import logging
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import threading
import time
import socket
import os
import matplotlib.pyplot as plt
from io import BytesIO
import base64

from src.AI.regime_detector import VolatilityRegimeDetector
from src.AI.risk_manager import RiskManager
from src.AI.position_sizer import AdaptivePositionSizer
from src.AI.models.sentiment_analysis import SentimentAnalyzer
from src.AI.indicators.volatility import VolatilityIndicators
from src.AI.utils.cache import regime_cache

# Configure logger
logger = logging.getLogger(__name__)

class RealtimeAnalytics:
    """
    Real-time analytics for AI-driven trading.
    
    Attributes:
        db_path (str): Path to the SQLite database
        regime_detector (VolatilityRegimeDetector): Volatility regime detector
        risk_manager (RiskManager): Risk manager
        alert_thresholds (dict): Alert thresholds for various metrics
        websocket_port (int): Port for WebSocket server
    """
    
    def __init__(self, 
                db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db',
                websocket_port: int = 8765,
                alert_config_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/AI/config/alerts.json'):
        """
        Initialize real-time analytics.
        
        Args:
            db_path: Path to the SQLite database
            websocket_port: Port for WebSocket server
            alert_config_path: Path to alert configuration file
        """
        self.db_path = db_path
        self.websocket_port = websocket_port
        self.alert_config_path = alert_config_path
        
        # Initialize components
        self.regime_detector = VolatilityRegimeDetector(db_path=db_path)
        self.risk_manager = RiskManager(db_path=db_path)
        self.position_sizer = AdaptivePositionSizer(db_path=db_path)
        self.sentiment_analyzer = SentimentAnalyzer(model_type='ensemble', db_path=db_path)
        
        # Load alert configuration
        self.alert_thresholds = self._load_alert_config()
        
        # Initialize monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.alert_history = []
        self.last_check_time = {}
        
        logger.info("Initialized real-time analytics module")
    
    def _load_alert_config(self) -> Dict[str, Any]:
        """
        Load alert configuration.
        
        Returns:
            Dictionary with alert thresholds
        """
        # Default configuration
        default_config = {
            'volatility_regime_change': {
                'enabled': True,
                'check_interval_minutes': 5
            },
            'correlation_change': {
                'enabled': True,
                'threshold': 0.2,
                'check_interval_minutes': 15
            },
            'drawdown': {
                'enabled': True,
                'threshold': 5.0,  # Percent
                'check_interval_minutes': 10
            },
            'sentiment_change': {
                'enabled': True,
                'threshold': 0.3,
                'check_interval_minutes': 60
            },
            'position_risk': {
                'enabled': True,
                'threshold': 2.0,  # Risk ratio
                'check_interval_minutes': 5
            }
        }
        
        # Try to load configuration from file
        try:
            if os.path.exists(self.alert_config_path):
                with open(self.alert_config_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                # Merge with default config
                for key, value in loaded_config.items():
                    if key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
                        
                logger.info(f"Loaded alert configuration from {self.alert_config_path}")
            else:
                logger.warning(f"Alert configuration file not found: {self.alert_config_path}")
                logger.info("Using default alert thresholds")
                
                # Create the config directory if it doesn't exist
                os.makedirs(os.path.dirname(self.alert_config_path), exist_ok=True)
                
                # Save the default configuration
                with open(self.alert_config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Failed to load alert configuration: {str(e)}")
            logger.info("Using default alert thresholds")
                
        return default_config
    
    def start_monitoring(self) -> bool:
        """
        Start real-time monitoring.
        
        Returns:
            True if successful
        """
        if self.is_monitoring:
            logger.warning("Monitoring is already active")
            return False
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("Started real-time monitoring")
        return True
        
    def stop_monitoring(self) -> bool:
        """
        Stop real-time monitoring.
        
        Returns:
            True if successful
        """
        if not self.is_monitoring:
            logger.warning("Monitoring is not active")
            return False
            
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
            
        logger.info("Stopped real-time monitoring")
        return True
    
    def _monitoring_loop(self) -> None:
        """
        Main monitoring loop.
        """
        while self.is_monitoring:
            try:
                # Check all alert conditions
                self._check_volatility_regime_changes()
                self._check_correlation_changes()
                self._check_drawdown_alerts()
                self._check_sentiment_changes()
                self._check_position_risk_alerts()
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Sleep and retry
    
    def _should_check(self, alert_type: str) -> bool:
        """
        Check if enough time has passed since last check.
        
        Args:
            alert_type: Type of alert
            
        Returns:
            True if should check now
        """
        if not self.alert_thresholds.get(alert_type, {}).get('enabled', False):
            return False
            
        now = datetime.now()
        last_check = self.last_check_time.get(alert_type, datetime.min)
        interval = self.alert_thresholds.get(alert_type, {}).get('check_interval_minutes', 5)
        
        if (now - last_check).total_seconds() >= interval * 60:
            self.last_check_time[alert_type] = now
            return True
            
        return False
    
    def _check_volatility_regime_changes(self) -> None:
        """
        Check for volatility regime changes.
        """
        if not self._should_check('volatility_regime_change'):
            return
            
        try:
            # Get active symbols from database
            symbols = self._get_active_symbols()
            
            for symbol in symbols:
                # Get current and previous regime
                current_regime = self.regime_detector.detect_current_regime(symbol)
                previous_regime = self._get_previous_regime(symbol)
                
                # Check if regime changed
                if current_regime != previous_regime and previous_regime is not None:
                    alert = {
                        'type': 'volatility_regime_change',
                        'symbol': symbol,
                        'previous_regime': previous_regime,
                        'current_regime': current_regime,
                        'timestamp': datetime.now().timestamp(),
                        'message': f"Volatility regime changed from {previous_regime} to {current_regime} for {symbol}"
                    }
                    
                    self._record_alert(alert)
                    
        except Exception as e:
            logger.error(f"Error checking volatility regime changes: {str(e)}")
    
    def _check_correlation_changes(self) -> None:
        """
        Check for significant correlation changes.
        """
        if not self._should_check('correlation_change'):
            return
            
        try:
            # Get correlation data from risk manager
            correlation_changes = self.risk_manager.detect_correlation_changes(
                threshold=self.alert_thresholds.get('correlation_change', {}).get('threshold', 0.2)
            )
            
            for change in correlation_changes:
                alert = {
                    'type': 'correlation_change',
                    'symbols': [change['symbol1'], change['symbol2']],
                    'previous_correlation': change['previous_correlation'],
                    'current_correlation': change['current_correlation'],
                    'change': change['change'],
                    'timestamp': datetime.now().timestamp(),
                    'message': f"Correlation between {change['symbol1']} and {change['symbol2']} " +
                               f"changed by {change['change']:.2f} from {change['previous_correlation']:.2f} " +
                               f"to {change['current_correlation']:.2f}"
                }
                
                self._record_alert(alert)
                
        except Exception as e:
            logger.error(f"Error checking correlation changes: {str(e)}")
    
    def _check_drawdown_alerts(self) -> None:
        """
        Check for significant account drawdowns.
        """
        if not self._should_check('drawdown'):
            return
            
        try:
            # Get current drawdown from risk manager
            current_drawdown = self.risk_manager.get_current_drawdown()
            threshold = self.alert_thresholds.get('drawdown', {}).get('threshold', 5.0)
            
            if current_drawdown > threshold:
                alert = {
                    'type': 'drawdown',
                    'drawdown': current_drawdown,
                    'threshold': threshold,
                    'timestamp': datetime.now().timestamp(),
                    'message': f"Account drawdown of {current_drawdown:.2f}% exceeds threshold of {threshold:.2f}%"
                }
                
                self._record_alert(alert)
                
        except Exception as e:
            logger.error(f"Error checking drawdown: {str(e)}")
    
    def _check_sentiment_changes(self) -> None:
        """
        Check for significant sentiment changes.
        """
        if not self._should_check('sentiment_change'):
            return
            
        try:
            # Get active symbols
            symbols = self._get_active_symbols()
            threshold = self.alert_thresholds.get('sentiment_change', {}).get('threshold', 0.3)
            
            for symbol in symbols:
                # Get sentiment history
                sentiment_data = self.sentiment_analyzer.get_sentiment_history(symbol, days=2)
                
                if len(sentiment_data) >= 2:
                    current_sentiment = sentiment_data[-1].get('sentiment', 0)
                    previous_sentiment = sentiment_data[-2].get('sentiment', 0)
                    change = abs(current_sentiment - previous_sentiment)
                    
                    if change > threshold:
                        alert = {
                            'type': 'sentiment_change',
                            'symbol': symbol,
                            'previous_sentiment': previous_sentiment,
                            'current_sentiment': current_sentiment,
                            'change': change,
                            'timestamp': datetime.now().timestamp(),
                            'message': f"Sentiment for {symbol} changed significantly by {change:.2f} " +
                                       f"from {previous_sentiment:.2f} to {current_sentiment:.2f}"
                        }
                        
                        self._record_alert(alert)
                        
        except Exception as e:
            logger.error(f"Error checking sentiment changes: {str(e)}")
    
    def _check_position_risk_alerts(self) -> None:
        """
        Check for high-risk positions.
        """
        if not self._should_check('position_risk'):
            return
            
        try:
            # Get active positions from database
            positions = self._get_active_positions()
            threshold = self.alert_thresholds.get('position_risk', {}).get('threshold', 2.0)
            
            for position in positions:
                # Calculate risk metrics
                risk_metrics = self.risk_manager.calculate_position_risk_metrics(position['symbol'], position['size'])
                
                if risk_metrics.get('risk_ratio', 0) > threshold:
                    alert = {
                        'type': 'position_risk',
                        'symbol': position['symbol'],
                        'size': position['size'],
                        'risk_ratio': risk_metrics.get('risk_ratio', 0),
                        'timestamp': datetime.now().timestamp(),
                        'message': f"Position in {position['symbol']} has high risk ratio of {risk_metrics.get('risk_ratio', 0):.2f}"
                    }
                    
                    self._record_alert(alert)
                    
        except Exception as e:
            logger.error(f"Error checking position risk: {str(e)}")
    
    def _record_alert(self, alert: Dict[str, Any]) -> None:
        """
        Record an alert.
        
        Args:
            alert: Alert data
        """
        # Add alert to history
        self.alert_history.append(alert)
        
        # Trim history to 1000 items
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
            
        # Log alert
        logger.warning(f"ALERT: {alert['message']}")
        
        # Save alert to database
        self._save_alert_to_db(alert)
    
    def _save_alert_to_db(self, alert: Dict[str, Any]) -> None:
        """
        Save alert to database.
        
        Args:
            alert: Alert data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    symbol TEXT,
                    message TEXT NOT NULL,
                    alert_data TEXT,
                    timestamp INTEGER,
                    is_read INTEGER DEFAULT 0
                )
            ''')
            
            # Insert alert
            cursor.execute('''
                INSERT INTO ai_alerts (
                    alert_type, symbol, message, alert_data, timestamp
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                alert['type'],
                alert.get('symbol', None),
                alert['message'],
                json.dumps(alert),
                int(alert['timestamp'])
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save alert to database: {str(e)}")
    
    def get_recent_alerts(self, limit: int = 100, alert_type: str = None) -> List[Dict[str, Any]]:
        """
        Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            alert_type: Filter by alert type (None for all types)
            
        Returns:
            List of alerts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT alert_type, symbol, message, alert_data, timestamp FROM ai_alerts"
            params = []
            
            if alert_type:
                query += " WHERE alert_type = ?"
                params.append(alert_type)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alert_data = json.loads(row[3])
                alerts.append(alert_data)
                
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {str(e)}")
            return []
    
    def get_volatility_regime_transitions(self, symbol: str = None, days: int = 30) -> pd.DataFrame:
        """
        Get volatility regime transitions.
        
        Args:
            symbol: Market symbol (None for all symbols)
            days: Number of days of history
            
        Returns:
            DataFrame with regime transitions
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate start date
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Build query
            query = """
                SELECT symbol, date, regime, regime_data
                FROM volatility_regimes
                WHERE date >= ?
            """
            params = [start_date]
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
                
            query += " ORDER BY date ASC"
            
            # Execute query
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Parse regime data
            if 'regime_data' in df.columns:
                df['regime_details'] = df['regime_data'].apply(lambda x: json.loads(x) if x else None)
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to get volatility regime transitions: {str(e)}")
            return pd.DataFrame()
    
    def get_correlation_changes(self, days: int = 30) -> pd.DataFrame:
        """
        Get market correlation changes.
        
        Args:
            days: Number of days of history
            
        Returns:
            DataFrame with correlation changes
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate start date
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Build query
            query = """
                SELECT symbol1, symbol2, date, correlation_value, snapshot_data
                FROM market_correlations
                WHERE date >= ?
                ORDER BY date ASC
            """
            
            # Execute query
            df = pd.read_sql_query(query, conn, params=[start_date])
            conn.close()
            
            # Parse snapshot data
            if 'snapshot_data' in df.columns:
                df['correlation_details'] = df['snapshot_data'].apply(lambda x: json.loads(x) if x else None)
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to get correlation changes: {str(e)}")
            return pd.DataFrame()
    
    def get_position_risk_metrics(self) -> pd.DataFrame:
        """
        Get current position risk metrics.
        
        Returns:
            DataFrame with risk metrics for active positions
        """
        positions = self._get_active_positions()
        
        if not positions:
            return pd.DataFrame()
            
        results = []
        for position in positions:
            # Calculate risk metrics
            metrics = self.risk_manager.calculate_position_risk_metrics(position['symbol'], position['size'])
            
            # Add to results
            result = {
                'symbol': position['symbol'],
                'position_size': position['size'],
                'entry_price': position.get('entry_price', 0),
                'current_price': position.get('current_price', 0),
                'pnl': position.get('pnl', 0),
                'risk_ratio': metrics.get('risk_ratio', 0),
                'max_loss': metrics.get('max_loss', 0),
                'value_at_risk': metrics.get('var', 0),
                'regime': metrics.get('regime', 'unknown')
            }
            
            results.append(result)
            
        return pd.DataFrame(results)
    
    def generate_real_time_dashboard(self) -> Dict[str, Any]:
        """
        Generate real-time dashboard data.
        
        Returns:
            Dictionary with dashboard data
        """
        dashboard = {
            'timestamp': datetime.now().timestamp(),
            'active_positions': self._get_active_positions(),
            'recent_alerts': self.get_recent_alerts(limit=10),
            'volatility_regimes': self._get_current_regimes(),
            'account_metrics': self._get_account_metrics(),
            'risk_metrics': self._get_risk_metrics(),
            'performance_metrics': self._get_performance_metrics()
        }
        
        return dashboard
    
    def generate_regime_transition_chart(self, symbol: str, days: int = 30) -> str:
        """
        Generate regime transition chart.
        
        Args:
            symbol: Market symbol
            days: Number of days of history
            
        Returns:
            Base64 encoded PNG image
        """
        # Get regime transition data
        regime_data = self.get_volatility_regime_transitions(symbol, days)
        
        if regime_data.empty:
            return None
            
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepare data
        dates = pd.to_datetime(regime_data['date'])
        regimes = regime_data['regime'].astype(int)
        
        # Plot regimes
        ax.plot(dates, regimes, 'o-', markersize=8)
        
        # Add regime labels
        regime_labels = {0: 'Low', 1: 'Medium', 2: 'High'}
        ax.set_yticks([0, 1, 2])
        ax.set_yticklabels(['Low', 'Medium', 'High'])
        
        # Add labels and title
        ax.set_xlabel('Date')
        ax.set_ylabel('Volatility Regime')
        ax.set_title(f'Volatility Regime Transitions - {symbol}')
        ax.grid(True, alpha=0.3)
        
        # Convert to base64 image
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        
        return image_data
    
    def generate_risk_metrics_chart(self) -> str:
        """
        Generate risk metrics chart.
        
        Returns:
            Base64 encoded PNG image
        """
        # Get risk metrics for active positions
        risk_metrics = self.get_position_risk_metrics()
        
        if risk_metrics.empty:
            return None
            
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Prepare data
        symbols = risk_metrics['symbol']
        risk_ratios = risk_metrics['risk_ratio']
        
        # Plot risk ratios
        bars = ax.bar(symbols, risk_ratios)
        
        # Color bars by risk level
        for i, bar in enumerate(bars):
            risk_ratio = risk_ratios.iloc[i]
            if risk_ratio < 1.0:
                bar.set_color('green')
            elif risk_ratio < 2.0:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        
        # Add threshold line
        ax.axhline(y=2.0, color='r', linestyle='--', label='Risk Threshold')
        
        # Add labels and title
        ax.set_xlabel('Symbol')
        ax.set_ylabel('Risk Ratio')
        ax.set_title('Position Risk Metrics')
        ax.grid(True, alpha=0.3)
        
        # Rotate x labels
        plt.xticks(rotation=45)
        
        # Add legend
        ax.legend()
        
        # Convert to base64 image
        buffer = BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        
        return image_data
    
    def _get_active_symbols(self) -> List[str]:
        """
        Get list of active trading symbols.
        
        Returns:
            List of market symbols
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query active symbols from trading signals
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM trading_signals
                ORDER BY symbol
            """)
            
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to get active symbols: {str(e)}")
            return []
    
    def _get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Get active trading positions.
        
        Returns:
            List of position dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query active positions
            cursor.execute("""
                SELECT symbol, direction, size, entry_price, current_price, 
                       pnl, open_time
                FROM active_positions
                WHERE status = 'OPEN'
                ORDER BY symbol
            """)
            
            columns = ['symbol', 'direction', 'size', 'entry_price', 'current_price', 'pnl', 'open_time']
            positions = []
            
            for row in cursor.fetchall():
                position = {columns[i]: row[i] for i in range(len(columns))}
                positions.append(position)
                
            conn.close()
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get active positions: {str(e)}")
            return []
    
    def _get_previous_regime(self, symbol: str) -> Optional[int]:
        """
        Get previous volatility regime for a symbol.
        
        Args:
            symbol: Market symbol
            
        Returns:
            Previous regime (0, 1, or 2) or None if not available
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the second most recent regime
            cursor.execute("""
                SELECT regime
                FROM volatility_regimes
                WHERE symbol = ?
                ORDER BY date DESC, id DESC
                LIMIT 1 OFFSET 1
            """, (symbol,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get previous regime: {str(e)}")
            return None
    
    def _get_current_regimes(self) -> Dict[str, int]:
        """
        Get current volatility regimes for all active symbols.
        
        Returns:
            Dictionary mapping symbols to regimes
        """
        symbols = self._get_active_symbols()
        regimes = {}
        
        for symbol in symbols:
            regime = self.regime_detector.detect_current_regime(symbol)
            regimes[symbol] = regime
            
        return regimes
    
    def _get_account_metrics(self) -> Dict[str, Any]:
        """
        Get account metrics.
        
        Returns:
            Dictionary with account metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest account balance
            cursor.execute("""
                SELECT balance, equity, margin_used, margin_level, 
                       equity_change_day, equity_change_month, timestamp
                FROM account_balances
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'balance': row[0],
                    'equity': row[1],
                    'margin_used': row[2],
                    'margin_level': row[3],
                    'equity_change_day': row[4],
                    'equity_change_month': row[5],
                    'timestamp': row[6]
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get account metrics: {str(e)}")
            return {}
    
    def _get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get risk metrics.
        
        Returns:
            Dictionary with risk metrics
        """
        try:
            # Get risk metrics from risk manager
            portfolio_risk = self.risk_manager.calculate_portfolio_risk_metrics()
            drawdown = self.risk_manager.get_current_drawdown()
            var = self.risk_manager.calculate_value_at_risk()
            
            return {
                'current_drawdown': drawdown,
                'max_drawdown': portfolio_risk.get('max_drawdown', 0),
                'total_exposure': portfolio_risk.get('total_exposure', 0),
                'risk_exposure_ratio': portfolio_risk.get('risk_exposure_ratio', 0),
                'value_at_risk': var,
                'sharpe_ratio': portfolio_risk.get('sharpe_ratio', 0),
                'calmar_ratio': portfolio_risk.get('calmar_ratio', 0)
            }
                
        except Exception as e:
            logger.error(f"Failed to get risk metrics: {str(e)}")
            return {}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get performance metrics
            cursor.execute("""
                SELECT win_count, loss_count, win_rate, avg_win, avg_loss,
                       profit_factor, expectancy, max_streak, drawdown
                FROM performance_metrics
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'win_count': row[0],
                    'loss_count': row[1],
                    'win_rate': row[2],
                    'avg_win': row[3],
                    'avg_loss': row[4],
                    'profit_factor': row[5],
                    'expectancy': row[6],
                    'max_streak': row[7],
                    'drawdown': row[8]
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {}


class AlertSystem:
    """
    Alert system for real-time notifications.
    
    Attributes:
        db_path (str): Path to the SQLite database
        alert_handlers (dict): Dictionary of alert handlers
    """
    
    def __init__(self, 
                db_path: str = '/home/jamso-ai-server/Jamso-Ai-Engine/src/Database/Webhook/trading_signals.db'):
        """
        Initialize alert system.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.alert_handlers = {}
        
        # Initialize alert table
        self._init_alert_table()
        
        logger.info("Initialized alert system")
    
    def _init_alert_table(self) -> None:
        """
        Initialize alert table in database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create alert table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    symbol TEXT,
                    message TEXT NOT NULL,
                    alert_data TEXT,
                    timestamp INTEGER,
                    is_read INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize alert table: {str(e)}")
    
    def register_handler(self, alert_type: str, handler: callable) -> None:
        """
        Register an alert handler.
        
        Args:
            alert_type: Type of alert
            handler: Handler function
        """
        self.alert_handlers[alert_type] = handler
        logger.info(f"Registered handler for alert type: {alert_type}")
    
    def trigger_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Trigger an alert.
        
        Args:
            alert: Alert data
            
        Returns:
            True if successful
        """
        alert_type = alert.get('type')
        
        # Save alert to database
        self._save_alert(alert)
        
        # Log alert
        logger.warning(f"ALERT: {alert.get('message', 'No message')}")
        
        # Call appropriate handler if registered
        if alert_type in self.alert_handlers:
            try:
                self.alert_handlers[alert_type](alert)
                return True
            except Exception as e:
                logger.error(f"Error in alert handler for {alert_type}: {str(e)}")
                return False
        
        return True
    
    def _save_alert(self, alert: Dict[str, Any]) -> None:
        """
        Save alert to database.
        
        Args:
            alert: Alert data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert alert
            cursor.execute('''
                INSERT INTO ai_alerts (
                    alert_type, symbol, message, alert_data, timestamp
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                alert.get('type'),
                alert.get('symbol'),
                alert.get('message', 'No message'),
                json.dumps(alert),
                int(alert.get('timestamp', datetime.now().timestamp()))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save alert: {str(e)}")
    
    def get_alerts(self, 
                 alert_type: str = None, 
                 symbol: str = None,
                 limit: int = 100,
                 unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get alerts from database.
        
        Args:
            alert_type: Filter by alert type (None for all)
            symbol: Filter by symbol (None for all)
            limit: Maximum number of alerts to return
            unread_only: Only return unread alerts
            
        Returns:
            List of alert dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT id, alert_type, symbol, message, alert_data, timestamp, is_read FROM ai_alerts"
            conditions = []
            params = []
            
            if alert_type:
                conditions.append("alert_type = ?")
                params.append(alert_type)
                
            if symbol:
                conditions.append("symbol = ?")
                params.append(symbol)
                
            if unread_only:
                conditions.append("is_read = 0")
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alert = {
                    'id': row[0],
                    'type': row[1],
                    'symbol': row[2],
                    'message': row[3],
                    'data': json.loads(row[4]) if row[4] else {},
                    'timestamp': row[5],
                    'is_read': bool(row[6])
                }
                alerts.append(alert)
                
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get alerts: {str(e)}")
            return []
    
    def mark_as_read(self, alert_id: int) -> bool:
        """
        Mark an alert as read.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update alert
            cursor.execute('''
                UPDATE ai_alerts
                SET is_read = 1
                WHERE id = ?
            ''', (alert_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark alert as read: {str(e)}")
            return False
