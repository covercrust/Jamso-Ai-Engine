#!/usr/bin/env python3
"""
Memory Monitor for Jamso-AI Engine

This script monitors the memory usage of Gunicorn workers and provides recommendations
for optimizing memory usage. It also checks CPU usage to ensure all cores are being
properly utilized.
"""
import psutil
import time
import os
import sys
import subprocess
import signal
import logging
from datetime import datetime
import fcntl

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'memory_monitor.log')

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger('memory_monitor')

PID_FILE = '/tmp/jamso_memory_monitor.pid'

def singleton_check():
    try:
        pidfile = open(PID_FILE, 'w')
        fcntl.lockf(pidfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pidfile.write(str(os.getpid()))
        pidfile.flush()
        return pidfile
    except IOError:
        logger.error('Another instance of memory_monitor.py is already running. Exiting.')
        sys.exit(1)

def get_gunicorn_processes():
    """Get all Gunicorn worker processes"""
    gunicorn_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'gunicorn' in proc.info['name'] or (proc.info['cmdline'] and 'gunicorn' in ' '.join(proc.info['cmdline'])):
                gunicorn_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return gunicorn_processes

def check_memory_usage():
    """Check memory usage of Gunicorn workers"""
    procs = get_gunicorn_processes()
    if not procs:
        logger.warning("No Gunicorn processes found")
        return
        
    total_memory = psutil.virtual_memory().total / (1024 * 1024 * 1024)  # GB
    used_memory = 0
    process_count = 0
    
    logger.info(f"Found {len(procs)} Gunicorn processes")
    for proc in procs:
        try:
            proc_memory = proc.memory_info().rss / (1024 * 1024)  # MB
            logger.info(f"Process {proc.pid}: {proc_memory:.2f} MB")
            used_memory += proc_memory
            process_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    used_memory_gb = used_memory / 1024  # Convert to GB
    logger.info(f"Total Gunicorn memory usage: {used_memory_gb:.2f} GB of {total_memory:.2f} GB available")
    logger.info(f"Memory utilization: {(used_memory_gb / total_memory) * 100:.2f}%")
    
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    avg_cpu = sum(cpu_percent) / len(cpu_percent)
    logger.info(f"CPU usage per core: {cpu_percent}")
    logger.info(f"Average CPU usage: {avg_cpu:.2f}%")
    
    # Provide optimization recommendations
    if used_memory_gb < total_memory * 0.3 and avg_cpu > 70:
        logger.warning("Memory usage is low but CPU is high. Consider using more worker processes.")
    elif used_memory_gb > total_memory * 0.8:
        logger.warning("Memory usage is high. Consider reducing worker count.")

# Only referenced by setup_performance_cron.sh. If you do not use the cron job, this can be removed. Otherwise, keep for monitoring.

def main():
    pidfile = singleton_check()
    logger.info("Starting memory monitor for Jamso-AI Engine")
    
    try:
        while True:
            check_memory_usage()
            # Check every 5 minutes
            time.sleep(300)
    except KeyboardInterrupt:
        logger.info("Memory monitor stopped by user")
        sys.exit(0)
    finally:
        pidfile.close()

if __name__ == "__main__":
    main()
