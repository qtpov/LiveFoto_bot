from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from .session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    level = Column(Integer, default=1)
    last_achievement = Column(String, default="")

class Quest(Base):
    __tablename__ = "quests"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, on_review, completed, rejected
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class Moderation(Base):
    __tablename__ = "moderation"
    id = Column(Integer, primary_key=True)
    quest_id = Column(Integer, ForeignKey("quests.id"))
    status = Column(String, default="pending")  # approved, rejected
    moderator_id = Column(Integer)
    timestamp = Column(DateTime, default=func.now())