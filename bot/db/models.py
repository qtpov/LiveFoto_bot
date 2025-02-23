from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, Boolean, DateTime, func, ARRAY
from sqlalchemy.orm import relationship
from .session import Base
#
# class Quest(Base):
#     __tablename__ = "quests"
#     id = Column(Integer, primary_key=True)
#     title = Column(String, nullable=False)
#     description = Column(String)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)  # Название задания
    description = Column(String)  # Текст задания
    options = Column(ARRAY(String))  # Массив строк с вариантами ответов
    correct_answer = Column(String)  # Правильный ответ

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    level = Column(Integer, default=1)
    last_achievement = Column(String, default="")
    day = Column(Integer, default=1)


class UserResult(Base):
    __tablename__ = "user_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # Связь с User
    task_id = Column(Integer, ForeignKey("tasks.id"))  # Связь с Task
    state = Column(String, nullable=False)
    attempt = Column(Integer, default=1)
    result = Column(Integer, default=1) #можно сделать процент верных ответов из всех

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))  # Связь с User
    user = relationship("User")

class Moderation(Base):
    __tablename__ = "moderation"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))  # Связь с task
    status = Column(String, default="pending")  # approved, rejected
    user_id = Column(Integer,ForeignKey("users.id"))  # ID юзера
    #timestamp = Column(DateTime, default=func.now())