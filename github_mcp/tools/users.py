"""
Инструменты для работы с пользователями GitHub.

Этот модуль предоставляет MCP инструменты для:
- Получения информации о пользователях
- Просмотра подписчиков и подписок
- Работы с организациями
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient


def register_user_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для работы с пользователями."""

    @mcp.tool()
    async def get_authenticated_user() -> dict:
        """
        Получить информацию о текущем авторизованном пользователе.

        Возвращает данные пользователя, связанного с токеном GitHub.
        """
        result = await client.get_authenticated_user()
        return {
            "login": result.get("login"),
            "name": result.get("name"),
            "email": result.get("email"),
            "bio": result.get("bio"),
            "html_url": result.get("html_url"),
            "avatar_url": result.get("avatar_url"),
            "company": result.get("company"),
            "location": result.get("location"),
            "public_repos": result.get("public_repos"),
            "public_gists": result.get("public_gists"),
            "followers": result.get("followers"),
            "following": result.get("following"),
            "created_at": result.get("created_at"),
        }

    @mcp.tool()
    async def get_user(username: str) -> dict:
        """
        Получить информацию о пользователе по username.

        Args:
            username: Имя пользователя GitHub
        """
        result = await client.get_user(username)
        return {
            "login": result.get("login"),
            "name": result.get("name"),
            "bio": result.get("bio"),
            "html_url": result.get("html_url"),
            "avatar_url": result.get("avatar_url"),
            "company": result.get("company"),
            "location": result.get("location"),
            "blog": result.get("blog"),
            "public_repos": result.get("public_repos"),
            "public_gists": result.get("public_gists"),
            "followers": result.get("followers"),
            "following": result.get("following"),
            "created_at": result.get("created_at"),
        }

    @mcp.tool()
    async def list_followers(
        username: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список подписчиков пользователя.

        Args:
            username: Имя пользователя (если не указано — текущий)
            per_page: Количество на странице (макс. 100)
            page: Номер страницы
        """
        followers = await client.list_followers(username, per_page, page)
        return [
            {
                "login": f.get("login"),
                "html_url": f.get("html_url"),
                "avatar_url": f.get("avatar_url"),
            }
            for f in followers
        ]

    @mcp.tool()
    async def list_following(
        username: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список подписок пользователя.

        Args:
            username: Имя пользователя (если не указано — текущий)
            per_page: Количество на странице (макс. 100)
            page: Номер страницы
        """
        following = await client.list_following(username, per_page, page)
        return [
            {
                "login": f.get("login"),
                "html_url": f.get("html_url"),
                "avatar_url": f.get("avatar_url"),
            }
            for f in following
        ]

    @mcp.tool()
    async def list_user_organizations(
        username: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список организаций пользователя.

        Args:
            username: Имя пользователя (если не указано — текущий)
            per_page: Количество на странице (макс. 100)
            page: Номер страницы
        """
        orgs = await client.list_user_orgs(username, per_page, page)
        return [
            {
                "login": o.get("login"),
                "description": o.get("description"),
                "html_url": f"https://github.com/{o.get('login')}",
                "avatar_url": o.get("avatar_url"),
            }
            for o in orgs
        ]
