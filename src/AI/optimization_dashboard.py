#!/usr/bin/env python3
"""
Capital.com API Optimization Dashboard

This module provides a simple dashboard for visualizing optimization results from the
Capital.com API integration.

The dashboard displays:
- Historical optimization results
- Performance metrics comparison
- Parameter evolution over time 
- Current vs. historical performance charts
- Optimization performance across different symbols
"""

import os
import sys
import json
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import argparse
import logging
from pathlib import Path
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import dotenv for loading environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file if it exists
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables may not be loaded properly.")

# Add parent directory to path to access the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Import the fallback optimizer for strategy evaluation
try:
    from src.AI.fallback_optimizer import supertrend_strategy, calculate_metrics
except ImportError:
    logger.error("Failed to import fallback_optimizer. Dashboard may not work properly.")

class OptimizationDashboard:
    """
    Dashboard for visualization of optimization results from Capital.com API.
    """
    
    def __init__(self, results_dir=None):
        """
        Initialize the dashboard with results directory
        
        Args:
            results_dir: Directory containing optimization JSON result files
        """
        # Default to project's results directory if not specified
        if results_dir is None:
            results_dir = os.path.join(parent_dir, "Results", "Optimization")
        
        # Create the directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)
        
        self.results_dir = results_dir
        self.results_data = self._load_optimization_results()
        
        if not self.results_data:
            logger.warning(f"No optimization results found in {results_dir}")
            logger.info("Please run optimization first to generate results")
        else:
            logger.info(f"Loaded {len(self.results_data)} optimization results")
    
    def _load_optimization_results(self):
        """
        Load optimization results from JSON files in the results directory
        
        Returns:
            List of dictionaries containing optimization results
        """
        results_data = []
        pattern = os.path.join(self.results_dir, "capital_com_optimized_params_*.json")
        
        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Add filename for reference
                    data['filename'] = os.path.basename(file_path)
                    results_data.append(data)
                    logger.debug(f"Loaded results from {file_path}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {str(e)}")
        
        return results_data
    
    def create_dashboard(self, port=8050):
        """
        Create and run the Dash web application
        
        Args:
            port: Port number for the dashboard server
        """
        # Create Dash app
        app = dash.Dash(__name__, title="Capital.com Optimization Dashboard")
        
        # Prepare data for dropdowns
        symbols = sorted(list(set(r['metadata']['symbol'] for r in self.results_data if 'metadata' in r)))
        timeframes = sorted(list(set(r['metadata']['timeframe'] for r in self.results_data if 'metadata' in r)))
        objectives = sorted(list(set(r['metadata']['objective'] for r in self.results_data if 'metadata' in r)))
        
        # Define layout
        app.layout = html.Div([
            html.H1("Capital.com API Optimization Dashboard"),
            
            html.Div([
                html.Div([
                    html.H3("Filter Results"),
                    html.Label("Symbol:"),
                    dcc.Dropdown(
                        id='symbol-dropdown',
                        options=[{'label': s, 'value': s} for s in symbols],
                        value=symbols[0] if symbols else None,
                        clearable=True
                    ),
                    html.Label("Timeframe:"),
                    dcc.Dropdown(
                        id='timeframe-dropdown',
                        options=[{'label': t, 'value': t} for t in timeframes],
                        value=None,
                        clearable=True
                    ),
                    html.Label("Objective:"),
                    dcc.Dropdown(
                        id='objective-dropdown',
                        options=[{'label': o, 'value': o} for o in objectives],
                        value=None,
                        clearable=True
                    ),
                ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
                
                html.Div([
                    html.H3("Date Range"),
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date_placeholder_text="Start Date",
                        end_date_placeholder_text="End Date",
                        calendar_orientation='horizontal',
                    ),
                ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
                
                html.Div([
                    html.Button(
                        'Refresh Data', 
                        id='refresh-button', 
                        n_clicks=0,
                        style={'margin-top': '20px'}
                    ),
                ], style={'width': '20%', 'display': 'inline-block', 'padding': '10px', 'vertical-align': 'bottom'}),
                
            ], style={'display': 'flex'}),
            
            html.Div([
                html.Div([
                    html.H3("Performance Metrics"),
                    dcc.Graph(id='metrics-chart')
                ], style={'width': '49%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("Parameter Evolution"),
                    dcc.Graph(id='params-chart')
                ], style={'width': '49%', 'display': 'inline-block'}),
            ]),
            
            html.Div([
                html.Div([
                    html.H3("Top Strategies by Return"),
                    dcc.Graph(id='top-return-chart')
                ], style={'width': '49%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("Top Strategies by Sharpe Ratio"),
                    dcc.Graph(id='top-sharpe-chart')
                ], style={'width': '49%', 'display': 'inline-block'}),
            ]),
            
            html.Div([
                html.H3("Detailed Results Table"),
                html.Div(id='results-table')
            ]),
            
            html.Div(id='selected-data', style={'display': 'none'})
        ])
        
        # Callbacks
        @app.callback(
            Output('selected-data', 'children'),
            [
                Input('refresh-button', 'n_clicks'),
                Input('symbol-dropdown', 'value'),
                Input('timeframe-dropdown', 'value'),
                Input('objective-dropdown', 'value'),
                Input('date-picker-range', 'start_date'),
                Input('date-picker-range', 'end_date')
            ]
        )
        def filter_data(n_clicks, symbol, timeframe, objective, start_date, end_date):
            # Reload data if refresh button clicked
            if n_clicks > 0:
                self.results_data = self._load_optimization_results()
            
            # Filter data based on selections
            filtered_data = self.results_data
            
            if symbol:
                filtered_data = [r for r in filtered_data if r.get('metadata', {}).get('symbol') == symbol]
            
            if timeframe:
                filtered_data = [r for r in filtered_data if r.get('metadata', {}).get('timeframe') == timeframe]
                
            if objective:
                filtered_data = [r for r in filtered_data if r.get('metadata', {}).get('objective') == objective]
            
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                filtered_data = [r for r in filtered_data if 'metadata' in r and 
                                  datetime.strptime(r['metadata'].get('date', '2000-01-01'), '%Y-%m-%d %H:%M:%S') >= start_dt]
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                filtered_data = [r for r in filtered_data if 'metadata' in r and 
                                  datetime.strptime(r['metadata'].get('date', '2100-01-01'), '%Y-%m-%d %H:%M:%S') <= end_dt]
            
            return json.dumps(filtered_data)
        
        @app.callback(
            [
                Output('metrics-chart', 'figure'),
                Output('params-chart', 'figure'),
                Output('top-return-chart', 'figure'),
                Output('top-sharpe-chart', 'figure'),
                Output('results-table', 'children')
            ],
            [Input('selected-data', 'children')]
        )
        def update_charts(json_data):
            filtered_data = json.loads(json_data) if json_data else []
            
            if not filtered_data:
                empty_fig = {
                    'data': [],
                    'layout': {
                        'title': 'No data available',
                        'xaxis': {'title': ''},
                        'yaxis': {'title': ''}
                    }
                }
                empty_table = html.P("No data available. Please run optimization or adjust filters.")
                return empty_fig, empty_fig, empty_fig, empty_fig, empty_table
            
            # Prepare data for charts
            dates = []
            returns = []
            sharpes = []
            drawdowns = []
            win_rates = []
            profit_factors = []
            
            # Parameter tracking
            atr_periods = []
            atr_multipliers = []
            stop_losses = []
            take_profits = []
            
            # Additional metadata
            symbols = []
            timeframes = []
            
            for result in filtered_data:
                if 'metadata' in result and 'metrics' in result and 'params' in result:
                    try:
                        date_str = result['metadata'].get('date', '')
                        if date_str:
                            dates.append(datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S'))
                            
                            metrics = result['metrics']
                            returns.append(metrics.get('total_return', 0))
                            sharpes.append(metrics.get('sharpe_ratio', 0))
                            drawdowns.append(metrics.get('max_drawdown', 0))
                            win_rates.append(metrics.get('win_rate', 0))
                            profit_factors.append(metrics.get('profit_factor', 0))
                            
                            params = result['params']
                            atr_periods.append(params.get('atr_period', 0))
                            atr_multipliers.append(params.get('atr_multiplier', 0))
                            stop_losses.append(params.get('stop_loss', 0))
                            take_profits.append(params.get('take_profit', 0))
                            
                            symbols.append(result['metadata'].get('symbol', ''))
                            timeframes.append(result['metadata'].get('timeframe', ''))
                    except Exception as e:
                        logger.error(f"Error processing result: {e}")
            
            # Create metrics chart
            metrics_fig = go.Figure()
            if dates:
                metrics_fig.add_trace(go.Scatter(x=dates, y=returns, mode='lines+markers', name='Total Return %'))
                metrics_fig.add_trace(go.Scatter(x=dates, y=sharpes, mode='lines+markers', name='Sharpe Ratio'))
                metrics_fig.add_trace(go.Scatter(x=dates, y=drawdowns, mode='lines+markers', name='Max Drawdown %'))
                metrics_fig.add_trace(go.Scatter(x=dates, y=win_rates, mode='lines+markers', name='Win Rate %'))
                
                metrics_fig.update_layout(
                    title='Performance Metrics Over Time',
                    xaxis_title='Date',
                    yaxis_title='Value',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    template='plotly_white'
                )
            
            # Create parameters chart
            params_fig = go.Figure()
            if dates:
                params_fig.add_trace(go.Scatter(x=dates, y=atr_periods, mode='lines+markers', name='ATR Period'))
                params_fig.add_trace(go.Scatter(x=dates, y=atr_multipliers, mode='lines+markers', name='ATR Multiplier'))
                params_fig.add_trace(go.Scatter(x=dates, y=stop_losses, mode='lines+markers', name='Stop Loss'))
                params_fig.add_trace(go.Scatter(x=dates, y=take_profits, mode='lines+markers', name='Take Profit'))
                
                params_fig.update_layout(
                    title='Parameter Evolution Over Time',
                    xaxis_title='Date',
                    yaxis_title='Value',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    template='plotly_white'
                )
            
            # Create top returns chart
            df = pd.DataFrame({
                'Date': dates,
                'Return': returns,
                'Symbol': symbols,
                'Timeframe': timeframes
            })
            
            top_return_fig = px.bar(
                df.sort_values('Return', ascending=False).head(10),
                x='Symbol',
                y='Return',
                color='Timeframe',
                text='Return',
                title='Top 10 Strategies by Return %',
                labels={'Return': 'Total Return %', 'Symbol': 'Market Symbol'}
            )
            
            top_return_fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            
            # Create top sharpe chart
            df['Sharpe'] = sharpes
            top_sharpe_fig = px.bar(
                df.sort_values('Sharpe', ascending=False).head(10),
                x='Symbol',
                y='Sharpe',
                color='Timeframe',
                text='Sharpe',
                title='Top 10 Strategies by Sharpe Ratio',
                labels={'Sharpe': 'Sharpe Ratio', 'Symbol': 'Market Symbol'}
            )
            
            top_sharpe_fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            
            # Create results table
            results_table = html.Table(
                # Header
                [html.Tr([
                    html.Th('Date'),
                    html.Th('Symbol'),
                    html.Th('Timeframe'),
                    html.Th('Return %'),
                    html.Th('Sharpe'),
                    html.Th('Win Rate %'),
                    html.Th('Drawdown %'),
                ])] +
                # Body
                [html.Tr([
                    html.Td(dates[i].strftime('%Y-%m-%d')),
                    html.Td(symbols[i]),
                    html.Td(timeframes[i]),
                    html.Td(f"{returns[i]:.2f}"),
                    html.Td(f"{sharpes[i]:.2f}"),
                    html.Td(f"{win_rates[i]:.2f}"),
                    html.Td(f"{drawdowns[i]:.2f}"),
                ]) for i in range(min(len(dates), 15))],  # Show only the last 15 entries
                style={'width': '100%', 'border-collapse': 'collapse'}
            )
            
            return metrics_fig, params_fig, top_return_fig, top_sharpe_fig, results_table
        
        # Start the server
        logger.info(f"Starting dashboard on port {port}")
        app.run_server(debug=True, port=port)

def main():
    """Main function to run the dashboard."""
    parser = argparse.ArgumentParser(description="Capital.com API Optimization Dashboard")
    parser.add_argument("--dir", type=str, help="Directory containing optimization results")
    parser.add_argument("--port", type=int, default=8050, help="Port to run the dashboard on")
    args = parser.parse_args()
    
    try:
        # Try to install dash if not already installed
        try:
            import dash
        except ImportError:
            logger.info("Dash not installed. Attempting to install it...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "dash", "plotly"])
            logger.info("Dash installed successfully")
            import dash
            from dash import dcc, html
            from dash.dependencies import Input, Output
            import plotly.graph_objs as go
            import plotly.express as px
        
        logger.info("Starting Capital.com API Optimization Dashboard")
        dashboard = OptimizationDashboard(args.dir)
        dashboard.create_dashboard(args.port)
        return 0
        
    except ImportError:
        logger.error("Failed to import required modules for the dashboard")
        logger.error("Please install dash and plotly: pip install dash plotly pandas matplotlib")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
