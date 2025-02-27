from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import SessionLocal
from ..db.models import User
from sqlalchemy.exc import SQLAlchemyError
from aiogram import Router, types, F
from bot.keyboards.inline import go_profile_keyboard

router = Router()

async def get_mini_games(msg: types.Message):
    try:
        async with SessionLocal() as session:
            # Получаем пользователя из базы данных
            result = await session.execute(select(User).filter_by(telegram_id=msg.from_user.id))
            user = result.scalars().first()

            if not user:
                await msg.message.answer("Вы не зарегистрированы!")
                return

            # Проверяем день сотрудника
            if user.day == 2:
                await msg.message.answer("Доступна 1 мини-игра!")
                # Здесь можно вызвать функцию для первой игры
            elif user.day == 3:
                await msg.message.answer("Доступны 2 мини-игры!")
                # Здесь можно вызвать функции для двух игр
            else:
                await msg.message.edit_text("Мини-игры пока недоступны.",reply_markup=go_profile_keyboard())
    except SQLAlchemyError as e:
        await msg.message.answer("Произошла ошибка при работе с базой данных. Попробуйте позже.")
        print(f"Database error: {e}")

@router.callback_query(F.data == "games")
async def send_mini_games(callback: types.CallbackQuery):
    await get_mini_games(callback)
    await callback.answer()