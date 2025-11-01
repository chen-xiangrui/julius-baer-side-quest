# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
# Use host.docker.internal for Docker Desktop (Mac/Windows)
# For Linux, use --add-host=host.docker.internal:host-gateway when running
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BANKING_API_URL=http://host.docker.internal:8123

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY banking_client.py .
COPY api_client.py .
COPY config.py .
COPY models.py .
COPY services.py .
COPY config/ config/

# Create non-root user for security
RUN useradd -m -u 1000 bankinguser && \
    chown -R bankinguser:bankinguser /app

USER bankinguser

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
ENTRYPOINT ["python", "banking_client.py"]

# Default arguments (can be overridden)
CMD ["--from", "ACC1000", "--to", "ACC1001", "--amount", "100.00"]
