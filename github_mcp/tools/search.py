"""
Инструменты для поиска в GitHub.

Этот модуль предоставляет MCP инструменты для:
- Поиска по коду
- Поиска репозиториев
- Поиска issues и PR
"""

from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient


def register_search_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для поиска."""

    @mcp.tool()
    async def search_code(
        query: str,
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """
        Поиск по коду в GitHub.

        Примеры запросов:
        - "addClass in:file language:js" — искать addClass в JS файлах
        - "user:defunkt extension:rb" — искать в репозиториях defunkt с расширением .rb
        - "repo:owner/repo filename:config" — искать в конкретном репозитории

        Args:
            query: Поисковый запрос (синтаксис GitHub Search)
            per_page: Количество результатов (макс. 100)
            page: Номер страницы
        """
        result = await client.search_code(query, per_page, page)
        items = result.get("items", [])
        return {
            "total_count": result.get("total_count"),
            "items": [
                {
                    "name": i.get("name"),
                    "path": i.get("path"),
                    "repository": i.get("repository", {}).get("full_name"),
                    "html_url": i.get("html_url"),
                    "sha": i.get("sha"),
                }
                for i in items
            ],
        }

    @mcp.tool()
    async def search_repositories(
        query: str,
        sort: str = "stars",
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """
        Поиск репозиториев в GitHub.

        Примеры запросов:
        - "tetris language:python" — репозитории Tetris на Python
        - "stars:>1000 language:go" — популярные Go репозитории
        - "topic:machine-learning" — репозитории по теме ML

        Args:
            query: Поисковый запрос (синтаксис GitHub Search)
            sort: Сортировка (stars, forks, help-wanted-issues, updated)
            per_page: Количество результатов (макс. 100)
            page: Номер страницы
        """
        result = await client.search_repositories(query, sort, per_page, page)
        items = result.get("items", [])
        return {
            "total_count": result.get("total_count"),
            "items": [
                {
                    "full_name": i.get("full_name"),
                    "description": i.get("description"),
                    "html_url": i.get("html_url"),
                    "stargazers_count": i.get("stargazers_count"),
                    "forks_count": i.get("forks_count"),
                    "language": i.get("language"),
                    "updated_at": i.get("updated_at"),
                }
                for i in items
            ],
        }

    @mcp.tool()
    async def search_issues(
        query: str,
        sort: str = "created",
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """
        Поиск issues и Pull Requests в GitHub.

        Примеры запросов:
        - "is:issue is:open label:bug" — открытые баги
        - "is:pr is:merged author:username" — мёрженные PR от пользователя
        - "repo:owner/repo is:issue" — issues в конкретном репозитории

        Args:
            query: Поисковый запрос (синтаксис GitHub Search)
            sort: Сортировка (created, updated, comments)
            per_page: Количество результатов (макс. 100)
            page: Номер страницы
        """
        result = await client.search_issues(query, sort, per_page, page)
        items = result.get("items", [])
        return {
            "total_count": result.get("total_count"),
            "items": [
                {
                    "number": i.get("number"),
                    "title": i.get("title"),
                    "state": i.get("state"),
                    "html_url": i.get("html_url"),
                    "repository_url": i.get("repository_url"),
                    "author": i.get("user", {}).get("login"),
                    "labels": [label.get("name") for label in i.get("labels", [])],
                    "created_at": i.get("created_at"),
                    "is_pull_request": "pull_request" in i,
                }
                for i in items
            ],
        }
