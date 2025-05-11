#!/bin/bash
# Stop Jamso AI Server local development services
# This script stops both the webhook server and the SSH tunnel

# Configuration
WEBHOOK_PID_FILE="./tmp/webhook.pid"
TUNNEL_PID_FILE="./tmp/tunnel.pid"

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

# Stop all services
stop_process "${WEBHOOK_PID_FILE}" "Webhook server"
stop_process "${TUNNEL_PID_FILE}" "SSH tunnel"

echo "All Jamso AI Server services have been stopped."