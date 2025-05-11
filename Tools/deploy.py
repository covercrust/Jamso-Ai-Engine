#!/usr/bin/env python3
"""
Deploy the reverse proxy to the cPanel server
"""
import os
import argparse
import subprocess
import logging
import time
import sys

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
KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tunnel_key")
REMOTE_DIR = "trading.colopio.com"  # Updated to match the folder name from your info
PYTHON_VENV = "/home/colopio/virtualenv/trading.colopio.com/3.12/bin/activate"
HTACCESS_CONTENT = """
# .htaccess file for trading.colopio.com
RewriteEngine On
RewriteRule ^(.*)$ http://localhost:8080/$1 [P,L]
"""
PYTHON_APP_CONFIG = f"""
#!/bin/bash
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
    parser.add_argument('--key', default=KEY_PATH, help=f'SSH key path (default: {KEY_PATH})')
    parser.add_argument('--remote-dir', default=REMOTE_DIR, help=f'Remote directory (default: {REMOTE_DIR})')
    return parser.parse_args()

def run_ssh_command(args, command):
    """Run an SSH command on the remote server"""
    ssh_command = [
        "ssh",
        "-p", str(args.port),
        "-i", args.key,
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
    """Upload a file to the remote server using SCP"""
    logger.info(f"Uploading {local_path} to {remote_path}")
    
    scp_command = [
        "scp",
        "-P", str(args.port),
        "-i", args.key,
        local_path,
        f"{args.user}@{args.host}:{remote_path}"
    ]
    
    try:
        subprocess.run(scp_command, check=True)
        logger.info(f"Upload successful")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"SCP upload failed: {e}")
        return False

def create_remote_directory(args):
    """Create the remote directory structure"""
    logger.info(f"Creating remote directory: {args.remote_dir}")
    result = run_ssh_command(args, f"mkdir -p {args.remote_dir}")
    return result is not None

def create_htaccess(args):
    """Create .htaccess file on the remote server"""
    logger.info("Creating .htaccess file")
    remote_path = f"{args.remote_dir}/.htaccess"
    command = f"cat > {remote_path} << 'EOL'\n{HTACCESS_CONTENT}\nEOL"
    result = run_ssh_command(args, command)
    return result is not None

def create_python_app_config(args):
    """Create Python app configuration on the remote server"""
    logger.info("Creating Python app configuration")
    remote_path = f"{args.remote_dir}/start_proxy.sh"
    command = f"cat > {remote_path} << 'EOL'\n{PYTHON_APP_CONFIG}\nEOL"
    result = run_ssh_command(args, command)
    if result is not None:
        # Make the script executable
        run_ssh_command(args, f"chmod +x {remote_path}")
        return True
    return False

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

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Check if key file exists
    if not os.path.exists(args.key):
        logger.error(f"SSH key file does not exist: {args.key}")
        sys.exit(1)
    
    # Make sure key has correct permissions
    os.chmod(args.key, 0o600)
    
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
    if not create_python_app_config(args):
        logger.error("Failed to create Python app configuration")
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