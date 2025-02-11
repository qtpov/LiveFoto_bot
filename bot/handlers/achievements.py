from aiogram import types
from ..db.session import SessionLocal
from ..db.models import Achievement, User


async def get_achievements(message: types.Message):
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        await message.answer("Вы не зарегистрированы!")
        return

    achievements = session.query(Achievement).filter_by(user_id=user.id).all()
    if not achievements:
        await message.answer("У вас пока нет ачивок.")
    else:
        text = "\n".join([f"{a.name} - {a.description}" for a in achievements])
        await message.answer(f"Ваши ачивки:\n{text}")

    session.close()
