"""
GitHub MCP Server — главный модуль сервера.

Этот модуль создаёт MCP сервер на базе FastMCP с регистрацией
всех инструментов для полного контроля GitHub.
"""

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .client import GitHubClient
from .config import settings
from .tools import (
    register_action_tools,
    register_branch_tools,
    register_file_tools,
    register_gist_tools,
    register_issue_tools,
    register_pr_tools,
    register_repository_tools,
    register_search_tools,
    register_user_tools,
)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """
    Управление жизненным циклом сервера.
    """
    logger.info("Запуск GitHub MCP Server...")

    if not settings.gh_token:
        logger.warning("GH_TOKEN не установлен!")

    # Используем глобальный клиент или создаем новый для проверки
    client = GitHubClient()
    try:
        user = await client.get_authenticated_user()
        logger.info(f"Авторизован как: {user.get('login')} ✓")
    except Exception as e:
        logger.warning(f"Не удалось проверить авторизацию: {e}")

    try:
        yield {"client": client}
    finally:
        await client.close()
        logger.info("GitHub MCP Server остановлен")


# Создаём MCP сервер
mcp = FastMCP(
    name=settings.server_name,
    lifespan=lifespan,
    stateless_http=True,  # Рекомендуется для HTTP/Web клиентов
    json_response=True,  # Рекомендуется для HTTP/Web клиентов
    # НАСТРОЙКИ БЕЗОПАСНОСТИ: Разрешаем всё для локальной сети
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
        allowed_hosts=["*"],
        allowed_origins=["*"],
    ),
)

# Инициализируем клиент для инструментов
_client = GitHubClient()

# Регистрируем все инструменты
register_repository_tools(mcp, _client)
register_file_tools(mcp, _client)
register_branch_tools(mcp, _client)
register_issue_tools(mcp, _client)
register_pr_tools(mcp, _client)
register_action_tools(mcp, _client)
register_user_tools(mcp, _client)
register_gist_tools(mcp, _client)
register_search_tools(mcp, _client)


@mcp.resource("github://user")
async def get_current_user_resource() -> str:
    """Информация о пользователе."""
    user = await _client.get_authenticated_user()
    return f"# GitHub User: {user.get('login')}\nURL: {user.get('html_url')}"


def main() -> None:
    """Запуск сервера в режиме stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
