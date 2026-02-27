# Dockerfile for Sentient-Grid Streaming Backend
# Builds a container that runs the grid simulation and publishes to Kafka/MQTT

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for security
RUN useradd -m -u 1000 griduser && chown -R griduser:griduser /app
USER griduser

# Expose any monitoring ports if needed
# EXPOSE 8080

# Default entrypoint: run the backend
ENTRYPOINT ["python", "stream_backend.py"]

# Default arguments (can be overridden with `docker run`)
CMD []
