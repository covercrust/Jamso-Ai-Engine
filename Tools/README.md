# Jamso AI Engine Maintenance Tools

This directory contains various tools for maintaining and optimizing the Jamso AI Engine application.

## System Maintenance Scripts

| Script | Purpose |
|--------|---------|
| `system_cleanup.sh` | Comprehensive system cleanup (runs all cleanup scripts) |
| `cleanup_cache.sh` | Cleans Python cache files and temporary files |
| `cleanup_redis.sh` | Cleans Redis cache |
| `cleanup_sessions.py` | Cleans expired user sessions |
| `fix_permissions.sh` | Fixes file permissions |
| `health_check.sh` | Performs system health check |

## Monitoring Tools

| Script | Purpose |
|--------|---------|
| `monitor_resources.py` | Monitors system resources (CPU, memory) |
| `memory_monitor.py` | Focused memory monitoring |

## Performance Optimization

| Script | Purpose |
|--------|---------|
| `memory_optimizer.py` | Optimizes memory usage |
| `flask_memory_optimizer.py` | Optimizes Flask memory usage |
| `optimize_db.py` | Optimizes database performance |

## Usage

Most scripts can be run directly from the Jamso AI Engine root directory:

```bash
# For system cleanup
./Tools/system_cleanup.sh

# For health check
./Tools/health_check.sh

# For monitoring
./Tools/monitor_resources.py
```

See the `Docs/Maintenance_Guide.md` file for detailed instructions on when and how to use these tools.

## Best Practices

1. **Regular Maintenance**: Run `system_cleanup.sh` weekly
2. **Before Deployment**: Always run cleanup before deploying new code
3. **After Errors**: Run `health_check.sh` to diagnose issues
4. **Performance Issues**: Use monitoring tools to identify bottlenecks

## Adding New Tools

When adding new maintenance tools:

1. Place the script in this directory
2. Make it executable with `chmod +x script_name.sh`
3. Document it in this README and in `Docs/Maintenance_Guide.md`
4. Include appropriate error handling and logging
