from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import SessionLocal
from ..db.models import User
from sqlalchemy.exc import SQLAlchemyError
from bot.keyboards.inline import go_profile_keyboard
from .quiz_game import start_quiz_game
from .own_game import start_own_game
from .knowledge_test import start_knowledge_test

router = Router()


async def check_user_access(msg: types.Message | types.CallbackQuery) -> tuple[bool, User | None]:
    try:
        async with SessionLocal() as session:
            result = await session.execute(select(User).filter_by(telegram_id=msg.from_user.id))
            user = result.scalars().first()
            if not user:
                if isinstance(msg, types.CallbackQuery):
                    await msg.message.answer("Вы не зарегистрированы!")
                else:
                    await msg.answer("Вы не зарегистрины!")
                return False, None
            return True, user
    except SQLAlchemyError as e:
        if isinstance(msg, types.CallbackQuery):
            await msg.message.answer("Произошла ошибка при работе с базой данных. Попробуйте позже.")
        else:
            await msg.answer("Произошла ошибка при работе с базой данных. Попробуйте позже.")
        print(f"Database error: {e}")
        return False, None


@router.callback_query(F.data == "games")
async def send_mini_games(callback: types.CallbackQuery):
    access, user = await check_user_access(callback)
    if not access:
        await callback.answer()
        return

    if user.day == 2:
        await start_quiz_game(callback)
    elif user.day == 3:
        await show_games_menu(callback.message)
    else:
        await callback.message.edit_text("Мини-игры пока недоступны.", reply_markup=go_profile_keyboard())
    await callback.answer()

@router.callback_query(F.data == "game_quiz")
async def handle_quiz_game(callback: CallbackQuery, state: FSMContext):
    await start_quiz_game(callback, state)
    await callback.answer()

@router.callback_query(F.data == "game_own")
async def handle_own_game(callback: CallbackQuery, state: FSMContext):
    await start_own_game(callback, state)
    await callback.answer()

@router.callback_query(F.data == "game_knowledge")
async def handle_knowledge_test(callback: CallbackQuery, state: FSMContext):
    await start_knowledge_test(callback, state)
    await callback.answer()


async def show_games_menu(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Кто хочет стать Фотографом",
            callback_data="game_quiz"
        ),
        types.InlineKeyboardButton(
            text="Своя игра",
            callback_data="game_own"
        ),
        types.InlineKeyboardButton(
            text="Срез знаний",
            callback_data="game_knowledge"
        ),
        types.InlineKeyboardButton(
            text="Назад",
            callback_data="profile"
        )
    )
    builder.adjust(1)
    await message.edit_text(
        "Выберите мини-игру:",
        reply_markup=builder.as_markup()
    )