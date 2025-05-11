# Use Python 3.12 slim image for better compatibility
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including PostgreSQL client and development libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt ./
# Create a temporary requirements file without gevent and greenlet
RUN grep -v "gevent\|greenlet" requirements.txt > requirements_no_gevent.txt && \
    pip install --no-cache-dir -r requirements_no_gevent.txt && \
    # Install alternatives to gevent
    pip install --no-cache-dir uvicorn==0.28.0 eventlet==0.35.0

# Copy the entire application into the container
COPY . .

# Add the current directory to PYTHONPATH so modules can be found
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Expose the port the app runs on
EXPOSE 5000

# Set the default command to run the application
CMD ["python", "Dashboard/app.py"]
