#!/usr/bin/env python3

import sys
import os
import site

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

print("\nTrying to import flask_wtf.csrf...")
try:
    import flask_wtf.csrf
    print("✅ Import successful!")
    print(f"Module path: {flask_wtf.__file__}")
except ImportError as e:
    print(f"❌ Import failed: {e}")

print("\nSite packages directories:")
for path in site.getsitepackages():
    print(f"  - {path}")
    
# Try to find the flask_wtf directory
print("\nLooking for flask_wtf package...")
for sp in site.getsitepackages():
    potential_path = os.path.join(sp, "flask_wtf")
    if os.path.exists(potential_path):
        print(f"Found at: {potential_path}")
        print("Contents:")
        for item in os.listdir(potential_path):
            print(f"  - {item}")
