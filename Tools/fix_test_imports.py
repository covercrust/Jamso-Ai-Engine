#!/usr/bin/env python3
"""
This script fixes the import paths in the integration test files.
"""
import os
import re

TEST_DIR = '/home/jamso-ai-server/Jamso-Ai-Engine/Tests/Capital.com'
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'

# Pattern to match existing sys.path.insert line
path_insert_pattern = r'sys\.path\.insert\(0,\s*[^)]+\)'

# Replacement text for consistent import
replacement_text = '''# Fix import issue by adding the project root to the Python path
PROJECT_ROOT = '/home/jamso-ai-server/Jamso-Ai-Engine'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now imports should work correctly'''

for filename in os.listdir(TEST_DIR):
    if filename.startswith('integration_test_') and filename.endswith('.py'):
        filepath = os.path.join(TEST_DIR, filename)
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check if the file already has the correct import pattern
        if 'if PROJECT_ROOT not in sys.path:' in content:
            print(f"[SKIP] {filename} already has the correct import pattern")
            continue
        
        # Find where to insert our fix - look for sys.path.insert
        if re.search(path_insert_pattern, content):
            # Replace existing sys.path.insert
            modified_content = re.sub(
                r'(# Configure paths\n.*\n)' + path_insert_pattern, 
                r'\1' + replacement_text, 
                content
            )
            
            # If the previous replacement didn't work, try a more general approach
            if modified_content == content:
                modified_content = re.sub(
                    path_insert_pattern, 
                    replacement_text, 
                    content
                )
            
            # If still no match, look for import statements to insert before them
            if modified_content == content:
                from_import_match = re.search(r'(from\s+src\.)', content)
                if from_import_match:
                    pos = from_import_match.start()
                    modified_content = content[:pos] + replacement_text + "\n\n" + content[pos:]
        else:
            # No sys.path.insert found, look for the first import from src
            from_import_match = re.search(r'(from\s+src\.)', content)
            if from_import_match:
                pos = from_import_match.start()
                modified_content = content[:pos] + replacement_text + "\n\n" + content[pos:]
            else:
                print(f"[ERROR] {filename} - Could not find a suitable position to insert the import fix")
                continue
        
        # Write the modified content back to the file
        with open(filepath, 'w') as f:
            f.write(modified_content)
        
        print(f"[FIXED] {filename}")

print("Done!")
