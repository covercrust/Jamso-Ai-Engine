#!/usr/bin/env python3
"""
Script to check GitHub repository settings and print instructions.
"""
import subprocess
import sys

def get_remote_settings():
    """Get the current Git remote settings."""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "Error: Unable to get remote settings."
    except Exception as e:
        return f"Error: {e}"

def print_instructions(current_settings):
    """Print instructions for GitHub setup."""
    print("\n===== GITHUB REPOSITORY SETUP =====")
    
    if current_settings:
        print("Current remote settings:")
        print(current_settings)
        print("\nIf these settings are incorrect, remove them with:")
        print("$ git remote remove origin")
    else:
        print("No remote repository configured.")
    
    print("\nTo set up a new GitHub repository:")
    print("1. Create a repository on GitHub: https://github.com/new")
    print("2. Enter 'Jamso-Ai-Engine' as the repository name")
    print("3. Set visibility (public/private) as desired")
    print("4. Click 'Create repository'")
    
    print("\nAfter creating the repository, connect your local repository:")
    print("$ git remote add origin https://github.com/YOUR_USERNAME/Jamso-Ai-Engine.git")
    print("$ git push -u origin master")
    
    print("\nReplace YOUR_USERNAME with your actual GitHub username.")
    
    print("\nTo use SSH instead of HTTPS (recommended if you have SSH keys set up):")
    print("$ git remote add origin git@github.com:YOUR_USERNAME/Jamso-Ai-Engine.git")
    
    print("\nIf you get 'Repository not found' errors, make sure:")
    print("1. The repository exists on GitHub")
    print("2. You're using the correct username in the URL")
    print("3. You have appropriate access permissions")
    print("4. You've authenticated with GitHub")

def main():
    print("Checking Git repository settings...")
    
    current_settings = get_remote_settings()
    print_instructions(current_settings)
    
    print("\nFor more automated setup, you can use our tool:")
    print("$ python Tools/create_github_repo.py")

if __name__ == "__main__":
    main()
