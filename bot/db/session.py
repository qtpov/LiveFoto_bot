from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import dotenv

# Загружаем переменные из .env
dotenv.load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # Получаем строку подключения из переменной окружения

# Настройка SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Функция инициализации базы данных (создание таблиц)
async def init_db():
    from models import User, Quest, Achievement, Moderation  # Импортируем модели, чтобы они были зарегистрированы
    Base.metadata.create_all(bind=engine)  # Создаём таблицы
    print("База данных и таблицы созданы!")
