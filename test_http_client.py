"""
Тестовый клиент для проверки GitHub MCP HTTP Server.
"""
import asyncio
import logging
import sys
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_client():
    url = "http://localhost:8080/mcp"
    logger.info(f"Подключение к {url}...")
    
    # Получаем API ключ из настроек
    from github_mcp.config import settings
    headers = {}
    if settings.mcp_api_key:
        headers["X-API-Key"] = settings.mcp_api_key
        logger.info("Использование API ключа для аутентификации.")

    try:
        # Используем streamablehttp_client с передачей заголовков
        async with streamablehttp_client(url, headers=headers) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                logger.info("Инициализация сессии...")
                await session.initialize()
                
                logger.info("Запрос списка инструментов...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                logger.info(f"Найдено инструментов: {len(tools)}")
                
                # Попробуем вызвать get_authenticated_user
                if any(t.name == "get_authenticated_user" for t in tools):
                    logger.info("Вызов get_authenticated_user...")
                    # Передаем пустые аргументы {} так как JSON Schema требует обьект
                    result = await session.call_tool("get_authenticated_user", {})
                    
                    # Извлекаем текст из контента (TextContent)
                    if result.content and len(result.content) > 0:
                        content = result.content[0]
                        if hasattr(content, 'text'):
                            logger.info(f"Результат (text): {content.text}")
                        else:
                            logger.info(f"Результат (raw): {content}")
                    else:
                        logger.info("Результат (пустой)")
                else:
                    logger.warning("Инструмент get_authenticated_user не найден")
                
                logger.info("Тест успешно завершён!")
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_client())
