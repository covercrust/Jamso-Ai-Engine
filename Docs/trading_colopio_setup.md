# Setting Up trading.colopio.com with SSH Tunnel

This guide provides step-by-step instructions for setting up a secure connection between trading.colopio.com on cPanel and the jamso-ai-server backend.

## Prerequisites

- SSH access to both servers
- Python 3.6+ installed on both servers
- Permission to create SSH keys and configure cPanel

## Step 1: Confirm Domain and Server Information

The domain `trading.colopio.com` resolves to `162.0.215.185`, which is the IP of the cPanel server.

```
$ nslookup trading.colopio.com
Server:		8.8.8.8
Address:	8.8.8.8#53

Non-authoritative answer:
Name:	trading.colopio.com
Address: 162.0.215.185
```

cPanel server details:
- Server IP: 162.0.215.185
- Username: colopio
- SSH port: 21098

Backend server details:
- Server: jamso-ai-server
- IP: 192.168.10.175 (internal IP)
- Service port: 5000

## Step 2: Set Up SSH Keys

On the jamso-ai-server, generate SSH keys if they don't already exist:

```bash
# Check if keys exist
ls -la ~/.ssh/id_rsa*

# If not, generate them
ssh-keygen -t rsa -b 4096
```

Copy the SSH key to the cPanel server:

```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub -p 21098 colopio@162.0.215.185
```

If the command above doesn't work, you can manually copy the key:

```bash
# Display your public key
cat ~/.ssh/id_rsa.pub

# Then copy it and add to ~/.ssh/authorized_keys on the cPanel server
ssh -p 21098 colopio@162.0.215.185
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Step 3: Deploy the Reverse Proxy to cPanel

Run the deployment script from the jamso-ai-server:

```bash
chmod +x /home/jamso-ai-server/Jamso-Ai-Engine/Tools/deploy_cpanel_proxy.sh
/home/jamso-ai-server/Jamso-Ai-Engine/Tools/deploy_cpanel_proxy.sh
```

This will copy all necessary files to the cPanel server.

## Step 4: Set Up the Python App in cPanel

1. Log in to cPanel
2. Find "Setup Python App" in the Software section
3. Create a new application with these settings:
   - Python version: 3.8 or higher
   - Application root: /home/colopio/trading.colopio.com
   - Application URL: trading.colopio.com
   - Application startup file: passenger_wsgi.py
   - Application Entry point: application
   - Passenger app mode: enabled

## Step 5: Start the SSH Tunnel

From the jamso-ai-server, start the SSH tunnel:

```bash
chmod +x /home/jamso-ai-server/Jamso-Ai-Engine/Tools/start_ssh_tunnel.sh
/home/jamso-ai-server/Jamso-Ai-Engine/Tools/start_ssh_tunnel.sh
```

## Step 6: Set Up Automatic Monitoring

Add the monitoring script to crontab on the jamso-ai-server:

```bash
crontab -e
```

Add these lines:

```
# Check and restart SSH tunnel every 5 minutes if needed
*/5 * * * * /home/jamso-ai-server/Jamso-Ai-Engine/Tools/monitor_ssh_tunnel.sh

# Clean up old log files weekly
0 0 * * 0 find /home/jamso-ai-server/tunnel_logs -name "*.log" -type f -mtime +7 -delete
```

## Step 7: Install as a Systemd Service (Optional)

For automatic startup and management, install the systemd service:

```bash
sudo cp /home/jamso-ai-server/ssh-tunnel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ssh-tunnel
sudo systemctl start ssh-tunnel
```

## Step 8: Verify the Setup

1. Check if the tunnel is running:
   ```bash
   ps aux | grep "ssh -N -R"
   ```

2. Test the connection from the cPanel server:
   ```bash
   ssh -p 21098 colopio@162.0.215.185
   nc -zv localhost 5000
   ```

3. Check the proxy status:
   ```bash
   curl http://trading.colopio.com/status
   ```

4. Verify the website is accessible:
   ```bash
   curl http://trading.colopio.com/
   ```

## Troubleshooting

### Tunnel Connection Issues

If the tunnel doesn't establish:

1. Check SSH key permissions:
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/id_rsa
   chmod 644 ~/.ssh/id_rsa.pub
   ```

2. Verify SSH connectivity:
   ```bash
   ssh -vv -p 21098 colopio@162.0.215.185
   ```

3. Check tunnel logs:
   ```bash
   cat ~/tunnel_logs/tunnel.log
   ```

### Proxy Issues

If the proxy doesn't work:

1. Check logs on cPanel:
   ```bash
   ssh -p 21098 colopio@162.0.215.185
   cat ~/trading.colopio.com/logs/proxy.log
   cat ~/trading.colopio.com/logs/passenger_wsgi.log
   ```

2. Restart the proxy on cPanel:
   ```bash
   cd ~/trading.colopio.com
   ./start_proxy.sh
   ```

3. Verify Python app is running in cPanel:
   ```bash
   ps aux | grep python
   ```

## Security Considerations

1. The SSH tunnel only forwards traffic for trading.colopio.com
2. Domain validation ensures only trading.colopio.com requests are processed
3. SSH key authentication provides secure access without passwords
4. Regular monitoring ensures the tunnel remains operational

## Maintenance

- Logs are stored in `~/tunnel_logs/` on jamso-ai-server
- Logs are stored in `~/trading.colopio.com/logs/` on cPanel
- The monitor script will automatically restart the tunnel if it fails
- Old logs are automatically cleaned up after 7 days
