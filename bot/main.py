
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from .configurate import settings

from .handlers import start, profile, achievements, moderation, quests, games, knowledge_base
from .db import init_db


# Логирование
logging.basicConfig(level=logging.INFO)

# Создаём бота и диспетчер
bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Регистрируем хендлеры
dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(achievements.router)
dp.include_router(moderation.router)
dp.include_router(quests.router)
dp.include_router(games.router)
dp.include_router(knowledge_base.router)


async def main():
    logging.info("Запуск базы данных...")
    await init_db()

    logging.info("Запуск бота...")
    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="achievements", description="Ачивки"),
    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
