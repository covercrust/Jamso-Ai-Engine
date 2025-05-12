#!/usr/bin/env python3
"""
Session File Cleanup Script
Deletes old Flask-Session files from the instance/sessions directory to prevent file bloat.
"""
import os
import time
import sys

# Default session directory (adjust if needed)
SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'sessions')
# Delete files older than this many days
MAX_AGE_DAYS = 7

now = time.time()
max_age = MAX_AGE_DAYS * 86400

def cleanup_sessions(session_dir=SESSION_DIR, max_age=max_age):
    if not os.path.isdir(session_dir):
        print(f"[INFO] Session directory does not exist: {session_dir}")
        return
    deleted = 0
    for fname in os.listdir(session_dir):
        fpath = os.path.join(session_dir, fname)
        if os.path.isfile(fpath):
            try:
                if now - os.path.getmtime(fpath) > max_age:
                    os.remove(fpath)
                    deleted += 1
            except Exception as e:
                print(f"[ERROR] Could not delete {fpath}: {e}")
    print(f"[INFO] Deleted {deleted} old session files from {session_dir}")

if __name__ == "__main__":
    cleanup_sessions()
