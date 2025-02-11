import asyncio
from session import init_db

# Создание и инициализация базы данных
async def create_tables():
    await init_db()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_tables())
