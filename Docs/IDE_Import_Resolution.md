# IDE Import Resolution Issues

This document provides solutions for IDE import resolution issues, particularly with Flask-WTF and other packages.

## Common Issues

### Flask-WTF Import Errors in VS Code

VS Code's Pylance language server may show errors like:
```
Import "flask_wtf.csrf" could not be resolved
```

This happens even when:
- The package is correctly installed
- The imports work when running Python scripts 
- The application functions correctly

## Solutions

### 1. Configure VS Code to Use the Correct Python Interpreter

Ensure VS Code is using the correct Python interpreter:

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type "Python: Select Interpreter"
3. Select the appropriate interpreter for your environment

### 2. Configure Path Mappings

To help VS Code find packages installed in non-standard locations:

1. Open `.vscode/settings.json`
2. Add the package paths to the `python.analysis.extraPaths` setting:

```json
{
  "python.analysis.extraPaths": [
    "/home/jamso-ai-server/.local/lib/python3.12/site-packages"
  ],
  "python.analysis.diagnosticSeverityOverrides": {
    "reportMissingImports": "information"
  }
}
```

### 3. Run the Diagnostic Tool

We provide a diagnostic tool that shows package paths and installation information:

```bash
python3 Tools/flask_wtf_diagnostic.py
```

This will help identify where packages are installed and diagnose any issues.

### 4. Environment-Specific Fixes

#### Using a Virtual Environment

If you're using a virtual environment, make sure VS Code is configured to use it:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

#### User-Level Installations

For packages installed at the user level with pip (using `pip install --user`):

```json
{
  "python.analysis.extraPaths": [
    "~/.local/lib/python3.12/site-packages"
  ]
}
```

## Development Best Practices

1. **Use Virtual Environments**: Create a dedicated virtual environment for each project
2. **Document Dependencies**: Keep requirements.txt up to date
3. **Use IDE Configuration Files**: Commit `.vscode/settings.json` to help team members

## Notes on External Python Management

In systems where Python is externally managed (like Debian/Ubuntu system Python), consider:

1. Using virtual environments
2. Using `pipx` for tool installation
3. Using user-level pip installs with `pip install --user`
