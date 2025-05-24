# AI Module Developer Guide

## Introduction

This guide provides information for developers looking to extend or customize the AI trading module in the Jamso-AI-Engine. The AI module is designed with extensibility in mind, allowing you to add new algorithms, features, or integrations.

## Architecture Overview

The AI trading module follows a modular architecture with these core components:

1. **VolatilityRegimeDetector**: Identifies market states using K-means clustering
2. **AdaptivePositionSizer**: Dynamically adjusts position sizes based on market conditions
3. **RiskManager**: Controls trading risk with various risk metrics
4. **MarketDataCollector**: Gathers and stores market data for analysis
5. **PerformanceMonitor**: Analyzes trading strategy performance through backtesting
6. **Support utilities**: Caching, database access, and dashboard integration

```
src/AI/
├── __init__.py                # Module exports
├── regime_detector.py         # Volatility regime detection
├── position_sizer.py          # Adaptive position sizing
├── risk_manager.py            # Risk management
├── data_collector.py          # Market data collection
├── dashboard_integration.py   # Dashboard integration
├── performance_monitor.py     # Backtesting and performance analysis
├── example_strategies.py      # Example trading strategies
├── run_backtest.py            # Backtest runner script
├── parameter_optimizer.py     # Strategy parameter optimization
├── backtest_utils.py          # Backtesting utilities
├── models/                    # Custom AI models
├── indicators/                # Technical indicators
├── utils/                     # Utility functions
│   ├── __init__.py
│   └── cache.py               # Caching system
└── scripts/                   # Automation scripts
    ├── collect_market_data.py
    ├── train_regime_models.py
    └── test_ai_modules.py
```

## Extension Points

### 1. Adding New AI Models

To add a new AI model for market analysis or prediction:

1. Create a new Python module in the `src/AI/models/` directory
2. Implement your model class with standard methods:
   - `__init__()`: Initialize model parameters
   - `train()`: Train the model with market data
   - `predict()`: Make predictions with the model
3. Add appropriate database tables if needed
4. Add your model to the `src/AI/__init__.py` exports

**Example: Adding a Neural Network Predictor**

```python
# src/AI/models/neural_predictor.py
import numpy as np
from tensorflow import keras
import logging

logger = logging.getLogger(__name__)

class NeuralNetworkPredictor:
    """
    Neural network-based market direction predictor.
    """
    
    def __init__(self, lookback_period=14, forecast_horizon=5, layers=None):
        """
        Initialize the neural network predictor.
        
        Args:
            lookback_period: Number of periods to use for prediction
            forecast_horizon: Number of periods to forecast
            layers: Custom layer configuration
        """
        self.lookback_period = lookback_period
        self.forecast_horizon = forecast_horizon
        self.layers = layers or [64, 32]
        self.model = None
        
    def build_model(self, input_dim):
        """Build the neural network model."""
        model = keras.Sequential()
        model.add(keras.layers.Dense(self.layers[0], activation='relu', input_dim=input_dim))
        
        for units in self.layers[1:]:
            model.add(keras.layers.Dense(units, activation='relu'))
            
        model.add(keras.layers.Dense(1, activation='sigmoid'))
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        
        self.model = model
        return model
        
    def prepare_features(self, market_data):
        """Prepare features from market data."""
        # Feature engineering code here
        pass
        
    def train(self, market_data, epochs=100, validation_split=0.2):
        """Train the model with market data."""
        X, y = self.prepare_features(market_data)
        
        if self.model is None:
            self.build_model(X.shape[1])
            
        history = self.model.fit(
            X, y,
            epochs=epochs,
            validation_split=validation_split,
            verbose=1
        )
        
        return history
        
    def predict(self, market_data):
        """Make predictions with the model."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
            
        X, _ = self.prepare_features(market_data)
        predictions = self.model.predict(X)
        
        return predictions
```

Then add it to `src/AI/__init__.py`:

