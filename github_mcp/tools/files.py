"""
Инструменты для работы с файлами в репозиториях GitHub.

Этот модуль предоставляет MCP инструменты для:
- Чтения содержимого файлов и директорий
- Создания, обновления и удаления файлов
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient
from ..config import settings


def register_file_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для работы с файлами."""

    @mcp.tool()
    async def get_file_content(
        path: str,
        repo: Optional[str] = None,
        ref: Optional[str] = None,
    ) -> dict:
        """
        Получить содержимое файла из репозитория текущего владельца.

        Args:
            path: Путь к файлу в репозитории
            repo: Название репозитория (опционально)
            ref: Ветка или коммит (опционально, по умолчанию — основная ветка)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        result = await client.get_contents(final_owner, final_repo, path, ref)

        if isinstance(result, list):
            return {"error": f"Путь {path} — это директория, используйте get_directory_content"}

        return {
            "name": result.get("name"),
            "path": result.get("path"),
            "sha": result.get("sha"),
            "size": result.get("size"),
            "encoding": result.get("encoding"),
            "content": result.get("content"),
            "html_url": result.get("html_url"),
            "download_url": result.get("download_url"),
        }

    @mcp.tool()
    async def get_directory_content(
        path: str = "",
        repo: Optional[str] = None,
        ref: Optional[str] = None,
    ) -> list[dict]:
        """
        Получить содержимое директории репозитория текущего владельца.

        Args:
            path: Путь к директории (пустая строка для корня)
            repo: Название репозитория (опционально)
            ref: Ветка или коммит (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return [{"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}]

        result = await client.get_contents(final_owner, final_repo, path, ref)

        if isinstance(result, dict):
            return [
                {
                    "error": f"Путь {path} — это файл, используйте get_file_content",
                    "name": result.get("name"),
                }
            ]

        return [
            {
                "name": item.get("name"),
                "path": item.get("path"),
                "type": item.get("type"),
                "size": item.get("size"),
                "sha": item.get("sha"),
                "html_url": item.get("html_url"),
            }
            for item in result
        ]

    @mcp.tool()
    async def create_file(
        path: str,
        content: str,
        message: str,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> dict:
        """
        Создать новый файл в репозитории текущего владельца.

        Args:
            path: Путь к новому файлу
            content: Содержимое файла
            message: Сообщение коммита
            repo: Название репозитория (опционально)
            branch: Ветка (опционально, по умолчанию — основная)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        result = await client.create_file(
            final_owner, final_repo, path, content, message, branch
        )

        return {
            "status": "success",
            "path": result.get("content", {}).get("path"),
            "sha": result.get("content", {}).get("sha"),
            "html_url": result.get("content", {}).get("html_url"),
            "commit_sha": result.get("commit", {}).get("sha"),
            "commit_message": result.get("commit", {}).get("message"),
        }

    @mcp.tool()
    async def update_file(
        path: str,
        content: str,
        message: str,
        sha: str,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> dict:
        """
        Обновить существующий файл в репозитории текущего владельца.

        Args:
            path: Путь к файлу
            content: Новое содержимое файла
            message: Сообщение коммита
            sha: SHA текущего файла (получить через get_file_content)
            repo: Название репозитория (опционально)
            branch: Ветка (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        result = await client.update_file(
            final_owner, final_repo, path, content, message, sha, branch
        )

        return {
            "status": "success",
            "path": result.get("content", {}).get("path"),
            "sha": result.get("content", {}).get("sha"),
            "html_url": result.get("content", {}).get("html_url"),
            "commit_sha": result.get("commit", {}).get("sha"),
            "commit_message": result.get("commit", {}).get("message"),
        }

    @mcp.tool()
    async def delete_file(
        path: str,
        message: str,
        sha: str,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> dict:
        """
        Удалить файл из репозитория текущего владельца.

        Args:
            path: Путь к файлу
            message: Сообщение коммита
            sha: SHA файла для удаления (получить через get_file_content)
            repo: Название репозитория (опционально)
            branch: Ветка (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        result = await client.delete_file(
            final_owner, final_repo, path, message, sha, branch
        )

        return {
            "status": "success",
            "message": f"Файл {path} удалён",
            "commit_sha": result.get("commit", {}).get("sha"),
        }
