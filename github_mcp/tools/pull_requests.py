"""
Инструменты для работы с Pull Requests в GitHub.

Этот модуль предоставляет MCP инструменты для:
- Создания и редактирования PR
- Просмотра и мержа PR
- Работы с комментариями и ревью
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient
from ..config import settings


def register_pr_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для работы с Pull Requests."""

    @mcp.tool()
    async def list_pull_requests(
        repo: Optional[str] = None,
        state: str = "open",
        head: Optional[str] = None,
        base: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список Pull Request'ов в репозитории текущего владельца.

        Args:
            repo: Название репозитория (опционально)
            state: Состояние (open, closed, all)
            head: Фильтр по исходной ветке (опционально)
            base: Фильтр по целевой ветке (опционально)
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

        prs = await client.list_pull_requests(
            final_owner, final_repo, state, head, base, per_page, page
        )
        return [
            {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "state": pr.get("state"),
                "html_url": pr.get("html_url"),
                "author": pr.get("user", {}).get("login"),
                "head": pr.get("head", {}).get("ref"),
                "base": pr.get("base", {}).get("ref"),
                "draft": pr.get("draft"),
                "mergeable": pr.get("mergeable"),
                "created_at": pr.get("created_at"),
                "updated_at": pr.get("updated_at"),
            }
            for pr in prs
        ]

    @mcp.tool()
    async def get_pull_request(
        pull_number: int,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Получить информацию о Pull Request в репозитории текущего владельца.

        Args:
            pull_number: Номер PR
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.get_pull_request(final_owner, final_repo, pull_number)
        return {
            "number": result.get("number"),
            "title": result.get("title"),
            "body": result.get("body"),
            "state": result.get("state"),
            "html_url": result.get("html_url"),
            "author": result.get("user", {}).get("login"),
            "head": result.get("head", {}).get("ref"),
            "base": result.get("base", {}).get("ref"),
            "draft": result.get("draft"),
            "mergeable": result.get("mergeable"),
            "mergeable_state": result.get("mergeable_state"),
            "merged": result.get("merged"),
            "merged_by": (
                result.get("merged_by", {}).get("login")
                if result.get("merged_by")
                else None
            ),
            "commits": result.get("commits"),
            "additions": result.get("additions"),
            "deletions": result.get("deletions"),
            "changed_files": result.get("changed_files"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "merged_at": result.get("merged_at"),
        }

    @mcp.tool()
    async def create_pull_request(
        title: str,
        head: str,
        repo: Optional[str] = None,
        base: str = "main",
        body: str = "",
        draft: bool = False,
    ) -> dict:
        """
        Создать Pull Request в репозитории текущего владельца.

        Args:
            title: Заголовок PR
            head: Исходная ветка с изменениями
            repo: Название репозитория (опционально)
            base: Целевая ветка (по умолчанию main)
            body: Описание PR (поддерживает Markdown)
            draft: Создать как черновик (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.create_pull_request(
            final_owner, final_repo, title, head, base, body, draft
        )
        return {
            "status": "success",
            "number": result.get("number"),
            "title": result.get("title"),
            "html_url": result.get("html_url"),
            "state": result.get("state"),
        }

    @mcp.tool()
    async def update_pull_request(
        pull_number: int,
        repo: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        base: Optional[str] = None,
    ) -> dict:
        """
        Обновить Pull Request в репозитории текущего владельца.

        Args:
            pull_number: Номер PR
            repo: Название репозитория (опционально)
            title: Новый заголовок (опционально)
            body: Новое описание (опционально)
            state: Новое состояние (open/closed) (опционально)
            base: Новая целевая ветка (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.update_pull_request(
            final_owner, final_repo, pull_number, title, body, state, base
        )
        return {
            "status": "success",
            "number": result.get("number"),
            "title": result.get("title"),
            "state": result.get("state"),
            "html_url": result.get("html_url"),
        }

    @mcp.tool()
    async def merge_pull_request(
        pull_number: int,
        repo: Optional[str] = None,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        merge_method: str = "merge",
    ) -> dict:
        """
        Мержить Pull Request в репозитории текущего владельца.

        Args:
            pull_number: Номер PR
            repo: Название репозитория (опционально)
            commit_title: Заголовок коммита мержа (опционально)
            commit_message: Сообщение коммита мержа (опционально)
            merge_method: Метод мержа (merge, squash, rebase)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.merge_pull_request(
            final_owner,
            final_repo,
            pull_number,
            commit_title,
            commit_message,
            merge_method,
        )
        return {
            "status": "success",
            "merged": result.get("merged"),
            "message": result.get("message"),
            "sha": result.get("sha"),
        }

    @mcp.tool()
    async def list_pr_commits(
        pull_number: int,
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список коммитов Pull Request в репозитории текущего владельца.

        Args:
            pull_number: Номер PR
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

        commits = await client.list_pr_commits(
            final_owner, final_repo, pull_number, per_page, page
        )
        return [
            {
                "sha": c.get("sha"),
                "message": c.get("commit", {}).get("message", "").split("\n")[0],
                "author": c.get("commit", {}).get("author", {}).get("name"),
                "date": c.get("commit", {}).get("author", {}).get("date"),
            }
            for c in commits
        ]

    @mcp.tool()
    async def list_pr_files(
        pull_number: int,
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список изменённых файлов Pull Request в репозитории текущего владельца.

        Args:
            pull_number: Номер PR
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

        files = await client.list_pr_files(
            final_owner, final_repo, pull_number, per_page, page
        )
        return [
            {
                "filename": f.get("filename"),
                "status": f.get("status"),
                "additions": f.get("additions"),
                "deletions": f.get("deletions"),
                "changes": f.get("changes"),
                "patch": (
                    f.get("patch", "")[:500] + "..."
                    if len(f.get("patch", "")) > 500
                    else f.get("patch")
                ),
            }
            for f in files
        ]

    @mcp.tool()
    async def create_pr_review(
        pull_number: int,
        body: str,
        repo: Optional[str] = None,
        event: str = "COMMENT",
    ) -> dict:
        """
        Создать ревью Pull Request в репозитории текущего владельца.

        Args:
            pull_number: Номер PR
            body: Текст ревью
            repo: Название репозитория (опционально)
            event: Тип ревью (APPROVE, REQUEST_CHANGES, COMMENT)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.create_pr_review(
            final_owner, final_repo, pull_number, body, event
        )
        return {
            "status": "success",
            "id": result.get("id"),
            "state": result.get("state"),
            "html_url": result.get("html_url"),
        }

    @mcp.tool()
    async def list_pr_comments(
        pull_number: int,
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить комментарии к Pull Request в репозитории текущего владельца.

        Args:
            pull_number: Номер PR
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

        comments = await client.list_pr_comments(
            final_owner, final_repo, pull_number, per_page, page
        )
        return [
            {
                "id": c.get("id"),
                "body": c.get("body"),
                "path": c.get("path"),
                "author": c.get("user", {}).get("login"),
                "created_at": c.get("created_at"),
                "html_url": c.get("html_url"),
            }
            for c in comments
        ]