```python
from src.AI.models.neural_predictor import NeuralNetworkPredictor

__all__ = [
    # Existing exports
    'VolatilityRegimeDetector',
    'AdaptivePositionSizer',
    'RiskManager',
    # New model
    'NeuralNetworkPredictor'
]
```

### 2. Implementing Custom Technical Indicators

To add custom technical indicators for market analysis:

1. Create a new indicator module in `src/AI/indicators/`
2. Implement indicator functions that work with pandas DataFrames
3. Add tests for your indicators

**Example: Adding Advanced Volatility Indicators**

```python
# src/AI/indicators/volatility.py
import numpy as np
import pandas as pd

def average_true_range(df, period=14):
    """
    Calculate Average True Range (ATR).
    
    Args:
        df: DataFrame with OHLC data
        period: ATR period
        
    Returns:
        Series with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close'].shift(1)
    
    tr1 = high - low
    tr2 = abs(high - close)
    tr3 = abs(low - close)
    
    tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr

def normalized_volatility(df, period=20, annualization_factor=252):
    """
    Calculate normalized volatility (annualized).
    
    Args:
        df: DataFrame with price data
        period: Volatility calculation period
        annualization_factor: Annualization factor (252 for daily data)
        
    Returns:
        Series with normalized volatility values
    """
    returns = df['close'].pct_change()
    volatility = returns.rolling(window=period).std() * np.sqrt(annualization_factor)
    
    return volatility
```

### 3. Extending Risk Management

To add new risk management strategies:

1. Extend the `RiskManager` class or create a specialized risk manager
2. Add new risk metrics and evaluation methods
3. Integrate with the existing trading flow

**Example: Adding Portfolio-based Risk Management**

```python
# src/AI/risk/portfolio_risk_manager.py
from src.AI.risk_manager import RiskManager
import numpy as np
import pandas as pd

class PortfolioRiskManager(RiskManager):
    """
    Enhanced risk manager with portfolio-level risk controls.
    """
    
    def __init__(self, max_portfolio_risk=10.0, sector_concentration_limit=25.0, **kwargs):
        """
        Initialize portfolio risk manager.
        
        Args:
            max_portfolio_risk: Maximum portfolio risk percentage
            sector_concentration_limit: Maximum sector concentration percentage
            **kwargs: Base RiskManager parameters
        """
        super().__init__(**kwargs)
        self.max_portfolio_risk = max_portfolio_risk
        self.sector_concentration_limit = sector_concentration_limit
        
    def get_portfolio_positions(self, account_id):
        """Get current portfolio positions."""
        # Database query to get portfolio positions
        pass
        
    def calculate_portfolio_risk(self, account_id):
        """Calculate current portfolio risk."""
        positions = self.get_portfolio_positions(account_id)
        
        # Calculate portfolio-level risk metrics
        # (Could use correlation-weighted VaR, expected shortfall, etc.)
        pass
        
    def evaluate_portfolio_impact(self, signal_data, account_id):
        """Evaluate impact of a new trade on portfolio risk."""
        current_risk = self.calculate_portfolio_risk(account_id)
        
        # Simulate adding the new position
        # Calculate marginal contribution to risk
        # Check if it exceeds limits
        pass
    
    def evaluate_trade_risk(self, signal_data, account_id):
        """
        Override base method to include portfolio-level risk evaluation.
        """
        # First check basic risk metrics from parent class
        base_evaluation = super().evaluate_trade_risk(signal_data, account_id)
        
        if base_evaluation['status'] != 'APPROVED':
            return base_evaluation
            
        # Then check portfolio-level impact
        portfolio_impact = self.evaluate_portfolio_impact(signal_data, account_id)
        
        if portfolio_impact['exceeds_limit']:
            return {
                'status': 'REJECTED',
                'rejection_reason': portfolio_impact['reason'],
                'risk_level': 'HIGH',
                'portfolio_metrics': portfolio_impact['metrics']
            }
            
        # Otherwise, approve with additional portfolio metrics
        return {
            'status': 'APPROVED',
            'risk_level': base_evaluation['risk_level'],
            'portfolio_metrics': portfolio_impact['metrics'],
            **base_evaluation
        }
```

