#!/bin/bash
# Run Jamso AI Server locally for development
# This script launches both the webhook server and the SSH tunnel

# Set up environment
set -e  # Exit on error
source .venv/bin/activate
source Tools/load_env.sh || echo "Warning: Environment file not loaded"

# Configuration
export FLASK_ENV=development
export FLASK_DEBUG=1
LOG_DIR="./Logs"
WEBHOOK_LOG="${LOG_DIR}/webhook.log"
TUNNEL_LOG="${LOG_DIR}/tunnel.log"
WEBHOOK_PID_FILE="./tmp/webhook.pid"
TUNNEL_PID_FILE="./tmp/tunnel.pid"

# Ensure log directory and tmp directory exist
mkdir -p "${LOG_DIR}"
mkdir -p "./tmp"

# Function to check if a process is running
is_running() {
    local pid_file="$1"
    if [[ -f "${pid_file}" ]]; then
        local pid=$(cat "${pid_file}")
        if ps -p "${pid}" > /dev/null; then
            return 0  # Process is running
        fi
    fi
    return 1  # Process is not running
}

# Function to stop a process
stop_process() {
    local pid_file="$1"
    local process_name="$2"
    if [[ -f "${pid_file}" ]]; then
        local pid=$(cat "${pid_file}")
        if ps -p "${pid}" > /dev/null; then
            echo "Stopping ${process_name} (PID: ${pid})..."
            kill "${pid}" 2>/dev/null || kill -9 "${pid}" 2>/dev/null
            rm -f "${pid_file}"
            echo "${process_name} stopped."
        else
            echo "${process_name} not running, removing stale PID file."
            rm -f "${pid_file}"
        fi
    else
        echo "${process_name} not running."
    fi
}

# Stop any existing processes
stop_process "${WEBHOOK_PID_FILE}" "Webhook server"
stop_process "${TUNNEL_PID_FILE}" "SSH tunnel"

# Start the webhook server with proper path and environment
echo "Starting Webhook server..."
cd "$(dirname "$0")"  # Make sure we're in the right directory
export PYTHONPATH="$(pwd)"
python -m Webhook.app >> "${WEBHOOK_LOG}" 2>&1 &
WEBHOOK_PID=$!
echo ${WEBHOOK_PID} > "${WEBHOOK_PID_FILE}"
echo "Webhook server started with PID: ${WEBHOOK_PID}"
echo "Webhook logs at: ${WEBHOOK_LOG}"

# Wait for webhook server to initialize
echo "Waiting for webhook server to initialize..."
sleep 5

# Verify webhook server is running
if ! ps -p ${WEBHOOK_PID} > /dev/null; then
    echo "ERROR: Webhook server failed to start. Check logs at ${WEBHOOK_LOG}"
    cat "${WEBHOOK_LOG}" | tail -20  # Show the last 20 lines of the log
    exit 1
fi

# Test if webhook server is accessible
echo "Testing webhook server..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 > /dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: Webhook server may not be accessible on port 5000."
    echo "Checking last few lines of webhook log:"
    cat "${WEBHOOK_LOG}" | tail -20
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        stop_process "${WEBHOOK_PID_FILE}" "Webhook server"
        exit 1
    fi
fi

# Start the SSH tunnel with fixed port and retry logic
echo "Starting SSH tunnel..."
python tunnel.py --remote-port=22222 --remote-port-change=22223 >> "${TUNNEL_LOG}" 2>&1 &
TUNNEL_PID=$!
echo ${TUNNEL_PID} > "${TUNNEL_PID_FILE}"
echo "SSH tunnel started with PID: ${TUNNEL_PID}"
echo "Tunnel logs at: ${TUNNEL_LOG}"

# Wait for tunnel to initialize
echo "Waiting for SSH tunnel to initialize..."
sleep 10

# Check if tunnel is running
if ! ps -p ${TUNNEL_PID} > /dev/null; then
    echo "ERROR: SSH tunnel failed to start. Check logs at ${TUNNEL_LOG}"
    cat "${TUNNEL_LOG}" | tail -20  # Show the last 20 lines of the log
    stop_process "${WEBHOOK_PID_FILE}" "Webhook server"
    exit 1
fi

echo "====================================="
echo "Jamso AI Server started successfully!"
echo "====================================="
echo "Webhook server running on: http://localhost:5000"
echo "External access via: https://trading.colopio.com"
echo ""
echo "To stop all services, run: ./stop_local.sh"
echo "Or press Ctrl+C to exit and stop all processes"
echo ""
echo "Monitoring logs (press Ctrl+C to exit)..."
echo "====================================="

# Trap to handle Ctrl+C and cleanup
trap 'echo "Stopping services..."; stop_process "${WEBHOOK_PID_FILE}" "Webhook server"; stop_process "${TUNNEL_PID_FILE}" "SSH tunnel"; echo "All services stopped."; exit 0' INT

# Monitor logs and periodically check if processes are still running
while true; do
    # Check if webhook server is still running
    if ! ps -p ${WEBHOOK_PID} > /dev/null; then
        echo "ERROR: Webhook server (PID: ${WEBHOOK_PID}) has stopped unexpectedly."
        stop_process "${TUNNEL_PID_FILE}" "SSH tunnel"
        exit 1
    fi
    
    # Check if tunnel is still running
    if ! ps -p ${TUNNEL_PID} > /dev/null; then
        echo "ERROR: SSH tunnel (PID: ${TUNNEL_PID}) has stopped unexpectedly."
        echo "Restarting tunnel..."
        python tunnel.py --remote-port=22222 --remote-port-change=22223 >> "${TUNNEL_LOG}" 2>&1 &
        TUNNEL_PID=$!
        echo ${TUNNEL_PID} > "${TUNNEL_PID_FILE}"
        echo "SSH tunnel restarted with PID: ${TUNNEL_PID}"
    fi
    
    # Show latest log entries
    echo "--- Latest webhook log ---"
    tail -5 "${WEBHOOK_LOG}"
    echo "--- Latest tunnel log ---"
    tail -5 "${TUNNEL_LOG}"
    echo "-------------------------"
    
    # Sleep before next check
    sleep 60
done
