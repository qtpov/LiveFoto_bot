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
from bot.db.models import Task
from bot.keyboards.inline import gender_keyboard, form_keyboard, go_profile_keyboard
import logging

router = Router()

class Registration(StatesGroup):
    name = State()
    age = State()
    gender = State()

class TaskCreation(StatesGroup):
    title = State()
    description = State()
    options = State()
    correct_answer = State()

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Введи своё ФИО:")
    await state.set_state(Registration.name)

# Клавиатура для меню
def make_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Добавить задание"))
    builder.add(KeyboardButton(text="Показать задания"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@router.message(Command("quests"))
async def start(message: types.Message):
    await message.answer("Выбери действие:", reply_markup=make_keyboard())

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

# Обработка кнопки "Добавить задание"
@router.message(F.text == "Добавить задание")
async def add_task(message: types.Message, state: FSMContext):
    await message.answer("Введите название задания:")
    await state.set_state(TaskCreation.title)

# Обработка ввода названия задания
@router.message(TaskCreation.title)
async def process_task_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите текст задания:")
    await state.set_state(TaskCreation.description)

# Обработка ввода текста задания
@router.message(TaskCreation.description)
async def process_task_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите варианты ответов через запятую:")
    await state.set_state(TaskCreation.options)

# Обработка ввода вариантов ответов
@router.message(TaskCreation.options)
async def process_task_options(message: types.Message, state: FSMContext):
    options = message.text.split(",")
    await state.update_data(options=options)
    await message.answer("Введите правильный ответ:")
    await state.set_state(TaskCreation.correct_answer)

# Обработка ввода правильного ответа
@router.message(TaskCreation.correct_answer)
async def process_task_correct_answer(message: types.Message, state: FSMContext):
    async with SessionLocal() as db:
        correct_answer = message.text
        data = await state.get_data()

        task = Task(
            title=data["title"],
            description=data["description"],
            options=data["options"],
            correct_answer=correct_answer
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

    await message.answer(f"Задание '{data['title']}' успешно добавлено!", reply_markup=make_keyboard())
    await state.clear()

# Обработка кнопки "Показать задания"
@router.message(F.text == "Показать задания")
async def show_tasks(message: types.Message):
    async with SessionLocal() as db:
        result = await db.execute(select(Task))
        tasks = result.scalars().all()

        if not tasks:
            await message.answer("Заданий пока нет.")
            return

        for task in tasks:
            await message.answer(
                f"Название: {task.title}\n"
                f"Описание: {task.description}\n"
                f"Варианты: {', '.join(task.options)}\n"
                f"Правильный ответ: {task.correct_answer}"
            )