FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /app/

RUN useradd -ms /bin/bash appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD python main.py "1+1" || exit 1

ENTRYPOINT ["python", "main.py"]