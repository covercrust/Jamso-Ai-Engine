#!/usr/bin/env python3
"""
Deploy the reverse proxy to the cPanel server (password-based authentication)
"""
import os
import argparse
import subprocess
import logging
import time
import sys
import tempfile
import getpass

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
    return parser.parse_args()

def add_host_to_known_hosts(args):
    """Add the remote host key to the known_hosts file using ssh-keyscan"""
    known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
    os.makedirs(os.path.dirname(known_hosts_path), exist_ok=True)
    
    logger.info(f"Adding {args.host}:{args.port} to known_hosts file")
    
    # Use ssh-keyscan to get the host key
    try:
        result = subprocess.run(
            ["ssh-keyscan", "-p", str(args.port), args.host],
            capture_output=True, 
            text=True, 
            check=True
        )
        host_key = result.stdout.strip()
        
        # Append to known_hosts file if not already there
        with open(known_hosts_path, "a+") as f:
            f.seek(0)
            if host_key and host_key not in f.read():
                f.write(host_key + "\n")
                logger.info(f"Added host key for {args.host}:{args.port}")
            else:
                logger.info(f"Host key for {args.host}:{args.port} already exists")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get host key: {e}")
        return False

def run_ssh_command(args, command):
    """Run an SSH command on the remote server using sshpass for password authentication"""
    ssh_command = [
        "sshpass", "-p", CPANEL_PASSWORD,
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-p", str(args.port),
        f"{args.user}@{args.host}",
        command
    ]
    
    try:
        result = subprocess.run(ssh_command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"SSH command failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None

def upload_file(args, local_path, remote_path):
    """Upload a file to the remote server using SCP with sshpass for password authentication"""
    logger.info(f"Uploading {local_path} to {remote_path}")
    
    scp_command = [
        "sshpass", "-p", CPANEL_PASSWORD,
        "scp",
        "-o", "StrictHostKeyChecking=no",
        "-P", str(args.port),
        local_path,
        f"{args.user}@{args.host}:{remote_path}"
    ]
    
    try:
        subprocess.run(scp_command, check=True, capture_output=True)
        logger.info(f"Upload successful")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"SCP upload failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def create_remote_directory(args):
    """Create the remote directory structure"""
    logger.info(f"Creating remote directory: {args.remote_dir}")
    result = run_ssh_command(args, f"mkdir -p {args.remote_dir}")
    return result is not None

def create_remote_file(args, remote_path, content):
    """Create a file on the remote server with the given content"""
    logger.info(f"Creating remote file: {remote_path}")
    
    # Create a temporary file locally
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    
    # Upload the temporary file
    result = upload_file(args, temp_path, remote_path)
    
    # Delete the temporary file
    os.unlink(temp_path)
    
    return result

def create_htaccess(args):
    """Create .htaccess file on the remote server"""
    logger.info("Creating .htaccess file")
    return create_remote_file(args, f"{args.remote_dir}/.htaccess", HTACCESS_FILE)

def create_start_proxy_script(args):
    """Create start_proxy.sh script on the remote server"""
    logger.info("Creating start_proxy.sh script")
    result = create_remote_file(args, f"{args.remote_dir}/start_proxy.sh", START_PROXY_SCRIPT)
    if result:
        # Make the script executable
        run_ssh_command(args, f"chmod +x {args.remote_dir}/start_proxy.sh")
    return result

def create_logs_directory(args):
    """Create logs directory on the remote server"""
    logger.info("Creating logs directory")
    result = run_ssh_command(args, f"mkdir -p {args.remote_dir}/logs")
    return result is not None

def upload_reverse_proxy(args):
    """Upload the reverse proxy script to the remote server"""
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reverse_proxy.py")
    remote_path = f"{args.remote_dir}/reverse_proxy.py"
    result = upload_file(args, local_path, remote_path)
    if result:
        # Make the script executable
        run_ssh_command(args, f"chmod +x {remote_path}")
    return result

def upload_requirements(args):
    """Upload the requirements file to the remote server"""
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy_requirements.txt")
    remote_path = f"{args.remote_dir}/requirements.txt"
    return upload_file(args, local_path, remote_path)

def install_requirements(args):
    """Install Python requirements on the remote server"""
    logger.info("Installing Python requirements")
    command = f"source {PYTHON_VENV} && cd {args.remote_dir} && pip install -r requirements.txt"
    result = run_ssh_command(args, command)
    if result is not None:
        logger.info("Requirements installed successfully")
        return True
    else:
        logger.error("Failed to install requirements")
        return False

def start_proxy_on_remote(args):
    """Start the proxy on the remote server"""
    logger.info("Starting proxy on remote server")
    result = run_ssh_command(args, f"cd {args.remote_dir} && ./start_proxy.sh")
    if result is not None:
        logger.info("Proxy started successfully")
        return True
    else:
        logger.error("Failed to start proxy")
        return False

def check_sshpass_installed():
    """Check if sshpass is installed on the system"""
    try:
        subprocess.run(["sshpass", "-V"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_sshpass():
    """Attempt to install sshpass"""
    logger.info("Attempting to install sshpass...")
    try:
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(["apt-get", "install", "-y", "sshpass"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Check if sshpass is installed
    if not check_sshpass_installed():
        logger.warning("sshpass is not installed. Attempting to install it...")
        if not install_sshpass():
            logger.error("Failed to install sshpass. Please install it manually and try again.")
            logger.error("You can install it on Ubuntu/Debian with: sudo apt-get install sshpass")
            logger.error("On CentOS/RHEL with: sudo yum install sshpass")
            sys.exit(1)
    
    # Add remote host to known_hosts
    if not add_host_to_known_hosts(args):
        logger.warning("Failed to add host to known_hosts, continuing anyway...")
    
    # Step 1: Create remote directory
    if not create_remote_directory(args):
        logger.error("Failed to create remote directory")
        sys.exit(1)
    
    # Step 2: Create logs directory
    if not create_logs_directory(args):
        logger.error("Failed to create logs directory")
        sys.exit(1)
    
    # Step 3: Upload reverse proxy script
    if not upload_reverse_proxy(args):
        logger.error("Failed to upload reverse proxy script")
        sys.exit(1)
    
    # Step 4: Upload requirements file
    if not upload_requirements(args):
        logger.error("Failed to upload requirements file")
        sys.exit(1)
    
    # Step 5: Install Python requirements
    if not install_requirements(args):
        logger.error("Failed to install Python requirements")
        sys.exit(1)
    
    # Step 6: Create .htaccess file
    if not create_htaccess(args):
        logger.error("Failed to create .htaccess file")
        sys.exit(1)
    
    # Step 7: Create Python app configuration
    if not create_start_proxy_script(args):
        logger.error("Failed to create start proxy script")
        sys.exit(1)
    
    # Step 8: Start the proxy
    if not start_proxy_on_remote(args):
        logger.error("Failed to start proxy on remote server")
        sys.exit(1)
    
    logger.info("Deployment completed successfully!")
    logger.info("The reverse proxy is now running on the remote server")
    logger.info("You can now start the local tunnel: python3 tunnel.py")

if __name__ == "__main__":
    main()