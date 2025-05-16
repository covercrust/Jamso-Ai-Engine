#!/bin/bash
# Deployment script for trading.colopio.com reverse proxy
# Transfers necessary files to cPanel server and sets up the reverse proxy

set -e

# Configuration
CPANEL_USER="colopio"
CPANEL_HOST="162.0.215.185"
CPANEL_SSH_PORT=21098
SITE_DIR="trading.colopio.com"  # The directory on cPanel server for the domain
LOCAL_TEMPLATES="/home/jamso-ai-server/tmp"
SSH_KEY="$HOME/.ssh/id_rsa"     # Path to SSH private key
DOMAIN="trading.colopio.com"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying reverse proxy for $DOMAIN to cPanel server ${CPANEL_HOST}${NC}"

# Create local templates directory if it doesn't exist
mkdir -p $LOCAL_TEMPLATES

# Check SSH connectivity first
echo -e "${YELLOW}Testing SSH connectivity to cPanel server...${NC}"
if ! ssh -i "$SSH_KEY" -p $CPANEL_SSH_PORT -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no $CPANEL_USER@$CPANEL_HOST "echo Connection successful"; then
    echo -e "${RED}Cannot connect to cPanel server. Please check SSH credentials and connectivity.${NC}"
    echo -e "${YELLOW}Make sure you have set up SSH key authentication:${NC}"
    echo -e "${GREEN}ssh-copy-id -i ~/.ssh/id_rsa.pub -p $CPANEL_SSH_PORT $CPANEL_USER@$CPANEL_HOST${NC}"
    exit 1
fi

# Create reverse_proxy.py template
echo -e "${GREEN}Creating reverse_proxy.py template...${NC}"
cat > "$LOCAL_TEMPLATES/reverse_proxy.py" << 'EOF'
#!/usr/bin/env python3
"""
Reverse Proxy for trading.colopio.com
- Forwards requests to backend server through SSH tunnel
- Works with cPanel Python Application
- Handles HTTP and HTTPS traffic
"""
import socket
import select
import sys
import threading
import time
import os
import logging
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
import http.client
from urllib.parse import urlparse
import io
import gzip
import argparse
import json

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "proxy.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('reverse_proxy')

