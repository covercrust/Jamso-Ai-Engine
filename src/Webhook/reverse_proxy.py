#!/usr/bin/env python3
"""
Reverse Proxy for Jamso AI Server
Runs on cPanel server to forward requests from trading.colopio.com to the local webhook server
"""
import socket
import select
import sys
import threading
import time
import os
import logging
import signal
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import http.client
from urllib.parse import urlparse
import io
import gzip

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

# Default configuration
LISTEN_PORT = 8080
LOCAL_PORT = 8000  # Updated port for SSH tunnel
LOCAL_HOST = '127.0.0.1'

# Try to get configuration from environment variables (useful for cPanel Python Apps)
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', LISTEN_PORT))
LOCAL_PORT = int(os.environ.get('LOCAL_PORT', LOCAL_PORT))
LOCAL_HOST = os.environ.get('LOCAL_HOST', LOCAL_HOST)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Reverse proxy for Jamso AI Webhook Server')
    parser.add_argument('--listen-port', type=int, default=LISTEN_PORT, help=f'Port to listen on (default: {LISTEN_PORT})')
    parser.add_argument('--local-port', type=int, default=LOCAL_PORT, help=f'Local port to forward to (default: {LOCAL_PORT})')
    parser.add_argument('--local-host', default=LOCAL_HOST, help=f'Local host to forward to (default: {LOCAL_HOST})')
    return parser.parse_args()

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler that forwards requests to the webhook server through the SSH tunnel"""
    
    def __init__(self, *args, **kwargs):
        self.local_host = LOCAL_HOST
        self.local_port = LOCAL_PORT
        super().__init__(*args, **kwargs)
    
    def setup(self):
        self.local_host = self.server.local_host
        self.local_port = self.server.local_port
        return super().setup()
    
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
        """Forward the request to the webhook server through the SSH tunnel"""
        try:
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
            logger.info(f"Forwarding {method} request from {client_addr} to {self.local_host}:{self.local_port}{path}")
            
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

class ProxyHTTPServer(HTTPServer):
    """Custom HTTP server that includes local host and port configuration"""
    
    def __init__(self, server_address, request_handler_class, local_host, local_port):
        self.local_host = local_host
        self.local_port = local_port
        super().__init__(server_address, request_handler_class)

def start_proxy_server(args):
    """Start the HTTP proxy server"""
    server = ProxyHTTPServer(('0.0.0.0', args.listen_port), ProxyHTTPRequestHandler, args.local_host, args.local_port)
    logger.info(f"Starting reverse proxy server on port {args.listen_port}")
    logger.info(f"Forwarding requests to {args.local_host}:{args.local_port}")
    
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