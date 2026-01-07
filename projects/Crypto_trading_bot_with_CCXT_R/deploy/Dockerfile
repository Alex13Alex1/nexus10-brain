# syntax=docker/dockerfile:1
# Crypto Trading Bot - Docker Container
# AI Factory v0.7 Nexus

# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final stage
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user for security
RUN useradd -m -u 1000 botuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/botuser/.local
ENV PATH=/home/botuser/.local/bin:$PATH

# Copy application code
COPY --chown=botuser:botuser . .

# Create logs directory
RUN mkdir -p /app/logs && chown botuser:botuser /app/logs

# Switch to non-root user
USER botuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Labels
LABEL maintainer="AI Factory v0.7 Nexus"
LABEL version="1.0"
LABEL description="Crypto Trading Bot with RSI + Bollinger Bands"

# Healthcheck - verify Python can import ccxt
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import ccxt; print('OK')" || exit 1

# Run the trading bot
CMD ["python", "main_fixed.py"]
