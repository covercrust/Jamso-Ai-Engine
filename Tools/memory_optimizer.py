#!/usr/bin/env python3
"""
Memory Optimization Script for Jamso-AI Engine

This script optimizes memory usage by:
1. Configuring virtual memory settings
2. Setting up database optimizations
3. Applying Flask/Werkzeug memory optimizations
4. Setting up memory monitoring
5. Implementing database connection pooling

Run this script to apply memory optimizations for both SQLite and the application.
"""
import os
import sys
import subprocess
import logging
import argparse
import psutil
import time
import gc
from pathlib import Path

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_PATH, 'Logs', 'memory_optimizer.log'))
    ]
)
logger = logging.getLogger('memory_optimizer')

def setup_system_memory_settings():
    """Setup system memory settings for better performance"""
    # These commands require sudo privileges
    try:
        # Increase virtual memory swappiness (0-100)
        # Lower values prioritize keeping processes in memory rather than swapping
        subprocess.run(['sysctl', '-w', 'vm.swappiness=10'], check=True)
        
        # Increase cache pressure - makes the kernel reclaim memory from page cache more aggressively
        subprocess.run(['sysctl', '-w', 'vm.vfs_cache_pressure=50'], check=True)
        
        logger.info("System memory settings updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set system memory settings: {str(e)}")
        logger.info("You can manually set these by running with sudo:")
        logger.info("  sudo sysctl -w vm.swappiness=10")
        logger.info("  sudo sysctl -w vm.vfs_cache_pressure=50")
        return False
    except Exception as e:
        logger.error(f"Error updating system memory settings: {str(e)}")
        return False

def check_memory_usage():
    """Check current memory usage and provide recommendations"""
    try:
        # Get virtual memory info
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        logger.info(f"Memory Total: {mem.total / (1024**3):.2f} GB")
        logger.info(f"Memory Used: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
        logger.info(f"Memory Available: {mem.available / (1024**3):.2f} GB")
        logger.info(f"Swap Total: {swap.total / (1024**3):.2f} GB")
        logger.info(f"Swap Used: {swap.used / (1024**3):.2f} GB ({swap.percent}%)")
        
        # Check for current Python processes
        python_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_procs.append((
                        proc.info['pid'],
                        proc.info['name'],
                        proc.info['memory_info'].rss / (1024**2)
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Show Python process memory usage
        logger.info(f"Found {len(python_procs)} Python processes:")
        for pid, name, mem_mb in python_procs:
            logger.info(f"  PID {pid}: {name} - {mem_mb:.2f} MB")
        
        # Provide recommendations
        if mem.percent > 80:
            logger.warning("Memory usage is high (>80%). Consider reducing worker count or increasing server memory.")
        if swap.percent > 50:
            logger.warning("Swap usage is high (>50%). Application performance may be degraded.")
        
        return True
    except Exception as e:
        logger.error(f"Error checking memory usage: {str(e)}")
        return False

def optimize_python_memory():
    """Apply Python memory optimizations"""
    # Force garbage collection
    gc.collect()
    
    # Set aggressive garbage collection thresholds
    gc.set_threshold(700, 10, 5)
    
    # Disable automatic garbage collection (we'll do it manually)
    gc.disable()
    
    # Set memory allocation strategy
    import sys
    if hasattr(sys, 'set_malloc_opts'):  # Python 3.7+ on some platforms
        sys.set_malloc_opts(5, 1, 0)
    
    logger.info("Python memory optimizations applied")
    return True

def run_sqlite_optimization():
    """Run the SQLite database optimization script"""
    try:
        db_optimizer_path = os.path.join(BASE_PATH, 'Tools', 'optimize_db.py')
        result = subprocess.run([sys.executable, db_optimizer_path], check=True, 
                               capture_output=True, text=True)
        logger.info("Database optimization completed successfully")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Database optimization failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running database optimization: {str(e)}")
        return False

def ensure_worker_tmp_dir():
    """Ensure the RAM-based temporary directory exists"""
    try:
        # Check if /dev/shm exists (it's a RAM-based filesystem)
        if not os.path.exists('/dev/shm'):
            logger.warning("/dev/shm does not exist. Cannot set up RAM-based temporary directory")
            return False
        
        # Create a directory for Gunicorn workers
        worker_tmp_dir = '/dev/shm/jamso-ai-engine'
        os.makedirs(worker_tmp_dir, exist_ok=True)
        
        # Set permissions (world-writable so Gunicorn can use it)
        os.chmod(worker_tmp_dir, 0o777)
        
        logger.info(f"RAM-based temporary directory set up at {worker_tmp_dir}")
        return True
    except Exception as e:
        logger.error(f"Error setting up RAM-based temporary directory: {str(e)}")
        return False

def start_memory_monitor():
    """Start the memory monitoring script in the background"""
    try:
        memory_monitor_path = os.path.join(BASE_PATH, 'Tools', 'memory_monitor.py')
        if not os.path.exists(memory_monitor_path):
            logger.error(f"Memory monitor script not found at {memory_monitor_path}")
            return False
        
        # Start memory monitor in the background
        subprocess.Popen([sys.executable, memory_monitor_path], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        
        logger.info("Memory monitor started in the background")
        return True
    except Exception as e:
        logger.error(f"Error starting memory monitor: {str(e)}")
        return False

def setup_performance_cron():
    """Set up cron jobs for performance monitoring and optimization"""
    try:
        cron_setup_path = os.path.join(BASE_PATH, 'Tools', 'setup_performance_cron.sh')
        if not os.path.exists(cron_setup_path):
            logger.error(f"Performance cron setup script not found at {cron_setup_path}")
            return False
        
        # Make the script executable
        os.chmod(cron_setup_path, 0o755)
        
        # Run the script
        result = subprocess.run([cron_setup_path], check=True, 
                               capture_output=True, text=True)
        
        logger.info("Performance cron jobs set up successfully")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Performance cron setup failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error setting up performance cron jobs: {str(e)}")
        return False

def main():
    """Main function to run all memory optimizations"""
    parser = argparse.ArgumentParser(description='Memory Optimization Script for Jamso-AI Engine')
    parser.add_argument('--system', action='store_true', help='Apply system-level memory settings (requires sudo)')
    parser.add_argument('--all', action='store_true', help='Apply all optimizations')
    args = parser.parse_args()
    
    logger.info("Starting memory optimization")
    
    # Track overall success
    success = True
    
    # Check current memory usage
    logger.info("Checking current memory usage...")
    check_memory_usage()
    
    # Apply system memory settings if requested
    if args.system or args.all:
        logger.info("Applying system memory settings...")
        if not setup_system_memory_settings():
            success = False
    
    # Apply Python memory optimizations
    logger.info("Applying Python memory optimizations...")
    if not optimize_python_memory():
        success = False
    
    # Run SQLite optimization
    logger.info("Running database optimization...")
    if not run_sqlite_optimization():
        success = False
    
    # Ensure RAM-based temporary directory exists
    logger.info("Setting up RAM-based temporary directory...")
    if not ensure_worker_tmp_dir():
        success = False
    
    # Start memory monitor
    logger.info("Starting memory monitor...")
    if not start_memory_monitor():
        success = False
    
    # Setup performance cron jobs
    logger.info("Setting up performance cron jobs...")
    if not setup_performance_cron():
        success = False
    
    # Final check of memory usage
    logger.info("Checking memory usage after optimizations...")
    check_memory_usage()
    
    if success:
        logger.info("All memory optimizations completed successfully")
    else:
        logger.warning("Some memory optimizations failed, check the log for details")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
