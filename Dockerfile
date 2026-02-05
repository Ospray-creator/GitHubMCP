FROM python:3.11-slim

# Установка рабочей директории
WORKDIR /app

# Сначала копируем только файл с зависимостями для кэширования
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование остального кода
COPY . .

# Установка самого пакета
RUN pip install --no-cache-dir -e .

# Открытие порта 8080 для HTTP-сервера
EXPOSE 8080

# Запуск HTTP-сервера по умолчанию
CMD ["python", "-m", "github_mcp.http_server", "--host", "0.0.0.0", "--port", "8080"]