"""
GitHub MCP Server — полный контроль GitHub через Model Context Protocol.

Этот пакет предоставляет MCP сервер с 45+ инструментами для работы с GitHub API:
- Репозитории: создание, удаление, форки
- Файлы: чтение, создание, обновление, удаление
- Ветки: управление ветками и коммитами
- Issues: полное управление с метками и комментариями
- Pull Requests: создание, мерж, ревью
- GitHub Actions: запуск/отмена workflows
- Пользователи и Gists
"""

__version__ = "1.0.0"
__author__ = "Ospray-creator"

from .client import GitHubClient
from .config import settings

__all__ = ["settings", "GitHubClient", "__version__"]
