#!/usr/bin/env python3
"""
Scheduled Parameter Optimization Process

This script implements a scheduled optimization process that runs optimizations
on a regular basis, compares results over time, and alerts on parameter degradation.

Usage:
    python scheduled_optimization.py --interval 24 --symbols BTCUSD,EURUSD --timeframes HOUR,DAY
    
    To run as a background service:
    nohup python scheduled_optimization.py --daemon > optimization_log.txt 2>&1 &
"""

import os
import sys
import time
import argparse
import json
import logging
import signal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import threading
import subprocess

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Import mobile alerts for notifications
from src.AI.mobile_alerts import MobileAlertManager
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Create logs directory if it doesn't exist
logs_dir = os.path.join(parent_dir, 'src', 'Logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
log_file = os.path.join(logs_dir, 'scheduled_optimization.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database for storing optimization history
DB_PATH = os.path.join(parent_dir, 'parameter_history.db')

def initialize_database():
    """Initialize the database for storing optimization history."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create table for optimization history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS optimization_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            timeframe TEXT,
            objective TEXT,
            return_value REAL,
            sharpe_ratio REAL,
            max_drawdown REAL,
            win_rate REAL,
            total_trades INTEGER,
            params_json TEXT
        )
        ''')
        
        # Create table for alerts
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS optimization_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            timeframe TEXT,
            alert_type TEXT,
            message TEXT,
            acknowledged INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

def store_optimization_result(symbol: str, timeframe: str, objective: str, 
                             metrics: dict, params: dict):
    """Store optimization result in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO optimization_history
        (timestamp, symbol, timeframe, objective, return_value, sharpe_ratio, 
         max_drawdown, win_rate, total_trades, params_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            symbol,
            timeframe,
            objective,
            metrics.get('total_return', 0),
            metrics.get('sharpe_ratio', 0),
            metrics.get('max_drawdown', 0),
            metrics.get('win_rate', 0),
            metrics.get('total_trades', 0),
            json.dumps(params)
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Stored optimization result for {symbol} {timeframe} {objective}")
    except Exception as e:
        logger.error(f"Error storing optimization result: {str(e)}")

def get_previous_optimization(symbol: str, timeframe: str, objective: str) -> Tuple[dict, dict]:
    """Get the most recent optimization result for a symbol/timeframe/objective."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT return_value, sharpe_ratio, max_drawdown, win_rate, total_trades, params_json
        FROM optimization_history
        WHERE symbol = ? AND timeframe = ? AND objective = ?
        ORDER BY timestamp DESC
        LIMIT 1
        ''', (symbol, timeframe, objective))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'total_return': row[0],
                'sharpe_ratio': row[1],
                'max_drawdown': row[2],
                'win_rate': row[3],
                'total_trades': row[4]
            }, json.loads(row[5])
        else:
            return None, None
    except Exception as e:
        logger.error(f"Error getting previous optimization: {str(e)}")
        return None, None

def log_alert(symbol: str, timeframe: str, alert_type: str, message: str):
    """Log an alert to the database and send notification."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO optimization_alerts
        (timestamp, symbol, timeframe, alert_type, message)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            symbol,
            timeframe,
            alert_type,
            message
        ))
        
        conn.commit()
        conn.close()
        
        # Log to file as well
        logger.warning(f"ALERT ({alert_type}): {symbol} {timeframe} - {message}")
        
        # Send email notification if configured
        send_alert_email(f"Parameter Optimization Alert: {symbol} {timeframe}", message)
        
    except Exception as e:
        logger.error(f"Error logging alert: {str(e)}")

def send_alert_email(subject: str, message: str):
    """Send an email alert if email configuration is available."""
    try:
        # Check for email configuration
        config_path = os.path.join(parent_dir, 'src', 'Credentials', 'email_config.json')
        
        if not os.path.exists(config_path):
            logger.warning("Email configuration not found, skipping email alert")
            return
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = config.get('from_email')
        msg['To'] = config.get('to_email')
        msg['Subject'] = subject
        
        body = f"""
        <html>
        <body>
            <h2>Parameter Optimization Alert</h2>
            <p>{message}</p>
            <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>This is an automated message from the APOP system.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(config.get('smtp_server'), config.get('smtp_port'))
        server.starttls()
        server.login(config.get('username'), config.get('password'))
        server.send_message(msg)
        server.quit()
        
        logger.info("Alert email sent successfully")
    except Exception as e:
        logger.error(f"Error sending email alert: {str(e)}")

def check_parameter_degradation(symbol: str, timeframe: str, objective: str, 
                              current_metrics: dict, previous_metrics: dict) -> bool:
    """
    Check if parameter performance has degraded significantly
    
    Returns True if degradation is detected, False otherwise
    """
    if not previous_metrics:
        return False
    
    # Calculate degradation percentages
    return_degradation = ((previous_metrics['total_return'] - current_metrics['total_return']) / 
                        abs(previous_metrics['total_return'])) if previous_metrics['total_return'] != 0 else 0
    
    sharpe_degradation = ((previous_metrics['sharpe_ratio'] - current_metrics['sharpe_ratio']) / 
                        abs(previous_metrics['sharpe_ratio'])) if previous_metrics['sharpe_ratio'] != 0 else 0
    
    drawdown_increase = ((current_metrics['max_drawdown'] - previous_metrics['max_drawdown']) / 
                        abs(previous_metrics['max_drawdown'])) if previous_metrics['max_drawdown'] != 0 else 0
    
    # Check degradation thresholds
    degraded = False
    message = []
    
    if return_degradation > 0.2:  # 20% reduction in returns
        degraded = True
        message.append(f"Return degraded by {return_degradation*100:.1f}% "
                     f"({previous_metrics['total_return']:.2f}% -> {current_metrics['total_return']:.2f}%)")
    
    if sharpe_degradation > 0.2:  # 20% reduction in Sharpe ratio
        degraded = True
        message.append(f"Sharpe ratio degraded by {sharpe_degradation*100:.1f}% "
                     f"({previous_metrics['sharpe_ratio']:.2f} -> {current_metrics['sharpe_ratio']:.2f})")
    
    if drawdown_increase > 0.3:  # 30% increase in drawdown
        degraded = True
        message.append(f"Max drawdown increased by {drawdown_increase*100:.1f}% "
                     f"({previous_metrics['max_drawdown']:.2f}% -> {current_metrics['max_drawdown']:.2f}%)")
    
    # Log alert if degradation detected
    if degraded:
        alert_message = f"Parameter degradation detected: {', '.join(message)}"
        log_alert(symbol, timeframe, "DEGRADATION", alert_message)
        
        # Send mobile alert for significant degradation
        try:
            # Get access to the alert manager from the running optimizer instance
            if 'optimizer' in globals() and hasattr(globals()['optimizer'], 'alert_manager'):
                alert_manager = globals()['optimizer'].alert_manager
                
                # Determine alert level based on degradation severity
                level = "warning"
                if return_degradation > 0.3 or sharpe_degradation > 0.3 or drawdown_increase > 0.5:
                    level = "critical"
                
                alert_manager.send_alert(
                    f"{symbol} {timeframe} Performance Degradation",
                    alert_message,
                    level=level,
                    data={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "objective": objective,
                        "previous_metrics": previous_metrics,
                        "current_metrics": current_metrics
                    }
                )
        except Exception as e:
            logger.error(f"Error sending mobile alert: {str(e)}")
    
    return degraded

def plot_optimization_history(symbol: str, timeframe: str, objective: str, output_file: str = None):
    """Plot optimization history for a symbol/timeframe/objective combination."""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Query for optimization history
        query = '''
        SELECT timestamp, return_value, sharpe_ratio, max_drawdown, win_rate
        FROM optimization_history
        WHERE symbol = ? AND timeframe = ? AND objective = ?
        ORDER BY timestamp ASC
        '''
        
        df = pd.read_sql_query(query, conn, params=(symbol, timeframe, objective))
        conn.close()
        
        if df.empty:
            logger.warning(f"No optimization history found for {symbol} {timeframe} {objective}")
            return
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create plot
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # Return plot
        axes[0, 0].plot(df['timestamp'], df['return_value'], marker='o')
        axes[0, 0].set_title('Total Return (%)')
        axes[0, 0].grid(True, linestyle='--', alpha=0.7)
        
        # Sharpe ratio plot
        axes[0, 1].plot(df['timestamp'], df['sharpe_ratio'], marker='o', color='green')
        axes[0, 1].set_title('Sharpe Ratio')
        axes[0, 1].grid(True, linestyle='--', alpha=0.7)
        
        # Max drawdown plot
        axes[1, 0].plot(df['timestamp'], df['max_drawdown'], marker='o', color='red')
        axes[1, 0].set_title('Max Drawdown (%)')
        axes[1, 0].grid(True, linestyle='--', alpha=0.7)
        
        # Win rate plot
        axes[1, 1].plot(df['timestamp'], df['win_rate'], marker='o', color='orange')
        axes[1, 1].set_title('Win Rate (%)')
        axes[1, 1].grid(True, linestyle='--', alpha=0.7)
        
        # Add title
        fig.suptitle(f'Optimization History: {symbol} {timeframe} ({objective})', fontsize=16)
        
        plt.tight_layout(rect=(0, 0, 1, 0.95))
        
        # Save or display
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logger.info(f"Optimization history plot saved to {output_file}")
        else:
            plt.show()
            
    except Exception as e:
        logger.error(f"Error plotting optimization history: {str(e)}")

def run_optimization(symbol: str, timeframe: str, objective: str, 
                    days: int = 30, max_evals: int = 20, use_sentiment: bool = True):
    """Run an optimization for a symbol/timeframe/objective combination."""
    try:
        logger.info(f"Starting optimization for {symbol} {timeframe} {objective}")
        
        # Generate output file path
        output_file = os.path.join(
            parent_dir, 
            f"capital_com_optimized_params_{symbol}_{timeframe}_{objective}.json"
        )
        
        # Build command
        cmd = [
            "python3", 
            os.path.join(parent_dir, "src", "AI", "capital_data_optimizer.py"),
            f"--symbol={symbol}",
            f"--timeframe={timeframe}",
            f"--objective={objective}",
            f"--days={days}",
            f"--max-evals={max_evals}",
            f"--output={output_file}"
        ]
        
        if use_sentiment:
            cmd.append("--use-sentiment")
        
        # Run optimization
        logger.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Optimization failed with exit code {process.returncode}")
            logger.error(f"Error output: {process.stderr}")
            return None, None
        else:
            logger.info(f"Optimization completed successfully")
            logger.debug(f"Output: {process.stdout}")
            
            # Read the results
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    results = json.load(f)
                
                params = results.get('params', {})
                metrics = results.get('metrics', {})
                
                # Store in database
                store_optimization_result(symbol, timeframe, objective, metrics, params)
                
                # Check for parameter degradation
                previous_metrics, previous_params = get_previous_optimization(symbol, timeframe, objective)
                degraded = False
                if previous_metrics and metrics:
                    degraded = check_parameter_degradation(symbol, timeframe, objective, metrics, previous_metrics)
                
                # Run out-of-sample testing
                run_out_of_sample_test(output_file)
                
                # Send mobile alert for optimization completion
                try:
                    if 'optimizer' in globals() and hasattr(globals()['optimizer'], 'alert_manager'):
                        alert_manager = globals()['optimizer'].alert_manager
                        
                        # Send info alert for successful optimization
                        level = "info"
                        if degraded:
                            level = "warning"  # Parameter degradation already triggered a warning or critical alert
                            
                        # Only send info alerts for significant improvements
                        if (level == "info" and 
                            (not previous_metrics or 
                             metrics['total_return'] > previous_metrics['total_return'] * 1.1 or
                             metrics['sharpe_ratio'] > previous_metrics['sharpe_ratio'] * 1.1)):
                            
                            alert_manager.send_alert(
                                f"{symbol} {timeframe} Optimization Complete",
                                f"Return: {metrics['total_return']:.2f}%, Sharpe: {metrics['sharpe_ratio']:.2f}, " +
                                f"Win Rate: {metrics['win_rate']:.1f}%, Drawdown: {metrics['max_drawdown']:.2f}%",
                                level=level,
                                data={
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                    "objective": objective,
                                    "metrics": metrics,
                                    "params": params
                                }
                            )
                except Exception as e:
                    logger.error(f"Error sending mobile alert: {str(e)}")
                
                return metrics, params
            else:
                logger.error(f"Output file not found: {output_file}")
                return None, None
    except Exception as e:
        logger.error(f"Error running optimization: {str(e)}")
        return None, None

def run_out_of_sample_test(params_file: str):
    """Run out-of-sample testing for a parameter file."""
    try:
        logger.info(f"Running out-of-sample test for {params_file}")
        
        # Build command
        cmd = [
            "python3", 
            os.path.join(parent_dir, "src", "AI", "test_optimized_params.py"),
            f"--params-file={params_file}",
            "--days=60",
            "--mode=historical",
            "--mc-simulations=50"
        ]
        
        # Run test
        logger.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Out-of-sample test failed with exit code {process.returncode}")
            logger.error(f"Error output: {process.stderr}")
        else:
            logger.info(f"Out-of-sample test completed successfully")
            
    except Exception as e:
        logger.error(f"Error running out-of-sample test: {str(e)}")

def generate_dashboard():
    """Generate a performance dashboard for all optimized symbols."""
    try:
        logger.info("Generating performance dashboard")
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        
        # Get all symbol/timeframe/objective combinations
        query = '''
        SELECT DISTINCT symbol, timeframe, objective
        FROM optimization_history
        ORDER BY symbol, timeframe, objective
        '''
        
        combinations = pd.read_sql_query(query, conn)
        
        if combinations.empty:
            logger.warning("No optimization history found")
            conn.close()
            return
        
        # Create a dashboard directory if it doesn't exist
        dashboard_dir = os.path.join(parent_dir, 'dashboard')
        os.makedirs(dashboard_dir, exist_ok=True)
        
        # Generate plots for each combination
        for _, row in combinations.iterrows():
            symbol = row['symbol']
            timeframe = row['timeframe']
            objective = row['objective']
            
            output_file = os.path.join(
                dashboard_dir,
                f"history_{symbol}_{timeframe}_{objective}.png"
            )
            
            plot_optimization_history(symbol, timeframe, objective, output_file)
        
        # Create HTML dashboard
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Parameter Optimization Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .chart-container { margin-bottom: 30px; border: 1px solid #ddd; padding: 10px; }
                .chart-title { font-weight: bold; margin-bottom: 10px; }
                .chart { max-width: 100%; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
            </style>
        </head>
        <body>
            <h1>Jamso-AI-Engine Parameter Optimization Dashboard</h1>
            <p>Last updated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
            
            <h2>Recent Optimizations</h2>
            <table>
                <tr>
                    <th>Symbol</th>
                    <th>Timeframe</th>
                    <th>Objective</th>
                    <th>Last Run</th>
                    <th>Return</th>
                    <th>Sharpe</th>
                    <th>Drawdown</th>
                    <th>Win Rate</th>
                </tr>
        '''
        
        # Get most recent optimization for each combination
        for _, row in combinations.iterrows():
            symbol = row['symbol']
            timeframe = row['timeframe']
            objective = row['objective']
            
            query = '''
            SELECT timestamp, return_value, sharpe_ratio, max_drawdown, win_rate
            FROM optimization_history
            WHERE symbol = ? AND timeframe = ? AND objective = ?
            ORDER BY timestamp DESC
            LIMIT 1
            '''
            
            recent = pd.read_sql_query(query, conn, params=(symbol, timeframe, objective))
            
            if not recent.empty:
                timestamp = pd.to_datetime(recent['timestamp'].iloc[0]).strftime('%Y-%m-%d %H:%M:%S')
                return_val = f"{recent['return_value'].iloc[0]:.2f}%"
                sharpe = f"{recent['sharpe_ratio'].iloc[0]:.2f}"
                drawdown = f"{recent['max_drawdown'].iloc[0]:.2f}%"
                win_rate = f"{recent['win_rate'].iloc[0]:.2f}%"
                
                html += f'''
                <tr>
                    <td>{symbol}</td>
                    <td>{timeframe}</td>
                    <td>{objective}</td>
                    <td>{timestamp}</td>
                    <td>{return_val}</td>
                    <td>{sharpe}</td>
                    <td>{drawdown}</td>
                    <td>{win_rate}</td>
                </tr>
                '''
        
        html += '''
            </table>
            
            <h2>Performance Charts</h2>
        '''
        
        # Add charts to dashboard
        for _, row in combinations.iterrows():
            symbol = row['symbol']
            timeframe = row['timeframe']
            objective = row['objective']
            
            chart_file = f"history_{symbol}_{timeframe}_{objective}.png"
            chart_path = os.path.join(dashboard_dir, chart_file)
            
            if os.path.exists(chart_path):
                html += f'''
                <div class="chart-container">
                    <div class="chart-title">{symbol} {timeframe} ({objective})</div>
                    <img class="chart" src="{chart_file}" alt="{symbol} {timeframe} chart">
                </div>
                '''
        
        html += '''
            <h2>Recent Alerts</h2>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>Symbol</th>
                    <th>Timeframe</th>
                    <th>Type</th>
                    <th>Message</th>
                </tr>
        '''
        
        # Get recent alerts
        query = '''
        SELECT timestamp, symbol, timeframe, alert_type, message
        FROM optimization_alerts
        ORDER BY timestamp DESC
        LIMIT 10
        '''
        
        alerts = pd.read_sql_query(query, conn)
        
        for _, alert in alerts.iterrows():
            timestamp = pd.to_datetime(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            html += f'''
            <tr>
                <td>{timestamp}</td>
                <td>{alert['symbol']}</td>
                <td>{alert['timeframe']}</td>
                <td>{alert['alert_type']}</td>
                <td>{alert['message']}</td>
            </tr>
            '''
        
        html += '''
            </table>
        </body>
        </html>
        '''
        
        # Write HTML dashboard
        dashboard_path = os.path.join(dashboard_dir, 'index.html')
        with open(dashboard_path, 'w') as f:
            f.write(html)
        
        logger.info(f"Dashboard generated at {dashboard_path}")
        
        # Close database connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")

class ScheduledOptimizer:
    """Class to handle scheduled optimization process."""
    
    def __init__(self, interval_hours: float = 24.0, symbols: List[str] = None, 
                timeframes: List[str] = None, objectives: List[str] = None):
        """Initialize the scheduled optimizer."""
        self.interval_hours = interval_hours
        self.symbols = symbols or ["BTCUSD", "EURUSD", "US500"]
        self.timeframes = timeframes or ["HOUR", "DAY"]
        self.objectives = objectives or ["sharpe", "risk_adjusted"]
        self.running = False
        self.stop_event = threading.Event()
        self.days = 30
        self.max_evals = 20
        self.use_sentiment = True
        
        # Initialize mobile alerts manager
        self.alert_manager = MobileAlertManager()
    
    def start(self):
        """Start the scheduled optimization process."""
        self.running = True
        self.stop_event.clear()
        
        # Initialize database
        initialize_database()
        
        logger.info(f"Starting scheduled optimization process")
        logger.info(f"Interval: {self.interval_hours} hours")
        logger.info(f"Symbols: {', '.join(self.symbols)}")
        logger.info(f"Timeframes: {', '.join(self.timeframes)}")
        logger.info(f"Objectives: {', '.join(self.objectives)}")
        
        # Send mobile alert for scheduler start
        try:
            self.alert_manager.send_alert(
                "Optimization Scheduler Started",
                f"Scheduled optimization process started for {len(self.symbols)} symbols, " +
                f"{len(self.timeframes)} timeframes, and {len(self.objectives)} objectives. " +
                f"Interval: {self.interval_hours} hours.",
                level="info"
            )
        except Exception as e:
            logger.error(f"Error sending mobile alert: {str(e)}")
        
        # Run first optimization immediately
        self._run_all_optimizations()
        
        # Start scheduler loop
        while self.running and not self.stop_event.is_set():
            # Sleep for the specified interval
            for _ in range(int(self.interval_hours * 60 * 60)):  # Convert hours to seconds
                if self.stop_event.is_set():
                    break
                time.sleep(1)
            
            if self.running and not self.stop_event.is_set():
                self._run_all_optimizations()
    
    def stop(self):
        """Stop the scheduled optimization process."""
        logger.info("Stopping scheduled optimization process")
        self.running = False
        self.stop_event.set()
        
        # Send mobile alert for scheduler stop
        try:
            self.alert_manager.send_alert(
                "Optimization Scheduler Stopped",
                "Scheduled optimization process has been stopped.",
                level="warning"
            )
        except Exception as e:
            logger.error(f"Error sending mobile alert: {str(e)}")
    
    def _run_all_optimizations(self):
        """Run optimizations for all configured combinations."""
        start_time = time.time()
        logger.info("Starting optimization batch")
        
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                for objective in self.objectives:
                    try:
                        if not self.running or self.stop_event.is_set():
                            return
                            
                        logger.info(f"Optimizing {symbol} {timeframe} {objective}")
                        metrics, params = run_optimization(
                            symbol, timeframe, objective, 
                            days=self.days, max_evals=self.max_evals,
                            use_sentiment=self.use_sentiment
                        )
                        
                        if metrics and params:
                            logger.info(f"Optimization successful: {metrics}")
                        else:
                            logger.warning(f"Optimization unsuccessful for {symbol} {timeframe} {objective}")
                            
                    except Exception as e:
                        logger.error(f"Error during optimization {symbol} {timeframe} {objective}: {str(e)}")
        
        # Generate dashboard after all optimizations
        generate_dashboard()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed optimization batch in {elapsed_time:.2f} seconds")

def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info("Received termination signal")
    if hasattr(signal_handler, "optimizer") and signal_handler.optimizer:
        signal_handler.optimizer.stop()
    sys.exit(0)

def main():
    """Main function to handle command-line arguments and run the scheduler."""
    parser = argparse.ArgumentParser(description="Scheduled Parameter Optimization Process")
    parser.add_argument("--interval", type=float, default=24.0, help="Optimization interval in hours")
    parser.add_argument("--symbols", type=str, default="BTCUSD,EURUSD,US500", 
                       help="Comma-separated list of symbols to optimize")
    parser.add_argument("--timeframes", type=str, default="HOUR,DAY", 
                       help="Comma-separated list of timeframes to optimize")
    parser.add_argument("--objectives", type=str, default="sharpe,risk_adjusted", 
                       help="Comma-separated list of objectives to optimize")
    parser.add_argument("--days", type=int, default=30, help="Days of historical data to use")
    parser.add_argument("--max-evals", type=int, default=20, help="Maximum evaluations per optimization")
    parser.add_argument("--use-sentiment", action="store_true", help="Use sentiment data in optimization")
    parser.add_argument("--dashboard-only", action="store_true", 
                       help="Generate dashboard only without running optimizations")
    parser.add_argument("--daemon", action="store_true", help="Run as a daemon/service")
    parser.add_argument("--mobile-alerts", action="store_true", help="Enable mobile alerts")
    parser.add_argument("--alert-level", type=str, default="warning", choices=["info", "warning", "critical"],
                      help="Minimum alert level to send")
    
    args = parser.parse_args()
    
    # Split comma-separated lists
    symbols = args.symbols.split(",") if args.symbols else ["BTCUSD"]
    timeframes = args.timeframes.split(",") if args.timeframes else ["HOUR"]
    objectives = args.objectives.split(",") if args.objectives else ["sharpe"]
    
    if args.dashboard_only:
        # Generate dashboard only
        initialize_database()
        generate_dashboard()
        return
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the optimizer
    optimizer = ScheduledOptimizer(
        interval_hours=args.interval,
        symbols=symbols,
        timeframes=timeframes,
        objectives=objectives
    )
    optimizer.days = args.days
    optimizer.max_evals = args.max_evals
    optimizer.use_sentiment = args.use_sentiment
    
    # Store reference for signal handler and make it global for other functions
    signal_handler.optimizer = optimizer
    globals()['optimizer'] = optimizer
    
    # Run optimizer (blocking call)
    try:
        optimizer.start()
    except (KeyboardInterrupt, SystemExit):
        optimizer.stop()
    except Exception as e:
        logger.error(f"Error in scheduled optimizer: {str(e)}")
        optimizer.stop()

if __name__ == "__main__":
    main()
