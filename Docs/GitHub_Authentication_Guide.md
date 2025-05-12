# GitHub Authentication Guide

This guide explains how to authenticate with GitHub to push your code to a repository.

## Setting Up GitHub Authentication

GitHub no longer accepts regular passwords for Git operations. Instead, you need to use:

1. A Personal Access Token (for HTTPS)
2. SSH keys (for SSH)

## Option 1: Using a Personal Access Token (PAT)

### 1. Create a Personal Access Token on GitHub

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token" (classic)
3. Give your token a name (e.g., "Jamso AI Engine")
4. Set an expiration date
5. Select scopes: at minimum, you need "repo" for full control of repositories
6. Click "Generate token"
7. **IMPORTANT**: Copy your token immediately. You won't be able to see it again!

### 2. Use the Token for Git Operations

When pushing to GitHub, you'll be prompted for username and password:

- For username: Enter your GitHub username
- For password: Enter your Personal Access Token (not your GitHub password)

### 3. Store Your Credentials (Optional)

To avoid entering your credentials each time:

```bash
# Store credentials in Git's credential helper (less secure)
git config --global credential.helper store

# Or store them temporarily (more secure)
git config --global credential.helper 'cache --timeout=3600'
```

## Option 2: Using SSH Keys (Recommended)

### 1. Check for Existing SSH Keys

```bash
ls -al ~/.ssh
```

Look for files named `id_rsa` and `id_rsa.pub` or similar.

### 2. Generate a New SSH Key (if needed)

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Press Enter to accept the default file location and enter a passphrase if desired.

### 3. Add the SSH Key to the SSH Agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 4. Add the SSH Key to GitHub

1. Copy your public key to clipboard:

   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. Go to [GitHub Settings > SSH and GPG keys](https://github.com/settings/keys)
3. Click "New SSH key"
4. Add a title (e.g., "Work Laptop")
5. Paste your key
6. Click "Add SSH key"

### 5. Update Your Remote URL to Use SSH

```bash
# Check current remote
git remote -v

# Change from HTTPS to SSH
git remote set-url origin git@github.com:covercrust/Jamso-Ai-Engine.git
```

### 6. Test Your SSH Connection

```bash
ssh -T git@github.com
```

You should see a message like: "Hi username! You've successfully authenticated..."

## Troubleshooting

### "Remote repository not found" Error

This usually means:

1. The repository doesn't exist on GitHub yet
2. You're using the wrong username in the URL
3. You don't have access to the repository

### Authentication Failed

1. For HTTPS: Make sure you're using your Personal Access Token, not your password
2. For SSH: Make sure your SSH key is added to GitHub and your SSH agent

### Other Issues

For other issues, see the [GitHub documentation](https://docs.github.com/en/authentication).
