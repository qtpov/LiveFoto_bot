
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from .configurate import settings

from .handlers import commands, profile, achievements, moderation, quests, games, knowledge_base, registration, admin_panel,quests_day2, quests_day3
from .db.init_db import init_db


# Логирование
logging.basicConfig(level=logging.INFO)

# Создаём бота и диспетчер
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Регистрируем хендлеры
dp.include_router(commands.router)
dp.include_router(profile.router)
dp.include_router(achievements.router)
dp.include_router(moderation.moderation_router)
dp.include_router(quests.router)
dp.include_router(games.router)
dp.include_router(knowledge_base.router)
dp.include_router(registration.router)
dp.include_router(admin_panel.router)
dp.include_router(quests_day2.router)
dp.include_router(quests_day3.router)


async def main():
    logging.info("Запуск базы данных...")
    await init_db()

    logging.info("Запуск бота...")
    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="admin_panel", description="Профиль"),

    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
