"""
Конфигурация GitHub MCP Server.

Использует Pydantic Settings для безопасной загрузки переменных окружения
с валидацией и значениями по умолчанию.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GitHub API настройки
    gh_token: str = Field(
        default="",
        description="GitHub Personal Access Token с необходимыми правами",
    )
    gh_default_owner: str | None = Field(
        default=None,
        description="Владелец репозитория по умолчанию (username или организация)",
    )
    gh_default_repo: str | None = Field(
        default=None,
        description="Репозиторий по умолчанию",
    )
    gh_allowed_repos: str = Field(
        default="",
        description="Разрешённые репозитории в формате owner/repo или owner/* (через запятую)",
    )

    # Настройки логирования
    log_level: str = Field(default="INFO", description="Уровень логирования")

    # Настройки сервера
    server_name: str = Field(
        default="GitHub MCP Server",
        description="Название MCP сервера",
    )
    mcp_api_key: str | None = Field(
        default=None,
        description="API Key для доступа к HTTP серверу (X-API-Key или Bearer)",
    )

    # Runtime состояние (не из env)
    _runtime_owner: str | None = None
    _runtime_repo: str | None = None

    @field_validator("gh_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Валидация токена GitHub."""
        if v and not (
            v.startswith("ghp_") or v.startswith("github_pat_") or v.startswith("gho_")
        ):
            # Разрешаем токены старого формата тоже
            pass
        return v

    @property
    def allowed_repos_list(self) -> list[tuple[str, str | None]]:
        """Парсинг списка разрешённых репозиториев."""
        if not self.gh_allowed_repos:
            return []

        result = []
        for item in self.gh_allowed_repos.split(","):
            item = item.strip()
            if not item:
                continue
            if "/" in item:
                owner, repo = item.split("/", 1)
                # owner/* означает все репозитории владельца
                if repo == "*":
                    result.append((owner, None))
                else:
                    result.append((owner, repo))
            else:
                # Только owner — разрешить все его репозитории
                result.append((item, None))
        return result

    def is_repo_allowed(self, owner: str, repo: str) -> bool:
        """Проверка, разрешён ли доступ к репозиторию."""
        allowed = self.allowed_repos_list
        if not allowed:
            # Если список пуст — разрешить всё
            return True

        for allowed_owner, allowed_repo in allowed:
            if allowed_owner == owner:
                # Если repo=None — разрешены все репозитории владельца
                if allowed_repo is None or allowed_repo == repo:
                    return True
        return False

    def get_owner_repo(
        self, owner: str | None = None, repo: str | None = None
    ) -> tuple[str, str]:
        """Получить owner/repo с учётом runtime и default значений."""
        # Очищаем входные данные от пробелов
        o = (owner or "").strip()
        r = (repo or "").strip()

        # ОСНОВНОЕ ПРАВИЛО: Если owner не указан или это плейсхолдер "user",
        # используем владельца из настроек.
        # Это предотвращает ошибки, когда модель говорит "user/repo"
        final_owner = (
            o
            if (o and o.lower() != "user")
            else (self._runtime_owner or self.gh_default_owner)
        )
        final_repo = (
            r
            if (r and r.lower() != "repo")
            else (self._runtime_repo or self.gh_default_repo)
        )

        if not final_owner:
            error_msg = (
                "Владелец репозитория (owner) не установлен. "
                "Проверьте GH_DEFAULT_OWNER в .env или установите через set_default_repo."
            )
            raise ValueError(error_msg)

        if not final_repo:
            # Мы разрешаем repo быть None только в специфических случаях (например, list_user_repos),
            # но get_owner_repo обычно вызывается там, где repo обязателен.
            pass

        return final_owner, final_repo

    def set_default_repo(self, owner: str, repo: str) -> None:
        """Установить репозиторий по умолчанию для runtime."""
        if not self.is_repo_allowed(owner, repo):
            raise ValueError(f"Репозиторий {owner}/{repo} не в списке разрешённых")
        self._runtime_owner = owner
        self._runtime_repo = repo


@lru_cache
def get_settings() -> Settings:
    """Получить singleton настроек."""
    return Settings()


# Глобальный экземпляр настроек
settings = get_settings()
