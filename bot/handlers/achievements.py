from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import SessionLocal
from ..db.models import Achievement, User
from sqlalchemy.exc import SQLAlchemyError
from aiogram import Router, types, F
from bot.keyboards.inline import go_profile_keyboard

router = Router()

async def get_achievements(msg: types.Message):
    try:
        async with SessionLocal() as session:
            result = await session.execute(select(User).filter_by(telegram_id=msg.from_user.id))
            user = result.scalars().first()

            if not user:
                await msg.message.answer("Вы не зарегистрированы!")
                return

            result = await session.execute(select(Achievement).filter_by(user_id=user.id))
            achievements = result.scalars().all()

            if not achievements:
                await msg.message.edit_text("У вас пока нет ачивок.",reply_markup=go_profile_keyboard())
            else:
                text = "\n".join([f"{a.name} - {a.description}" for a in achievements])
                await msg.message.answer(f"Ваши ачивки:\n{text}")
    except SQLAlchemyError as e:
        await msg.message.answer("Произошла ошибка при работе с базой данных. Попробуйте позже.")
        print(f"Database error: {e}")


@router.callback_query(F.data == "achievements")
async def send_achievements(callback: types.CallbackQuery):
    await get_achievements(callback)
    await callback.answer()