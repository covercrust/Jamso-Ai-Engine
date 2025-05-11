# Directory Structure Migration Guide

This document provides guidance on the migration from the old directory structure (`/Backend/`) to the new structure (`/src/`).

## Overview of Changes

The Jamso AI Engine codebase has been reorganized for better maintainability and clarity. The primary changes are:

1. The main code directory has been renamed from `/Backend/` to `/src/`
2. Database paths have been updated from `/Backend/Database/` to `/src/Database/`
3. Certain database files have been moved:
   - From: `/Database/Webhook/users.db`
   - To: `/Database/Users/users.db`

## Path References

If you're updating code that references paths, here's what you need to know:

### File and Module Imports

```python
# Old imports
from Backend.Webhook.app import flask_app
from Backend.Utils.rate_limiter import rate_limit

# New imports
from src.Webhook.app import flask_app
from src.Optional.rate_limiter import rate_limit
```

### Configuration Paths

```python
# Old paths
config_path = os.path.join(BASE_DIR, 'Backend', 'Utils', 'Config', 'active_account.json')
log_file_path = os.path.join(BASE_DIR, 'Backend', 'Logs', 'client.log')

# New paths
config_path = os.path.join(BASE_DIR, 'src', 'Credentials', 'active_account.json')
log_file_path = os.path.join(BASE_DIR, 'src', 'Logs', 'client.log')
```

### Environment Variables

```bash
# Old
export FLASK_APP="Backend.Webhook.app"

# New
export FLASK_APP="src.Webhook.app"
```

## Running the Application

```bash
# Old
python -m Backend.Webhook.app

# New
python -m src.Webhook.app
```

## Database Access

For code that accesses database files directly, update the paths:

```python
# Old
database_path = os.path.join(BASE_DIR, 'Backend', 'Database', 'Webhook', 'trading_signals.db')

# New
database_path = os.path.join(BASE_DIR, 'src', 'Database', 'Webhook', 'trading_signals.db')
```

## Logging Configuration

The logging configuration has been updated to use the new paths:

```python
# Old
loggers = {
    "Backend": {
        "level": "DEBUG",
        ...
    },
    "Backend.Webhook": {
        "level": "DEBUG",
        ...
    }
}

# New
loggers = {
    "src": {
        "level": "DEBUG",
        ...
    },
    "src.Webhook": {
        "level": "DEBUG",
        ...
    }
}
```

## Tests

All test files have been updated to use the new imports. If you add new tests, make sure to import from the `src` package:

```python
# Example test import
from src.Webhook.app import flask_app
```

## Troubleshooting

If you encounter issues with imports or file paths:

1. Check that you're using `src.` instead of `Backend.` in imports
2. Verify file paths in any code that accesses files directly
3. Make sure environment variables are updated in your deployment scripts
4. Check for hardcoded references to the old directory structure

For further assistance, contact the development team.
