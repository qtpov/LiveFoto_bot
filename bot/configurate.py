import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "your_default_token_here")
    DB_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot/db/database.db")
    ADMIN_ID: int = os.getenv("ADMIN_ID", "")

settings = Settings()
