#!/bin/bash
# Run Jamso AI Server with performance monitoring
# This script launches both the server and monitoring tools

# Check Redis connection if used
if command -v redis-cli >/dev/null 2>&1; then
    echo "Checking Redis connection..."
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "Warning: Redis connection failed. Some features may not work correctly."
        echo "You may need to start Redis with: sudo systemctl start redis"
    else
        echo "Redis connection successful."
    fi
fi

# Clean up before starting
echo "Running quick cleanup before startup..."
./Tools/cleanup_cache.sh

# Start Jamso AI Server in the background
echo "Starting Jamso AI Server..."
./run_local.sh &
SERVER_PID=$!

# Give the server time to initialize
sleep 5

# Start the resource monitor in the background
echo "Starting resource monitoring..."
./Tools/monitor_resources.py -i 300 &
MONITOR_PID=$!

# Function to clean up on exit
cleanup() {
    echo "Stopping all services..."
    kill $SERVER_PID 2>/dev/null
    kill $MONITOR_PID 2>/dev/null
    ./stop_local.sh
    echo "All services stopped."
    exit 0
}

# Register the cleanup function for SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo "========================================"
echo "Jamso AI Server and monitoring started!"
echo "========================================"
echo "Server running at: http://localhost:5000"
echo "Logs available in the Logs directory"
echo ""
echo "Press Ctrl+C to stop all services"
echo "========================================"

# Wait for user to press Ctrl+C
wait $SERVER_PID
