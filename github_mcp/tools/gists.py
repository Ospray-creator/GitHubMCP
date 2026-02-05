"""
Инструменты для работы с Gists в GitHub.

Этот модуль предоставляет MCP инструменты для:
- Создания, чтения, обновления и удаления Gists
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient


def register_gist_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для работы с Gists."""

    @mcp.tool()
    async def list_gists(
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список Gists текущего пользователя.

        Args:
            per_page: Количество на странице (макс. 100)
            page: Номер страницы
        """
        #username=None означает текущего пользователя
        gists = await client.list_gists(None, per_page, page)
        return [
            {
                "id": g.get("id"),
                "description": g.get("description"),
                "html_url": g.get("html_url"),
                "public": g.get("public"),
                "files": list(g.get("files", {}).keys()),
                "comments": g.get("comments"),
                "created_at": g.get("created_at"),
                "updated_at": g.get("updated_at"),
            }
            for g in gists
        ]

    @mcp.tool()
    async def get_gist(gist_id: str) -> dict:
        """
        Получить Gist по ID.

        Args:
            gist_id: ID Gist
        """
        result = await client.get_gist(gist_id)

        files = {}
        for filename, file_data in result.get("files", {}).items():
            files[filename] = {
                "filename": file_data.get("filename"),
                "type": file_data.get("type"),
                "language": file_data.get("language"),
                "size": file_data.get("size"),
                "content": file_data.get("content"),
            }

        return {
            "id": result.get("id"),
            "description": result.get("description"),
            "html_url": result.get("html_url"),
            "public": result.get("public"),
            "files": files,
            "owner": result.get("owner", {}).get("login"),
            "comments": result.get("comments"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
        }

    @mcp.tool()
    async def create_gist(
        filename: str,
        content: str,
        description: str = "",
        public: bool = False,
    ) -> dict:
        """
        Создать новый Gist.

        Args:
            filename: Имя файла
            content: Содержимое файла
            description: Описание Gist
            public: Публичный (True) или секретный (False)
        """
        files = {filename: {"content": content}}
        result = await client.create_gist(files, description, public)
        return {
            "status": "success",
            "id": result.get("id"),
            "html_url": result.get("html_url"),
            "public": result.get("public"),
        }

    @mcp.tool()
    async def create_multi_file_gist(
        files_json: str,
        description: str = "",
        public: bool = False,
    ) -> dict:
        """
        Создать Gist с несколькими файлами.

        Args:
            files_json: JSON объект с файлами в формате {"filename": {"content": "..."}}
            description: Описание Gist
            public: Публичный (True) или секретный (False)
        """
        import json

        try:
            files = json.loads(files_json)
        except json.JSONDecodeError:
            return {"error": "Некорректный JSON в параметре files_json"}

        result = await client.create_gist(files, description, public)
        return {
            "status": "success",
            "id": result.get("id"),
            "html_url": result.get("html_url"),
            "public": result.get("public"),
            "files": list(result.get("files", {}).keys()),
        }

    @mcp.tool()
    async def update_gist(
        gist_id: str,
        filename: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """
        Обновить Gist.

        Args:
            gist_id: ID Gist
            filename: Имя файла для обновления (опционально)
            content: Новое содержимое файла (опционально)
            description: Новое описание (опционально)
        """
        files = None
        if filename and content:
            files = {filename: {"content": content}}

        result = await client.update_gist(gist_id, files, description)
        return {
            "status": "success",
            "id": result.get("id"),
            "html_url": result.get("html_url"),
            "files": list(result.get("files", {}).keys()),
        }

    @mcp.tool()
    async def delete_gist(gist_id: str) -> dict:
        """
        Удалить Gist.

        ВНИМАНИЕ: Это действие необратимо!

        Args:
            gist_id: ID Gist
        """
        await client.delete_gist(gist_id)
        return {
            "status": "success",
            "message": f"Gist {gist_id} удалён",
        }