### 4. Adding Dashboard Visualizations

To add new visualizations for AI insights:

1. Extend the `AIDashboardIntegration` class with new data retrieval methods
2. Create associated frontend visualizations using your preferred charting library
3. Add the visualization to the dashboard

**Example: Adding Regime Transition Analysis**

```python
# Add to src/AI/dashboard_integration.py

def get_regime_transitions(self, symbol, days=90):
    """
    Get regime transition data for visualization.
    
    Args:
        symbol: Market symbol
        days: Number of days of history
        
    Returns:
        Dict with regime transition data
    """
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Get regime data with chronological ordering
        query = """
        SELECT timestamp, regime_id, volatility_level
        FROM volatility_regimes
        WHERE symbol = ? AND timestamp >= ?
        ORDER BY timestamp ASC
        """
        
        cursor.execute(query, (symbol, start_date))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {'symbol': symbol, 'transitions': [], 'error': 'No regime data found'}
        
        # Analyze transitions
        transitions = []
        for i in range(1, len(rows)):
            prev_date, prev_regime, prev_level = rows[i-1]
            curr_date, curr_regime, curr_level = rows[i]
            
            if prev_regime != curr_regime:
                transitions.append({
                    'from_date': prev_date,
                    'to_date': curr_date,
                    'from_regime': prev_regime,
                    'to_regime': curr_regime,
                    'from_level': prev_level,
                    'to_level': curr_level,
                    'days_in_previous': self._days_between(
                        self._get_regime_start(symbol, prev_regime, prev_date), 
                        prev_date
                    )
                })
        
        # Calculate transition statistics
        regime_durations = {}
        for regime in set(row[1] for row in rows):
            durations = self._calculate_regime_durations(symbol, regime, rows)
            regime_durations[regime] = {
                'mean_days': np.mean(durations) if durations else 0,
                'max_days': max(durations) if durations else 0,
                'volatility_level': next((row[2] for row in rows if row[1] == regime), 'UNKNOWN')
            }
        
        return {
            'symbol': symbol,
            'transitions': transitions,
            'regime_durations': regime_durations,
            'total_regimes_detected': len(regime_durations)
        }
        
    except Exception as e:
        logger.error(f"Error getting regime transitions: {e}")
        return {'symbol': symbol, 'error': str(e), 'transitions': []}
        
def _days_between(self, start_date, end_date):
    """Calculate days between two date strings."""
    try:
        d1 = datetime.strptime(start_date, '%Y-%m-%d')
        d2 = datetime.strptime(end_date, '%Y-%m-%d')
        return (d2 - d1).days
    except:
        return 0
        
def _get_regime_start(self, symbol, regime_id, before_date):
    """Get the start date of a regime."""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT MIN(timestamp)
        FROM volatility_regimes
        WHERE symbol = ? AND regime_id = ? AND timestamp <= ?
        """
        cursor.execute(query, (symbol, regime_id, before_date))
        result = cursor.fetchone()[0]
        conn.close()
        
        return result or before_date
        
    except Exception as e:
        logger.error(f"Error getting regime start: {e}")
        return before_date
        
def _calculate_regime_durations(self, symbol, regime_id, regime_data):
    """Calculate durations of regime occurrences."""
    durations = []
    current_start = None
    
    for i, (date, regime, _) in enumerate(regime_data):
        if regime == regime_id and current_start is None:
            current_start = date
        elif regime != regime_id and current_start is not None:
            durations.append(self._days_between(current_start, date))
            current_start = None
            
    # Handle case where the last regime extends to the present
    if current_start is not None:
        durations.append(self._days_between(
            current_start, 
            datetime.now().strftime('%Y-%m-%d')
        ))
        
    return durations
```

## Database Schema Extensions

When adding new features, you may need to extend the database schema.

### Guidelines for Adding Tables

1. Create your schema updates in a migration script
2. Use prepared statements to prevent SQL injection
3. Add appropriate indices for query optimization
4. Document the schema changes

**Example: Adding Model Performance Tracking**

