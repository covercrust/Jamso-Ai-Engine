#!/usr/bin/env python3
"""
Temporary health check script to verify Python imports
"""
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Try importing core dependencies
try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError as e:
    print(f"Error importing Flask: {str(e)}")

try:
    import sklearn
    print(f"scikit-learn version: {sklearn.__version__}")
except ImportError as e:
    print(f"Error importing scikit-learn: {str(e)}")

try:
    import pandas as pd
    print(f"Pandas version: {pd.__version__}")
except ImportError as e:
    print(f"Error importing pandas: {str(e)}")

try:
    import numpy as np
    print(f"NumPy version: {np.__version__}")
except ImportError as e:
    print(f"Error importing numpy: {str(e)}")

try:
    import psutil
    print(f"psutil version: {psutil.__version__}")
except ImportError as e:
    print(f"Error importing psutil: {str(e)}")

# Check Python path
print("\nPython Path:")
for p in sys.path:
    print(f"  {p}")
