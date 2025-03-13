from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, Boolean, DateTime, func, ARRAY, Text
from sqlalchemy.orm import relationship
from .session import Base

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    options = Column(ARRAY(String))
    correct_answer = Column(String)
    day = Column(Integer)
    quest_id = Column(Integer)
    photo = Column(String, nullable=True)  # Новое поле для хранения ссылки на фото
    type = Column(String, default="multiple_choice")  # Тип квеста: "multiple_choice", "photo_moderation", "hint", etc.

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, nullable=False)
    birth_date = Column(String)
    phone = Column(String)
    address = Column(String)
    vacancy = Column(String)
    desired_salary = Column(String)
    marital_status = Column(String)
    children = Column(String)
    education = Column(Text)
    additional_education = Column(Text)
    work_experience = Column(Text)
    health_restrictions = Column(Text)
    criminal_record = Column(String)
    preferred_schedule = Column(String)
    medical_book = Column(String)
    military_service = Column(String)
    start_date = Column(String)
    vacancy_source = Column(String)
    relatives_contacts = Column(Text)
    friends_contacts = Column(Text)
    personal_data_consent = Column(Boolean, default=False)
    user = relationship("User", back_populates="profile")

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
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class UserResult(Base):
    __tablename__ = "user_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    quest_id = Column(Integer)
    state = Column(String, nullable=False)
    attempt = Column(Integer, default=1)
    result = Column(Integer, default=0)

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    user = relationship("User")

class Moderation(Base):
    __tablename__ = "moderation"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    status = Column(String, default="pending")
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))