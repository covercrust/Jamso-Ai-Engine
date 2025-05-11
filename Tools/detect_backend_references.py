#!/usr/bin/env python3
"""
Updated path issue detector for the new directory structure.
This script scans for any remaining references to the old Backend directory structure.
"""

import os
import re
import sys
from typing import List, Dict, Any

# Patterns to search for
BACKEND_PATTERNS = [
    r'from\s+Backend\.', 
    r'import\s+Backend\.', 
    r'Backend/Database',
    r'/Backend/',
    r'"Backend\.',
    r"'Backend\."
]

def scan_files(directory: str, extensions: List[str] = None) -> List[str]:
    """Find all files with given extensions in a directory recursively."""
    if extensions is None:
        extensions = ['.py', '.sh', '.md', '.txt', '.json']
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                files.append(os.path.join(root, filename))
    return files

def check_backend_references(file_path: str) -> List[Dict[str, Any]]:
    """Check for references to the old Backend directory structure."""
    results = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        for pattern in BACKEND_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                results.append({
                    'pattern': pattern,
                    'matches': matches,
                    'count': len(matches)
                })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return results

def main():
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Scanning directory: {directory}")
    
    files = scan_files(directory)
    print(f"Found {len(files)} files to scan")
    
    backend_references = []
    
    for file_path in files:
        references = check_backend_references(file_path)
        if references:
            backend_references.append({
                'file': file_path,
                'references': references
            })
    
    if backend_references:
        print("\nFound references to old Backend structure in:")
        for item in backend_references:
            file_path = item['file']
            print(f"\n{file_path}")
            
            for ref in item['references']:
                pattern = ref['pattern']
                count = ref['count']
                print(f"  - Pattern '{pattern}': {count} occurrences")
        
        print(f"\nTotal files with Backend references: {len(backend_references)}")
        return 1
    else:
        print("\nNo references to old Backend structure found! Everything has been migrated.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
