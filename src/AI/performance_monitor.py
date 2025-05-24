"""
performance_monitor.py
Advanced performance monitoring for Jamso-AI-Engine:
- Automated backtesting
- Strategy benchmarking
- Parameter optimization
- Dashboard and analytics integration
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Callable, Optional

class BacktestResult:
    def __init__(self, equity_curve: pd.Series, trades: pd.DataFrame, metrics: Dict[str, Any]):
        self.equity_curve = equity_curve
        self.trades = trades
        self.metrics = metrics

class PerformanceMonitor:
    def __init__(self, strategy_fn: Callable, data: pd.DataFrame, params: Dict[str, Any]):
        self.strategy_fn = strategy_fn
        self.data = data
        self.params = params
        self.results: Optional[BacktestResult] = None

    def run_backtest(self) -> BacktestResult:
        """Run the strategy on historical data and collect performance metrics."""
        trades, equity_curve = self.strategy_fn(self.data, **self.params)
        metrics = self.calculate_metrics(equity_curve, trades)
        self.results = BacktestResult(equity_curve, trades, metrics)
        return self.results

    @staticmethod
    def calculate_metrics(equity_curve: pd.Series, trades: pd.DataFrame) -> Dict[str, Any]:
        returns = equity_curve.pct_change().dropna()
        metrics = {
            'total_return': equity_curve.iloc[-1] / equity_curve.iloc[0] - 1,
            'max_drawdown': PerformanceMonitor.max_drawdown(equity_curve),
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else np.nan,
            'num_trades': len(trades),
            'win_rate': (trades['pnl'] > 0).mean() if 'pnl' in trades else np.nan,
        }
        return metrics

    @staticmethod
    def max_drawdown(equity_curve: pd.Series) -> float:
        roll_max = equity_curve.cummax()
        drawdown = (equity_curve - roll_max) / roll_max
        return drawdown.min()

    def benchmark(self, other_results: List[BacktestResult]) -> pd.DataFrame:
        """Compare this strategy's metrics to others."""
        all_metrics = [self.results.metrics] + [r.metrics for r in other_results]
        return pd.DataFrame(all_metrics)

    def optimize_parameters(self, param_grid: Dict[str, List[Any]], max_evals: int = 20) -> Dict[str, Any]:
        """Grid/random search for best parameters by backtest performance."""
        import itertools
        best_params = self.params.copy()
        best_score = -np.inf
        all_param_combos = list(itertools.product(*param_grid.values()))
        np.random.shuffle(all_param_combos)
        for combo in all_param_combos[:max_evals]:
            test_params = dict(zip(param_grid.keys(), combo))
            trades, equity_curve = self.strategy_fn(self.data, **test_params)
            metrics = self.calculate_metrics(equity_curve, trades)
            score = metrics.get('sharpe_ratio', 0)
            if score > best_score:
                best_score = score
                best_params = test_params
        return best_params

    def to_dashboard_payload(self) -> Dict[str, Any]:
        """Format results for dashboard/analytics pipeline."""
        if not self.results:
            return {}
        return {
            'equity_curve': self.results.equity_curve.to_dict(),
            'metrics': self.results.metrics,
            'trades': self.results.trades.to_dict(orient='records'),
        }

# Example usage (to be replaced with actual strategy integration):
# def example_strategy(data, param1, param2):
#     ...
#     return trades_df, equity_curve_series
# monitor = PerformanceMonitor(example_strategy, data, {'param1': 10, 'param2': 0.5})
# result = monitor.run_backtest()
# print(result.metrics)
