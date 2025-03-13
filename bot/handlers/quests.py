from aiogram import Router, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from aiogram.filters import Command
from bot.db.models import Task, UserResult,User
from bot.db.crud import get_tasks, get_user_results
from aiogram.types import FSInputFile, InputMediaPhoto
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import create_inline_keyboard, create_inline_keyboard_2, cancel_keyboard, go_quests_keyboard, go_profile_keyboard
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from pathlib import Path
from sqlalchemy import select, func
import os
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
    photo = State()



@router.message(Command("add_quests"))
async def start(message: types.Message):
    if message.from_user.id != 693131022:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
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
async def process_task_day(message: types.Message, state: FSMContext):
    await state.update_data(quest_id=int(message.text))
    await message.answer("Отправьте путь к фото:")
    await state.set_state(TaskCreation.photo)

@router.message(TaskCreation.photo)
async def process_task_correct_answer(message: types.Message, state: FSMContext):
    async with SessionLocal() as db:
        photo = message.text
        data = await state.get_data()

        task = Task(
            title=data["title"],
            description=data["description"],
            options=data["options"],
            correct_answer=data["correct_answer"],
            day = data['day'],
            quest_id = data['quest_id'],
            photo = photo

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
                f"Правильный ответ: {task.correct_answer}\n"
                f"День: {task.day}\n"
                f"Номер квеста: {task.quest_id}\n"
                f"Сылка на фото: {task.photo}\n")

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
            "Какое поле вы хотите отредактировать? (title, description, options, correct_answer, day, quest_id, photo)",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(EditTaskStates.waiting_for_field)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID задания (число).")

@router.message(EditTaskStates.waiting_for_field)
async def process_field(message: types.Message, state: FSMContext):
    valid_fields = ["title", "description", "options", "correct_answer","day", "quest_id", "photo"]
    field = message.text.strip().lower()

    if field in valid_fields:
        await state.update_data(field=field)
        await message.answer(f"Введите новое значение для поля '{field}':")
        await state.set_state(EditTaskStates.waiting_for_new_value)
    else:
        await message.answer("Некорректное поле. Выберите одно из: title, description, options, correct_answer, day, quest_id, photo.")

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
        if field in ["day", "quest_id"]:
            new_value = int(new_value)
        setattr(task, field, new_value)  # Обновляем поле

        await session.commit()
        await session.refresh(task)

        await message.answer(f"Задание успешно обновлено!\nНовые данные:\n"
                                 f"Название: {task.title}\n"
                                 f"Описание: {task.description}\n"
                                 f"Варианты: {', '.join(task.options)}\n"
                                 f"Правильный ответ: {task.correct_answer}\n"
                                 f"День: {task.day}\n"
                                 f"Номер квеста: {task.quest_id}\n"
                                 f"Сылка на фото: {task.photo}\n")
        await state.clear()

@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Редактирование отменено.")
    await callback.answer()







async def get_current_day(user_id: int):
    async with SessionLocal() as session:
        user = await session.execute(select(User).filter(User.telegram_id == user_id))
        user = user.scalars().first()

        if not user:
            await message_or_callback.edit_text("Ты ещё не зарегистрирован! Напиши /start.")
            return

        curr_day = user.day
    return curr_day


@router.callback_query(F.data == "quests")
async def show_tasks(callback: types.CallbackQuery):
    current_day = await get_current_day(callback.from_user.id)  # Функция, которая возвращает текущий день

    async with SessionLocal() as db:
        # Получаем квесты на текущий день
        stmt = select(Task.quest_id, Task.title).where(Task.day == current_day).distinct(Task.quest_id)
        result = await db.execute(stmt)
        quests = result.all()

        if not quests:
            await callback.message.edit_text("Заданий на сегодня нет.",reply_markup=go_profile_keyboard())
            return

        # Получаем результаты пользователя
        user_id = callback.from_user.id
        user_results = await get_user_results(db, user_id=user_id)

        # Создаем словарь для хранения статусов квестов
        quest_statuses = {result.quest_id: result.state for result in user_results}

        # Проверяем, выполнены ли все квесты
        all_quests_completed = all(
            quest_statuses.get(quest_id, "не выполнен") == "выполнен" for quest_id, _ in quests
        )

        if all_quests_completed:
            await callback.message.edit_text("Все квесты на сегодня выполнены! 🎉",reply_markup=go_profile_keyboard())
            return

        # Формируем список квестов с их статусами
        text = "Доступно сегодня:\n"
        for quest in quests:
            quest_id, title = quest

            # Получаем все задачи для этого квеста
            tasks_stmt = select(Task.id).where(Task.quest_id == quest_id)
            tasks_result = await db.execute(tasks_stmt)
            task_ids = tasks_result.scalars().all()

            # Определяем статус квеста на основе статусов всех его задач
            statuses = [quest_statuses.get(quest_id, "не выполнен") for _ in task_ids]
            if all(status == "выполнен" for status in statuses):
                status = "выполнен"
            elif any(status == "на проверке" for status in statuses):
                status = "на проверке"
            else:
                status = "не выполнен"

            text += f"{title} - {status}\n"

        await callback.message.edit_text(text, reply_markup=go_quests_keyboard())
    await callback.answer()

# Базовый путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent

