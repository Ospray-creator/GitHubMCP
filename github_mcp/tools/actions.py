"""
Инструменты для работы с GitHub Actions.

Этот модуль предоставляет MCP инструменты для:
- Просмотра workflows и их запусков
- Запуска и отмены workflows
- Получения логов
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..client import GitHubClient
from ..config import settings


def register_action_tools(mcp: FastMCP, client: GitHubClient) -> None:
    """Регистрация инструментов для работы с GitHub Actions."""

    @mcp.tool()
    async def list_workflows(
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список workflows репозитория текущего владельца.

        Args:
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

        result = await client.list_workflows(final_owner, final_repo, per_page, page)
        workflows = result.get("workflows", [])
        return [
            {
                "id": w.get("id"),
                "name": w.get("name"),
                "path": w.get("path"),
                "state": w.get("state"),
                "html_url": w.get("html_url"),
                "created_at": w.get("created_at"),
                "updated_at": w.get("updated_at"),
            }
            for w in workflows
        ]

    @mcp.tool()
    async def get_workflow(
        workflow_id: int,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Получить информацию о workflow в репозитории текущего владельца.

        Args:
            workflow_id: ID workflow
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.get_workflow(final_owner, final_repo, workflow_id)
        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "path": result.get("path"),
            "state": result.get("state"),
            "html_url": result.get("html_url"),
            "badge_url": result.get("badge_url"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
        }

    @mcp.tool()
    async def trigger_workflow(
        workflow_id: int,
        ref: str = "main",
        inputs: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Запустить workflow в репозитории текущего владельца (workflow_dispatch).

        Args:
            workflow_id: ID workflow
            ref: Ветка для запуска (по умолчанию main)
            inputs: JSON строка с входными параметрами (опционально)
            repo: Название репозитория (опционально)
        """
        import json as json_module

        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        inputs_dict = None
        if inputs:
            try:
                inputs_dict = json_module.loads(inputs)
            except json_module.JSONDecodeError:
                return {"error": "Некорректный JSON в параметре inputs"}

        await client.trigger_workflow(
            final_owner, final_repo, workflow_id, ref, inputs_dict
        )
        return {
            "status": "success",
            "message": f"Workflow {workflow_id} запущен на ветке {ref}",
        }

    @mcp.tool()
    async def list_workflow_runs(
        workflow_id: Optional[int] = None,
        status: Optional[str] = None,
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список запусков workflow в репозитории текущего владельца.

        Args:
            workflow_id: ID workflow (опционально, для всех — None)
            status: Фильтр по статусу (queued, in_progress, completed)
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

        result = await client.list_workflow_runs(
            final_owner, final_repo, workflow_id, status, per_page, page
        )
        runs = result.get("workflow_runs", [])
        return [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "status": r.get("status"),
                "conclusion": r.get("conclusion"),
                "html_url": r.get("html_url"),
                "head_branch": r.get("head_branch"),
                "head_sha": r.get("head_sha")[:7] if r.get("head_sha") else None,
                "event": r.get("event"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "run_attempt": r.get("run_attempt"),
            }
            for r in runs
        ]

    @mcp.tool()
    async def get_workflow_run(
        run_id: int,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Получить информацию о запуске workflow в репозитории текущего владельца.

        Args:
            run_id: ID запуска
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        result = await client.get_workflow_run(final_owner, final_repo, run_id)
        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "status": result.get("status"),
            "conclusion": result.get("conclusion"),
            "html_url": result.get("html_url"),
            "head_branch": result.get("head_branch"),
            "head_sha": result.get("head_sha"),
            "event": result.get("event"),
            "run_attempt": result.get("run_attempt"),
            "workflow_id": result.get("workflow_id"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "run_started_at": result.get("run_started_at"),
        }

    @mcp.tool()
    async def cancel_workflow_run(
        run_id: int,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Отменить запуск workflow в репозитории текущего владельца.

        Args:
            run_id: ID запуска
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        await client.cancel_workflow_run(final_owner, final_repo, run_id)
        return {
            "status": "success",
            "message": f"Запуск workflow {run_id} отменён",
        }

    @mcp.tool()
    async def rerun_workflow(
        run_id: int,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Перезапустить workflow в репозитории текущего владельца.

        Args:
            run_id: ID запуска
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        await client.rerun_workflow(final_owner, final_repo, run_id)
        return {
            "status": "success",
            "message": f"Workflow {run_id} перезапущен",
        }

    @mcp.tool()
    async def list_workflow_jobs(
        run_id: int,
        repo: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """
        Получить список jobs запуска workflow в репозитории текущего владельца.

        Args:
            run_id: ID запуска
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

        result = await client.list_workflow_jobs(
            final_owner, final_repo, run_id, per_page, page
        )
        jobs = result.get("jobs", [])
        return [
            {
                "id": j.get("id"),
                "name": j.get("name"),
                "status": j.get("status"),
                "conclusion": j.get("conclusion"),
                "html_url": j.get("html_url"),
                "started_at": j.get("started_at"),
                "completed_at": j.get("completed_at"),
                "steps": [
                    {
                        "name": s.get("name"),
                        "status": s.get("status"),
                        "conclusion": s.get("conclusion"),
                    }
                    for s in j.get("steps", [])
                ],
            }
            for j in jobs
        ]

    @mcp.tool()
    async def get_workflow_logs_url(
        run_id: int,
        repo: Optional[str] = None,
    ) -> dict:
        """
        Получить URL для скачивания логов workflow в репозитории текущего владельца.

        Args:
            run_id: ID запуска
            repo: Название репозитория (опционально)
        """
        final_owner, final_repo = settings.get_owner_repo(None, repo)

        if not settings.is_repo_allowed(final_owner, final_repo):
            return {
                "error": f"Репозиторий {final_owner}/{final_repo} не в списке разрешённых"
            }

        logs_url = await client.download_workflow_logs(final_owner, final_repo, run_id)
        return {
            "logs_url": logs_url,
            "message": "Используйте этот URL для скачивания логов (требуется авторизация)",
        }
