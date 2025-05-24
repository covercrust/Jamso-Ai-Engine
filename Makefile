.PHONY: run test lint format clean clean-logs restart install_deps help

# Help
help:
	@echo "Jamso AI Server Makefile Commands:"
	@echo "  make run            - Run the application locally for development"
	@echo "  make test           - Run tests with pytest"
	@echo "  make lint           - Run code quality checks (flake8, black)"
	@echo "  make format         - Format code with black and isort"
	@echo "  make clean          - Remove generated files and caches"
	@echo "  make clean-logs     - Rotate and clean up log files in Logs/"
	@echo "  make restart        - Restart the application (touch tmp/restart.txt)"
	@echo "  make install_deps   - Install Python dependencies from requirements.txt"

# Run the application locally
run:
	./run_local.sh

# Run tests
test:
	PYTHONPATH=src pytest

# Lint the code
lint:
	source .venv/bin/activate && flake8 src/ && black --check src/

# Format the code
format:
	source .venv/bin/activate && black src/ && isort src/

# Clean generated files
clean:
	./Scripts/Maintenance/cleanup_cache.sh

# Rotate and clean up log files
clean-logs:
	bash Tools/logrotate_logs.sh

# Restart the application
restart:
	touch tmp/restart.txt
	@echo "Restart signal sent"

# Install dependencies
install_deps:
	source .venv/bin/activate && pip install -r requirements.txt
