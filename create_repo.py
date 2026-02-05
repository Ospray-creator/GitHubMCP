"""
Скрипт для создания нового репозитория GitHubMCP.
"""

import os
import requests
from github_mcp.config import settings

def create_repository():
    token = settings.gh_token
    if not token:
        print("GH_TOKEN не установлен в настройках.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Получаем имя пользователя из токена
    user_response = requests.get("https://api.github.com/user", headers=headers)
    if user_response.status_code != 200:
        print("Не удалось получить информацию о пользователе.")
        return

    username = user_response.json()["login"]

    # Создаем репозиторий
    repo_data = {
        "name": "GitHubMCP",
        "description": "Полнофункциональный GitHub MCP сервер для управления GitHub через Model Context Protocol",
        "private": False,  # Устанавливаем как публичный
        "auto_init": True,  # Инициализируем с README
        "gitignore_template": "Python",
        "license_template": "mit"
    }

    response = requests.post(
        f"https://api.github.com/user/repos",
        headers=headers,
        json=repo_data
    )

    if response.status_code == 201:
        repo_info = response.json()
        print(f"Репозиторий успешно создан: {repo_info['html_url']}")
        return repo_info['clone_url']
    else:
        print(f"Ошибка при создании репозитория: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    clone_url = create_repository()
    if clone_url:
        print(f"Клонируйте репозиторий: git clone {clone_url}")