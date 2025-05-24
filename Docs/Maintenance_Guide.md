# Jamso AI Engine Maintenance Guide

## System Cleanup Operations

The Jamso AI Engine includes several cleanup tools to maintain optimal performance and stability. This document explains how and when to use them.

### Regular Maintenance Tasks

| Task | Frequency | Command | Purpose |
|------|-----------|---------|---------|
| System Cleanup | Weekly | `./Tools/system_cleanup.sh` | Comprehensive cleanup of all caches and temporary files |
| Redis Cache Cleanup | After significant data changes | `./Tools/cleanup_redis.sh` | Clear Redis cache to ensure data consistency |
| Python Cache Cleanup | When experiencing strange behavior | `./Tools/cleanup_cache.sh` | Clear Python cache files to resolve code execution issues |
| Session Cleanup | Monthly | `python3 ./Tools/cleanup_sessions.py` | Remove expired user sessions |

### When to Run Maintenance

1. **After Deployment**: Always run system cleanup after deploying new code.
2. **Performance Issues**: If the application is running slowly, try Redis cleanup first.
3. **Errors After Code Changes**: Clear Python caches when seeing unexpected behavior after changes.
4. **Low Disk Space**: Run the comprehensive cleanup if disk space is running low.

### Cleanup Tools Explained

#### 1. System Cleanup (`system_cleanup.sh`)

This is the master cleanup script that performs all cleanup operations:
- Stops running services
- Cleans Python cache files
- Removes temporary files
- Cleans old log files
- Clears Redis cache
- Optimizes the database
- Fixes file permissions

#### 2. Redis Cleanup (`cleanup_redis.sh`)

Specifically targets the Redis cache:
- Flushes all Redis data using `redis-cli FLUSHALL`
- Useful when data consistency issues arise

#### 3. Cache Cleanup (`cleanup_cache.sh`)

Focuses on removing Python and application cache files:
- Removes `__pycache__` directories
- Deletes `.pyc`, `.pyo`, and `.pyd` files
- Cleans temporary files older than 7 days

#### 4. Permissions Fix (`fix_permissions.sh`)

Ensures all files have correct permissions:
- Sets appropriate read/write/execute permissions
- Fixes ownership issues

### Automating Maintenance

Consider setting up a cron job to run weekly maintenance:

```bash
# Add to crontab with: crontab -e
# Run system cleanup every Sunday at 2am
0 2 * * 0 /home/jamso-ai-server/Jamso-Ai-Engine/Tools/system_cleanup.sh >> /home/jamso-ai-server/Jamso-Ai-Engine/Logs/maintenance.log 2>&1
```

## Monitoring

The monitoring scripts provide insights into system performance:

- `./Tools/monitor_resources.py`: Tracks CPU, memory, and process usage
- `./run_with_monitoring.sh`: Runs the server with automatic resource monitoring

## Troubleshooting

If you encounter issues with the application:

1. Check the logs in the `Logs/` directory
2. Run `./Tools/system_cleanup.sh` to clear all caches
3. Restart the server with `./stop_local.sh` followed by `./run_local.sh`
4. If problems persist, check for Redis connection issues with `redis-cli ping`
