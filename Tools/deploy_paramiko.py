#!/usr/bin/env python3
"""
Deploy the reverse proxy to the cPanel server using Python's paramiko library for SSH
"""
import os
import sys
import argparse
import logging
import tempfile
import time
import socket
import getpass

try:
    import paramiko
except ImportError:
    print("Paramiko library not installed. Installing it now...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('deploy')

# Default configuration
CPANEL_USER = "colopio"
CPANEL_HOST = "162.0.215.185"
CPANEL_PORT = 21098
CPANEL_PASSWORD = "Bluetti@2024"  # Store password for automated authentication
REMOTE_DIR = "trading.colopio.com"
PYTHON_VENV = "/home/colopio/virtualenv/trading.colopio.com/3.12/bin/activate"

# Create these files inline to avoid issues with heredoc/cat redirection in SSH
HTACCESS_FILE = """
# .htaccess file for trading.colopio.com
RewriteEngine On
RewriteRule ^(.*)$ http://localhost:8080/$1 [P,L]
"""

START_PROXY_SCRIPT = f"""#!/bin/bash
# Start the reverse proxy server
source {PYTHON_VENV}
cd $HOME/{REMOTE_DIR}
nohup python3 reverse_proxy.py > proxy_output.log 2>&1 &
echo $! > proxy.pid
"""

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Deploy reverse proxy to cPanel server')
    parser.add_argument('--host', default=CPANEL_HOST, help=f'cPanel server hostname or IP (default: {CPANEL_HOST})')
    parser.add_argument('--port', type=int, default=CPANEL_PORT, help=f'SSH port (default: {CPANEL_PORT})')
    parser.add_argument('--user', default=CPANEL_USER, help=f'cPanel username (default: {CPANEL_USER})')
    parser.add_argument('--remote-dir', default=REMOTE_DIR, help=f'Remote directory (default: {REMOTE_DIR})')
    parser.add_argument('--password', default=CPANEL_PASSWORD, help=f'SSH password (default: {CPANEL_PASSWORD})')
    return parser.parse_args()

class SSHClient:
    """Class to handle SSH and SCP operations with paramiko"""
    
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.sftp = None
    
    def connect(self):
        """Connect to the remote server"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30
            )
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
        except paramiko.AuthenticationException:
            logger.error("Authentication failed. Please check your username and password.")
            return False
        except socket.timeout:
            logger.error(f"Connection to {self.host}:{self.port} timed out.")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH error: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the remote server"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
    
    def run_command(self, command):
        """Run a command on the remote server"""
        if not self.client:
            if not self.connect():
                return None
        
        try:
            logger.info(f"Running command: {command}")
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if exit_status != 0:
                logger.error(f"Command failed with exit status {exit_status}")
                logger.error(f"Error output: {error}")
                return None
            
            if error:
                logger.warning(f"Command succeeded but with message: {error}")
            
            return output
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return None
    
    def upload_file(self, local_path, remote_path):
        """Upload a file to the remote server"""
        if not self.client:
            if not self.connect():
                return False
        
        try:
            if not self.sftp:
                self.sftp = self.client.open_sftp()
            
            logger.info(f"Uploading {local_path} to {remote_path}")
            self.sftp.put(local_path, remote_path)
            logger.info("Upload successful")
            return True
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False

def create_remote_directory(ssh, args):
    """Create the remote directory structure"""
    logger.info(f"Creating remote directory: {args.remote_dir}")
    result = ssh.run_command(f"mkdir -p {args.remote_dir}")
    return result is not None

def create_logs_directory(ssh, args):
    """Create logs directory on the remote server"""
    logger.info("Creating logs directory")
    result = ssh.run_command(f"mkdir -p {args.remote_dir}/logs")
    return result is not None

def upload_reverse_proxy(ssh, args):
    """Upload the reverse proxy script to the remote server"""
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reverse_proxy.py")
    remote_path = f"{args.remote_dir}/reverse_proxy.py"
    result = ssh.upload_file(local_path, remote_path)
    if result:
        # Make the script executable
        ssh.run_command(f"chmod +x {args.remote_dir}/reverse_proxy.py")
    return result

def upload_requirements(ssh, args):
    """Upload the requirements file to the remote server"""
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy_requirements.txt")
    remote_path = f"{args.remote_dir}/requirements.txt"
    return ssh.upload_file(local_path, remote_path)

def create_htaccess(ssh, args):
    """Create .htaccess file on the remote server"""
    logger.info("Creating .htaccess file")
    
    # Create a temporary file locally
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(HTACCESS_FILE)
        temp_path = temp_file.name
    
    # Upload the temporary file
    result = ssh.upload_file(temp_path, f"{args.remote_dir}/.htaccess")
    
    # Delete the temporary file
    os.unlink(temp_path)
    
    return result

def create_start_proxy_script(ssh, args):
    """Create start_proxy.sh script on the remote server"""
    logger.info("Creating start_proxy.sh script")
    
    # Create a temporary file locally
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(START_PROXY_SCRIPT)
        temp_path = temp_file.name
    
    # Upload the temporary file
    result = ssh.upload_file(temp_path, f"{args.remote_dir}/start_proxy.sh")
    
    # Delete the temporary file
    os.unlink(temp_path)
    
    if result:
        # Make the script executable
        ssh.run_command(f"chmod +x {args.remote_dir}/start_proxy.sh")
    
    return result

def install_requirements(ssh, args):
    """Install Python requirements on the remote server"""
    logger.info("Installing Python requirements")
    command = f"source {PYTHON_VENV} && cd {args.remote_dir} && pip install -r requirements.txt"
    result = ssh.run_command(command)
    if result is not None:
        logger.info("Requirements installed successfully")
        return True
    else:
        logger.error("Failed to install requirements")
        return False

def start_proxy_on_remote(ssh, args):
    """Start the proxy on the remote server"""
    logger.info("Starting proxy on remote server")
    result = ssh.run_command(f"cd {args.remote_dir} && ./start_proxy.sh")
    if result is not None:
        logger.info("Proxy started successfully")
        return True
    else:
        logger.error("Failed to start proxy")
        return False

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create SSH client
    ssh = SSHClient(args.host, args.port, args.user, args.password)
    
    # Connect to the server
    if not ssh.connect():
        logger.error("Failed to connect to the server")
        sys.exit(1)
    
    try:
        # Step 1: Create remote directory
        if not create_remote_directory(ssh, args):
            logger.error("Failed to create remote directory")
            sys.exit(1)
        
        # Step 2: Create logs directory
        if not create_logs_directory(ssh, args):
            logger.error("Failed to create logs directory")
            sys.exit(1)
        
        # Step 3: Upload reverse proxy script
        if not upload_reverse_proxy(ssh, args):
            logger.error("Failed to upload reverse proxy script")
            sys.exit(1)
        
        # Step 4: Upload requirements file
        if not upload_requirements(ssh, args):
            logger.error("Failed to upload requirements file")
            sys.exit(1)
        
        # Step 5: Install Python requirements
        if not install_requirements(ssh, args):
            logger.error("Failed to install Python requirements")
            sys.exit(1)
        
        # Step 6: Create .htaccess file
        if not create_htaccess(ssh, args):
            logger.error("Failed to create .htaccess file")
            sys.exit(1)
        
        # Step 7: Create Python app configuration
        if not create_start_proxy_script(ssh, args):
            logger.error("Failed to create start proxy script")
            sys.exit(1)
        
        # Step 8: Start the proxy
        if not start_proxy_on_remote(ssh, args):
            logger.error("Failed to start proxy on remote server")
            sys.exit(1)
        
        logger.info("Deployment completed successfully!")
        logger.info("The reverse proxy is now running on the remote server")
        logger.info("You can now start the local tunnel: python3 tunnel.py")
    
    finally:
        # Always disconnect from the server
        ssh.disconnect()

if __name__ == "__main__":
    main()