import asyncio
from session import init_db  # Подключаем функцию для инициализации базы данных

# Создание и инициализация базы данных
async def create_tables():
    await init_db()

# Запуск инициализации
if __name__ == "__main__":
    asyncio.run(create_tables())  # Используем asyncio.run для автоматического управления циклом событий