```sql
-- Add to src/Database/ai_schema_updates.sql

CREATE TABLE IF NOT EXISTS ai_model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    accuracy REAL,
    precision_metric REAL,
    recall REAL,
    f1_score REAL,
    training_duration INTEGER,
    prediction_horizon INTEGER,
    parameters TEXT,
    model_version TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_model_perf_model ON ai_model_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_model_perf_symbol ON ai_model_performance(symbol);
CREATE INDEX IF NOT EXISTS idx_model_perf_timestamp ON ai_model_performance(timestamp);
```

And the corresponding Python function:

```python
def log_model_performance(model_name, symbol, metrics, parameters=None, notes=None):
    """
    Log AI model performance metrics to the database.
    
    Args:
        model_name: Name of the AI model
        symbol: Trading symbol
        metrics: Dictionary of performance metrics
        parameters: Model parameters (dict)
        notes: Additional notes
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO ai_model_performance
        (model_name, symbol, accuracy, precision_metric, recall, f1_score,
         training_duration, prediction_horizon, parameters, model_version, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model_name,
            symbol,
            metrics.get('accuracy'),
            metrics.get('precision'),
            metrics.get('recall'),
            metrics.get('f1_score'),
            metrics.get('training_duration'),
            metrics.get('prediction_horizon'),
            json.dumps(parameters) if parameters else None,
            metrics.get('model_version', '1.0'),
            notes
        ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error logging model performance: {e}")
```

## Testing Extensions

When extending the AI module, follow these testing practices:

1. Add unit tests for new functionality
2. Include performance benchmarks
3. Add your tests to the existing testing framework

**Example: Testing a New AI Model**

```python
# Add to src/AI/scripts/test_ai_modules.py

class NeuralPredictorTests(unittest.TestCase):
    """Tests for the NeuralNetworkPredictor class."""
    
    def __init__(self, *args, symbols=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.symbols = symbols or ['EURUSD', 'BTCUSD']
        self.predictor = NeuralNetworkPredictor()
        
    def setUp(self):
        # Prepare test data
        pass
        
    def test_model_training(self):
        """Test that the model can be trained."""
        # Test code here
        pass
        
    def test_prediction_accuracy(self):
        """Test prediction accuracy."""
        # Test code here
        pass
```

Then add the test cases to the main testing function:

```python
# Add to main() in src/AI/scripts/test_ai_modules.py
if args.component in ['all', 'neural_predictor']:
    test_suite.addTest(NeuralPredictorTests('test_model_training', symbols=symbols))
    test_suite.addTest(NeuralPredictorTests('test_prediction_accuracy', symbols=symbols))
```

## Performance Considerations

When extending the AI trading module, consider these performance guidelines:

1. **Use caching for computationally expensive operations**

   ```python
   from src.AI.utils.cache import cached, ai_model_cache
   
   @cached(ai_model_cache, key_prefix='prediction')
   def predict_market(symbol, lookback_days=30):
       # Expensive prediction logic
       return result
   ```

2. **Optimize database queries**

   - Use indices for frequently queried columns
   - Avoid SELECT * queries
   - Use prepared statements
   - Consider query execution plans

3. **Implement batch processing for heavy operations**

   ```python
   def process_symbols_in_batches(symbols, batch_size=10):
       """Process symbols in batches to avoid memory issues."""
       for i in range(0, len(symbols), batch_size):
           batch = symbols[i:i+batch_size]
           # Process batch
           yield batch_results
   ```

4. **Use parallelization for independent operations**

   ```python
   import concurrent.futures
   
   def analyze_multiple_symbols(symbols):
       """Analyze multiple symbols in parallel."""
       results = {}
       
       with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
           future_to_symbol = {
               executor.submit(analyze_symbol, symbol): symbol 
               for symbol in symbols
           }
           
           for future in concurrent.futures.as_completed(future_to_symbol):
               symbol = future_to_symbol[future]
               try:
                   results[symbol] = future.result()
               except Exception as e:
                   results[symbol] = {'error': str(e)}
                   
       return results
   ```

