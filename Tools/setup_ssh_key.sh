#!/bin/bash
# Fix SSH key authentication for cPanel server
# This script sets up passwordless SSH access to the cPanel server

# Configuration
CPANEL_USER="colopio"
CPANEL_HOST="162.0.215.185"
CPANEL_SSH_PORT=21098
SSH_KEY="$HOME/.ssh/id_rsa"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up SSH key authentication for $CPANEL_USER@$CPANEL_HOST${NC}"

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${YELLOW}SSH key not found. Generating a new key...${NC}"
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY" -N ""
    echo -e "${GREEN}SSH key generated at $SSH_KEY${NC}"
fi

# Ensure proper permissions
chmod 700 ~/.ssh
chmod 600 "$SSH_KEY"
chmod 644 "$SSH_KEY.pub"

# Copy the key to the server
echo -e "${YELLOW}You will be prompted for the password one last time to copy your SSH key.${NC}"
echo -e "${YELLOW}After this, you should be able to connect without a password.${NC}"
echo

# Use ssh-copy-id if available
if command -v ssh-copy-id &> /dev/null; then
    ssh-copy-id -i "$SSH_KEY.pub" -p $CPANEL_SSH_PORT $CPANEL_USER@$CPANEL_HOST
else
    # Manual approach if ssh-copy-id is not available
    echo -e "${YELLOW}ssh-copy-id not found, using manual approach...${NC}"
    
    # Create a temporary script
    TMP_SCRIPT=$(mktemp)
    cat > "$TMP_SCRIPT" << EOF
#!/bin/bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo "$(cat $SSH_KEY.pub)" >> ~/.ssh/authorized_keys
EOF
    
    # Copy and execute the script on the remote server
    cat "$TMP_SCRIPT" | ssh -p $CPANEL_SSH_PORT $CPANEL_USER@$CPANEL_HOST 'bash -s'
    rm "$TMP_SCRIPT"
fi

# Test the connection
echo -e "${GREEN}Testing SSH connection...${NC}"
if ssh -i "$SSH_KEY" -p $CPANEL_SSH_PORT -o BatchMode=yes -o ConnectTimeout=5 $CPANEL_USER@$CPANEL_HOST echo "Connection successful"; then
    echo -e "${GREEN}SSH key authentication is working! You can now connect without a password.${NC}"
else
    echo -e "${RED}SSH key authentication failed. Please check the server configuration.${NC}"
    echo -e "${YELLOW}Some hosting providers restrict SSH key authentication or have specific requirements.${NC}"
    echo -e "${YELLOW}You may need to contact your hosting provider for assistance.${NC}"
fi
