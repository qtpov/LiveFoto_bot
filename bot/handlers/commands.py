from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db.crud import add_user
from bot.db.session import SessionLocal
from bot.keyboards.inline import gender_keyboard, form_keyboard, go_profile_keyboard
import logging

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
    try:
        age = int(message.text)
        if age < 1 or age > 120:
            await message.answer("Пожалуйста, введите корректный возраст (от 1 до 120).")
            return
        await state.update_data(age=age)  # Сохраняем как число
        await message.answer("Твой пол?", reply_markup=gender_keyboard())
        await state.set_state(Registration.gender)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный возраст (число).")

@router.callback_query(Registration.gender, F.data.in_(["Male", "Female"]))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with SessionLocal() as session:
        try:
            await add_user(session, callback.from_user.id, data["name"], data["age"], callback.data)
            await callback.message.edit_text("Теперь заполни анкету *ссылка*", reply_markup=form_keyboard())
        except ValueError as e:
            await callback.message.answer(str(e))
        except Exception as e:
            await callback.message.answer("Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
            logging.error(f"Ошибка при регистрации: {e}")

    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "completed_form")
async def completed_profile(callback: types.CallbackQuery):
    await callback.message.edit_text("Регистрация завершена! Теперь перейди в профиль героя", reply_markup=go_profile_keyboard())
    await callback.answer()