from pathlib import Path
"""
File Manager Utility Module
"""

import os
import shutil
import subprocess
import logging
import sqlite3

# Source environment variables from env.sh
def source_env_file(env_file):
    """
    Sources environment variables from a file.
    """
    command = f"source {env_file} && env"
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
    if proc.stdout:
        for line in proc.stdout:
            line = line.decode('utf-8')
            key, _, value = line.partition("=")
            os.environ[key] = value.strip()
    proc.communicate()
    logging.debug(f"Environment variables sourced from {env_file}")

# Source the env.sh file
source_env_file(os.path.join(os.path.dirname(__file__), 'env.sh'))

# Constants
BASE_DIR = os.getenv('BASE_DIR', Path(__file__).resolve().parent)
ACCESS_DENIED_DIR = "Access Denied: Directory is outside the allowed environment."
ACCESS_DENIED_FILE = "Access Denied: File is outside the allowed environment."
TEST_FILE = "test.txt"

# Set up logging
logging.basicConfig(filename=os.path.join(BASE_DIR, "file_manager.log"),
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Superuser permissions check
def ensure_superuser_privileges():
    """
    Ensures the script is running with superuser permissions.
    """
    if os.geteuid() != 0:
        raise PermissionError("Superuser privileges are required to run this script.")

# Ensure base directory boundary
def is_within_base_dir(path):
    """
    Ensures that any path provided stays within the allowed base directory.
    """
    return os.path.commonpath([BASE_DIR, path]) == BASE_DIR

def list_files_in_directory(directory="."):
    """
    Lists all files in the specified directory.
    """
    directory_path = os.path.join(BASE_DIR, directory)
    if not is_within_base_dir(directory_path):
        return ACCESS_DENIED_DIR
    try:
        files = os.listdir(directory_path)
        logging.debug("Listed files in %s: %s", directory, files)
        return files
    except OSError as e:
        logging.error("Error listing files in directory %s: %s", directory, e)
        return f"Error: {e}"

def read_file(file_path):
    """
    Reads and returns the content of a file.
    """
    absolute_path = os.path.join(BASE_DIR, file_path)
    if not is_within_base_dir(absolute_path):
        return ACCESS_DENIED_FILE
    try:
        with open(absolute_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        logging.warning("File '%s' not found.", file_path)
        return f"Error: File '{file_path}' not found."
    except OSError as e:
        logging.error("Error reading file %s: %s", file_path, e)
        return f"Error: {e}"

def write_to_file(file_path, content, overwrite=True):
    """
    Writes or appends content to a specified file.
    """
    absolute_path = os.path.join(BASE_DIR, file_path)
    if not is_within_base_dir(absolute_path):
        return ACCESS_DENIED_FILE
    mode = "w" if overwrite else "a"
    try:
        with open(absolute_path, mode, encoding="utf-8") as file:
            file.write(content)
            action = "overwritten" if overwrite else "appended"
            logging.debug("File '%s' %s successfully.", file_path, action)
            return f"File '{file_path}' {action} successfully."
    except FileNotFoundError:
        logging.warning("File '%s' not found.", file_path)
        return f"Error: File '{file_path}' not found."
    except OSError as e:
        logging.error("Error writing to file %s: %s", file_path, e)
        return f"Error: {e}"

def move_file(src, dest):
    """
    Moves a file from source to destination.
    """
    src_path = os.path.join(BASE_DIR, src)
    dest_path = os.path.join(BASE_DIR, dest)
    if not is_within_base_dir(src_path) or not is_within_base_dir(dest_path):
        return "Access Denied: Operation outside the allowed environment."
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(src_path, dest_path)
        logging.debug("Moved file from %s to %s", src, dest)
        return f"File moved from '{src}' to '{dest}' successfully."
    except OSError as e:
        logging.error("Error moving file from %s to %s: %s", src, dest, e)
        return f"Error: {e}"

def delete_file(file_path):
    """
    Deletes a specified file.
    """
    absolute_path = os.path.join(BASE_DIR, file_path)
    if not is_within_base_dir(absolute_path):
        return ACCESS_DENIED_FILE
    try:
        os.remove(absolute_path)
        logging.debug("Deleted file %s", file_path)
        return f"File '{file_path}' deleted successfully."
    except FileNotFoundError:
        logging.warning("File '%s' not found.", file_path)
        return f"Error: File '{file_path}' not found."
    except OSError as e:
        logging.error("Error deleting file %s: %s", file_path, e)
        return f"Error: {e}"

def auto_fix_python_code(file_path):
    """
    Attempts to auto-fix Python code formatting using autopep8.
    """
    try:
        subprocess.run(["autopep8", "--in-place", file_path], check=True)
        return f"Auto-fix applied to {file_path}."
    except subprocess.CalledProcessError as e:
        return f"Auto-fix failed for {file_path}: {e}"

def attempt_db_fix(db_path):
    """
    Attempts to fix common database issues in SQLite databases.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("VACUUM;")  # Rebuilds the database
        conn.commit()
        conn.close()
        return f"Database fix applied to {db_path}."
    except sqlite3.DatabaseError as e:
        return f"Database fix failed for {db_path}: {e}"

def analyze_and_fix_app_files():
    """
    Scans the base directory for Python and database files, analyzes them, runs syntax checks,
    and attempts to auto-fix any issues found.
    """
    results = []

    def analyze_python_files():
        for root, _, files in os.walk(BASE_DIR):
            for file_name in files:
                if file_name.endswith(".py"):
                    file_path = os.path.join(root, file_name)
                    results.append(f"Analyzing Python file: {file_path}")

                    try:
                        subprocess.run(["python3.13", "-m", "py_compile", file_path], check=True)
                        results.append(f"No syntax errors in {file_name}.")
                    except subprocess.CalledProcessError as e:
                        results.append(f"Syntax error in {file_name}: {e}")
                        results.append(auto_fix_python_code(file_path))

    def analyze_database_files():
        for root, _, files in os.walk(BASE_DIR):
            for file_name in files:
                if file_name.endswith(".db"):
                    db_path = os.path.join(root, file_name)
                    results.append(f"Analyzing database file: {db_path}")

                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA integrity_check;")
                        if cursor.fetchone()[0] == "ok":
                            results.append(f"Database {file_name} passed integrity check.")
                        else:
                            results.append(f"Integrity issue in {file_name}")
                            results.append(attempt_db_fix(db_path))
                        conn.close()
                    except sqlite3.DatabaseError as e:
                        results.append(f"Database error in {file_name}: {e}")
                        results.append(attempt_db_fix(db_path))

    analyze_python_files()
    analyze_database_files()
    return results

def list_capabilities():
    """
    Lists all the available functions in this module.
    """
    functions = {
        "list_files_in_directory": "Lists all files in the specified directory.",
        "read_file": "Reads and returns the content of a file.",
        "write_to_file": "Writes or appends content to a specified file.",
        "move_file": "Moves a file from source to destination.",
        "delete_file": "Deletes a specified file.",
        "analyze_and_fix_app_files": "Automatically analyzes and fixes Python and database files in the directory."
    }
    for func, desc in functions.items():
        print(f"{func}: {desc}")

# Main function
if __name__ == "__main__":
    list_capabilities()
    try:
        ensure_superuser_privileges()
        print(list_files_in_directory())
        print(analyze_and_fix_app_files())
    except PermissionError as e:
        print(e)
        logging.error(e)