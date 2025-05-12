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

GUNICORN_CMD = [
    sys.executable, '-m', 'gunicorn',
    '--bind', '0.0.0.0:5000',
    '--workers', '12',  # Increased to 12 to better utilize 32GB RAM; adjust as needed
    '--timeout', '120',
    '--log-level', 'info',
    '--access-logfile', 'Logs/gunicorn_access.log',
    '--error-logfile', 'Logs/gunicorn_error.log',
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
