from pathlib import Path
"""
File Manager Utility Module - Direct Integration
"""

import os
import shutil
import subprocess
import logging
import sqlite3

# Set up logging
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = os.path.join(BASE_DIR, "file_manager.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Environment and permissions
def ensure_superuser_privileges():
    """Ensures the script is running with superuser permissions."""
    if os.geteuid() != 0:
        raise PermissionError("Superuser privileges required.")

def is_within_base_dir(path: str) -> bool:
    """Checks if the given path is within the base directory."""
    return os.path.commonpath([BASE_DIR, os.path.abspath(path)]) == BASE_DIR

# Core file operations
def list_files_in_directory(directory="."):
    """Lists all files in the specified directory."""
    directory_path = os.path.join(BASE_DIR, directory)
    if not is_within_base_dir(directory_path):
        return "Access Denied: Directory outside allowed environment."
    try:
        files = os.listdir(directory_path)
        logging.debug(f"Listed files in {directory}: {files}")
        return files
    except Exception as e:
        logging.error(f"Error listing files in directory {directory}: {e}")
        return str(e)

def read_file(file_path: str):
    """Reads and returns the content of a file."""
    absolute_path = os.path.join(BASE_DIR, file_path)
    if not is_within_base_dir(absolute_path):
        return "Access Denied: File outside allowed environment."
    try:
        with open(absolute_path, "r", encoding="utf-8") as file:
            content = file.read()
        logging.debug(f"Read file {file_path}.")
        return content
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return str(e)

def write_to_file(file_path: str, content: str, overwrite=True):
    """Writes or appends content to a file."""
    absolute_path = os.path.join(BASE_DIR, file_path)
    if not is_within_base_dir(absolute_path):
        return "Access Denied: File outside allowed environment."
    mode = "w" if overwrite else "a"
    try:
        with open(absolute_path, mode, encoding="utf-8") as file:
            file.write(content)
        action = "overwritten" if overwrite else "appended"
        logging.debug(f"File '{file_path}' {action} successfully.")
        return f"File '{file_path}' {action} successfully."
    except Exception as e:
        logging.error(f"Error writing to file {file_path}: {e}")
        return str(e)

def move_file(src: str, dest: str):
    """Moves a file from source to destination."""
    src_path = os.path.join(BASE_DIR, src)
    dest_path = os.path.join(BASE_DIR, dest)
    if not is_within_base_dir(src_path) or not is_within_base_dir(dest_path):
        return "Access Denied: Operation outside the allowed environment."
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(src_path, dest_path)
        logging.debug(f"Moved file from {src} to {dest}.")
        return f"File moved from {src} to {dest}."
    except Exception as e:
        logging.error(f"Error moving file from {src} to {dest}: {e}")
        return str(e)

def delete_file(file_path: str):
    """Deletes a specified file."""
    absolute_path = os.path.join(BASE_DIR, file_path)
    if not is_within_base_dir(absolute_path):
        return "Access Denied: File outside allowed environment."
    try:
        os.remove(absolute_path)
        logging.debug(f"Deleted file {file_path}.")
        return f"File '{file_path}' deleted successfully."
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {e}")
        return str(e)

# Automation and analysis
def auto_fix_python_code(file_path: str):
    """Auto-fixes Python code formatting using autopep8."""
    absolute_path = os.path.join(BASE_DIR, file_path)
    if not is_within_base_dir(absolute_path):
        return "Access Denied: File outside allowed environment."
    try:
        subprocess.run(["autopep8", "--in-place", absolute_path], check=True)
        logging.debug(f"Auto-fixed Python file {file_path}.")
        return f"Auto-fixed {file_path} successfully."
    except Exception as e:
        logging.error(f"Auto-fix failed for {file_path}: {e}")
        return str(e)

def analyze_and_fix_app_files():
    """Analyzes and fixes Python and database files in the base directory."""
    results = []
    for root, _, files in os.walk(BASE_DIR):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.endswith(".py"):
                logging.info(f"Analyzing Python file: {file_name}")
                try:
                    subprocess.run(["python", "-m", "py_compile", file_path], check=True)
                    results.append(f"No syntax errors in {file_name}.")
                except subprocess.CalledProcessError as e:
                    results.append(f"Syntax error in {file_name}: {e}")
                    results.append(auto_fix_python_code(file_path))
            elif file_name.endswith(".db"):
                logging.info(f"Checking database integrity: {file_name}")
                try:
                    conn = sqlite3.connect(file_path)
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check;")
                    if cursor.fetchone()[0] == "ok":
                        results.append(f"Database {file_name} passed integrity check.")
                    else:
                        results.append(f"Integrity issues in {file_name}.")
                    conn.close()
                except sqlite3.DatabaseError as e:
                    results.append(f"Database error in {file_name}: {e}")
    return results

# Initialization script (optional)
if __name__ == "__main__":
    print("File Manager loaded. Available functions:")
    print(" - list_files_in_directory(directory)")
    print(" - read_file(file_path)")
    print(" - write_to_file(file_path, content, overwrite=True)")
    print(" - move_file(src, dest)")
    print(" - delete_file(file_path)")
    print(" - auto_fix_python_code(file_path)")
    print(" - analyze_and_fix_app_files()")