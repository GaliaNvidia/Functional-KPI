# Use Python 3.11 slim image for smaller size and better security
FROM dockerhub.nvidia.com/python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/database/software_quality.db

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    vim \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy application code
COPY . .

# Install Python dependencies using uv with pre-release flag
RUN uv pip install --system -e .

# Create database directory and set up the database with sample data
RUN mkdir -p /app/database && \
    mkdir -p /app/output_data && \
    python setup_database.py

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Expose port (NAT typically uses 8000)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/docs || exit 1

# Run the NAT application
CMD ["nat", "serve", "--config_file", "configs/config-prod.yaml", "--host", "0.0.0.0", "--port", "8000"]
