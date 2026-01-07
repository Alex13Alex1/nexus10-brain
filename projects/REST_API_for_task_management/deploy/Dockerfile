FROM python:3.11-slim

# Установка зависимостей
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Команда для запуска приложения
CMD ["python", "main_fixed.py"]

# .dockerignore рекомендации
# Игнорируйте временные файлы, кэш pip и другие ненужные файлы
# __pycache__/
# *.pyc
# *.pyo
# .env
# .git
# .DS_Store
# *.egg-info/
# .pytest_cache/