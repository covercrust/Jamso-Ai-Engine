#!/bin/bash
# Monitor script for SSH tunnel
# Checks if the tunnel is active and restarts it if necessary
# Add to crontab to run every 5 minutes

# Load environment variables
source ~/.bash_profile 2>/dev/null

LOG_FILE="$HOME/tunnel_logs/monitor.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Domain being tunneled
DOMAIN="trading.colopio.com"
CPANEL_HOST="162.0.215.185"
CPANEL_SSH_PORT=21098

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if tunnel is active
check_tunnel() {
    # Look for SSH processes with the tunnel flags
    if pgrep -f "ssh -N -R 5000:localhost:5000.*$CPANEL_HOST" > /dev/null; then
        TUNNEL_PID=$(pgrep -f "ssh -N -R 5000:localhost:5000.*$CPANEL_HOST")
        log "Tunnel is active with PID $TUNNEL_PID"
        
        # Check how long the tunnel has been running
        if [ -d "/proc/$TUNNEL_PID" ]; then
            UPTIME=$(ps -o etimes= -p "$TUNNEL_PID")
            log "Tunnel has been running for $UPTIME seconds"
        fi
        
        # Check if the tunnel is actually working by attempting to connect through it
        if nc -z localhost 5000 >/dev/null 2>&1; then
            log "Local service on port 5000 is responding"
            
            # Try to check if the remote end of the tunnel is working
            # This requires an SSH command to the cPanel server
            if command -v expect >/dev/null 2>&1; then
                # Use expect to avoid password prompts
                REMOTE_CHECK=$(expect -c "
                spawn ssh -p $CPANEL_SSH_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null colopio@$CPANEL_HOST \"nc -z localhost 5000\"
                expect {
                    \"password:\" { exit 1 }
                    eof { exit 0 }
                    timeout { exit 2 }
                }
                " 2>/dev/null)
                
                if [ $? -eq 0 ]; then
                    log "Remote port 5000 is accessible through tunnel"
                    return 0
                else
                    log "Remote port check failed, tunnel may be broken"
                    return 1
                fi
            else
                # If expect is not available, assume tunnel is working if local process exists
                log "Cannot verify remote end of tunnel (expect not installed)"
                return 0
            fi
        else
            log "Local service on port 5000 is not responding"
            return 1
        fi
    else
        log "Tunnel is not active"
        return 1
    fi
}

# Start or restart the tunnel
start_tunnel() {
    log "Starting SSH tunnel for $DOMAIN..."
    
    # Kill any existing tunnel processes
    pkill -f "ssh -N -R 5000:localhost:5000" >/dev/null 2>&1
    
    # Start the tunnel using the script
    "$HOME/Jamso-Ai-Engine/Tools/start_ssh_tunnel.sh" &
    
    sleep 5
    
    # Check if it started successfully
    if check_tunnel; then
        log "Tunnel started successfully"
        return 0
    else
        log "Failed to start tunnel"
        return 1
    fi
}

# Check if the website is accessible via DNS
check_website() {
    if command -v curl >/dev/null 2>&1; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/ 2>/dev/null)
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
            log "Website $DOMAIN is accessible (HTTP $HTTP_CODE)"
            return 0
        else
            log "Website $DOMAIN returned HTTP code $HTTP_CODE"
            return 1
        fi
    else
        log "Cannot check website (curl not installed)"
        # Assume it's working if we can't check
        return 0
    fi
}

# Main execution
log "Starting tunnel monitor check for $DOMAIN"

# First check if our local service is running
if ! nc -z localhost 5000 >/dev/null 2>&1; then
    log "WARNING: Local service on port 5000 is not running. Tunnel will not work until the service is started."
fi

# Check and restart tunnel if needed
if ! check_tunnel; then
    log "Tunnel needs to be restarted"
    start_tunnel
    
    # Verify website accessibility after restart
    sleep 10
    check_website
fi

log "Monitor check complete"
