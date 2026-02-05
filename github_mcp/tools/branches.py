"""
Инструменты для работы с ветками и коммитами GitHub.

Этот модуль предоставляет MCP инструменты для:
- Управления ветками (создание, удаление, просмотр)
- Просмотра коммитов
- Сравнения веток
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient
from ..config import settings


def register_branch_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для работы с ветками."""

    @mcp.tool()
    async def list_branches(
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список веток репозитория текущего владельца.

        Args:
            repo: Название репозитория (опционально)
            per_page: Количество на странице (макс. 100)
            page: Номер страницы
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return [{"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}]

        branches = await client.list_branches(final_owner, final_repo, per_page, page)
        return [
            {
                "name": b.get("name"),
                "sha": b.get("commit", {}).get("sha"),
                "protected": b.get("protected"),
            }
            for b in branches
        ]

    @mcp.tool()
    async def get_branch(
        branch: str,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Получить информацию о ветке компании текущего владельца.

        Args:
            branch: Название ветки
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        result = await client.get_branch(final_owner, final_repo, branch)
        return {
            "name": result.get("name"),
            "sha": result.get("commit", {}).get("sha"),
            "protected": result.get("protected"),
            "commit_message": result.get("commit", {}).get("commit", {}).get("message"),
            "commit_author": result.get("commit", {}).get("commit", {}).get("author", {}).get("name"),
            "commit_date": result.get("commit", {}).get("commit", {}).get("author", {}).get("date"),
        }

    @mcp.tool()
    async def create_branch(
        branch_name: str,
        repo: Optional[str] = None,
        from_ref: str = "main",
    ) -> dict:
        """
        Создать новую ветку в репозитории текущего владельца.

        Args:
            branch_name: Название новой ветки
            repo: Название репозитория (опционально)
            from_ref: Исходная ветка или коммит (по умолчанию main)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        result = await client.create_branch(final_owner, final_repo, branch_name, from_ref)
        return {
            "status": "success",
            "ref": result.get("ref"),
            "sha": result.get("object", {}).get("sha"),
            "url": result.get("url"),
        }

    @mcp.tool()
    async def delete_branch(
        branch: str,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Удалить ветку в репозитории текущего владельца.

        ВНИМАНИЕ: Это действие необратимо!

        Args:
            branch: Название ветки для удаления
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        await client.delete_branch(final_owner, final_repo, branch)
        return {
            "status": "success",
            "message": f"Ветка {branch} удалена",
        }

    @mcp.tool()
    async def list_commits(
        repo: Optional[str] = None,
        sha: Optional[str] = None,
        path: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить историю коммитов в репозитории текущего владельца.

        Args:
            repo: Название репозитория (опционально)
            sha: Ветка или коммит для начала списка (опционально)
            path: Фильтр по пути файла (опционально)
            per_page: Количество на странице (макс. 100)
            page: Номер страницы
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return [{"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}]

        commits = await client.list_commits(final_owner, final_repo, sha, path, per_page, page)
        return [
            {
                "sha": c.get("sha"),
                "message": c.get("commit", {}).get("message", "").split("\n")[0],  # Первая строка
                "author": c.get("commit", {}).get("author", {}).get("name"),
                "date": c.get("commit", {}).get("author", {}).get("date"),
                "html_url": c.get("html_url"),
            }
            for c in commits
        ]

    @mcp.tool()
    async def get_commit(
        ref: str,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Получить информацию о коммите в репозитории текущего владельца.

        Args:
            ref: SHA коммита или ветка
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        result = await client.get_commit(final_owner, final_repo, ref)
        return {
            "sha": result.get("sha"),
            "message": result.get("commit", {}).get("message"),
            "author": result.get("commit", {}).get("author", {}).get("name"),
            "author_email": result.get("commit", {}).get("author", {}).get("email"),
            "date": result.get("commit", {}).get("author", {}).get("date"),
            "html_url": result.get("html_url"),
            "stats": result.get("stats"),
            "files_count": len(result.get("files", [])),
        }

    @mcp.tool()
    async def compare_branches(
        base: str,
        head: str,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Сравнить две ветки или коммита в репозитории текущего владельца.

        Args:
            base: Базовая ветка/коммит
            head: Сравниваемая ветка/коммит
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {"error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"}

        result = await client.compare_commits(final_owner, final_repo, base, head)
        return {
            "status": result.get("status"),
            "ahead_by": result.get("ahead_by"),
            "behind_by": result.get("behind_by"),
            "total_commits": result.get("total_commits"),
            "html_url": result.get("html_url"),
            "files_changed": len(result.get("files", [])),
            "commits": [
                {
                    "sha": c.get("sha")[:7],
                    "message": c.get("commit", {}).get("message", "").split("\n")[0],
                }
                for c in result.get("commits", [])[:10]  # Первые 10 коммитов
            ],
        }
