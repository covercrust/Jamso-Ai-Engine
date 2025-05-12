#!/usr/bin/env python3
"""
Script to check the structure of the users table
"""
import os
import sys
import sqlite3

# Setup base path
BASE_PATH = '/home/jamso-ai-server/Jamso-Ai-Engine'
sys.path.append(BASE_PATH)

# Database path
DB_PATH = os.path.join(BASE_PATH, 'src', 'Database', 'Users', 'users.db')

def check_table_structure():
    """Check the structure of the users table"""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Users Table Structure:")
        print("======================")
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}, Not Null: {col[3]}, Default: {col[4]}, Primary Key: {col[5]}")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_table_structure()
