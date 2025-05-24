#!/usr/bin/env python3
"""
Utility script to verify Flask-WTF installation and imports.
This script helps diagnose import issues with Flask-WTF CSRF.
"""
import sys
import importlib.util
import importlib.metadata
import os
import site


def check_module(module_name):
    """Check if a module can be imported."""
    try:
        module = importlib.import_module(module_name)
        return True, module
    except ImportError as e:
        return False, e


def find_package_path(package_name):
    """Find the path where a package is installed."""
    try:
        # Try using importlib.metadata to find the package
        package_info = next((p for p in importlib.metadata.distributions() 
                            if p.metadata['Name'].lower() == package_name.lower()), None)
        if package_info:
            file_path = str(package_info.locate_file(''))
            if file_path:
                return os.path.dirname(file_path)
    except Exception:
        # Silent exception handling
        pass
    
    # Fallback method using importlib
    try:
        spec = importlib.util.find_spec(package_name.replace("-", "_"))
        if spec and spec.origin:
            return os.path.dirname(spec.origin)
    except Exception:
        pass
    
    return None


def main():
    """Verify Flask-WTF and related imports."""
    print("\n=== Flask-WTF Verification Tool ===")
    print("Checking Flask-WTF installation and imports...\n")
    
    modules_to_check = [
        "flask",
        "flask_wtf",
        "flask_wtf.csrf"
    ]
    
    all_passed = True
    module_paths = {}
    
    # Check Python environment
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Print site-packages paths
    print("\nSite packages directories:")
    for path in site.getsitepackages():
        print(f"  - {path}")
    
    print("\nModule import status:")
    for module_name in modules_to_check:
        success, result = check_module(module_name)
        if success and not isinstance(result, Exception):  # Ensure result is not an Exception
            # Make sure result has __file__ attribute before using it
            if hasattr(result, '__file__') and result.__file__:
                file_path = result.__file__
                abs_path = os.path.abspath(file_path)
                module_paths[module_name] = os.path.dirname(abs_path)
                print(f"✅ {module_name:<15} successfully imported from {abs_path}")
            else:
                # Handle built-in modules without __file__
                module_paths[module_name] = "built-in"
                print(f"✅ {module_name:<15} successfully imported (built-in module)")
        else:
            error_msg = str(result) if isinstance(result, Exception) else "Unknown error"
            print(f"❌ {module_name:<15} FAILED to import: {error_msg}")
            all_passed = False
    
    # Print package paths
    print("\nPackage locations:")
    for pkg_name in ['flask', 'flask-wtf']:
        path = find_package_path(pkg_name)
        if path:
            print(f"  - {pkg_name:<10}: {path}")
        else:
            print(f"  - {pkg_name:<10}: Not found")
    
    if all_passed:
        print("\nModule paths:")
        for name, path in module_paths.items():
            print(f"  - {name:<15}: {path}")
            
        print("\n✅ All modules imported successfully!")
        print("\nVS Code IDE Configuration:")
        print("If you're seeing import errors in VS Code:")
        print("1. Ensure you've selected the correct Python interpreter in VS Code")
        print(f"   Current Python: {sys.executable}")
        print("2. Add this to your .vscode/settings.json file:")
        print("   {")
        print('     "python.analysis.extraPaths": [')
        # Filter out built-in paths
        valid_paths = [p for p in module_paths.values() if p != "built-in"]
        for path in set(valid_paths):
            print(f'       "{path}",')
        print('     ],')
        print('     "python.analysis.diagnosticSeverityOverrides": {')
        print('       "reportMissingImports": "information"')
        print('     }')
        print("   }")
        print("3. Try restarting VS Code or reloading the window")
        
    else:
        print("\n❌ Some imports failed. Try running:")
        print("   pip install Flask-WTF")
        
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
