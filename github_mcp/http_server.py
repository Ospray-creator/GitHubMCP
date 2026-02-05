"""
HTTP транспорт для GitHub MCP Server с аутентификацией.
"""

import argparse
import uvicorn
import contextlib
import logging
import sys
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse

from .server import mcp
from .config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

class AuthMiddleware:
    """
    Middleware для проверки API Key.
    Поддерживает заголовок X-API-Key и Authorization: Bearer <key>.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Если API Key не настроен — пропускаем всех
        if not settings.mcp_api_key:
            await self.app(scope, receive, send)
            return

        # Извлекаем заголовки
        headers = dict(scope.get("headers", []))
        
        # Проверяем X-API-Key
        api_key = headers.get(b"x-api-key", b"").decode()
        
        # Проверяем Authorization: Bearer
        auth_header = headers.get(b"authorization", b"").decode()
        if not api_key and auth_header.startswith("Bearer "):
            api_key = auth_header[7:]

        if api_key != settings.mcp_api_key:
            logger.warning(f"Unauthorized access attempt from {scope.get('client')}")
            response = JSONResponse(
                {"detail": "Unauthorized: Invalid API Key"}, 
                status_code=401
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

class ForceSSEMiddleware:
    """
    Middleware для форсирования заголовка 'Accept: text/event-stream'.
    Исправляет ошибку '406 Not Acceptable' для клиентов, которые не отправляют этот заголовок.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and scope["path"].endswith("/mcp") and scope["method"] == "GET":
            new_headers = []
            has_accept = False
            for k, v in scope["headers"]:
                if k.lower() == b"accept":
                    new_headers.append((k, b"text/event-stream"))
                    has_accept = True
                else:
                    new_headers.append((k, v))
            if not has_accept:
                new_headers.append((b"accept", b"text/event-stream"))
            scope["headers"] = new_headers
        await self.app(scope, receive, send)

@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    """Жизненный цикл для инициализации сессий."""
    logger.info("Инициализация менеджера сессий MCP...")
    async with mcp.session_manager.run():
        yield
    logger.info("Менеджер сессий MCP остановлен.")

def create_app() -> Starlette:
    app = Starlette(
        routes=[
            Mount("/", app=mcp.streamable_http_app()),
        ],
        lifespan=lifespan,
    )

    # 1. Прослойка аутентификации (проверяется первой)
    app.add_middleware(AuthMiddleware)

    # 2. Форсируем SSE заголовок
    app.add_middleware(ForceSSEMiddleware)

    # 3. Стандартный CORS для MCP
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )

    return app

def main():
    parser = argparse.ArgumentParser(description="GitHub MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Хост")
    parser.add_argument("--port", type=int, default=8080, help="Порт")

    args = parser.parse_args()

    app = create_app()

    logger.info(f"🚀 Запуск GitHub MCP HTTP Server на http://{args.host}:{args.port}")
    if settings.mcp_api_key:
        logger.info(f"🔐 Аутентификация включена (API Key настроен)")
    else:
        logger.info(f"⚠️ Аутентификация выключена (MCP_API_KEY не задан)")
    
    logger.info(f"📍 Эндпоинт для OpenWebUI: http://192.168.1.10:{args.port}/mcp")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )

if __name__ == "__main__":
    main()
