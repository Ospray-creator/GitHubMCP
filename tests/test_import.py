from github_mcp import server, client, config

def test_imports():
    """Проверка того, что основные модули проекта успешно импортируются."""
    assert server
    assert client
    assert config
