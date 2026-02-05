import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path для корректного импорта модулей
sys.path.append(str(Path(__file__).parent.parent))
