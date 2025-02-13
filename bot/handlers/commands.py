from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db.crud import add_user
router = Router()


class Registration(StatesGroup):
    name = State()
    age = State()
    gender = State()

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Введи своё ФИО:")
    await state.set_state(Registration.name)

@router.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Registration.age)

@router.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Твой пол? (М/Ж)")
    await state.set_state(Registration.gender)

@router.message(Registration.gender)
async def process_gender(message: types.Message, state: FSMContext):
    data = await state.get_data()
    add_user(message.from_user.id, data["name"], data["age"], message.text)
    await state.clear()
    await message.answer("Регистрация завершена! Теперь перейди в профиль героя командой /profile")
