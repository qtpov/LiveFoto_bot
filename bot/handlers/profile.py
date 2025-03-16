from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from bot.db.models import User, Achievement, Moderation
from sqlalchemy import delete
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import profile_keyboard

router = Router()

class ClearDBConfirmation(StatesGroup):
    confirm = State()

# Общая функция для отображения профиля
async def show_profile(user_id: int, message_or_callback: types.Message | types.CallbackQuery):
    async with SessionLocal() as session:
        user = await session.execute(select(User).filter(User.telegram_id == user_id))
        user = user.scalars().first()

        if not user:
            await message_or_callback.answer("Ты ещё не зарегистрирован! Напиши /start.")
            return

        last_achievement = await session.execute(select(Achievement).filter_by(user_id=user.id).order_by(Achievement.id.desc()))
        last_achievement = last_achievement.scalars().first()
        achievement_text = last_achievement.name if last_achievement else "Нет ачивок"

        text = (
            f'🧑‍💻 *Профиль героя*'
            f'\n\n👤 ФИО: {user.full_name}'
            f'\n🎂 Возраст: {user.age}'
            f'\n🏆 Последняя ачивка: {achievement_text}'
            f'\n📅 День: {user.day}'
        )

    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.edit_text(text, parse_mode="Markdown", reply_markup=profile_keyboard())
    else:
        await message_or_callback.answer(text, parse_mode="Markdown", reply_markup=profile_keyboard())

# Обработчик для команды /profile
@router.message(Command("profile"))
async def profile_command(message: types.Message):
    await show_profile(message.from_user.id, message)

# Обработчик для callback с data="profile"
@router.callback_query(F.data == "profile")
async def profile_callback(callback: types.CallbackQuery):
    await show_profile(callback.from_user.id, callback)

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
                #await session.execute(delete(Achievement))
                #await session.execute(delete(Moderation))
                await session.commit()
                await message.answer("База данных успешно очищена.")
            except Exception as e:
                await session.rollback()
                await message.answer(f"Произошла ошибка при очистке базы данных: {e}")
    else:
        await message.answer("Очистка базы данных отменена.")
    await state.clear()