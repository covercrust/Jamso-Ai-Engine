#!/usr/bin/env python3
"""
Jamso-AI Engine Unified Launcher (Production)
Starts the unified webhook+dashboard app using Gunicorn for production.
"""
import subprocess
import socket
import sys
import time
import os
import multiprocessing

# Advanced resource optimization for high-memory (32GB) and multi-core (4) systems
# Using more aggressive resource allocation to maximize performance
cpu_count = multiprocessing.cpu_count()

# Advanced memory-optimized worker calculation
# For high-memory (32GB) systems, we can use (2*cores)+1 formula with increased per-worker memory allocation
# This ensures all cores are fully utilized while maintaining good memory-to-CPU ratio 
# and allowing each worker to use more memory for caching and performance
worker_count = min((2 * cpu_count) + 1, 9)  # 9 workers for 4 cores and 32GB RAM
# With 9 workers on 32GB, each worker can use ~3GB of RAM for better performance

# Optimized thread count for I/O operations
# Higher thread count allows better handling of I/O-bound tasks
# Thread count is balanced to avoid excessive context switching while maximizing throughput
thread_count = 4  # 6 threads per worker for better I/O handling and memory utilization

# Calculate total concurrent operations
total_concurrent = worker_count * thread_count
print(f"[INFO] Configuring for high memory utilization: {worker_count} workers × {thread_count} threads = {total_concurrent} concurrent operations")

GUNICORN_CMD = [
    sys.executable, '-m', 'gunicorn',
    '--bind', '0.0.0.0:5000',
    '--workers', str(worker_count),  # Increased for better CPU utilization
    '--threads', str(thread_count),  # More threads for better I/O parallelism
    '--worker-class', 'gthread',  # Thread-based worker model for mixed CPU/IO workloads
    '--worker-connections', '2000',  # Doubled connection capacity 
    '--backlog', '4096',  # Increased pending connection queue
    '--max-requests', '2000',  # Worker recycling for memory management
    '--max-requests-jitter', '400',  # Prevent simultaneous worker restarts
    '--timeout', '180',  # Increased for handling complex requests
    '--keep-alive', '10',  # Increased keep-alive for connection reuse
    # Additional memory optimization flags 
    '--worker-tmp-dir', '/dev/shm',  # Use RAM-based temp directory
    '--log-level', 'info',
    '--access-logfile', 'Logs/gunicorn_access.log',
    '--error-logfile', 'Logs/gunicorn_error.log',
    # Memory optimization flags
    '--limit-request-line', '8190',  # Increased from default 4094
    '--forwarded-allow-ips', '*',  # Trust X-Forwarded-* headers
    # High-performance preload flag loads application code once in the master process
    # This reduces memory usage and speeds up worker initialization
    '--preload',
    'src.Webhook.app:create_app()'
]

def is_running(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0

def start_gunicorn():
    if is_running('127.0.0.1', 5000):
        print("[INFO] Unified app already running on 127.0.0.1:5000.")
        return None
    print("[ACTION] Starting unified webhook+dashboard app with Gunicorn on 0.0.0.0:5000...")
    # Start Gunicorn as a background process
    return subprocess.Popen(GUNICORN_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print("=== Jamso-AI Engine Unified Launcher (Production) ===")
    start_gunicorn()
    # Wait for app to be ready
    for _ in range(15):
        if is_running('127.0.0.1', 5000):
            break
        time.sleep(1)
    else:
        print("[ERROR] Failed to start unified app with Gunicorn.")
        sys.exit(1)
    print("[INFO] Unified app started with Gunicorn. Access dashboard and API at http://localhost:5000/")
    print("[INFO] Gunicorn will keep running in the background, even if you close VS Code or your terminal.")
    print("[INFO] To stop it, use: pkill -f gunicorn")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping Gunicorn (use 'pkill -f gunicorn' if needed)...")
        sys.exit(0)

if __name__ == "__main__":
    main()
