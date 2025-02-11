from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Берём URL БД (формат: postgresql://user:password@host/dbname)
DB_URL = os.getenv("DATABASE_URL", "postgresql://your_user:your_password@localhost/bot_db")

# Создаём движок SQLAlchemy
engine = create_engine(DB_URL, echo=False)

# Создаём сессию
SessionLocal = sessionmaker(bind=engine)

# Базовый класс для моделей
Base = declarative_base()
