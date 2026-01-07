FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY main.py /app/

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Healthcheck to ensure the application is running
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:5000/ || exit 1

# Command to run the application
CMD ["python", "main.py"]