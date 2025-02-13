from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from .models import User, Quest, Achievement, Moderation

async def get_user_by_tg_id(session: AsyncSession, telegram_id: int):
    result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    return result.scalars().first()

async def add_user(session: AsyncSession, telegram_id: int, full_name: str, age: int, gender: str):
    try:
        user = User(telegram_id=telegram_id, full_name=full_name, age=age, gender=gender)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()  # Откатываем транзакцию
        raise ValueError("Пользователь с таким telegram_id уже существует.")

async def give_achievement(session: AsyncSession, user_id: int, name: str, description: str):
    achievement = Achievement(user_id=user_id, name=name, description=description)
    session.add(achievement)
    await session.commit()

