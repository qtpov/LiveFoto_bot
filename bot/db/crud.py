from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from .models import User, Achievement, Moderation, Task, UserProfile, UserResult

async def get_user_by_tg_id(session: AsyncSession, telegram_id: int):
    result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    return result.scalars().first()

# async def add_user(session: AsyncSession, telegram_id: int, full_name: str, age: int, gender: str):
#     try:
#         user = User(telegram_id=telegram_id, full_name=full_name, age=age, gender=gender)
#         session.add(user)
#         await session.commit()
#         await session.refresh(user)
#         return user
#     except IntegrityError:
#         await session.rollback()  # Откатываем транзакцию
#         raise ValueError("Пользователь с таким telegram_id уже существует.")

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
            address=profile_data.get("address", ""),
            vacancy=profile_data.get("vacancy", ""),
            desired_salary=profile_data.get("desired_salary", ""),
            marital_status=profile_data.get("marital_status", ""),
            children=profile_data.get("children", ""),
            education=profile_data.get("education", ""),
            additional_education=profile_data.get("additional_education", ""),
            work_experience=profile_data.get("work_experience", ""),
            health_restrictions=profile_data.get("health_restrictions", ""),
            criminal_record=profile_data.get("criminal_record", ""),
            preferred_schedule=profile_data.get("preferred_schedule", ""),
            medical_book=profile_data.get("medical_book", ""),
            military_service=profile_data.get("military_service", ""),
            start_date=profile_data.get("start_date", ""),
            vacancy_source=profile_data.get("vacancy_source", ""),
            relatives_contacts=profile_data.get("relatives_contacts", ""),
            friends_contacts=profile_data.get("friends_contacts", ""),
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

async def give_achievement(session: AsyncSession, user_id: int, name: str, description: str):
    achievement = Achievement(user_id=user_id, name=name, description=description)
    session.add(achievement)
    await session.commit()


async def get_tasks(db: AsyncSession, day: int):
    """
    Получает задачи, сгруппированные по quest_id, для указанного дня.
    """
    stmt = (
        select(Task.quest_id, Task.title)
        .where(Task.day == day)  # Фильтруем по дню
        .group_by(Task.quest_id, Task.title)  # Группируем по quest_id и title
    )
    result = await db.execute(stmt)
    return result.all()

async def get_user_results(db: AsyncSession, user_id: int):
    """
    Получает результаты пользователя для определения статуса квестов.
    """
    stmt = select(UserResult).where(UserResult.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()