from aiogram import Router, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from aiogram.filters import Command
from bot.db.models import UserResult, User
from bot.db.crud import get_tasks, get_user_results
from aiogram.types import FSInputFile, InputMediaPhoto
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.inline import *
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from pathlib import Path
from sqlalchemy import select, func
import os

router = Router()

# Словарь с распределением квестов по дням
quests_by_day = {
    1: [
        (1, "Знакомство с локацией"),
        (2, "Места для фото"),
        (3, "Знакомство с Базой")
    ],
    2: [
        (4, "Приборка локаций"),
        (5, "Места для фото 2.0"),
        (6, "Фото клиента")
    ],
    3: [
        (7, "Товары и цены"),
        (8, "Продажи теория"),
        (9, "Знакомство с коллегами")
    ],
    # Добавьте остальные дни
}

# Получение текущего дня пользователя
async def get_current_day(user_id: int):
    async with SessionLocal() as session:
        user = await session.execute(select(User).filter(User.telegram_id == user_id))
        user = user.scalars().first()

        if not user:
            await message_or_callback.edit_text("Ты ещё не зарегистрирован! Напиши /start.")
            return

        curr_day = user.day
    return curr_day

# Добавление квестов в user_results
async def add_quests_to_user_results(user_id: int, day: int):
    async with SessionLocal() as session:
        for quest_id, _ in quests_by_day[day]:  # Берем только ID квестов
            # Проверяем, существует ли уже запись для этого квеста
            existing_result = await session.execute(
                select(UserResult).filter(
                    UserResult.user_id == user_id,
                    UserResult.quest_id == quest_id
                )
            )
            existing_result = existing_result.scalars().first()

            if not existing_result:
                # Если записи нет, создаём новую
                user_result = UserResult(
                    user_id=user_id,
                    quest_id=quest_id,
                    state="не выполнен",
                    attempt=1,
                    result=0
                )
                session.add(user_result)
        await session.commit()

class QuestState(StatesGroup):
    waiting_for_answer = State()

# Словарь с правильными ответами для каждого вопроса
correct_answers = {
    1: "base",
    2: "stand",
    3: "entrance",
    4: "food-court",
    5: "toilet"
}

# Жесткое описание квестов

@router.callback_query(F.data == "start_quest")
async def quest_1(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_quest_id = user_data.get("current_quest_id", 1)  # Получаем текущий квест из состояния

    await state.set_state(QuestState.waiting_for_answer)
    await state.update_data(current_question=1)

    # Формируем абсолютный путь к файлу (с учетом папки handlers)
    relative_path = f"handlers/media/photo/map1.jpg"
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
        caption="Квест 1: \n"
        "Перед тобой карта парка, выбери кнопкой внизу что находится под номером 1",
        reply_markup=quest1_keyboard()
    )

    await callback.answer()

# Базовый путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent

# Обработчик callback'ов для всех вопросов
@router.callback_query(F.data.in_(correct_answers.values()), QuestState.waiting_for_answer)
async def handle_quest_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)
    current_quest_id = user_data.get("current_quest_id", 1)  # Получаем текущий квест из состояния

    async with SessionLocal() as session:
        # Получаем запись для текущего квеста
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == current_quest_id  # Используем текущий квест
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            # Если записи нет, создаём новую
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=current_quest_id,
                state="не выполнен",
                attempt=1,
                result=0
            )
            session.add(user_result)
            await session.commit()

        # Проверяем, выполнен ли уже квест
        if user_result.state == "выполнен":
            await callback.answer("Этот квест уже выполнен!")
            return

        # Проверяем ответ
        if callback.data == correct_answers[current_question]:
            correct_count += 1
            user_result.result += 1  # Увеличиваем result в БД
            await callback.answer('Верный ответ!')
        else:
            await callback.answer('Ответ неверный.')

        # Обновляем состояние квеста
        if current_question == len(correct_answers):
            user_result.state = "выполнен"  # Квест выполнен

        # Сохраняем изменения в БД
        await session.commit()

    # Обновляем состояние FSM
    await state.update_data(correct_count=correct_count)

    # Переход к следующему вопросу
    current_question += 1
    if current_question > len(correct_answers):
        # Все вопросы пройдены
        await callback.message.delete()
        await callback.message.answer(f"Все вопросы пройдены! 🎉\nВерных ответов: {correct_count} из {len(correct_answers)}")

        # Переход к следующему квесту
        current_day = await get_current_day(callback.from_user.id)
        quests_today = quests_by_day.get(current_day, [])
        next_quest_id = None

        # Находим следующий невыполненный квест
        for quest_id, _ in quests_today:
            if quest_id > current_quest_id:
                next_quest_id = quest_id
                break

        if next_quest_id:
            await state.update_data(current_quest_id=next_quest_id, current_question=1, correct_count=0)
            await globals()[f"quest_{next_quest_id}"](callback, state)
        else:
            await callback.message.answer("Все квесты на сегодня выполнены! 🎉")
            await state.clear()
    else:
        await state.update_data(current_question=current_question)
        await callback.message.edit_caption(
            caption=f"Вопрос {current_question}: Что находится под номером {current_question}?\n"
            f"Верных ответов: {correct_count} из {len(correct_answers)}",
            reply_markup=quest1_keyboard()
        )
    await callback.answer()



