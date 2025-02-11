from aiogram import Router, types
from aiogram.filters import Command
from database.session import get_db
from database.models import User, Achievement

router = Router()


@router.message(Command("profile"))
async def profile(message: types.Message):
    db = get_db()
    user = db.query(User).filter_by(telegram_id=message.from_user.id).first()
    if not user:
        await message.answer("Ты ещё не зарегистрирован! Напиши /start.")
        return

    last_achievement = db.query(Achievement).filter_by(user_id=user.id).order_by(Achievement.id.desc()).first()
    achievement_text = last_achievement.title if last_achievement else "Нет ачивок"

    text = f"""
🧑‍💻 *Профиль героя*  
👤 ФИО: {user.fio}  
🎂 Возраст: {user.age}  
🏆 Последняя ачивка: {achievement_text}  
"""
    await message.answer(text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Квесты")],
            [types.KeyboardButton(text="Мини-игры")],
            [types.KeyboardButton(text="Ачивки")],
            [types.KeyboardButton(text="База знаний")]
        ], resize_keyboard=True
    ))
