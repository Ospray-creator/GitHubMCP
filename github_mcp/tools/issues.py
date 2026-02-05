"""
Инструменты для работы с Issues в GitHub.

Этот модуль предоставляет MCP инструменты для:
- Создания, редактирования и закрытия issues
- Управления метками и назначениями
- Работы с комментариями
"""


from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient
from ..config import settings


def register_issue_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для работы с issues."""

    @mcp.tool()
    async def list_issues(
        repo: str | None = None,
        state: str = "open",
        labels: str | None = None,
        assignee: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список issues репозитория текущего владельца.

        Args:
            repo: Название репозитория (опционально)
            state: Состояние (open, closed, all)
            labels: Фильтр по меткам (через запятую)
            assignee: Фильтр по исполнителю
            per_page: Количество на странице (макс. 100)
            page: Номер страницы
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return [
                {
                    "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
                }
            ]

        issues = await client.list_issues(
            final_owner, final_repo, state, labels, assignee, per_page, page
        )
        return [
            {
                "number": i.get("number"),
                "title": i.get("title"),
                "state": i.get("state"),
                "html_url": i.get("html_url"),
                "author": i.get("user", {}).get("login"),
                "labels": [label.get("name") for label in i.get("labels", [])],
                "assignees": [a.get("login") for a in i.get("assignees", [])],
                "comments": i.get("comments"),
                "created_at": i.get("created_at"),
                "updated_at": i.get("updated_at"),
            }
            for i in issues
            if not i.get("pull_request")  # Исключаем PR (они тоже в issues API)
        ]

    @mcp.tool()
    async def get_issue(
        issue_number: int,
        repo: str | None = None,
    ) -> dict:
        """
        Получить информацию об issue в репозитории текущего владельца.

        Args:
            issue_number: Номер issue
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.get_issue(final_owner, final_repo, issue_number)
        return {
            "number": result.get("number"),
            "title": result.get("title"),
            "body": result.get("body"),
            "state": result.get("state"),
            "html_url": result.get("html_url"),
            "author": result.get("user", {}).get("login"),
            "labels": [label.get("name") for label in result.get("labels", [])],
            "assignees": [a.get("login") for a in result.get("assignees", [])],
            "milestone": (
                result.get("milestone", {}).get("title")
                if result.get("milestone")
                else None
            ),
            "comments": result.get("comments"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "closed_at": result.get("closed_at"),
        }

    @mcp.tool()
    async def create_issue(
        title: str,
        repo: str | None = None,
        body: str = "",
        labels: str | None = None,
        assignees: str | None = None,
    ) -> dict:
        """
        Создать новый issue в репозитории текущего владельца.

        Args:
            title: Заголовок issue
            repo: Название репозитория (опционально)
            body: Описание issue (поддерживает Markdown)
            labels: Метки через запятую (опционально)
            assignees: Исполнители через запятую (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        labels_list = [label.strip() for label in labels.split(",")] if labels else None
        assignees_list = (
            [a.strip() for a in assignees.split(",")] if assignees else None
        )

        result = await client.create_issue(
            final_owner, final_repo, title, body, labels_list, assignees_list
        )
        return {
            "status": "success",
            "number": result.get("number"),
            "title": result.get("title"),
            "html_url": result.get("html_url"),
        }

    @mcp.tool()
    async def update_issue(
        issue_number: int,
        repo: str | None = None,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        labels: str | None = None,
        assignees: str | None = None,
    ) -> dict:
        """
        Обновить issue в репозитории текущего владельца.

        Args:
            issue_number: Номер issue
            repo: Название репозитория (опционально)
            title: Новый заголовок (опционально)
            body: Новое описание (опционально)
            state: Новое состояние (open/closed) (опционально)
            labels: Новые метки через запятую (опционально)
            assignees: Новые исполнители через запятую (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        labels_list = [label.strip() for label in labels.split(",")] if labels else None
        assignees_list = (
            [a.strip() for a in assignees.split(",")] if assignees else None
        )

        result = await client.update_issue(
            final_owner,
            final_repo,
            issue_number,
            title,
            body,
            state,
            labels_list,
            assignees_list,
        )
        return {
            "status": "success",
            "number": result.get("number"),
            "title": result.get("title"),
            "state": result.get("state"),
            "html_url": result.get("html_url"),
        }

    @mcp.tool()
    async def close_issue(
        issue_number: int,
        repo: str | None = None,
    ) -> dict:
        """
        Закрыть issue в репозитории текущего владельца.

        Args:
            issue_number: Номер issue
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.update_issue(
            final_owner, final_repo, issue_number, state="closed"
        )
        return {
            "status": "success",
            "message": f"Issue #{issue_number} закрыт",
            "html_url": result.get("html_url"),
        }

    @mcp.tool()
    async def list_issue_comments(
        issue_number: int,
        repo: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить комментарии к issue в репозитории текущего владельца.

        Args:
            issue_number: Номер issue
            repo: Название репозитория (опционально)
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

        comments = await client.list_issue_comments(
            final_owner, final_repo, issue_number, per_page, page
        )
        return [
            {
                "id": c.get("id"),
                "body": c.get("body"),
                "author": c.get("user", {}).get("login"),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at"),
                "html_url": c.get("html_url"),
            }
            for c in comments
        ]

    @mcp.tool()
    async def create_issue_comment(
        issue_number: int,
        body: str,
        repo: str | None = None,
    ) -> dict:
        """
        Добавить комментарий к issue в репозитории текущего владельца.

        Args:
            issue_number: Номер issue
            body: Текст комментария (поддерживает Markdown)
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.create_issue_comment(
            final_owner, final_repo, issue_number, body
        )
        return {
            "status": "success",
            "id": result.get("id"),
            "html_url": result.get("html_url"),
        }

    @mcp.tool()
    async def list_labels(
        repo: str | None = None,
    ) -> list[dict]:
        """
        Получить список меток репозитория текущего владельца.

        Args:
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return [
                {
                    "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
                }
            ]

        labels = await client.list_labels(final_owner, final_repo)
        return [
            {
                "name": label.get("name"),
                "color": label.get("color"),
                "description": label.get("description"),
            }
            for label in labels
        ]

    @mcp.tool()
    async def add_labels(
        issue_number: int,
        labels: str,
        repo: str | None = None,
    ) -> dict:
        """
        Добавить метки к issue в репозитории текущего владельца.

        Args:
            issue_number: Номер issue
            labels: Метки через запятую
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        labels_list = [label.strip() for label in labels.split(",")]
        result = await client.add_labels(
            final_owner, final_repo, issue_number, labels_list
        )
        return {
            "status": "success",
            "labels": [label.get("name") for label in result],
        }
