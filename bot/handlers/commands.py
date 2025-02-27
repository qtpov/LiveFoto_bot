from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.crud import add_user
from bot.db.session import SessionLocal
from bot.db.models import Task,User
from bot.keyboards.inline import reg_keyboard
import logging

router = Router()

class Registration(StatesGroup):
    name = State()
    age = State()
    gender = State()

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer(f'Здравствуйте{message.from_user.full_name}!\nДля продолжения необходимо пройти регистрацию,'
                         f' для продолжения нажмите кнопку снизу',reply_markup=reg_keyboard())
    # user_id = message.from_user.id
    # async with SessionLocal() as session:
    #     user = await session.execute(select(User).filter(User.telegram_id == user_id))
    #     user = user.scalars().first()
    #
    # if not user:
    #     await message.answer("Привет! Введи своё ФИО:")
    #     await state.set_state(Registration.name)
    # else:
    #     await message.answer(f"С возвращением, {user.full_name}!",reply_markup=go_profile_keyboard())