## Configuration Management

To make your AI extensions configurable:

1. Use a configuration file or environment variables
2. Implement a configuration manager class
3. Document configuration options

**Example: Configuration Manager**

```python
# src/AI/utils/config.py
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AIConfigManager:
    """
    Configuration manager for AI module settings.
    
    Loads configuration from:
    1. Default settings
    2. Config file (if specified)
    3. Environment variables (overrides file settings)
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        'regime_detector': {
            'n_clusters': 3,
            'lookback_days': 60
        },
        'position_sizer': {
            'base_risk_percent': 1.0,
            'max_position_size': 5.0
        },
        'risk_manager': {
            'max_daily_risk': 5.0,
            'max_drawdown_threshold': 20.0
        },
        'data_collector': {
            'default_symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'BTCUSD'],
            'schedule_time': '00:00'
        }
    }
    
    def __init__(self, config_file=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to a JSON configuration file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load from file if specified
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
            
        # Override with environment variables
        self._load_from_env()
        
    def _load_from_file(self, config_file):
        """Load configuration from a JSON file."""
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                
            # Update config with file settings
            for section, settings in file_config.items():
                if section in self.config:
                    self.config[section].update(settings)
                else:
                    self.config[section] = settings
                    
            logger.info(f"Loaded configuration from {config_file}")
            
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Environment variables should be named like:
        # JAMSO_AI_SECTION_SETTING, e.g., JAMSO_AI_REGIME_DETECTOR_N_CLUSTERS
        
        prefix = 'JAMSO_AI_'
        for key in os.environ:
            if key.startswith(prefix):
                parts = key[len(prefix):].lower().split('_', 1)
                if len(parts) == 2:
                    section, setting = parts
                    if section in self.config:
                        try:
                            # Convert value to appropriate type
                            value = os.environ[key]
                            if setting in self.config[section]:
                                original_type = type(self.config[section][setting])
                                if original_type == bool:
                                    value = value.lower() in ('true', '1', 'yes')
                                else:
                                    value = original_type(value)
                                    
                                self.config[section][setting] = value
                                logger.debug(f"Overrode {section}.{setting} from environment")
                                
                        except Exception as e:
                            logger.warning(f"Failed to override {section}.{setting}: {e}")
    
    def get(self, section, setting=None, default=None):
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            setting: Setting name (None to get entire section)
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        if section not in self.config:
            return default
            
        if setting is None:
            return self.config[section]
            
        return self.config[section].get(setting, default)
    
    def get_all(self):
        """Get the entire configuration."""
        return self.config
```

## Deployment Best Practices

When deploying your AI extensions:

1. **Version your models**
   - Track model versions in the database
   - Implement A/B testing for new models

2. **Set up monitoring**
   - Log performance metrics
   - Track resource usage
   - Monitor prediction accuracy

3. **Establish fallback mechanisms**
   - Handle errors gracefully
   - Implement default values for failures
   - Use circuit breakers for critical components

## Documentation Standards

When documenting your extensions:

1. **Include docstrings** for all classes and methods
2. **Update API documentation** with new features
3. **Provide usage examples** in markdown
4. **Document configuration options** thoroughly

## Further Reading

For more information on specific topics:

