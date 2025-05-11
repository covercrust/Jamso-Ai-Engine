#!/usr/bin/env python3
"""
Process monitoring utilities for Jamso AI Server.
This module provides process monitoring capabilities if psutil is available.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

# Try to import psutil, which might not be available in all environments
try:
    import psutil
    is_psutil_available = True
except ImportError:
    logger.warning("psutil not available - some monitoring features will be disabled")
    is_psutil_available = False

class ProcessMonitor:
    """
    Monitor system and process resource usage
    """
    def __init__(self):
        if not is_psutil_available:
            raise ImportError("psutil is required for process monitoring")
        
        self.current_process = psutil.Process()
    
    def get_system_resources(self) -> Dict[str, Any]:
        """
        Get overall system resource usage
        """
        memory = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=0.1)
        disk_usage = psutil.disk_usage('/')
        
        return {
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'cpu_usage': cpu_usage,
            'disk': {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': disk_usage.percent
            }
        }
    
    def get_process_resources(self, pid: Optional[int] = None) -> Dict[str, Any]:
        """
        Get resource usage for a specific process
        
        Args:
            pid: Process ID to monitor (uses current process if None)
        """
        if pid is None:
            process = self.current_process
        else:
            try:
                process = psutil.Process(pid)
            except psutil.NoSuchProcess:
                logger.error(f"No process with PID {pid}")
                return {}
        
        with process.oneshot():
            try:
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent(interval=0.1)
                
                return {
                    'pid': process.pid,
                    'name': process.name(),
                    'status': process.status(),
                    'memory': {
                        'rss': memory_info.rss,  # Resident Set Size
                        'vms': memory_info.vms,  # Virtual Memory Size
                    },
                    'cpu_percent': cpu_percent,
                    'threads': len(process.threads()),
                    'created': process.create_time(),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.error(f"Error getting process info: {e}")
                return {}
    
    def list_python_processes(self) -> List[Dict[str, Any]]:
        """
        List all running Python processes
        """
        python_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if it's a Python process
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    proc_info = {
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': ' '.join(proc.info['cmdline'] if proc.info['cmdline'] else []),
                        'status': proc.status()
                    }
                    python_processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return python_processes
