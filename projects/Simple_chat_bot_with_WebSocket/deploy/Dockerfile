# Используем базовый образ python:3.11-slim для уменьшения размера
FROM python:3.11-slim AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем непривилегированного пользователя для безопасности
RUN useradd -m nonrootuser

# Копируем исходный код приложения
COPY . .

# Переходим на финальный этап сборки
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем установленные зависимости из предыдущего этапа
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код приложения
COPY --from=builder /app /app

# Переключаемся на непривилегированного пользователя
USER nonrootuser

# Устанавливаем команду запуска
CMD ["python", "app.py"]

# Добавляем health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8765/health || exit 1

# Добавляем метаданные
LABEL maintainer="Your Name <your.email@example.com>"
LABEL version="1.0"
LABEL description="A simple WebSocket chat bot application"
