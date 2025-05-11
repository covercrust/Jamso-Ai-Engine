#!/usr/bin/env python3
"""
Path Issue Detector

This script scans the codebase for references to the old directory structure
and reports any files that might need updating.
"""

import os
import re
import sys
from pathlib import Path
import argparse
from typing import List, Dict, Set, Any

# Patterns to search for
PATTERNS = [
    r'from\s+Backend\.', 
    r'import\s+Backend\.', 
    r'Backend/Database',
    r'Backend/Utils',
    r'Backend/Webhook',
    r'Backend/Exchange',
    r'Backend/Logs'
]

# Directories to exclude
EXCLUDED_DIRS = [
    '.git',
    '.venv',
    'venv',
    '__pycache__',
    'node_modules'
]

# File extensions to check
INCLUDED_EXTENSIONS = [
    '.py', '.sh', '.md', '.txt', '.json', '.yml', '.yaml', '.ipynb'
]

def scan_python_files(directory: str) -> List[str]:
    """Find all Python files in a directory recursively."""
    python_files = []
    for root, _, files in os.walk(directory):
        # Skip excluded directories
        if any(excluded in root for excluded in EXCLUDED_DIRS):
            continue
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_imports(file_path: str) -> Set[str]:
    """Extract import statements from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match import statements
        import_patterns = [
            r'^\s*from\s+([\w.]+)\s+import',  # from X import Y
            r'^\s*import\s+([\w.]+)(?:\s+as)?'  # import X or import X as Y
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.add(match.group(1))
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return imports

def check_hardcoded_paths(file_path: str) -> List[str]:
    """Check for hardcoded paths in a Python file."""
    hardcoded_paths = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Match potential hardcoded paths
        path_patterns = [
            r'[\'\"]\/\w+(?:\/\w+)+[\'\"]',  # '/path/to/something'
            r'[\'\"](?:\.\.\/)+\w+(?:\/\w+)*[\'\"]',  # '../path/to/something'
            r'os\.path\.join\([^)]*\)',  # os.path.join(...)
            r'os\.environ\.get\([\'\"]\w+[\'\"]'  # os.environ.get('PATH_VAR')
        ]
        
        for pattern in path_patterns:
            for match in re.finditer(pattern, content):
                hardcoded_paths.append(match.group(0))
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return hardcoded_paths

def main():
    """Main function to scan the project for path issues."""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        # Use the current directory as the default
        root_dir = os.getcwd()
    
    print(f"Scanning Python files in {root_dir} for potential path issues...")
    
    # Get all Python files
    python_files = scan_python_files(root_dir)
    print(f"Found {len(python_files)} Python files.")
    
    # Analyze imports and hardcoded paths
    problem_files = {}
    
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, root_dir)
        imports = extract_imports(file_path)
        hardcoded_paths = check_hardcoded_paths(file_path)
        
        # Check for problematic imports (adjust as needed)
        problematic_imports = {
            imp for imp in imports 
            if imp.startswith(('src.', 'Backend.')) or 
               (imp.count('.') > 2 and not imp.startswith('flask'))
        }
        
        # Combine findings
        if problematic_imports or hardcoded_paths:
            problem_files[rel_path] = {
                'problematic_imports': problematic_imports,
                'hardcoded_paths': hardcoded_paths
            }
    
    # Print the findings
    if problem_files:
        print("\nPotential path issues found:")
        for file_path, issues in problem_files.items():
            print(f"\n{file_path}:")
            
            if issues['problematic_imports']:
                print("  Problematic imports:")
                for imp in issues['problematic_imports']:
                    print(f"    - {imp}")
            
            if issues['hardcoded_paths']:
                print("  Hardcoded paths:")
                for path in issues['hardcoded_paths'][:5]:  # Limit to 5 for readability
                    print(f"    - {path}")
                if len(issues['hardcoded_paths']) > 5:
                    print(f"    - ... and {len(issues['hardcoded_paths']) - 5} more")
    else:
        print("\nNo potential path issues found!")

if __name__ == "__main__":
    main()
