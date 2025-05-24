"""
AI Module for Jamso-AI-Engine

This module provides advanced AI-driven trading functionality including:
- Volatility regime detection using K-means clustering
- Adaptive risk management
- Dynamic position sizing
- Market data collection and analysis
- Performance optimization with caching
- Dashboard integration for visualizations
- Advanced backtesting and performance monitoring
- Trading strategy examples and implementations
"""

from src.AI.regime_detector import VolatilityRegimeDetector
from src.AI.position_sizer import AdaptivePositionSizer
from src.AI.risk_manager import RiskManager
from src.AI.data_collector import MarketDataCollector, create_default_collector
from src.AI.dashboard_integration import AIDashboardIntegration
from src.AI.performance_monitor import PerformanceMonitor
from src.AI.example_strategies import jamso_ai_bot_strategy
from src.AI.backtest_utils import DataLoader, ResultSaver

__all__ = [
    'VolatilityRegimeDetector',
    'AdaptivePositionSizer',
    'RiskManager',
    'MarketDataCollector',
    'create_default_collector',
    'AIDashboardIntegration',
    'PerformanceMonitor',
    'jamso_ai_bot_strategy',
    'DataLoader',
    'ResultSaver'
]
