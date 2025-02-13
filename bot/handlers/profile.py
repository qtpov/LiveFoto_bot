from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from bot.db.models import User, Achievement
from bot.db.session import SessionLocal
from bot.db.models import User, Quest, Achievement, Moderation
from sqlalchemy import delete
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import profile_keyboard

router = Router()

class ClearDBConfirmation(StatesGroup):
    confirm = State()



@router.message(Command("profile"))
async def profile(message: types.Message):
    async with SessionLocal() as session:
        user = await session.execute(select(User).filter(User.telegram_id == message.from_user.id))
        user = user.scalars().first()

        if not user:
            await message.answer("Ты ещё не зарегистрирован! Напиши /start.")
            return

        last_achievement = await session.execute(select(Achievement).filter_by(user_id=user.id).order_by(Achievement.id.desc()))
        last_achievement = last_achievement.scalars().first()
        achievement_text = last_achievement.name if last_achievement else "Нет ачивок"

        text =(f'🧑‍💻 *Профиль героя*'
               f'\n\n👤 ФИО: {user.full_name}'
               f'\n🎂 Возраст: {user.age}'
               f'\n🏆 Последняя ачивка: {achievement_text}')

    await message.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

# Команда для очистки базы данных
@router.message(Command("cleardb"))
async def clear_db(message: types.Message, state: FSMContext):
    if message.from_user.id != 693131022:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Вы уверены, что хотите очистить базу данных? (да/нет)")
    await state.set_state(ClearDBConfirmation.confirm)

@router.message(ClearDBConfirmation.confirm)
async def confirm_clear_db(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        async with SessionLocal() as session:
            try:
                await session.execute(delete(User))
                await session.execute(delete(Quest))
                await session.execute(delete(Achievement))
                await session.execute(delete(Moderation))
                await session.commit()
                await message.answer("База данных успешно очищена.")
            except Exception as e:
                await session.rollback()
                await message.answer(f"Произошла ошибка при очистке базы данных: {e}")
    else:
        await message.answer("Очистка базы данных отменена.")
    await state.clear()