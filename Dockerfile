FROM python:3.11-slim

# Установка рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY . .

# Установка зависимостей
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -e .

# Открытие порта 8080 для HTTP-сервера
EXPOSE 8080

# Запуск HTTP-сервера по умолчанию
CMD ["python", "-m", "github_mcp.http_server", "--host", "0.0.0.0", "--port", "8080"]