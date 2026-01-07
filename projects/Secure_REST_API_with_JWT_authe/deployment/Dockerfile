FROM python:3.11-slim

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Healthcheck to ensure the application is running
HEALTHCHECK CMD curl --fail http://localhost:5000/protected || exit 1

# Command to run the application
CMD ["python", "main.py"]