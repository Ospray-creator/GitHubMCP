# Docker для GitHub MCP Server

## Подготовка

Перед сборкой Docker-образа убедитесь, что у вас есть файл `.env` с необходимыми настройками:

```env
# GitHub Configuration
GH_TOKEN=ghp_your_token_here
GH_DEFAULT_OWNER=your-username
GH_DEFAULT_REPO=your-repo
GH_ALLOWED_REPOS=your-username/*

# Server Security
MCP_API_KEY=your_secret_key_here

# Logging
LOG_LEVEL=INFO
```

## Сборка и запуск с помощью Docker

### 1. Сборка образа

```bash
docker build -t github-mcp .
```

### 2. Запуск контейнера

```bash
docker run -d \
  --name github-mcp \
  -p 8080:8080 \
  -e GH_TOKEN=ghp_your_token_here \
  -e GH_DEFAULT_OWNER=your_username \
  -e GH_DEFAULT_REPO=your_repo \
  -e GH_ALLOWED_REPOS=your_username/* \
  -e MCP_API_KEY=your_secret_key_here \
  github-mcp
```

## Сборка и запуск с помощью Docker Compose

### 1. Установка переменных окружения

Скопируйте `.env.example` в `.env` и укажите свои значения:

```bash
cp .env.example .env
# Отредактируйте .env файл
```

### 2. Запуск сервиса

```bash
docker-compose up -d
```

## Использование

После запуска сервер будет доступен по адресу:

- HTTP: `http://localhost:8080`
- MCP endpoint: `http://localhost:8080/mcp`

Для подключения к MCP-клиентам (Claude Desktop, Cursor, Windsurf) используйте следующую конфигурацию:

```json
{
  "mcpServers": {
    "github": {
      "uri": "http://localhost:8080/mcp",
      "headers": {
        "X-API-Key": "your_secret_key_here"
      }
    }
  }
}
```

## Проверка работоспособности

После запуска можно проверить, работает ли сервер:

```bash
curl -H "X-API-Key: your_secret_key_here" http://localhost:8080/mcp
```

## Остановка

Для остановки контейнера:

```bash
# При запуске через docker run
docker stop github-mcp

# При запуске через docker-compose
docker-compose down
```