# Default configuration (can be overridden by environment variables)
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', 8080))
LOCAL_PORT = int(os.environ.get('LOCAL_PORT', 5000))  # Port of the SSH tunnel
LOCAL_HOST = os.environ.get('LOCAL_HOST', '127.0.0.1')
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', 'trading.colopio.com').split(',')

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Reverse proxy for trading.colopio.com')
    parser.add_argument('--listen-port', type=int, default=LISTEN_PORT, help=f'Port to listen on (default: {LISTEN_PORT})')
    parser.add_argument('--local-port', type=int, default=LOCAL_PORT, help=f'Local port to forward to (default: {LOCAL_PORT})')
    parser.add_argument('--local-host', default=LOCAL_HOST, help=f'Local host to forward to (default: {LOCAL_HOST})')
    parser.add_argument('--allowed-domains', default=','.join(ALLOWED_DOMAINS), help=f'Comma-separated list of allowed domains (default: {",".join(ALLOWED_DOMAINS)})')
    return parser.parse_args()

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler that forwards requests to the backend server through the SSH tunnel"""
    
    def setup(self):
        self.local_host = self.server.local_host
        self.local_port = self.server.local_port
        self.allowed_domains = self.server.allowed_domains
        return super().setup()
    
    def _is_allowed_domain(self):
        """Check if the request is for an allowed domain"""
        host = self.headers.get('Host', '')
        if not host:
            return False
        
        # Strip port number if present
        domain = host.split(':')[0]
        
        # Check against allowed domains
        for allowed in self.allowed_domains:
            if domain == allowed or (allowed.startswith('*.') and domain.endswith(allowed[1:])):
                return True
        
        return False
    
    def do_GET(self):
        """Handle GET requests"""
        self._handle_request('GET')
        
    def do_POST(self):
        """Handle POST requests"""
        self._handle_request('POST')
        
    def do_PUT(self):
        """Handle PUT requests"""
        self._handle_request('PUT')
        
    def do_DELETE(self):
        """Handle DELETE requests"""
        self._handle_request('DELETE')
        
    def do_HEAD(self):
        """Handle HEAD requests"""
        self._handle_request('HEAD')
        
    def do_OPTIONS(self):
        """Handle OPTIONS requests"""
        self._handle_request('OPTIONS')
        
    def _handle_request(self, method):
        """Forward the request to the backend server through the SSH tunnel"""
        try:
            # Special handling for status endpoint
            if self.path == '/status' or self.path == '/health':
                self._handle_status_request()
                return
                
            # Check if domain is allowed
            if not self._is_allowed_domain():
                self.send_error(403, "Forbidden: Domain not allowed")
                return
            
            # Parse the URL
            url = urlparse(self.path)
            path = url.path
            if url.query:
                path += '?' + url.query
                
            # Read request headers
            headers = {k: v for k, v in self.headers.items()}
            
            # Read request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Log the request
            client_addr = self.client_address[0]
            host = self.headers.get('Host', 'unknown')
            logger.info(f"Forwarding {method} request from {client_addr} to {self.local_host}:{self.local_port}{path} (Host: {host})")
            
            # Check if tunnel is accessible before trying to connect
            tunnel_active = False
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                result = s.connect_ex((self.local_host, self.local_port))
                tunnel_active = (result == 0)
                s.close()
            except:
                tunnel_active = False
            
            if not tunnel_active:
                logger.error(f"SSH tunnel is not active. Cannot forward request to {self.local_host}:{self.local_port}")
                self.send_error(502, "Bad Gateway: SSH tunnel is not active")
                return
            
            # Connect to the local server through the SSH tunnel
            conn = http.client.HTTPConnection(self.local_host, self.local_port)
            
            # Forward the request
            conn.request(method, path, body, headers)
            
            # Get the response
            response = conn.getresponse()
            
            # Forward the response status and headers
            self.send_response(response.status)
            
            # Forward response headers
            for header, value in response.getheaders():
                if header.lower() != 'transfer-encoding':  # Skip chunked encoding, we'll handle it
                    self.send_header(header, value)
            self.end_headers()
            
            # Forward response body
            response_data = response.read()
            self.wfile.write(response_data)
            
            # Close the connection
            conn.close()
            
            logger.info(f"Forwarded response: {response.status} ({len(response_data)} bytes)")
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(502, f"Bad Gateway: {str(e)}")
    
    def _handle_status_request(self):
        """Handle status/health check requests"""
        try:
            # Check tunnel connectivity
            tunnel_active = False
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                result = s.connect_ex((self.local_host, self.local_port))
                tunnel_active = (result == 0)
                s.close()
            except:
                tunnel_active = False
            
            # Create status response
            status_info = {
                "status": "healthy" if tunnel_active else "degraded",
                "proxy": {
                    "running": True,
                    "allowed_domains": self.allowed_domains,
                    "listen_port": self.server.server_port
                },
                "tunnel": {
                    "active": tunnel_active,
                    "endpoint": f"{self.local_host}:{self.local_port}"
                },
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(status_info).encode('utf-8'))
            logger.info(f"Handled status request, tunnel active: {tunnel_active}")
            
        except Exception as e:
            logger.error(f"Error handling status request: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")

class ProxyHTTPServer(HTTPServer):
    """Custom HTTP server that includes local host and port configuration"""
    
    def __init__(self, server_address, request_handler_class, local_host, local_port, allowed_domains):
        self.local_host = local_host
        self.local_port = local_port
        self.allowed_domains = allowed_domains
        super().__init__(server_address, request_handler_class)

def start_proxy_server(args):
    """Start the HTTP proxy server"""
    allowed_domains = args.allowed_domains.split(',')
    server = ProxyHTTPServer(('0.0.0.0', args.listen_port), ProxyHTTPRequestHandler, 
                            args.local_host, args.local_port, allowed_domains)
    
    logger.info(f"Starting reverse proxy server on port {args.listen_port}")
    logger.info(f"Forwarding requests to {args.local_host}:{args.local_port}")
    logger.info(f"Allowed domains: {', '.join(allowed_domains)}")
    
    # Handle SIGTERM gracefully
    def handle_sigterm(signum, frame):
        logger.info("Received SIGTERM signal, shutting down...")
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        server.shutdown()
    finally:
        server.server_close()

def main():
    """Main entry point"""
    args = parse_arguments()
    start_proxy_server(args)

if __name__ == "__main__":
    main()
EOF

# Create passenger_wsgi.py template
echo -e "${GREEN}Creating passenger_wsgi.py template...${NC}"
cat > "$LOCAL_TEMPLATES/passenger_wsgi.py" << 'EOF'
#!/usr/bin/env python3
"""
Passenger WSGI configuration for trading.colopio.com
Serves as the entry point for the reverse proxy
"""
import os
import sys
import logging
from threading import Thread
import time
import socket
import json

# Set up logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    filename=os.path.join(log_dir, 'passenger_wsgi.log'),
    filemode='a'
)
logger = logging.getLogger('passenger_wsgi')

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Domain specific configuration
DOMAIN = 'trading.colopio.com'
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', 8080))
LOCAL_PORT = int(os.environ.get('LOCAL_PORT', 5000))
LOCAL_HOST = os.environ.get('LOCAL_HOST', '127.0.0.1')
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', DOMAIN).split(',')

# Log startup information
logger.info(f"Starting passenger_wsgi for {DOMAIN}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Configuration: LOCAL_HOST={LOCAL_HOST}, LOCAL_PORT={LOCAL_PORT}, LISTEN_PORT={LISTEN_PORT}")

# Import the reverse proxy application
try:
    from reverse_proxy import ProxyHTTPRequestHandler, ProxyHTTPServer
    logger.info("Successfully imported reverse_proxy module")
except ImportError as e:
    logger.error(f"Failed to import reverse_proxy module: {e}")
    
    # Create a simple application that returns an error
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        error_message = f"Error: Reverse proxy module not found. Please contact administrator.\nDetails: {str(e)}"
        logger.error(error_message)
        return [error_message.encode('utf-8')]
else:
    # Global variables for the proxy server
    proxy_server = None
    proxy_thread = None
    
    def start_proxy():
        global proxy_server
        try:
            logger.info(f"Starting proxy server on port {LISTEN_PORT}")
            proxy_server = ProxyHTTPServer(
                ('127.0.0.1', LISTEN_PORT),
                ProxyHTTPRequestHandler,
                LOCAL_HOST,
                LOCAL_PORT,
                ALLOWED_DOMAINS
            )
            proxy_server.serve_forever()
        except Exception as e:
            logger.error(f"Error starting proxy server: {e}")
    
    # Start the proxy server in a separate thread
    try:
        proxy_thread = Thread(target=start_proxy, daemon=True)
        proxy_thread.start()
        logger.info("Proxy thread started")
    except Exception as e:
        logger.error(f"Failed to start proxy thread: {e}")
    
    # WSGI application function
    def application(environ, start_response):
        # Check if proxy is running
        if proxy_thread and not proxy_thread.is_alive():
            logger.error("Proxy thread is not running. Attempting to restart.")
            try:
                global proxy_thread
                proxy_thread = Thread(target=start_proxy, daemon=True)
                proxy_thread.start()
                logger.info("Proxy thread restarted")
            except Exception as e:
                logger.error(f"Failed to restart proxy thread: {e}")
        
        # Check if request path is for status/health check
        path_info = environ.get('PATH_INFO', '')
        if path_info == '/status' or path_info == '/health':
            # Return detailed status information
            status = '200 OK'
            response_headers = [('Content-type', 'application/json')]
            start_response(status, response_headers)
            
            # Check if tunnel is working
            tunnel_working = False
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                result = s.connect_ex((LOCAL_HOST, LOCAL_PORT))
                tunnel_working = (result == 0)
                s.close()
            except:
                tunnel_working = False
                
            status_info = {
                'status': 'healthy' if proxy_thread and proxy_thread.is_alive() and tunnel_working else 'unhealthy',
                'domain': DOMAIN,
                'proxy_running': bool(proxy_thread and proxy_thread.is_alive()),
                'tunnel_connected': tunnel_working,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return [json.dumps(status_info).encode('utf-8')]
        else:
            # For normal requests, just return a simple status
            status = '200 OK'
            response_headers = [('Content-type', 'text/plain')]
            start_response(status, response_headers)
            
            if proxy_thread and proxy_thread.is_alive():
                message = f"Reverse proxy for {DOMAIN} is running"
                logger.info(f"Status check: {message}")
                return [message.encode('utf-8')]
            else:
                message = f"Reverse proxy for {DOMAIN} is not running. Check logs for details."
                logger.warning(f"Status check: {message}")
                return [message.encode('utf-8')]
EOF

# Create start_proxy.sh script
echo -e "${GREEN}Creating start_proxy.sh template...${NC}"
cat > "$LOCAL_TEMPLATES/start_proxy.sh" << 'EOF'
#!/bin/bash
# Start script for trading.colopio.com reverse proxy
# This script is used to start the proxy on cPanel server

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="trading.colopio.com"
APP_DIR=~/trading.colopio.com
LOG_DIR=~/logs
PID_FILE=$LOG_DIR/proxy.pid

# Create directories
mkdir -p $LOG_DIR
mkdir -p $APP_DIR/logs

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 is not installed. Please install it via cPanel Python Selector.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}Using Python version: $PYTHON_VERSION${NC}"

# Check if we have the necessary files
if [ ! -f $APP_DIR/reverse_proxy.py ]; then
    echo -e "${RED}Reverse proxy files are missing. Please deploy them first.${NC}"
    exit 1
fi

# Check if proxy is already running
if [ -f $PID_FILE ] && ps -p $(cat $PID_FILE) > /dev/null; then
    echo -e "${YELLOW}Proxy is already running with PID $(cat $PID_FILE)${NC}"
    echo -e "${YELLOW}To restart, kill the process first: kill $(cat $PID_FILE)${NC}"
    exit 0
fi

# Install required Python packages if they don't exist
echo -e "${GREEN}Checking for required Python packages...${NC}"
python3 -c "import http.client" 2>/dev/null || pip3 install --user httplib2
python3 -c "import urllib.parse" 2>/dev/null || pip3 install --user urllib3

# Set environment variables
export LISTEN_PORT=8080
export LOCAL_PORT=5000
export LOCAL_HOST=127.0.0.1
export ALLOWED_DOMAINS=$DOMAIN

# Check if tunnel is working
echo -e "${GREEN}Checking if SSH tunnel is working...${NC}"
if nc -z -w2 $LOCAL_HOST $LOCAL_PORT; then
    echo -e "${GREEN}SSH tunnel is working! Port $LOCAL_PORT is accessible.${NC}"
else
    echo -e "${YELLOW}WARNING: SSH tunnel does not appear to be working.${NC}"
    echo -e "${YELLOW}Make sure the SSH tunnel is established from the backend server.${NC}"
    echo -e "${YELLOW}The proxy will start but won't be able to forward requests until the tunnel is working.${NC}"
fi

# Start the proxy in the background
echo -e "${GREEN}Starting reverse proxy for $DOMAIN...${NC}"
cd $APP_DIR
nohup python3 reverse_proxy.py > $LOG_DIR/proxy.log 2>&1 &

# Save the PID
echo $! > $PID_FILE
echo -e "${GREEN}Proxy started with PID $(cat $PID_FILE)${NC}"

# Check if it's working
sleep 2
if ps -p $(cat $PID_FILE) > /dev/null; then
    echo -e "${GREEN}Proxy is running!${NC}"
    echo -e "${GREEN}Log file: $LOG_DIR/proxy.log${NC}"
    
    # Check if Passenger is configured
    if [ -f $APP_DIR/passenger_wsgi.py ]; then
        echo -e "${GREEN}Passenger WSGI file found.${NC}"
        echo -e "${GREEN}The proxy should also be accessible through the domain: http://$DOMAIN/${NC}"
    else
        echo -e "${YELLOW}Warning: passenger_wsgi.py not found. The proxy won't be accessible via the domain unless you configure it.${NC}"
    fi
else
    echo -e "${RED}Error: Proxy failed to start. Check the log file: $LOG_DIR/proxy.log${NC}"
    exit 1
fi

# Display helpful commands
echo -e "\n${GREEN}Helpful commands:${NC}"
echo -e "${YELLOW}View logs:${NC} cat $LOG_DIR/proxy.log"
echo -e "${YELLOW}Stop proxy:${NC} kill \$(cat $PID_FILE)"
echo -e "${YELLOW}Check status:${NC} ps -p \$(cat $PID_FILE) && echo 'Running' || echo 'Stopped'"
echo -e "${YELLOW}Test connection:${NC} curl http://localhost:8080/status"
EOF

# Make the script executable
chmod +x "$LOCAL_TEMPLATES/start_proxy.sh"

# Create cPanel python.py file for Python app (required by cPanel)
cat > "$LOCAL_TEMPLATES/python.py" << 'EOF'
import passenger_wsgi
application = passenger_wsgi.application
EOF

# Create .htaccess file to ensure proper handling
cat > "$LOCAL_TEMPLATES/.htaccess" << 'EOF'
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ /python.py/$1 [L]
EOF

# Deploy the files to cPanel
echo -e "${GREEN}Deploying files to cPanel server...${NC}"

# Create site directory on cPanel if it doesn't exist
ssh -i "$SSH_KEY" -p $CPANEL_SSH_PORT $CPANEL_USER@$CPANEL_HOST "mkdir -p ~/$SITE_DIR/logs"

# Transfer files to cPanel
scp -i "$SSH_KEY" -P $CPANEL_SSH_PORT "$LOCAL_TEMPLATES/reverse_proxy.py" $CPANEL_USER@$CPANEL_HOST:~/$SITE_DIR/
scp -i "$SSH_KEY" -P $CPANEL_SSH_PORT "$LOCAL_TEMPLATES/passenger_wsgi.py" $CPANEL_USER@$CPANEL_HOST:~/$SITE_DIR/
scp -i "$SSH_KEY" -P $CPANEL_SSH_PORT "$LOCAL_TEMPLATES/start_proxy.sh" $CPANEL_USER@$CPANEL_HOST:~/$SITE_DIR/
scp -i "$SSH_KEY" -P $CPANEL_SSH_PORT "$LOCAL_TEMPLATES/python.py" $CPANEL_USER@$CPANEL_HOST:~/$SITE_DIR/
scp -i "$SSH_KEY" -P $CPANEL_SSH_PORT "$LOCAL_TEMPLATES/.htaccess" $CPANEL_USER@$CPANEL_HOST:~/$SITE_DIR/

# Set proper permissions
ssh -i "$SSH_KEY" -p $CPANEL_SSH_PORT $CPANEL_USER@$CPANEL_HOST "chmod +x ~/$SITE_DIR/start_proxy.sh"

echo -e "${GREEN}Deployment complete. Files transferred to cPanel server.${NC}"
echo -e "${YELLOW}Now run the following commands to start the service on the cPanel server:${NC}"
echo -e "${GREEN}ssh -i $SSH_KEY -p $CPANEL_SSH_PORT $CPANEL_USER@$CPANEL_HOST${NC}"
echo -e "${GREEN}cd ~/$SITE_DIR && ./start_proxy.sh${NC}"

echo -e "${YELLOW}Make sure to configure SSH key authentication between backend and cPanel servers.${NC}"
echo -e "${YELLOW}To set up the reverse tunnel, run:${NC}"
echo -e "${GREEN}/home/jamso-ai-server/Jamso-Ai-Engine/Tools/start_ssh_tunnel.sh${NC}"
