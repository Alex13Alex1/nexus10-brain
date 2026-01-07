FROM python:3.11-slim AS builder

WORKDIR /app

COPY . .

RUN useradd -m appuser

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app /app

RUN pip install --no-cache-dir .

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD python -c "import sys; sys.exit(0)"

LABEL maintainer="Your Name <your.email@example.com>" \
      version="1.0" \
      description="A simple calculator CLI application."

ENTRYPOINT ["python", "calculator.py"]