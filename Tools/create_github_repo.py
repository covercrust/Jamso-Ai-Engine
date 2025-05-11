#!/usr/bin/env python3
"""
Script to create a GitHub repository for the Jamso AI Engine project.
"""
import os
import requests
import subprocess
import getpass
import json

def create_github_repo(token, repo_name, description="Jamso AI Engine trading platform", private=True):
    """Create a new GitHub repository."""
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": False
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"Repository {repo_name} created successfully!")
        return response.json()["html_url"]
    else:
        print(f"Failed to create repository. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def push_to_github(repo_url):
    """Push the local repository to GitHub."""
    # Verify if the repository already has a remote origin
    check_remote = subprocess.run(
        ["git", "remote", "-v"], 
        capture_output=True, 
        text=True
    )
    
    if "origin" in check_remote.stdout:
        # Remove the existing origin
        subprocess.run(["git", "remote", "remove", "origin"])
    
    # Add the new remote origin
    add_remote = subprocess.run(
        ["git", "remote", "add", "origin", repo_url],
        capture_output=True,
        text=True
    )
    
    if add_remote.returncode != 0:
        print(f"Error adding remote: {add_remote.stderr}")
        return False
    
    # Push to GitHub
    push = subprocess.run(
        ["git", "push", "-u", "origin", "master"],
        capture_output=True,
        text=True
    )
    
    if push.returncode != 0:
        print(f"Error pushing to GitHub: {push.stderr}")
        return False
    
    print("Successfully pushed to GitHub!")
    return True

def main():
    print("=== GitHub Repository Setup ===")
    print("This script will create a GitHub repository for your project.")
    print("You will need a GitHub personal access token with 'repo' scope.")
    print("Get one at: https://github.com/settings/tokens\n")
    
    token = getpass.getpass("Enter your GitHub personal access token: ")
    repo_name = input("Enter repository name [Jamso-Ai-Engine]: ") or "Jamso-Ai-Engine"
    description = input("Enter repository description [Jamso AI Engine trading platform]: ") or "Jamso AI Engine trading platform"
    private_input = input("Make repository private? (y/n) [y]: ").lower() or "y"
    private = private_input.startswith("y")
    
    repo_url = create_github_repo(token, repo_name, description, private)
    
    if repo_url:
        print(f"Repository created at: {repo_url}")
        
        push_confirm = input("Push local repository to GitHub now? (y/n) [y]: ").lower() or "y"
        if push_confirm.startswith("y"):
            push_to_github(repo_url)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
