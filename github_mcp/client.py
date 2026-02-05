"""
Асинхронный GitHub API клиент.

Использует httpx для асинхронных HTTP-запросов к GitHub REST API v3.
"""

import base64
import logging
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """Исключение для ошибок GitHub API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    """Асинхронный клиент для GitHub REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None):
        """
        Инициализация клиента.

        Args:
            token: GitHub токен (если не указан, берётся из настроек)
        """
        self.token = token or settings.gh_token
        self._client: httpx.AsyncClient | None = None

    @property
    def headers(self) -> dict[str, str]:
        """Заголовки для запросов к API."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-MCP-Server/1.0.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Получить или создать HTTP клиент."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=self.headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Закрыть HTTP клиент."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> Any:
        """
        Выполнить HTTP запрос к GitHub API.

        Args:
            method: HTTP метод (GET, POST, PUT, PATCH, DELETE)
            endpoint: Эндпоинт API (без базового URL)
            params: Query параметры
            json_data: JSON тело запроса

        Returns:
            Ответ API как dict или list

        Raises:
            GitHubError: При ошибке API
        """
        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_data,
            )

            # Обработка ошибок
            if response.status_code >= 400:
                error_message = f"GitHub API ошибка: {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                    if "errors" in error_data:
                        errors = [
                            e.get("message", str(e)) for e in error_data["errors"]
                        ]
                        error_message += f" ({', '.join(errors)})"
                except Exception:
                    error_message = response.text or error_message

                logger.error(
                    f"GitHub API error: {response.status_code} {method} {response.url} - {error_message}"
                )
                raise GitHubError(error_message, response.status_code)

            # Пустой ответ (204 No Content)
            if response.status_code == 204:
                return {"success": True}

            # Парсинг JSON ответа
            if response.content:
                return response.json()
            return {}

        except httpx.TimeoutException as e:
            raise GitHubError(f"Таймаут запроса к GitHub API: {e}") from e
        except httpx.RequestError as e:
            raise GitHubError(f"Ошибка соединения с GitHub API: {e}") from e

    # ========================
    # Репозитории
    # ========================

    async def get_repository(self, owner: str, repo: str) -> dict:
        """Получить информацию о репозитории."""
        return await self._request("GET", f"/repos/{owner}/{repo}")

    async def list_user_repos(
        self,
        username: str | None = None,
        type: str = "all",
        sort: str = "updated",
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """Список репозиториев пользователя."""
        if username:
            endpoint = f"/users/{username}/repos"
        else:
            endpoint = "/user/repos"

        return await self._request(
            "GET",
            endpoint,
            params={"type": type, "sort": sort, "per_page": per_page, "page": page},
        )

    async def list_org_repos(
        self,
        org: str,
        type: str = "all",
        sort: str = "updated",
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """Список репозиториев организации."""
        return await self._request(
            "GET",
            f"/orgs/{org}/repos",
            params={"type": type, "sort": sort, "per_page": per_page, "page": page},
        )

    async def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = False,
        auto_init: bool = True,
        org: str | None = None,
    ) -> dict:
        """Создать новый репозиторий."""
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
        }

        if org:
            endpoint = f"/orgs/{org}/repos"
        else:
            endpoint = "/user/repos"

        return await self._request("POST", endpoint, json_data=data)

    async def delete_repository(self, owner: str, repo: str) -> dict:
        """Удалить репозиторий."""
        return await self._request("DELETE", f"/repos/{owner}/{repo}")

    async def fork_repository(
        self,
        owner: str,
        repo: str,
        organization: str | None = None,
        name: str | None = None,
    ) -> dict:
        """Форкнуть репозиторий."""
        data = {}
        if organization:
            data["organization"] = organization
        if name:
            data["name"] = name

        return await self._request(
            "POST", f"/repos/{owner}/{repo}/forks", json_data=data or None
        )

    async def list_forks(
        self, owner: str, repo: str, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список форков репозитория."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/forks",
            params={"per_page": per_page, "page": page},
        )

    async def list_contributors(
        self, owner: str, repo: str, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список контрибьюторов репозитория."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/contributors",
            params={"per_page": per_page, "page": page},
        )

    async def list_languages(self, owner: str, repo: str) -> dict:
        """Языки программирования в репозитории."""
        return await self._request("GET", f"/repos/{owner}/{repo}/languages")

    # ========================
    # Содержимое файлов
    # ========================

    async def get_contents(
        self, owner: str, repo: str, path: str = "", ref: str | None = None
    ) -> dict | list[dict]:
        """Получить содержимое файла или директории."""
        params = {}
        if ref:
            params["ref"] = ref

        result = await self._request(
            "GET", f"/repos/{owner}/{repo}/contents/{path}", params=params or None
        )

        # Декодирование base64 содержимого файла
        if (
            isinstance(result, dict)
            and result.get("encoding") == "base64"
            and "content" in result
        ):
            try:
                result["content"] = base64.b64decode(result["content"]).decode("utf-8")
                result["encoding"] = "utf-8"
            except Exception as e:
                logger.warning(f"Не удалось декодировать содержимое: {e}")

        return result

    async def create_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str | None = None,
    ) -> dict:
        """Создать новый файл."""
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        }
        if branch:
            data["branch"] = branch

        return await self._request(
            "PUT", f"/repos/{owner}/{repo}/contents/{path}", json_data=data
        )

    async def update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        sha: str,
        branch: str | None = None,
    ) -> dict:
        """Обновить существующий файл."""
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "sha": sha,
        }
        if branch:
            data["branch"] = branch

        return await self._request(
            "PUT", f"/repos/{owner}/{repo}/contents/{path}", json_data=data
        )

    async def delete_file(
        self,
        owner: str,
        repo: str,
        path: str,
        message: str,
        sha: str,
        branch: str | None = None,
    ) -> dict:
        """Удалить файл."""
        data = {
            "message": message,
            "sha": sha,
        }
        if branch:
            data["branch"] = branch

        return await self._request(
            "DELETE", f"/repos/{owner}/{repo}/contents/{path}", json_data=data
        )

    # ========================
    # Ветки и коммиты
    # ========================

    async def list_branches(
        self, owner: str, repo: str, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список веток репозитория."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches",
            params={"per_page": per_page, "page": page},
        )

    async def get_branch(self, owner: str, repo: str, branch: str) -> dict:
        """Информация о ветке."""
        return await self._request("GET", f"/repos/{owner}/{repo}/branches/{branch}")

    async def create_branch(
        self, owner: str, repo: str, branch_name: str, from_ref: str = "main"
    ) -> dict:
        """Создать новую ветку."""
        # Получить SHA исходной ветки
        ref_data = await self._request(
            "GET", f"/repos/{owner}/{repo}/git/ref/heads/{from_ref}"
        )
        sha = ref_data["object"]["sha"]

        # Создать новую ветку
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            json_data={"ref": f"refs/heads/{branch_name}", "sha": sha},
        )

    async def delete_branch(self, owner: str, repo: str, branch: str) -> dict:
        """Удалить ветку."""
        return await self._request(
            "DELETE", f"/repos/{owner}/{repo}/git/refs/heads/{branch}"
        )

    async def list_commits(
        self,
        owner: str,
        repo: str,
        sha: str | None = None,
        path: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """Список коммитов."""
        params = {"per_page": per_page, "page": page}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path

        return await self._request(
            "GET", f"/repos/{owner}/{repo}/commits", params=params
        )

    async def get_commit(self, owner: str, repo: str, ref: str) -> dict:
        """Информация о коммите."""
        return await self._request("GET", f"/repos/{owner}/{repo}/commits/{ref}")

    async def compare_commits(
        self, owner: str, repo: str, base: str, head: str
    ) -> dict:
        """Сравнить две ветки/коммита."""
        return await self._request(
            "GET", f"/repos/{owner}/{repo}/compare/{base}...{head}"
        )

    # ========================
    # Issues
    # ========================

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: str | None = None,
        assignee: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """Список issues."""
        params = {"state": state, "per_page": per_page, "page": page}
        if labels:
            params["labels"] = labels
        if assignee:
            params["assignee"] = assignee

        return await self._request(
            "GET", f"/repos/{owner}/{repo}/issues", params=params
        )

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        """Получить issue."""
        return await self._request(
            "GET", f"/repos/{owner}/{repo}/issues/{issue_number}"
        )

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> dict:
        """Создать issue."""
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees

        return await self._request(
            "POST", f"/repos/{owner}/{repo}/issues", json_data=data
        )

    async def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> dict:
        """Обновить issue."""
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels
        if assignees is not None:
            data["assignees"] = assignees

        return await self._request(
            "PATCH", f"/repos/{owner}/{repo}/issues/{issue_number}", json_data=data
        )

    async def list_issue_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """Список комментариев к issue."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            params={"per_page": per_page, "page": page},
        )

    async def create_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> dict:
        """Создать комментарий к issue."""
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json_data={"body": body},
        )

    async def list_labels(self, owner: str, repo: str) -> list[dict]:
        """Список меток репозитория."""
        return await self._request("GET", f"/repos/{owner}/{repo}/labels")

    async def add_labels(
        self, owner: str, repo: str, issue_number: int, labels: list[str]
    ) -> list[dict]:
        """Добавить метки к issue."""
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
            json_data={"labels": labels},
        )

    # ========================
    # Pull Requests
    # ========================

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        head: str | None = None,
        base: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict]:
        """Список pull request'ов."""
        params = {"state": state, "per_page": per_page, "page": page}
        if head:
            params["head"] = head
        if base:
            params["base"] = base

        return await self._request("GET", f"/repos/{owner}/{repo}/pulls", params=params)

    async def get_pull_request(self, owner: str, repo: str, pull_number: int) -> dict:
        """Получить pull request."""
        return await self._request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}")

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
        draft: bool = False,
    ) -> dict:
        """Создать pull request."""
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            json_data={
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft,
            },
        )

    async def update_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        base: str | None = None,
    ) -> dict:
        """Обновить pull request."""
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if base is not None:
            data["base"] = base

        return await self._request(
            "PATCH", f"/repos/{owner}/{repo}/pulls/{pull_number}", json_data=data
        )

    async def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        commit_title: str | None = None,
        commit_message: str | None = None,
        merge_method: str = "merge",
    ) -> dict:
        """Мержить pull request."""
        data = {"merge_method": merge_method}
        if commit_title:
            data["commit_title"] = commit_title
        if commit_message:
            data["commit_message"] = commit_message

        return await self._request(
            "PUT", f"/repos/{owner}/{repo}/pulls/{pull_number}/merge", json_data=data
        )

    async def list_pr_commits(
        self, owner: str, repo: str, pull_number: int, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список коммитов pull request'а."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}/commits",
            params={"per_page": per_page, "page": page},
        )

    async def list_pr_files(
        self, owner: str, repo: str, pull_number: int, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список файлов pull request'а."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}/files",
            params={"per_page": per_page, "page": page},
        )

    async def create_pr_review(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        body: str,
        event: str = "COMMENT",
    ) -> dict:
        """Создать ревью pull request'а."""
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
            json_data={"body": body, "event": event},
        )

    async def list_pr_comments(
        self, owner: str, repo: str, pull_number: int, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список комментариев pull request'а."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}/comments",
            params={"per_page": per_page, "page": page},
        )

    # ========================
    # GitHub Actions
    # ========================

    async def list_workflows(
        self, owner: str, repo: str, per_page: int = 30, page: int = 1
    ) -> dict:
        """Список workflows."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/workflows",
            params={"per_page": per_page, "page": page},
        )

    async def get_workflow(self, owner: str, repo: str, workflow_id: int | str) -> dict:
        """Информация о workflow."""
        return await self._request(
            "GET", f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}"
        )

    async def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: int | str,
        ref: str = "main",
        inputs: dict | None = None,
    ) -> dict:
        """Запустить workflow."""
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs

        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            json_data=data,
        )

    async def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int | str | None = None,
        status: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> dict:
        """Список запусков workflow."""
        if workflow_id:
            endpoint = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            endpoint = f"/repos/{owner}/{repo}/actions/runs"

        params = {"per_page": per_page, "page": page}
        if status:
            params["status"] = status

        return await self._request("GET", endpoint, params=params)

    async def get_workflow_run(self, owner: str, repo: str, run_id: int) -> dict:
        """Информация о запуске workflow."""
        return await self._request(
            "GET", f"/repos/{owner}/{repo}/actions/runs/{run_id}"
        )

    async def cancel_workflow_run(self, owner: str, repo: str, run_id: int) -> dict:
        """Отменить запуск workflow."""
        return await self._request(
            "POST", f"/repos/{owner}/{repo}/actions/runs/{run_id}/cancel"
        )

    async def rerun_workflow(self, owner: str, repo: str, run_id: int) -> dict:
        """Перезапустить workflow."""
        return await self._request(
            "POST", f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun"
        )

    async def list_workflow_jobs(
        self, owner: str, repo: str, run_id: int, per_page: int = 30, page: int = 1
    ) -> dict:
        """Список jobs запуска workflow."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
            params={"per_page": per_page, "page": page},
        )

    async def download_workflow_logs(self, owner: str, repo: str, run_id: int) -> str:
        """Получить URL для скачивания логов workflow."""
        # Возвращаем URL для редиректа на логи
        return f"{self.BASE_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"

    # ========================
    # Пользователи
    # ========================

    async def get_authenticated_user(self) -> dict:
        """Получить информацию о текущем пользователе."""
        return await self._request("GET", "/user")

    async def get_user(self, username: str) -> dict:
        """Получить информацию о пользователе."""
        return await self._request("GET", f"/users/{username}")

    async def list_followers(
        self, username: str | None = None, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список подписчиков."""
        if username:
            endpoint = f"/users/{username}/followers"
        else:
            endpoint = "/user/followers"

        return await self._request(
            "GET", endpoint, params={"per_page": per_page, "page": page}
        )

    async def list_following(
        self, username: str | None = None, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список подписок."""
        if username:
            endpoint = f"/users/{username}/following"
        else:
            endpoint = "/user/following"

        return await self._request(
            "GET", endpoint, params={"per_page": per_page, "page": page}
        )

    async def list_user_orgs(
        self, username: str | None = None, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список организаций пользователя."""
        if username:
            endpoint = f"/users/{username}/orgs"
        else:
            endpoint = "/user/orgs"

        return await self._request(
            "GET", endpoint, params={"per_page": per_page, "page": page}
        )

    # ========================
    # Gists
    # ========================

    async def list_gists(
        self, username: str | None = None, per_page: int = 30, page: int = 1
    ) -> list[dict]:
        """Список gists."""
        if username:
            endpoint = f"/users/{username}/gists"
        else:
            endpoint = "/gists"

        return await self._request(
            "GET", endpoint, params={"per_page": per_page, "page": page}
        )

    async def get_gist(self, gist_id: str) -> dict:
        """Получить gist."""
        return await self._request("GET", f"/gists/{gist_id}")

    async def create_gist(
        self,
        files: dict[str, dict[str, str]],
        description: str = "",
        public: bool = False,
    ) -> dict:
        """
        Создать gist.

        files имеет формат: {"filename.ext": {"content": "file content"}}
        """
        return await self._request(
            "POST",
            "/gists",
            json_data={"files": files, "description": description, "public": public},
        )

    async def update_gist(
        self,
        gist_id: str,
        files: dict[str, dict[str, str]] | None = None,
        description: str | None = None,
    ) -> dict:
        """Обновить gist."""
        data = {}
        if files is not None:
            data["files"] = files
        if description is not None:
            data["description"] = description

        return await self._request("PATCH", f"/gists/{gist_id}", json_data=data)

    async def delete_gist(self, gist_id: str) -> dict:
        """Удалить gist."""
        return await self._request("DELETE", f"/gists/{gist_id}")

    # ========================
    # Поиск
    # ========================

    async def search_code(self, query: str, per_page: int = 30, page: int = 1) -> dict:
        """Поиск по коду."""
        return await self._request(
            "GET",
            "/search/code",
            params={"q": query, "per_page": per_page, "page": page},
        )

    async def search_repositories(
        self, query: str, sort: str = "stars", per_page: int = 30, page: int = 1
    ) -> dict:
        """Поиск репозиториев."""
        return await self._request(
            "GET",
            "/search/repositories",
            params={"q": query, "sort": sort, "per_page": per_page, "page": page},
        )

    async def search_issues(
        self, query: str, sort: str = "created", per_page: int = 30, page: int = 1
    ) -> dict:
        """Поиск issues и PR."""
        return await self._request(
            "GET",
            "/search/issues",
            params={"q": query, "sort": sort, "per_page": per_page, "page": page},
        )
