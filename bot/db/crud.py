from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from .models import User, Achievement, UserProfile, UserResult

async def get_user_by_tg_id(session: AsyncSession, telegram_id: int):
    result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    return result.scalars().first()

async def add_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    age: int,
    gender: str,
    profile_data: dict  # Данные анкеты
):
    try:
        # Создаем пользователя
        user = User(telegram_id=telegram_id, full_name=full_name, age=age, gender=gender)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Создаем профиль пользователя (анкету)
        profile = UserProfile(
            user_id=user.id,  # Связь с пользователем
            full_name=profile_data.get("full_name", ""),
            birth_date=profile_data.get("birth_date", ""),
            phone=profile_data.get("phone", ""),
            personal_data_consent=profile_data.get("personal_data_consent", False)
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        return user
    except IntegrityError:
        await session.rollback()  # Откатываем транзакцию
        raise ValueError("Пользователь с таким telegram_id уже существует.")
    except Exception as e:
        await session.rollback()  # Откатываем транзакцию в случае других ошибок
        raise ValueError(f"Произошла ошибка при добавлении пользователя: {e}")

async def update_user_level(user_id: int, session):
    user = await session.execute(
        select(User).filter(User.telegram_id == user_id)
    )
    user = user.scalars().first()

    if not user:
        return
    else:
        user.level += 1
        await session.commit()

async def update_user_day(user_id: int, session):
    user = await session.execute(
        select(User).filter(User.telegram_id == user_id)
    )
    user = user.scalars().first()

    if not user:
        return
    else:
        user.day += 1
        await session.commit()



# Добавим в crud.py
async def get_all_users(session: AsyncSession):
    result = await session.execute(select(User))
    return result.scalars().all()

async def get_user_results(session: AsyncSession, user_id: int):
    stmt = select(UserResult).where(UserResult.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_user_achievements(session: AsyncSession, user_id: int):
    stmt = select(Achievement).where(Achievement.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()