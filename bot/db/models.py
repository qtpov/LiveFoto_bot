from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, Boolean, DateTime, func, ARRAY, Text
from sqlalchemy.orm import relationship
from .session import Base

# class Task(Base):
#     __tablename__ = "tasks"
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     description = Column(String)
#     options = Column(ARRAY(String))
#     correct_answer = Column(String)
#     day = Column(Integer)
#     quest_id = Column(Integer)
#     photo = Column(String, nullable=True)  # Новое поле для хранения ссылки на фото

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, nullable=False)  # ФИО
    birth_date = Column(String)  # Дата рождения
    phone = Column(String)  # Телефон
    personal_data_consent = Column(Boolean, default=False)  # Согласие на обработку персональных данных
    user = relationship("User", back_populates="profile")  # Связь с User

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)  # Уникальный идентификатор Telegram
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    level = Column(Integer, default=1)
    last_achievement = Column(String, default="")
    day = Column(Integer, default=1)
    profile = relationship("UserProfile", back_populates="user", uselist=False)  # Один-к-одному

class UserResult(Base):
    __tablename__ = "user_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))  # Связь с User по telegram_id
    quest_id = Column(Integer)  # Добавляем поле для хранения quest_id
    state = Column(String, nullable=False)
    attempt = Column(Integer, default=1)
    result = Column(Integer, default=0)  # Количество верных ответов для этого задания

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))  # Связь с User по telegram_id
    user = relationship("User")

class Moderation(Base):
    __tablename__ = "moderation"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))  # Связь с task
    status = Column(String, default="pending")  # approved, rejected
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))  # Связь с User по telegram_id
    #timestamp = Column(DateTime, default=func.now())