- [scikit-learn Documentation](https://scikit-learn.org/stable/documentation.html) - For machine learning models
- [TensorFlow Documentation](https://www.tensorflow.org/api_docs) - For neural networks
- [Pandas Documentation](https://pandas.pydata.org/docs/) - For data manipulation
- [SQLite Documentation](https://www.sqlite.org/docs.html) - For database operations

## Advanced Performance Monitoring & Dashboard Integration

The AI module now supports:
- Automated backtesting and benchmarking of strategies via `PerformanceMonitor`
- Parameter optimization routines for risk and strategy parameters
- API endpoint `/dashboard/api/advanced_backtest` for dashboard/analytics integration

### Extending the Dashboard
- Add new analytics visualizations by consuming the advanced backtest API
- See `performance_monitor.py` for available metrics and payloads

## Backtesting Framework

The Jamso AI Engine includes a comprehensive backtesting framework for evaluating and optimizing trading strategies. This section explains how to use and extend this system.

### Core Components

1. **PerformanceMonitor** (`performance_monitor.py`): Core class for analyzing strategy performance
   - Run backtests on historical data
   - Calculate performance metrics (returns, drawdown, Sharpe ratio, win rate)
   - Compare strategies using benchmark methods
   - Optimize strategy parameters

2. **Example Strategies** (`example_strategies.py`): Python implementations of trading strategies
   - SuperTrend algorithm (translated from Pine Script)
   - Input parameters match Pine Script inputs for consistency
   - Produces trades and equity curve for analysis

3. **Backtest Utilities** (`backtest_utils.py`): Helper functions
   - Load historical data from database, CSV or generate synthetic data
   - Save and load backtest results
   - Data preprocessing for strategy compatibility

4. **Backtest Runner** (`run_backtest.py`): Command-line interface
   - Easy-to-use script for running backtests
   - Supports multiple data sources and strategies
   - Performance visualization and reporting

5. **Parameter Optimizer** (`parameter_optimizer.py`): Find optimal parameters
   - Grid search across parameter spaces
   - Parallelized processing for speed
   - Visualization of parameter sensitivity

### Using the Backtest Runner

The `run_backtest.py` script provides a convenient command-line interface for backtesting:

```bash
# Basic usage
python src/AI/run_backtest.py --strategy supertrend --symbol EURUSD

# With parameter customization
python src/AI/run_backtest.py --strategy supertrend --atr-len 14 --fact 3.0 --risk-percent 1.5

# Using synthetic sample data
python src/AI/run_backtest.py --use-sample-data --days 365 --plot

# Parameter optimization
python src/AI/run_backtest.py --optimize --max-evals 50
```

For detailed options, run: `python src/AI/run_backtest.py --help`

### Adding a New Strategy

To add a new trading strategy to the backtesting framework:

1. **Create the strategy function** in `example_strategies.py` or a new file:

```python
def my_strategy(df, param1=10, param2=0.5, initial_capital=5000):
    """
    My custom trading strategy.
    
    Args:
        df: pandas DataFrame with OHLCV data
        param1, param2: Strategy parameters
        initial_capital: Starting capital
        
    Returns:
        trades: DataFrame of trades
        equity_curve: Series of equity values
    """
    # Implement strategy logic
    # ...
    
    # Return trades and equity curve
    return trades_df, equity_curve
```

2. **Register the strategy** in `run_backtest.py` and `parameter_optimizer.py`:

```python
STRATEGIES = {
    "supertrend": jamso_ai_bot_strategy,
    "my_strategy": my_strategy
}
```

3. **Add default parameters** to the `extract_strategy_params` function.

4. **Test thoroughly** with sample data before using with real data.

### Parameter Optimization

The parameter optimizer allows you to find optimal strategy parameters:

```bash
# Basic optimization
python src/AI/parameter_optimizer.py --strategy supertrend --symbol EURUSD

# Custom parameter grid
python src/AI/parameter_optimizer.py --params '{"atr_len": [5, 10, 15], "fact": [2.0, 2.5, 3.0]}'

# Optimize for specific objective
python src/AI/parameter_optimizer.py --objective risk_adjusted --visualize
```

### Dashboard Integration

The backtesting framework integrates with the dashboard through the `/dashboard/api/advanced_backtest` endpoint. This allows visualization of backtest results, including:

- Equity curves
- Drawdown charts
- Trade lists
- Performance metrics

To extend the dashboard with new visualizations, use the `to_dashboard_payload()` method of the `PerformanceMonitor` class.

### Further Reading

For more details on the backtesting system, refer to:

- `src/AI/BACKTEST_README.md` - Comprehensive guide to the backtesting system
- `src/AI/performance_monitor.py` - Core implementation of the backtest engine
- `Dashboard/controllers/dashboard_controller.py` - API endpoint implementation
