from aiogram import Router, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from aiogram.filters import Command
from bot.db.models import Task, UserResult
from bot.db.crud import get_tasks, get_user_results
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import create_inline_keyboard, create_inline_keyboard_2, cancel_keyboard
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from sqlalchemy import select
router = Router()

# Клавиатура для меню
def make_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Добавить задание"))
    builder.add(KeyboardButton(text="Показать задания"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

class TaskCreation(StatesGroup):
    title = State()
    description = State()
    options = State()
    correct_answer = State()
    day = State()
    quest_id = State()



@router.message(Command("quests"))
async def start(message: types.Message):
    await message.answer("Выбери действие:", reply_markup=make_keyboard())


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
async def process_task_day(message: types.Message, state: FSMContext):
    await state.update_data(correct_answer=message.text)
    await message.answer("Введите цифру дня на который расчитан квест:")
    await state.set_state(TaskCreation.day)

@router.message(TaskCreation.day)
async def process_task_day(message: types.Message, state: FSMContext):
    await state.update_data(day=int(message.text))
    await message.answer("Введите цифру номера группы заданий к которому добавить вопрос:")
    await state.set_state(TaskCreation.quest_id)

@router.message(TaskCreation.quest_id)
async def process_task_correct_answer(message: types.Message, state: FSMContext):
    async with SessionLocal() as db:
        quest_id = int(message.text)
        data = await state.get_data()

        task = Task(
            title=data["title"],
            description=data["description"],
            options=data["options"],
            correct_answer=data["correct_answer"],
            day = data['day'],
            quest_id = quest_id
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

class EditTaskStates(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_field = State()
    waiting_for_new_value = State()

@router.message(Command("edit_task"))
async def start_edit_task(message: types.Message, state: FSMContext):
    if message.from_user.id != 693131022:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Введите ID задания, которое хотите отредактировать:")
    await state.set_state(EditTaskStates.waiting_for_task_id)

@router.message(EditTaskStates.waiting_for_task_id)
async def process_task_id(message: types.Message, state: FSMContext):
    try:
        task_id = int(message.text)
        await state.update_data(task_id=task_id)
        await message.answer(
            "Какое поле вы хотите отредактировать? (title, description, options, correct_answer)",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(EditTaskStates.waiting_for_field)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID задания (число).")

@router.message(EditTaskStates.waiting_for_field)
async def process_field(message: types.Message, state: FSMContext):
    valid_fields = ["title", "description", "options", "correct_answer"]
    field = message.text.strip().lower()

    if field in valid_fields:
        await state.update_data(field=field)
        await message.answer(f"Введите новое значение для поля '{field}':")
        await state.set_state(EditTaskStates.waiting_for_new_value)
    else:
        await message.answer("Некорректное поле. Выберите одно из: title, description, options, correct_answer.")

@router.message(EditTaskStates.waiting_for_new_value)
async def process_new_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    task_id = data["task_id"]
    field = data["field"]
    new_value = message.text

    async with SessionLocal() as session:
        task = await session.execute(select(Task).filter(Task.id == task_id))
        task = task.scalars().first()

        if not task:
            await message.answer("Задание с таким ID не найдено.")
            await state.clear()
            return

        if field == "options":
            new_value = new_value.split(",")  # Преобразуем строку в массив
        setattr(task, field, new_value)  # Обновляем поле

        await session.commit()
        await session.refresh(task)

        await message.answer(f"Задание успешно обновлено!\nНовые данные:\n"
                                 f"Название: {task.title}\n"
                                 f"Описание: {task.description}\n"
                                 f"Варианты: {', '.join(task.options)}\n"
                                 f"Правильный ответ: {task.correct_answer}")
        await state.clear()

@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Редактирование отменено.")
    await callback.answer()







def get_current_day():
    # Пример логики: если сегодня первый день, возвращаем 1, и т.д.
    # Здесь можно использовать datetime для определения текущего дня
    return 1  # Заглушка, замените на реальную логику



def go_quests_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить", callback_data="start_quest")]
    ])


@router.callback_query(F.data == "quests")
async def show_tasks(callback: types.CallbackQuery):
    # Определяем текущий день (например, 1, 2, 3)
    current_day = get_current_day()  # Функция, которая возвращает текущий день

    async with SessionLocal() as db:
        # Получаем квесты на текущий день
        stmt = select(Task.quest_id, Task.title).where(Task.day == current_day).distinct(Task.quest_id)
        result = await db.execute(stmt)
        quests = result.all()

        if not quests:
            await callback.message.answer("Заданий на сегодня нет.")
            return

        # Получаем результаты пользователя
        user_id = callback.from_user.id
        user_results = await get_user_results(db, user_id=user_id)

        # Создаем словарь для хранения статусов квестов
        task_statuses = {result.task_id: result.state for result in user_results}

        # Формируем список квестов с их статусами
        text = "Доступно сегодня:\n"
        for quest in quests:
            quest_id, title = quest

            # Получаем все задачи для этого квеста
            tasks_stmt = select(Task.id).where(Task.quest_id == quest_id)
            tasks_result = await db.execute(tasks_stmt)
            task_ids = tasks_result.scalars().all()

            # Определяем статус квеста на основе статусов всех его задач
            statuses = [task_statuses.get(task_id, "не выполнен") for task_id in task_ids]
            if all(status == "выполнен" for status in statuses):
                status = "выполнен"
            elif any(status == "на проверке" for status in statuses):
                status = "на проверке"
            else:
                status = "не выполнен"

            text += f"{title} - {status}\n"

        await callback.message.answer(text, reply_markup=go_quests_keyboard())
    await callback.answer()

@router.callback_query(F.data == 'start_quest')
async def process_task_callback(callback: types.CallbackQuery):
    # Определяем, с какого квеста начинать (например, первый квест на текущий день)
    current_day = get_current_day()
    async with SessionLocal() as session:
        stmt = select(Task).where(Task.day == current_day).order_by(Task.quest_id, Task.id).limit(1)
        result = await session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await callback.message.answer("Заданий не найдено")
            return

        # Отправляем первое задание квеста
        await callback.message.edit_text(
            f"{task.title}\n{task.description}",
            reply_markup=create_inline_keyboard_2(task.options, callback_prefix=f"qw_{task.id}")
        )

    await callback.answer()

@router.callback_query(F.data.startswith("qw_"))
async def process_task1_callback(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])  # Извлекаем task_id из callback_data

    async with SessionLocal() as session:
        # Получаем текущее задание
        task = await session.execute(select(Task).filter(Task.id == task_id))
        task = task.scalars().first()

        if not task:
            await callback.message.answer("Заданий не найдено")
            return

        # Проверяем ответ
        if callback.data.split("_")[2] == task.correct_answer:
            await callback.answer('Верный ответ!')

            # Получаем следующее задание в текущем квесте
            next_task_stmt = select(Task).where(
                (Task.quest_id == task.quest_id) & (Task.id > task.id))
            next_task_result = await session.execute(next_task_stmt)
            next_task = next_task_result.scalars().first()

            if next_task:
                # Если есть следующее задание в текущем квесте, отправляем его
                await callback.message.edit_text(
                    f"{next_task.title}\n{next_task.description}",
                    reply_markup=create_inline_keyboard_2(next_task.options, callback_prefix=f"qw_{next_task.id}")
                )
            else:
                # Если задания в текущем квесте закончились, ищем следующий квест
                next_quest_stmt = select(Task).where(
                    (Task.day == task.day) & (Task.quest_id > task.quest_id))
                next_quest_result = await session.execute(next_quest_stmt)
                next_quest = next_quest_result.scalars().first()

                if next_quest:
                    # Если есть следующий квест, отправляем его первое задание
                    await callback.message.edit_text(
                        f"Поздравляем! Вы завершили квест '{task.quest_id}'.\n"
                        f"Начинаем следующий квест: '{next_quest.quest_id}'.\n"
                        f"{next_quest.title}\n{next_quest.description}",
                        reply_markup=create_inline_keyboard_2(next_quest.options, callback_prefix=f"qw_{next_quest.id}")
                    )
                else:
                    # Если квестов больше нет, сообщаем об этом
                    await callback.message.edit_text("Поздравляем! Вы прошли все квесты на сегодня.")
        else:
            await callback.message.edit_text('Ответ неверный. Попробуйте снова.')

    await callback.answer()