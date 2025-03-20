from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import SessionLocal
from ..db.models import Achievement, User
from sqlalchemy.exc import SQLAlchemyError
from aiogram import Router, types, F
from bot.keyboards.inline import go_profile_keyboard
from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Кэш для хранения ачивок пользователей (опционально)
achievements_cache = {}

# Количество ачивок на одной странице
ACHIEVEMENTS_PER_PAGE = 5

async def get_achievements(msg: types.Message | types.CallbackQuery, page: int = 1):
    try:
        user_id = msg.from_user.id

        # Проверяем кэш (если используется)
        if user_id in achievements_cache:
            achievements = achievements_cache[user_id]
        else:
            async with SessionLocal() as session:
                # Получаем пользователя по telegram_id
                user = await session.execute(select(User).filter_by(telegram_id=user_id))
                user = user.scalars().first()

                if not user:
                    await msg.answer("Вы не зарегистрированы!")
                    return

                # Получаем ачивки пользователя по user_id (telegram_id)
                result = await session.execute(select(Achievement).filter_by(user_id=user_id))
                achievements = result.scalars().all()

                # Сохраняем в кэш (опционально)
                achievements_cache[user_id] = achievements

        if not achievements:
            # Если ачивок нет
            response_text = "У вас пока нет ачивок. 😐"
            reply_markup = go_profile_keyboard()
        else:
            # Пагинация ачивок
            start = (page - 1) * ACHIEVEMENTS_PER_PAGE
            end = start + ACHIEVEMENTS_PER_PAGE
            achievements_page = achievements[start:end]

            # Формируем текст с ачивками
            achievements_text = "\n".join(
                [f" {hbold(a.name)}\n{hitalic(a.description)}\n" for a in achievements_page]
            )
            response_text = f"Ваши ачивки (страница {page}):\n{achievements_text}"

            # Создаем клавиатуру для пагинации
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[])
            if page > 1:
                reply_markup.inline_keyboard.append([
                    InlineKeyboardButton(text="⬅️ Назад", callback_data=f"achievements_{page - 1}")
                ])
            if end < len(achievements):
                reply_markup.inline_keyboard.append([
                    InlineKeyboardButton(text="Вперед ➡️", callback_data=f"achievements_{page + 1}")
                ])
            reply_markup.inline_keyboard.append([
                InlineKeyboardButton(text=" В профиль", callback_data="profile")
            ])

        # Отправляем сообщение
        if isinstance(msg, types.CallbackQuery):
            await msg.message.edit_text(response_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await msg.answer(response_text, reply_markup=reply_markup, parse_mode="HTML")

    except SQLAlchemyError as e:
        error_message = "Произошла ошибка при работе с базой данных. Попробуйте позже."
        if isinstance(msg, types.CallbackQuery):
            await msg.message.answer(error_message)
        else:
            await msg.answer(error_message)
        print(f"Database error: {e}")


@router.callback_query(F.data.startswith("achievements_"))
async def handle_achievements_pagination(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[1])
    await get_achievements(callback, page)
    await callback.answer()


@router.callback_query(F.data == "achievements")
async def send_achievements(callback: types.CallbackQuery):
    await get_achievements(callback)
    await callback.answer()