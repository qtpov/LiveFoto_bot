from aiogram import Router, types, F
from aiogram.filters import Command
from bot.db.models import Task
from bot.db.crud import get_tasks
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import create_inline_keyboard, create_inline_keyboard_2
from sqlalchemy.future import select
from bot.db.session import SessionLocal

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









@router.callback_query(F.data == "quests")
async def show_tasks(callback: types.CallbackQuery):
    # Получаем задания из базы данных
    async with SessionLocal() as db:
        tasks = await get_tasks(db)

        if not tasks:
            await callback.message.answer("Заданий пока нет.")
            return

        # Создаем инлайн-клавиатуру
        keyboard = create_inline_keyboard(tasks, callback_prefix="task_")

        # Отправляем сообщение с клавиатурой
        await callback.message.edit_text("Выберите задание:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("task_"))
async def process_task_callback(callback: types.CallbackQuery):
    # Извлекаем ID задания из callback_data
    task_id = int(callback.data.replace("task_", ""))
    async with SessionLocal() as session:
        task = await session.execute(select(Task).filter(Task.id == task_id))
        task = task.scalars().first()

        if not task:
            await callback.message.answer("Заданий не найдено")
            return

        # Здесь можно выполнить действия с выбранным заданием
        await callback.message.edit_text(
            f"{task.title}\n{task.description}",
            reply_markup=create_inline_keyboard_2(task.options, callback_prefix=f"qw_{task_id}")
        )

    # Подтверждаем обработку callback
    await callback.answer()

@router.callback_query(F.data.startswith("qw_"))
async def process_task1_callback(callback: types.CallbackQuery):
    task_id = int(callback.data[3:4])

    async with SessionLocal() as session:
        task = await session.execute(select(Task).filter(Task.id == task_id))
        task = task.scalars().first()

        next_task = await session.execute(select(Task).filter(Task.id == task_id + 1))
        next_task = next_task.scalars().first()

        if not task:
            await callback.message.answer("Заданий не найдено")
            return

        if callback.data[5:] == task.correct_answer:
            await callback.message.edit_text('верный ответ')
            # Добавить проверку на последнее задание
            if next_task:
                await callback.message.answer(
                    f"{next_task.title}\n{next_task.description}",
                    reply_markup=create_inline_keyboard_2(next_task.options, callback_prefix=f"qw_{task_id + 1}")
                )
            else:
                await callback.message.answer("Поздравляем! Вы прошли все задания.")
        else:
            await callback.message.edit_text('ответ неверный попробуй снова')
            return

    await callback.answer()