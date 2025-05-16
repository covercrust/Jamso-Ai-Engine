# SSH Tunnel and Reverse Proxy Setup for trading.colopio.com

This guide explains how to set up a secure SSH tunnel and reverse proxy between your cPanel shared hosting server and your backend server.

## Architecture Overview

```
Internet -> trading.colopio.com -> cPanel Server (Reverse Proxy) -> SSH Tunnel -> Backend Server (jamso-ai-server)
```

## Setup Instructions

### 1. On Backend Server (jamso-ai-server)

#### Prerequisites
- SSH key pair generated
- Python 3.x installed

#### Steps

1. Make sure the scripts are executable:
   ```bash
   chmod +x /home/jamso-ai-server/Jamso-Ai-Engine/Tools/start_ssh_tunnel.sh
   chmod +x /home/jamso-ai-server/Jamso-Ai-Engine/Tools/deploy_cpanel_proxy.sh
   chmod +x /home/jamso-ai-server/Jamso-Ai-Engine/Tools/monitor_ssh_tunnel.sh
   ```

2. Upload your SSH public key to the cPanel server to enable passwordless authentication:
   ```bash
   ssh-copy-id -i ~/.ssh/id_rsa.pub -p 21098 colopio@162.0.215.185
   ```

3. Deploy the reverse proxy files to the cPanel server:
   ```bash
   /home/jamso-ai-server/Jamso-Ai-Engine/Tools/deploy_cpanel_proxy.sh
   ```

4. Start the SSH tunnel:
   ```bash
   /home/jamso-ai-server/Jamso-Ai-Engine/Tools/start_ssh_tunnel.sh
   ```

5. Set up automatic monitoring by adding the provided crontab entries:
   ```bash
   crontab -e
   # Then add the contents of /home/jamso-ai-server/tunnel_crontab.txt
   ```

6. Install the systemd service file (requires sudo access):
   ```bash
   sudo cp /home/jamso-ai-server/ssh-tunnel.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable ssh-tunnel
   sudo systemctl start ssh-tunnel
   ```

### 2. On cPanel Server (colopio@162.0.215.185)

1. Log in to the cPanel server:
   ```bash
   ssh -p 21098 colopio@162.0.215.185
   ```

2. Make sure the deployed files are in place:
   ```bash
   ls -la ~/trading.colopio.com/
   ```

3. Start the reverse proxy:
   ```bash
   cd ~/trading.colopio.com
   ./start_proxy.sh
   ```

4. Configure the domain in cPanel to use the Python application.
   - Log in to cPanel
   - Find the "Setup Python App" section
   - Configure the app for trading.colopio.com
   - Set the application root to /home/colopio/trading.colopio.com
   - Ensure Python 3.x is selected as the Python version

## Troubleshooting

### Check if the SSH tunnel is running
```bash
ps aux | grep "ssh -N -R"
```

### Check if the reverse proxy is running
```bash
# On cPanel server
ps aux | grep "python.*reverse_proxy"
```

### View logs
```bash
# On backend server
cat ~/tunnel_logs/tunnel.log

# On cPanel server
cat ~/trading.colopio.com/logs/proxy.log
cat ~/trading.colopio.com/logs/passenger_wsgi.log
```

### Restart the SSH tunnel
```bash
# On backend server
pkill -f "ssh -N -R"
/home/jamso-ai-server/Jamso-Ai-Engine/Tools/start_ssh_tunnel.sh
```

### Restart the reverse proxy
```bash
# On cPanel server
pkill -f "python.*reverse_proxy"
cd ~/trading.colopio.com
./start_proxy.sh
```

## Security Considerations

1. The SSH tunnel only forwards traffic for trading.colopio.com
2. Domain validation ensures only trading.colopio.com requests are processed
3. SSH key authentication provides secure access without passwords
4. Regular monitoring ensures the tunnel remains operational
