#!/usr/bin/env python3
"""
Tunnel Client for Jamso AI Server
Creates an SSH reverse tunnel from the local webhook server to a remote server
"""
import subprocess
import time
import sys
import os
import signal
import logging
import argparse
from pathlib import Path
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("Logs", "tunnel.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ssh_tunnel')

# Default Configuration
CPANEL_USER = "colopio"
CPANEL_HOST = "162.0.215.185"
CPANEL_PORT = 21098
CPANEL_PASSWORD = "Bluetti@2024"  # Store password for automated authentication
REMOTE_PORT = 22222
LOCAL_PORT = 5000
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Create an SSH tunnel to connect the local webhook server to a remote server')
    parser.add_argument('--local-port', type=int, default=LOCAL_PORT, help=f'Local webhook server port (default: {LOCAL_PORT})')
    parser.add_argument('--remote-port', type=int, default=REMOTE_PORT, help=f'Remote port on cPanel server (default: {REMOTE_PORT})')
    parser.add_argument('--host', default=CPANEL_HOST, help=f'cPanel server hostname or IP (default: {CPANEL_HOST})')
    parser.add_argument('--port', type=int, default=CPANEL_PORT, help=f'SSH port (default: {CPANEL_PORT})')
    parser.add_argument('--user', default=CPANEL_USER, help=f'cPanel username (default: {CPANEL_USER})')
    parser.add_argument('--password', default=CPANEL_PASSWORD, help=f'SSH password (default: hidden)')
    parser.add_argument('--remote-port-change', type=int, default=None, help='Try a different remote port if default fails')
    return parser.parse_args()

def create_expect_script(args):
    """Create an expect script for automated password-based SSH tunneling"""
    script_content = f"""#!/usr/bin/expect -f
set timeout 60
spawn ssh -o StrictHostKeyChecking=no -N -R {args.remote_port}:localhost:{args.local_port} -p {args.port} {args.user}@{args.host}
expect {{
    "password:" {{
        send "{args.password}\\r"
        exp_continue
    }}
    "Error: remote port forwarding failed" {{
        exit 1
    }}
    timeout {{
        puts "Connection timed out"
        exit 1
    }}
    eof {{
        puts "Connection closed"
        exit 1
    }}
}}
"""
    # Create a temporary file for the expect script
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.exp') as script_file:
        script_file.write(script_content)
        script_path = script_file.name
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    return script_path

def check_expect_installed():
    """Check if expect is installed on the system"""
    try:
        subprocess.run(["which", "expect"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_tunnel_with_python_pexpect(args):
    """Establish SSH reverse tunnel using Python's pexpect module"""
    try:
        import pexpect
    except ImportError:
        logger.error("pexpect module not installed. Installing it now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pexpect"])
            import pexpect
        except Exception as e:
            logger.error(f"Failed to install pexpect: {e}")
            logger.error("Please install it manually: pip install pexpect")
            sys.exit(1)

    logger.info(f"Setting up SSH tunnel to {args.user}@{args.host}:{args.port}")
    logger.info(f"Forwarding remote port {args.remote_port} to local port {args.local_port}")
    
    while True:
        try:
            # Construct the SSH command
            ssh_command = f"ssh -o StrictHostKeyChecking=no -N -R {args.remote_port}:localhost:{args.local_port} -p {args.port} {args.user}@{args.host}"
            
            # Start the SSH process with pexpect
            child = pexpect.spawn(ssh_command)
            child.logfile_read = sys.stdout.buffer  # Display output for debugging
            
            # Wait for password prompt
            index = child.expect(['password:', 'Error: remote port forwarding failed', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
            
            if index == 0:  # Password prompt
                child.sendline(args.password)
                logger.info("SSH tunnel established. Press Ctrl+C to stop.")
                
                # Keep the tunnel running until interrupted
                child.expect([pexpect.EOF, pexpect.TIMEOUT])
                
                # If we get here, the connection was lost
                logger.warning("SSH tunnel connection lost. Reconnecting in 5 seconds...")
                time.sleep(5)
            
            elif index == 1:  # Port forwarding failed
                logger.error("Remote port forwarding failed. The port may be in use.")
                
                # Try a different port if specified
                if args.remote_port_change:
                    logger.info(f"Trying alternate port: {args.remote_port_change}")
                    args.remote_port = args.remote_port_change
                    continue
                
                # Otherwise increment the port and try again
                args.remote_port += 1
                logger.info(f"Trying next available port: {args.remote_port}")
                continue
            
            else:  # EOF or TIMEOUT
                logger.warning("Connection failed or timed out. Reconnecting in 10 seconds...")
                time.sleep(10)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt. Shutting down tunnel...")
            if 'child' in locals():
                child.close()
            break
        
        except Exception as e:
            logger.error(f"Error in tunnel: {e}")
            logger.info("Reconnecting in 10 seconds...")
            time.sleep(10)

def setup_tunnel_with_expect(args):
    """Establish SSH reverse tunnel using expect script"""
    logger.info(f"Setting up SSH tunnel to {args.user}@{args.host}:{args.port}")
    logger.info(f"Forwarding remote port {args.remote_port} to local port {args.local_port}")
    
    while True:
        try:
            # Create an expect script
            script_path = create_expect_script(args)
            
            # Run the expect script
            process = subprocess.Popen([script_path])
            logger.info("SSH tunnel established. Press Ctrl+C to stop.")
            
            # Wait for the process to terminate
            process.wait()
            
            # Check if the process failed due to port forwarding error
            if process.returncode == 1:
                logger.error("Remote port forwarding failed. The port may be in use.")
                
                # Try a different port if specified
                if args.remote_port_change:
                    logger.info(f"Trying alternate port: {args.remote_port_change}")
                    args.remote_port = args.remote_port_change
                else:
                    # Otherwise increment the port and try again
                    args.remote_port += 1
                    logger.info(f"Trying next available port: {args.remote_port}")
                
                # Clean up the script file
                os.unlink(script_path)
                continue
            
            # If we get here, the process terminated for another reason
            logger.warning("SSH tunnel connection lost. Reconnecting in 5 seconds...")
            time.sleep(5)
            
            # Clean up the script file
            os.unlink(script_path)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt. Shutting down tunnel...")
            if 'process' in locals():
                process.terminate()
                process.wait()
            if 'script_path' in locals() and os.path.exists(script_path):
                os.unlink(script_path)
            break
        
        except Exception as e:
            logger.error(f"Error in tunnel: {e}")
            logger.info("Reconnecting in 10 seconds...")
            time.sleep(10)
            if 'script_path' in locals() and os.path.exists(script_path):
                os.unlink(script_path)

def setup_tunnel(args):
    """Establish SSH reverse tunnel using a basic subprocess approach with password input"""
    logger.info(f"Setting up SSH tunnel to {args.user}@{args.host}:{args.port}")
    logger.info(f"Forwarding remote port {args.remote_port} to local port {args.local_port}")
    
    # Construct SSH command
    ssh_command = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-N",  # Don't execute a remote command
        "-R", f"{args.remote_port}:localhost:{args.local_port}",  # Remote port forwarding
        "-o", "ServerAliveInterval=60",  # Keep connection alive
        "-o", "ExitOnForwardFailure=yes",  # Exit if port forwarding fails
        "-p", str(args.port),  # SSH port
        f"{args.user}@{args.host}"
    ]
    
    # Start the SSH tunnel
    while True:
        try:
            # Let the user know they need to enter the password
            logger.info(f"Starting SSH tunnel. You will be prompted for the password for {args.user}@{args.host}")
            
            # Use subprocess.Popen to run the SSH command
            process = subprocess.Popen(
                ssh_command,
                stdin=sys.stdin,  # Connect to the terminal's stdin for password input
                stdout=sys.stdout,  # Show output
                stderr=sys.stderr
            )
            logger.info("SSH tunnel established. Press Ctrl+C to stop.")
            
            # Wait for the process to terminate
            process.wait()
            
            # If we get here, the process terminated - check exit code
            if process.returncode != 0:
                logger.warning(f"SSH tunnel exited with code {process.returncode}")
                
                # Try a different port if port forwarding failed
                if args.remote_port_change:
                    logger.info(f"Trying alternate port: {args.remote_port_change}")
                    ssh_command[4] = f"{args.remote_port_change}:localhost:{args.local_port}"
                    args.remote_port = args.remote_port_change
                    args.remote_port_change = None  # Only use it once
                else:
                    # Try the next port
                    args.remote_port += 1
                    logger.info(f"Trying next available port: {args.remote_port}")
                    ssh_command[4] = f"{args.remote_port}:localhost:{args.local_port}"
            
            logger.warning("SSH tunnel connection lost. Reconnecting in 5 seconds...")
            time.sleep(5)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt. Shutting down tunnel...")
            if 'process' in locals():
                process.terminate()
                process.wait()
            break
        
        except Exception as e:
            logger.error(f"Error in tunnel: {e}")
            logger.info("Reconnecting in 10 seconds...")
            time.sleep(10)

def main():
    """Main entry point"""
    # Create Logs directory if it doesn't exist
    os.makedirs("Logs", exist_ok=True)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Choose the appropriate tunnel setup method
    if check_expect_installed():
        logger.info("Using expect for automated password authentication")
        setup_tunnel_with_expect(args)
    else:
        try:
            # Try to import pexpect
            import pexpect
            logger.info("Using pexpect for automated password authentication")
            setup_tunnel_with_python_pexpect(args)
        except ImportError:
            # Fall back to manual password entry
            logger.warning("Neither expect nor pexpect is available. Using manual password entry.")
            logger.warning("You will need to enter the password when prompted.")
            setup_tunnel(args)

if __name__ == "__main__":
    main()