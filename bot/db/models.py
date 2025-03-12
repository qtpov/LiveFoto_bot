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

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), unique=True)  # Связь с User по telegram_id
    full_name = Column(String, nullable=False)  # ФИО
    birth_date = Column(String)  # Дата рождения
    phone = Column(String)  # Телефон
    address = Column(String)  # Адрес проживания
    vacancy = Column(String)  # Вакансия
    desired_salary = Column(String)  # Желаемый уровень з/п
    marital_status = Column(String)  # Семейное положение
    children = Column(String)  # Дети (возраст)
    education = Column(Text)  # Образование (ВУЗ, специальность)
    additional_education = Column(Text)  # Дополнительное обучение
    work_experience = Column(Text)  # Трудовая деятельность
    health_restrictions = Column(Text)  # Ограничения по работе / хронические заболевания
    criminal_record = Column(String)  # Судимости (статья)
    preferred_schedule = Column(String)  # Предпочтительный график работы
    medical_book = Column(String)  # Медицинская книжка
    military_service = Column(String)  # Отношение к воинской обязанности
    start_date = Column(String)  # Когда готов приступить к работе
    vacancy_source = Column(String)  # Откуда узнали о вакансии
    relatives_contacts = Column(Text)  # Контактные данные близких родственников
    friends_contacts = Column(Text)  # Контакты друзей/знакомых/родственников
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