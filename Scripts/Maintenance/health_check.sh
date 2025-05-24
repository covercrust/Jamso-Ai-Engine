#!/bin/bash
# Health Check Script for Jamso AI Engine
# This script performs a comprehensive health check of the system

echo "===== Jamso AI Engine Health Check ====="
echo "$(date)"
echo "---------------------------------------------"

# Function to check if a service is running
check_service() {
    local service_name="$1"
    local check_command="$2"
    local remediation="$3"
    
    echo "Checking $service_name..."
    if eval "$check_command" > /dev/null 2>&1; then
        echo "✅ $service_name is running properly."
    else
        echo "❌ $service_name is NOT running properly."
        echo "   Suggested fix: $remediation"
    fi
}

# Check if we're in the right directory
if [ ! -f "./run_local.sh" ]; then
    echo "Error: Please run this script from the Jamso AI Engine root directory."
    exit 1
fi

# Check if webhook server is running
webhook_pid=""
if [ -f "./tmp/webhook.pid" ]; then
    webhook_pid=$(cat ./tmp/webhook.pid)
    if ps -p "$webhook_pid" > /dev/null; then
        echo "✅ Webhook server is running with PID $webhook_pid."
    else
        echo "❌ Webhook server is NOT running (stale PID file)."
        echo "   Suggested fix: Run './run_local.sh' to start the server."
    fi
else
    echo "❌ Webhook server is NOT running (no PID file)."
    echo "   Suggested fix: Run './run_local.sh' to start the server."
fi

# Check Redis if it's expected to be used
check_service "Redis" "redis-cli ping" "Run 'sudo systemctl start redis'"

# Check disk space
echo "Checking disk space..."
df_output=$(df -h . | grep -v Filesystem)
disk_usage=$(echo "$df_output" | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 90 ]; then
    echo "❌ Disk space critical: $disk_usage% used."
    echo "   Suggested fix: Run './Tools/system_cleanup.sh' or free up disk space."
elif [ "$disk_usage" -gt 75 ]; then
    echo "⚠️ Disk space warning: $disk_usage% used."
    echo "   Suggested fix: Consider running './Tools/system_cleanup.sh'."
else
    echo "✅ Disk space is adequate: $disk_usage% used."
fi

# Check memory usage
echo "Checking memory usage..."
mem_available=$(free -m | grep Mem | awk '{print $7}')
mem_total=$(free -m | grep Mem | awk '{print $2}')
mem_percent=$((100 - (mem_available * 100 / mem_total)))

if [ "$mem_percent" -gt 90 ]; then
    echo "❌ Memory usage critical: $mem_percent% used."
    echo "   Suggested fix: Restart the server or free up memory."
elif [ "$mem_percent" -gt 75 ]; then
    echo "⚠️ Memory usage warning: $mem_percent% used."
else
    echo "✅ Memory usage is normal: $mem_percent% used."
fi

# Check for Python errors in log files
echo "Checking logs for errors..."
if grep -q "Error\|Exception\|Traceback" ./Logs/app.log 2>/dev/null; then
    echo "⚠️ Found errors in application logs."
    echo "   Suggested action: Check './Logs/app.log' for details."
else
    echo "✅ No critical errors found in application logs."
fi

# Check for required directories
echo "Checking required directories..."
for dir in "./Logs" "./tmp" "./instance"; do
    if [ -d "$dir" ]; then
        echo "✅ Directory $dir exists."
    else
        echo "❌ Directory $dir is missing."
        echo "   Suggested fix: Create directory with 'mkdir -p $dir'"
    fi
done

# Check Python environment
echo "Checking Python environment..."
if [ -d "./.venv" ]; then
    echo "✅ Virtual environment exists."
    if [ -f "./.venv/bin/python" ]; then
        python_version=$(./.venv/bin/python --version 2>&1)
        echo "✅ Python version: $python_version"
    else
        echo "❌ Python not found in virtual environment."
        echo "   Suggested fix: Recreate virtual environment with 'python -m venv .venv'"
    fi
else
    echo "❌ Virtual environment missing."
    echo "   Suggested fix: Create virtual environment with 'python -m venv .venv'"
fi

echo "---------------------------------------------"
echo "Health check completed on $(date)"
echo "For detailed system maintenance, see Docs/Maintenance_Guide.md"
echo "===== Health Check Finished ====="
