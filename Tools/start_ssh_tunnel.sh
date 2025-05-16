#!/bin/bash
# SSH tunnel script for trading.colopio.com
# Establishes a reverse SSH tunnel from backend server to cPanel
# This script should be run on the jamso-ai-server

# Configuration
CPANEL_USER="colopio"
CPANEL_HOST="162.0.215.185"
CPANEL_SSH_PORT=21098
REMOTE_PORT=5000  # The port on cPanel that will forward to our local service
LOCAL_PORT=5000   # The port on this server (jamso-ai-server) where our service runs
IDENTITY_FILE="$HOME/.ssh/id_rsa"  # SSH private key path
KEEP_ALIVE=60     # SSH KeepAlive interval
DOMAIN="trading.colopio.com"  # The domain this tunnel serves

# Create a log directory
LOG_DIR="$HOME/Jamso-Ai-Engine/Logs"
mkdir -p "$LOG_DIR"

# Log start
echo "$(date): Starting SSH tunnel for $DOMAIN to $CPANEL_USER@$CPANEL_HOST:$CPANEL_SSH_PORT" | tee -a "$LOG_DIR/tunnel.log"

# Check if port 5000 is already in use locally
if ss -tln | grep -q ":$LOCAL_PORT "; then
  echo "$(date): Local port $LOCAL_PORT is available for the service" | tee -a "$LOG_DIR/tunnel.log"
else
  echo "$(date): WARNING: Local port $LOCAL_PORT does not appear to be in use. Make sure your service is running." | tee -a "$LOG_DIR/tunnel.log"
fi

# Check if the identity file exists
if [ ! -f "$IDENTITY_FILE" ]; then
  echo "$(date): ERROR: SSH identity file $IDENTITY_FILE does not exist" | tee -a "$LOG_DIR/tunnel.log"
  exit 1
fi

# Test SSH connection first
echo "$(date): Testing SSH connection to $CPANEL_HOST..." | tee -a "$LOG_DIR/tunnel.log"
if ! ssh -i "$IDENTITY_FILE" -p $CPANEL_SSH_PORT -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no $CPANEL_USER@$CPANEL_HOST "echo Connection successful" > /dev/null 2>&1; then
  echo "$(date): ERROR: Cannot connect to cPanel server. Check SSH credentials and connectivity." | tee -a "$LOG_DIR/tunnel.log"
  exit 1
fi
echo "$(date): SSH connection test successful" | tee -a "$LOG_DIR/tunnel.log"

# SSH options explained:
# -N: Do not execute a command (tunnel only)
# -R: Sets up the remote port forwarding
# -i: Identity file (private key)
# -o ServerAliveInterval: Sends keep-alive packets to prevent disconnection
# -o ServerAliveCountMax: Number of alive messages without response before terminating
# -o ExitOnForwardFailure: Exit if port forwarding fails
# -o StrictHostKeyChecking=no: Don't prompt about unknown hosts
# -o UserKnownHostsFile=/dev/null: Don't update known_hosts file

echo "$(date): Establishing SSH tunnel..." | tee -a "$LOG_DIR/tunnel.log"

# Run the SSH tunnel in foreground (important for systemd)
exec ssh -N -R $REMOTE_PORT:localhost:$LOCAL_PORT \
    -i "$IDENTITY_FILE" \
    -p $CPANEL_SSH_PORT \
    -o ServerAliveInterval=$KEEP_ALIVE \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    $CPANEL_USER@$CPANEL_HOST 2>&1 | tee -a "$LOG_DIR/tunnel.log"
