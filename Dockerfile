FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY app ./app

# Переменные окружения
ENV PYTHONPATH=/app
ENV BALANCE_REDIS_HOST=redis
ENV BALANCE_REDIS_PORT=6379

EXPOSE 8000

CMD ["faststream", "run", "app.main:app",]
