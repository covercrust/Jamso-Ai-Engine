# Fixing trading.colopio.com Reverse Proxy Issues

This guide addresses the common issues with the trading.colopio.com reverse proxy setup, including 301 redirects and SSH authentication problems.

## Issue 1: SSH Password Prompts

The SSH key authentication is not set up correctly, which is why you're being prompted for a password when trying to check logs.

### Solution:

1. Run the SSH key setup script:
   ```bash
   /home/jamso-ai-server/Jamso-Ai-Engine/Tools/setup_ssh_key.sh
   ```

2. This script will:
   - Generate an SSH key if one doesn't exist
   - Copy the key to the cPanel server (you'll need to enter the password once)
   - Set proper permissions
   - Test the connection

3. After running this script, you should be able to connect without a password:
   ```bash
   ssh -p 21098 colopio@162.0.215.185 "echo Connection successful"
   ```

## Issue 2: 301 Moved Permanently Errors

The 301 redirect you're seeing is likely caused by one of these issues:

1. cPanel is forcing HTTPS redirects
2. The domain might be redirecting to a www subdomain
3. The reverse proxy isn't handling redirects properly

### Solution:

1. Redeploy the updated proxy:
   ```bash
   /home/jamso-ai-server/Jamso-Ai-Engine/Tools/deploy_cpanel_proxy.sh
   ```

2. SSH into the cPanel server (should now work without password):
   ```bash
   ssh -p 21098 colopio@162.0.215.185
   ```

3. Restart the proxy with the new settings:
   ```bash
   cd ~/trading.colopio.com
   ./start_proxy.sh
   ```

4. Test the status endpoint:
   ```bash
   curl -L http://trading.colopio.com/status
   ```
   Note the `-L` flag which follows redirects.

5. If you still see the 301 redirect, check the logs:
   ```bash
   ssh -p 21098 colopio@162.0.215.185 "cat ~/logs/proxy.log"
   ```

## Issue 3: Ensuring the SSH Tunnel is Active

For the reverse proxy to work, the SSH tunnel must be active.

### Solution:

1. On the jamso-ai-server, restart the SSH tunnel:
   ```bash
   pkill -f "ssh -N -R" # Kill any existing tunnels
   /home/jamso-ai-server/Jamso-Ai-Engine/Tools/start_ssh_tunnel.sh
   ```

2. Check if the tunnel is active:
   ```bash
   ps aux | grep "ssh -N -R"
   ```

3. Verify the tunnel is allowing connections:
   ```bash
   ssh -p 21098 colopio@162.0.215.185 "nc -zv localhost 5000"
   ```

## Testing the Complete Setup

After applying all fixes, run this comprehensive test:

1. Check if the tunnel is running:
   ```bash
   ps aux | grep "ssh -N -R"
   ```

2. Check if the proxy is running on cPanel:
   ```bash
   ssh -p 21098 colopio@162.0.215.185 "ps aux | grep python | grep reverse_proxy"
   ```

3. Test the status endpoint:
   ```bash
   curl -L http://trading.colopio.com/status
   ```

4. Check the logs for any errors:
   ```bash
   ssh -p 21098 colopio@162.0.215.185 "tail -30 ~/logs/proxy.log"
   ```

## Additional Troubleshooting

### cPanel Redirects

If you're still having issues with redirects, you may need to check cPanel's redirection settings:

1. Login to cPanel
2. Search for "Redirects" in the search bar
3. Check if there are any redirects configured for trading.colopio.com
4. If there are, either modify or remove them as needed

### SSL/HTTPS Configuration

If the issue is related to SSL certificates:

1. Login to cPanel
2. Go to "SSL/TLS Status"
3. Ensure trading.colopio.com has a valid certificate
4. If not, you can use "Let's Encrypt" to issue a free certificate

## Configuring Passenger for Python Apps

If the passenger_wsgi.py isn't being recognized properly:

1. Login to cPanel
2. Go to "Setup Python App"
3. Ensure the following settings:
   - Python Version: 3.8 or higher
   - Application Root: /home/colopio/trading.colopio.com
   - Application URL: trading.colopio.com
   - Application Entry Point: passenger_wsgi.application
   - Restart the application if needed
