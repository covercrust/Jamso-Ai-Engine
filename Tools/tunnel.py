#!/usr/bin/env python3
"""
SSH Tunnel Manager for trading.colopio.com reverse proxy
- Forwards local port 5000 to backend server's 5000
- Uses Paramiko for programmatic SSH tunneling
- Reads credentials from credentials database or environment
- Logs status and errors
- Can be run as a background process or systemd service
"""
import os
import sys
import time
import logging
import socket
import paramiko
import sqlite3
import atexit

# Logging setup
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'tunnel.log')
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger('tunnel')

# Tunnel config (edit as needed)
LOCAL_PORT = 5000
REMOTE_PORT = 5000
REMOTE_HOST = os.environ.get('BACKEND_HOST', '127.0.0.1')
SSH_HOST = os.environ.get('SSH_HOST', 'jamso-ai-server.com')
SSH_PORT = int(os.environ.get('SSH_PORT', '22'))
SSH_USER = os.environ.get('SSH_USER', 'jamso-ai-server')
SSH_KEY_PATH = os.environ.get('SSH_KEY_PATH', os.path.expanduser('~/.ssh/id_rsa'))
SSH_PASSWORD = os.environ.get('SSH_PASSWORD')
CREDENTIALS_DB = os.path.join(os.path.dirname(__file__), '../src/Database/Credentials/credentials.db')

PID_FILE = '/tmp/jamso_tunnel.pid'

# Ensure only one instance runs
def singleton_check():
    try:
        pidfile = open(PID_FILE, 'w')
        import fcntl
        fcntl.lockf(pidfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pidfile.write(str(os.getpid()))
        pidfile.flush()
        return pidfile
    except IOError:
        logger.error('Another instance of tunnel.py is already running. Exiting.')
        sys.exit(1)

def cleanup():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as e:
        logger.error(f"Error cleaning up PID file: {e}")

atexit.register(cleanup)

# Load credentials from database or environment
def load_credentials():
    global SSH_HOST, SSH_USER, SSH_PORT, SSH_KEY_PATH, SSH_PASSWORD, REMOTE_HOST, REMOTE_PORT
    service = os.environ.get('TUNNEL_SERVICE', 'cpanel')
    try:
        import sqlite3
        conn = sqlite3.connect(CREDENTIALS_DB)
        cur = conn.cursor()
        
        # Query modified to match the actual table structure
        cur.execute("SELECT credential_key, credential_value FROM credentials WHERE service_name = ?", (service,))
        creds = dict(cur.fetchall())
        
        # Get credential values with fallback to current values
        SSH_HOST = creds.get('ssh_host', SSH_HOST)
        SSH_USER = creds.get('ssh_user', SSH_USER)
        SSH_PORT = int(creds.get('ssh_port', SSH_PORT)) if creds.get('ssh_port') else SSH_PORT
        SSH_KEY_PATH = creds.get('ssh_key_path', SSH_KEY_PATH)
        SSH_PASSWORD = creds.get('ssh_password', SSH_PASSWORD)
        REMOTE_HOST = creds.get('backend_host', REMOTE_HOST)
        REMOTE_PORT = int(creds.get('backend_port', REMOTE_PORT)) if creds.get('backend_port') else REMOTE_PORT
        conn.close()
        logger.info(f"Loaded SSH tunnel credentials for service '{service}' from DB")
    except Exception as e:
        logger.warning(f"Could not load credentials from DB for service '{service}': {e}. Falling back to environment variables.")
        SSH_HOST = os.environ.get('SSH_HOST', SSH_HOST)
        SSH_USER = os.environ.get('SSH_USER', SSH_USER)
        SSH_PORT = int(os.environ.get('SSH_PORT', SSH_PORT))
        SSH_KEY_PATH = os.environ.get('SSH_KEY_PATH', SSH_KEY_PATH)
        SSH_PASSWORD = os.environ.get('SSH_PASSWORD', SSH_PASSWORD)
        REMOTE_HOST = os.environ.get('REMOTE_HOST', REMOTE_HOST)
        REMOTE_PORT = int(os.environ.get('REMOTE_PORT', REMOTE_PORT))
    
    # Validate essential credentials
    if not SSH_HOST or SSH_HOST == 'jamso-ai-server.com':
        logger.error('SSH_HOST is not set or is a placeholder. Set the SSH_HOST credential in the DB or the SSH_HOST environment variable.')
        sys.exit(1)

def create_ssh_tunnel():
    load_credentials()
    logger.info(f"Establishing SSH tunnel: localhost:{LOCAL_PORT} -> {REMOTE_HOST}:{REMOTE_PORT} via {SSH_USER}@{SSH_HOST}:{SSH_PORT}")
    max_retries = 5
    attempt = 0
    while attempt < max_retries:
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if SSH_PASSWORD:
                client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD, timeout=30)
            else:
                client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, key_filename=SSH_KEY_PATH, timeout=30)
            
            transport = client.get_transport()
            if not transport:
                raise Exception('No SSH transport')
            
            # Forward local port to remote host:port
            logger.info('SSH connection established, setting up port forwarding...')
            forward_tunnel(LOCAL_PORT, REMOTE_HOST, REMOTE_PORT, transport)
            
            # If we get here without exception, the tunnel is established
            logger.info(f"Tunnel established successfully on attempt {attempt+1}")
            return
            
        except (socket.timeout, paramiko.SSHException, socket.error) as e:
            attempt += 1
            logger.error(f"SSH tunnel error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {attempt * 5} seconds...")
                time.sleep(attempt * 5)  # Incremental backoff
            else:
                logger.error("Max SSH tunnel attempts reached. Exiting.")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            if client:
                try:
                    client.close()
                except:
                    pass

def forward_tunnel(local_port, remote_host, remote_port, transport):
    # Modified to use newer Paramiko API
    try:
        transport.request_port_forward('127.0.0.1', local_port)
        logger.info(f"Port forwarding started: local port {local_port} -> {remote_host}:{remote_port}")
        
        # Keep the connection alive
        while True:
            time.sleep(60)  # Check every minute
            if not transport.is_active():
                logger.error("SSH transport is no longer active. Reconnecting...")
                raise paramiko.SSHException("Transport closed")
                
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down tunnel")
        raise
    except Exception as e:
        logger.error(f"Port forwarding failed: {e}")
        raise

def main():
    pidfile = singleton_check()
    try:
        create_ssh_tunnel()
    except KeyboardInterrupt:
        logger.info('SSH tunnel stopped by user')
        sys.exit(0)
    except Exception as e:
        logger.error(f"Tunnel error: {e}")
        sys.exit(1)
    finally:
        try:
            pidfile.close()
        except:
            pass

if __name__ == "__main__":
    main()
