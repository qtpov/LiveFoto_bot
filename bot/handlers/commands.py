from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db.crud import add_user
from bot.db.session import SessionLocal

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
        age = int(message.text)  # Преобразуем строку в целое число
        if age < 1 or age > 120:  # Проверка на корректный возраст
            await message.answer("Пожалуйста, введите корректный возраст (от 1 до 120).")
            return
        await state.update_data(age=age)  # Сохраняем как число
        await message.answer("Твой пол? (М/Ж)")
        await state.set_state(Registration.gender)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный возраст (число).")


@router.message(Registration.gender)
async def process_gender(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with SessionLocal() as session:
        try:
            await add_user(session, message.from_user.id, data["name"], data["age"], message.text)
            await message.answer("Регистрация завершена! Теперь перейди в профиль героя командой /profile")
        except ValueError as e:
            await message.answer(str(e))  # Сообщаем пользователю об ошибке
        except Exception as e:
            await message.answer("Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
            logging.error(f"Ошибка при регистрации: {e}")  # Логируем ошибку для отладки

    await state.clear()