async def quest_2(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(QuestState.waiting_for_answer)
    await state.update_data(current_question=1)

    # Пример отправки сообщения для квеста 2
    await callback.message.answer("Квест 2: Ответьте на вопрос.")
    await callback.message.answer("Вопрос: Что находится под номером 1?")
    await callback.answer()

async def quest_3(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(QuestState.waiting_for_answer)
    await state.update_data(current_question=1)

    # Пример отправки сообщения для квеста 3
    await callback.message.answer("Квест 3: Знакомство с Базой.")
    await callback.message.answer("Вопрос: Что находится под номером 3?")
    await callback.answer()

# Вывод списка квестов на сегодня
async def show_todays_quests(callback: types.CallbackQuery, day: int):
    user_id = callback.from_user.id

    async with SessionLocal() as session:
        # Получаем все квесты для текущего дня
        quests_today = quests_by_day.get(day, [])

        # Получаем состояние квестов пользователя
        user_results = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == user_id,
                UserResult.quest_id.in_([quest[0] for quest in quests_today])  # Фильтруем по квестам текущего дня
            )
        )
        user_results = user_results.scalars().all()

        # Создаем словарь для быстрого доступа к состоянию квестов
        user_results_dict = {result.quest_id: result for result in user_results}

        # Формируем текст с пометками о выполнении
        text = "Квесты на сегодня:\n"
        for quest_id, quest_title in quests_today:
            status = "не выполнен"
            if quest_id in user_results_dict:
                if user_results_dict[quest_id].state == "выполнен":
                    status = "выполнен"
            text += f"{quest_id}: {quest_title} - {status}\n"

        # Отправляем сообщение с квестами
        await callback.message.edit_text(text, reply_markup=go_quests_keyboard())


# Запуск квестов для пользователя
@router.callback_query(F.data == "quests")
async def start_quests(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    current_day = await get_current_day(user_id)  # Функция, которая возвращает текущий день пользователя

    async with SessionLocal() as session:
        # Получаем все квесты для текущего дня
        quests_today = quests_by_day.get(current_day, [])

        # Получаем состояние квестов пользователя
        user_results = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == user_id,
                UserResult.quest_id.in_([quest[0] for quest in quests_today])  # Фильтруем по квестам текущего дня
            )
        )
        user_results = user_results.scalars().all()

        # Создаем словарь для быстрого доступа к состоянию квестов
        user_results_dict = {result.quest_id: result for result in user_results}

        # Находим первый невыполненный квест
        first_uncompleted_quest = None
        for quest_id, quest_title in quests_today:
            if quest_id not in user_results_dict or user_results_dict[quest_id].state != "выполнен":
                first_uncompleted_quest = quest_id
                break

        if first_uncompleted_quest is None:
            # Все квесты выполнены
            await callback.message.edit_text("Все квесты на сегодня выполнены! 🎉", reply_markup=go_profile_keyboard())
            await callback.answer()
            return

        # Начинаем с первого невыполненного квеста
        await state.update_data(current_quest_id=first_uncompleted_quest)
        await globals()[f"quest_{first_uncompleted_quest}"](callback, state)
        await callback.answer()
