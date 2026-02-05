"""
Инструменты для работы с репозиториями GitHub.

Этот модуль предоставляет MCP инструменты для:
- Получения информации о репозитории
- Создания и удаления репозиториев
- Работы с форками
- Получения списка контрибьюторов и языков
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient
from ..config import settings


def register_repository_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для работы с репозиториями."""

    @mcp.tool()
    async def set_default_repo(repo: str) -> dict:
        """
        Установить репозиторий по умолчанию для текущего владельца.

        Это позволяет не указывать repo в каждом запросе.

        Args:
            repo: Название репозитория
        """
        # Используем владельца по умолчанию из настроек
        owner = settings.gh_default_owner
        settings.set_default_repo(owner, repo)
        return {
            "status": "success",
            "message": f"Репозиторий по умолчанию установлен: {owner}/{repo}",
            "owner": owner,
            "repo": repo,
        }

    @mcp.tool()
    async def get_repository(
        repo: Optional[str] = None,
    ) -> dict:
        """
        Получить информацию о репозитории (для владельца по умолчанию).

        Args:
            repo: Название репозитория (опционально, если установлен по умолчанию)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.get_repository(final_owner, final_repo)
        return {
            "name": result.get("name"),
            "full_name": result.get("full_name"),
            "description": result.get("description"),
            "html_url": result.get("html_url"),
            "clone_url": result.get("clone_url"),
            "private": result.get("private"),
            "fork": result.get("fork"),
            "archived": result.get("archived"),
            "default_branch": result.get("default_branch"),
            "language": result.get("language"),
            "stargazers_count": result.get("stargazers_count"),
            "forks_count": result.get("forks_count"),
            "watchers_count": result.get("watchers_count"),
            "open_issues_count": result.get("open_issues_count"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "pushed_at": result.get("pushed_at"),
        }

    @mcp.tool()
    async def list_user_repos(
        type: str = "all",
        sort: str = "updated",
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список репозиториев текущего пользователя.

        Args:
            type: Тип репозиториев (all, owner, member)
            sort: Сортировка (created, updated, pushed, full_name)
            per_page: Количество на странице (макс. 100)
            page: Номер страницы
        """
        # Всегда список репозиториев для текущего пользователя (None в username означает /user/repos)
        repos = await client.list_user_repos(None, type, sort, per_page, page)
        return [
            {
                "name": r.get("name"),
                "full_name": r.get("full_name"),
                "description": r.get("description"),
                "html_url": r.get("html_url"),
                "private": r.get("private"),
                "fork": r.get("fork"),
                "stargazers_count": r.get("stargazers_count"),
                "language": r.get("language"),
                "updated_at": r.get("updated_at"),
            }
            for r in repos
        ]

    @mcp.tool()
    async def create_repository(
        name: str,
        description: str = "",
        private: bool = False,
        auto_init: bool = True,
    ) -> dict:
        """
        Создать новый репозиторий у текущего пользователя.

        Args:
            name: Название репозитория
            description: Описание репозитория
            private: Приватный репозиторий (default: False)
            auto_init: Инициализировать с README (default: True)
        """
        result = await client.create_repository(
            name, description, private, auto_init, None
        )
        return {
            "status": "success",
            "name": result.get("name"),
            "full_name": result.get("full_name"),
            "html_url": result.get("html_url"),
            "clone_url": result.get("clone_url"),
            "private": result.get("private"),
        }

    @mcp.tool()
    async def delete_repository(
        repo: Optional[str] = None,
    ) -> dict:
        """
        Удалить репозиторий текущего владельца.

        ВНИМАНИЕ: Это действие необратимо!

        Args:
            repo: Название репозитория
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        await client.delete_repository(final_owner, final_repo)
        return {
            "status": "success",
            "message": f"Репозиторий {final_owner}/{final_repo} удалён",
        }

    @mcp.tool()
    async def fork_repository(
        source_owner: str,
        source_repo: str,
        name: Optional[str] = None,
    ) -> dict:
        """
        Форкнуть чужой репозиторий к себе (текущему пользователю).

        Args:
            source_owner: Владелец исходного репозитория
            source_repo: Название исходного репозитория
            name: Новое имя форка (опционально)
        """
        # Форк всегда идет к текущему пользователю, если не указана организация
        result = await client.fork_repository(source_owner, source_repo, None, name)
        return {
            "status": "success",
            "name": result.get("name"),
            "full_name": result.get("full_name"),
            "html_url": result.get("html_url"),
            "clone_url": result.get("clone_url"),
        }

    @mcp.tool()
    async def list_forks(
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список форков репозитория текущего владельца.

        Args:
            repo: Название репозитория
            per_page: Количество на странице
            page: Номер страницы
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return [
                {
                    "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
                }
            ]

        forks = await client.list_forks(final_owner, final_repo, per_page, page)
        return [
            {
                "full_name": f.get("full_name"),
                "owner": f.get("owner", {}).get("login"),
                "html_url": f.get("html_url"),
                "created_at": f.get("created_at"),
            }
            for f in forks
        ]

    @mcp.tool()
    async def list_contributors(
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список контрибьюторов репозитория текущего владельца.

        Args:
            repo: Название репозитория
            per_page: Количество на странице
            page: Номер страницы
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return [
                {
                    "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
                }
            ]

        contributors = await client.list_contributors(
            final_owner, final_repo, per_page, page
        )
        return [
            {
                "login": c.get("login"),
                "avatar_url": c.get("avatar_url"),
                "html_url": c.get("html_url"),
                "contributions": c.get("contributions"),
            }
            for c in contributors
        ]

    @mcp.tool()
    async def list_languages(
        repo: Optional[str] = None,
    ) -> dict:
        """
        Получить статистику языков программирования в репозитории текущего владельца.

        Args:
            repo: Название репозитория
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        return await client.list_languages(final_owner, final_repo)
