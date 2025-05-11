#!/usr/bin/env python3
"""
Deploy the reverse proxy to the cPanel server using expect for automated password entry
"""
import os
import argparse
import subprocess
import logging
import time
import sys
import tempfile

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

# Expect script template for SSH
EXPECT_SSH_SCRIPT = """#!/usr/bin/expect -f
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -p {port} {user}@{host} {command}
expect {{
    "password:" {{ send "{password}\r"; exp_continue }}
    eof
}}
"""

# Expect script template for SCP
EXPECT_SCP_SCRIPT = """#!/usr/bin/expect -f
set timeout 30
spawn scp -o StrictHostKeyChecking=no -P {port} {local_path} {user}@{host}:{remote_path}
expect {{
    "password:" {{ send "{password}\r"; exp_continue }}
    eof
}}
"""

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Deploy reverse proxy to cPanel server')
    parser.add_argument('--host', default=CPANEL_HOST, help=f'cPanel server hostname or IP (default: {CPANEL_HOST})')
    parser.add_argument('--port', type=int, default=CPANEL_PORT, help=f'SSH port (default: {CPANEL_PORT})')
    parser.add_argument('--user', default=CPANEL_USER, help=f'cPanel username (default: {CPANEL_USER})')
    parser.add_argument('--remote-dir', default=REMOTE_DIR, help=f'Remote directory (default: {REMOTE_DIR})')
    return parser.parse_args()

def run_expect_script(script_content):
    """Run an expect script for SSH or SCP with automated password entry"""
    # Create a temporary file for the expect script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.exp') as script_file:
        script_file.write(script_content)
        script_path = script_file.name
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    try:
        # Run the expect script
        result = subprocess.run([script_path], capture_output=True, text=True)
        
        # Check for success (expect doesn't use exit codes very well)
        if result.returncode != 0:
            logger.error(f"Expect script failed with return code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return None
        
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Error running expect script: {e}")
        return None
    finally:
        # Clean up the temporary script
        os.unlink(script_path)

def run_ssh_command(args, command):
    """Run an SSH command on the remote server using expect for automated password entry"""
    # Format the expect script with the command and credentials
    script = EXPECT_SSH_SCRIPT.format(
        port=args.port,
        user=args.user,
        host=args.host,
        command=command,
        password=CPANEL_PASSWORD
    )
    
    return run_expect_script(script)

def upload_file(args, local_path, remote_path):
    """Upload a file to the remote server using SCP with expect for automated password entry"""
    logger.info(f"Uploading {local_path} to {remote_path}")
    
    # Format the expect script with the file paths and credentials
    script = EXPECT_SCP_SCRIPT.format(
        port=args.port,
        user=args.user,
        host=args.host,
        local_path=local_path,
        remote_path=remote_path,
        password=CPANEL_PASSWORD
    )
    
    result = run_expect_script(script)
    if result is not None:
        logger.info(f"Upload successful")
        return True
    else:
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

def check_expect_installed():
    """Check if expect is installed on the system"""
    try:
        subprocess.run(["which", "expect"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Check if expect is installed
    if not check_expect_installed():
        logger.error("expect is not installed. Please install it and try again.")
        logger.error("You can install it on Ubuntu/Debian with: sudo apt-get install expect")
        logger.error("On CentOS/RHEL with: sudo yum install expect")
        sys.exit(1)
    
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