@router.callback_query(F.data == 'start_quest')
async def process_task_callback(callback: types.CallbackQuery):

    # Получаем задачу из базы данных
    current_day = await get_current_day(callback.from_user.id)
    async with SessionLocal() as session:
        stmt = select(Task).where(Task.day == current_day).order_by(Task.quest_id, Task.id).limit(1)
        result = await session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await callback.message.answer("Заданий не найдено")
            return

        # Формируем абсолютный путь к файлу (с учетом папки handlers)
        relative_path = f"handlers/{task.photo}"
        photo_path = BASE_DIR / relative_path

        # Проверяем, существует ли файл
        if not photo_path.exists():
            await callback.message.answer("Файл с изображением не найден.")
            return

        # Отправляем фото
        await callback.message.delete()
        photo = FSInputFile(str(photo_path))  # Преобразуем Path в строку
        await callback.message.answer_photo(
            photo,
            caption=f"{task.title}\n{task.description}",
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

        # Получаем результат пользователя для этого задания
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == task.quest_id
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=task.quest_id,  # Сохраняем quest_id
                state="не выполнен",
                attempt=1,
                result=0
            )
            session.add(user_result)

        # Проверяем ответ
        if callback.data.split("_")[2] == task.correct_answer:
            user_result.result += 1
            user_result.state = "выполнен"
            await callback.answer('Верный ответ!')
        else:
            await callback.answer('Ответ неверный.')

        # Получаем следующее задание в текущем квесте
        next_task_stmt = select(Task).where(
            (Task.quest_id == task.quest_id) & (Task.id > task.id))
        next_task_result = await session.execute(next_task_stmt)
        next_task = next_task_result.scalars().first()

        if next_task:
            # Формируем абсолютный путь к файлу (с учетом папки handlers)
            relative_path = f"handlers/{next_task.photo}"
            photo_path = BASE_DIR / relative_path
            # Если есть следующее задание в текущем квесте, отправляем его
            photo = InputMediaPhoto(media=FSInputFile(str(photo_path)))
            await callback.message.edit_media(photo)
            await callback.message.edit_caption(caption=f"{next_task.title}\n{next_task.description}",
                                                reply_markup=create_inline_keyboard_2(next_task.options,
                                                                                      callback_prefix=f"qw_{next_task.id}")
                                                )
        else:
            # Если задания в текущем квесте закончились, ищем следующий квест
            next_quest_stmt = select(Task).where(
                (Task.day == task.day) & (Task.quest_id > task.quest_id))
            next_quest_result = await session.execute(next_quest_stmt)
            next_quest = next_quest_result.scalars().first()

            if next_quest:
                # Формируем абсолютный путь к файлу (с учетом папки handlers)
                relative_path = f"handlers/{next_quest.photo}"
                photo_path = BASE_DIR / relative_path

                # Подсчитываем общее количество верных ответов для текущего квеста
                total_correct_in_quest = user_result.result

                # Подсчитываем общее количество заданий в квесте
                total_tasks_in_quest = await session.execute(
                    select(func.count(Task.id)).filter(
                        Task.quest_id == task.quest_id
                    )
                )
                total_tasks_in_quest = total_tasks_in_quest.scalar() or 0

                # Если есть следующее задание в текущем квесте, отправляем его
                photo = InputMediaPhoto(media=FSInputFile(str(photo_path)))
                await callback.message.edit_media(media=photo)
                await callback.message.edit_caption(caption=f"Вы завершили квест {task.quest_id}.\n"
                                                            f"Верных ответов: {total_correct_in_quest} из {total_tasks_in_quest}\n"
                                                            f"Начинаем следующий квест.\n\n"
                                                            f"{next_quest.title}\n{next_quest.description}",
                                                    reply_markup=create_inline_keyboard_2(next_quest.options,
                                                                                          callback_prefix=f"qw_{next_quest.id}")
                                                    )
            else:
                await callback.message.delete()
                # Если квестов больше нет, сообщаем об этом
                # Подсчитываем общее количество верных ответов для текущего квеста
                total_correct_in_quest = user_result.result

                # Подсчитываем общее количество заданий в квесте
                total_tasks_in_quest = await session.execute(
                    select(func.count(Task.id)).filter(
                        Task.quest_id == task.quest_id
                    )
                )
                total_tasks_in_quest = total_tasks_in_quest.scalar() or 0

                # Проверяем, выполнены ли все задачи с первой попытки
                all_tasks_completed_first_try = await session.execute(
                    select(func.count(UserResult.id)).filter(
                        UserResult.user_id == callback.from_user.id,
                        UserResult.quest_id == task.quest_id,
                        UserResult.attempt == 1,
                        UserResult.state == "выполнен"
                    )
                )
                all_tasks_completed_first_try = all_tasks_completed_first_try.scalar() == total_tasks_in_quest

                # Если все задачи выполнены с первой попытки, выдаем ачивку
                if all_tasks_completed_first_try:
                    achievement = Achievement(
                        user_id=callback.from_user.id,
                        quest_id=task.quest_id,
                        name="Мастер квеста",
                        description="Выполнил все задачи квеста с первой попытки!"
                    )
                    session.add(achievement)
                    await session.commit()
                    await callback.message.answer(
                        "🎉 Поздравляем! Вы выполнили все задачи квеста с первой попытки и получили ачивку!"
                    )

                # Выводим сообщение с результатами
                await callback.message.answer(
                    f"Верных ответов: {total_correct_in_quest} из {total_tasks_in_quest}\n"
                    f"Поздравляем! Вы прошли все квесты на сегодня.\n",
                    reply_markup=go_profile_keyboard()
                )

        await session.commit()

    await callback.answer()