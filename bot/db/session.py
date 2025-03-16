from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import dotenv

# Загружаем переменные из .env
dotenv.load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:pa$$word@localhost/livefoto")

# Настройка SQLAlchemy
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()

# Функция инициализации базы данных (создание таблиц)
async def init_db():
    from .models import User, Achievement, Moderation

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Асинхронный вызов создания таблиц

    print("База данных и таблицы созданы!")