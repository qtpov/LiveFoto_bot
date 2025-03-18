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
from aiogram.utils.media_group import MediaGroupBuilder
from pathlib import Path
from sqlalchemy import select, func
from random import randint
import os

router = Router()

# Словарь с распределением квестов по дням
quests_by_day = {
    1: [
        (1, "Знакомство с локацией"),
        (2, "Места для фото"),
        (3, "Знакомство с Базой"),
        (4, "Чистота на локации"),
        (5, "Места для фото 2.0"),
        (6, "Фото с клиентом"),
        (7, "Товары и цены"),
        (8, "Теория продаж"),
        (9, "Знакомство с коллегами"),
        (10, "Внешний вид"),
        (11, "Фидбек")
    ],
    2: [
        (1, "Привыкни к аппарату"),
        (2, "Фотограф"),
        (3, "Зоны фотографирования"),
        (4, "1000 и 1 поза"),
        (5, "Силует"),
        (6, "Дожми до результата"),
        (7, "В здоровом теле здоровый дух"),
        (8, "Практика фотографирования"),
        (9, "Алгоритм действий"),
        (10, "Время и кадры"),
        (11, "Знакомство с коллегами"),
        (12, "Этапы продаж"),
        (13, "Подошел, сфоткал, победил"),
        (14, "5 продаж"),
        (15, "Сила отказов"),
        (16, "Фидбек")
    ],
    3: [
        (1, "Правильное фото"),
        (2, "Собери всё"),
        (3, "ФотоОхотник"),
        (4, "Полный цикл"),
        (5, "Ценность кадра"),
        (6, "Ценности компании"),
        (7, "Клиент"),
        (8, "Фидбек")
    ],
}
# Словарь с правильными ответами для каждого вопроса
correct_answers = {
    1: "base",
    2: "stand",
    3: "entrance",
    4: "food-court",
    5: "toilet"
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


# Жесткое описание квестов
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




correct_answers_qw2 = {
    1: 'Батуты',
    2: 'Лабиринт',
    3: 'Автоматы',
    4: 'Трон',
    5: 'Детская',
    6: 'Батуты',
    7: 'Трон',
    8: 'Лабиринт',
    9: 'Детская',
    10: 'Автоматы'

}
# Базовый путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent

# Обработчик callback'ов для всех вопросов 1 квеста
@router.callback_query(F.data.in_(correct_answers.values()), QuestState.waiting_for_answer)
async def handle_quest_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)
    current_quest_id = user_data.get("current_quest_id", 1)

    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == current_quest_id
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=current_quest_id,
                state="не выполнен",
                attempt=1,
                result=0
            )
            session.add(user_result)

        if user_result.state == "выполнен":
            await callback.answer("Этот квест уже выполнен!")
            return

        if callback.data == correct_answers[current_question]:
            correct_count += 1
            user_result.result += 1
            await callback.answer('Верный ответ!')
        else:
            await callback.answer('Ответ неверный.')

        if current_question == len(correct_answers):
            user_result.state = "выполнен"

        await session.commit()

    await state.update_data(correct_count=correct_count)

    current_question += 1
    if current_question > len(correct_answers):
        # Все вопросы пройдены, изменяем старое сообщение
        await callback.message.delete()
        # await callback.message.answer(
        #     caption=f"Все вопросы пройдены! 🎉\nВерных ответов: {correct_count} из {len(correct_answers)}"
        # )

        # Переход к следующему квесту
        next_quest_id = current_quest_id + 1
        current_day = await get_current_day(callback.from_user.id)
        quests_today = quests_by_day.get(current_day, [])

        if next_quest_id in [quest[0] for quest in quests_today]:
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
    await state.update_data(current_question=1, correct_count=0)

    # Получаем текущий вопрос
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)  # Получаем текущее количество верных ответов

    # Определяем папку для текущего вопроса
    folder_name = correct_answers_qw2[current_question]

    # Формируем абсолютный путь к файлам (с учетом папки handlers)
    relative_path1 = f"handlers/media/photo/Zone/{folder_name}/1.jpg"
    relative_path2 = f"handlers/media/photo/Zone/{folder_name}/2.jpg"
    photo_path1 = BASE_DIR / relative_path1
    photo_path2 = BASE_DIR / relative_path2

    # Проверяем, существуют ли файлы
    if not photo_path1.exists() or not photo_path2.exists():
        await callback.message.answer("Файлы с изображениями не найдены.")
        await callback.message.answer(str(photo_path2))
        return


    # Отправляем два фото как медиагруппу
    album_builder = MediaGroupBuilder(caption=f"Квест 2: Вопрос {current_question}\n"
                                              "Определи на какой локации сделаны фото\n"
                                              f"Верных ответов: {correct_count} из {len(correct_answers_qw2)}")  # Используем correct_answers_qw2

    album_builder.add(type="photo", media=FSInputFile(str(photo_path1)))
    album_builder.add(type="photo", media=FSInputFile(str(photo_path2)))

    photo_messages = await callback.message.answer_media_group(media=album_builder.build())

    # Сохраняем ID всех сообщений из медиагруппы
    photo_message_ids = [msg.message_id for msg in photo_messages]

    # Отправляем текст с вопросом и клавиатурой
    question_message = await callback.message.answer(
        "выбери нужный вариант из кнопок",
        reply_markup=quest2_keyboard()
    )

    # Сохраняем ID сообщений в состоянии
    await state.update_data(
        photo_message_ids=photo_message_ids,  # Список ID сообщений с фото
        question_message_id=question_message.message_id  # ID текстового сообщения
    )

    await callback.answer()


correct_answers_qw3 = {
    1: 'Сборка Техники',
    2: 'Фотографирование',
    3: 'Ретушь',
    4: 'Печать',
    5: 'Демонстрация'

}

#для 2 квеста
@router.callback_query(F.data.in_(correct_answers_qw2.values()), QuestState.waiting_for_answer)
async def handle_quest2_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)
    current_quest_id = user_data.get("current_quest_id", 1)

    # Получаем ID предыдущих сообщений
    photo_message_ids = user_data.get("photo_message_ids", [])  # Список ID сообщений с фото
    question_message_id = user_data.get("question_message_id")  # ID текстового сообщения

    # Удаляем предыдущие сообщения
    for message_id in photo_message_ids:
        await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=message_id)
    await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=question_message_id)

    async with SessionLocal() as session:
        # Получаем запись для текущего квеста
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == current_quest_id
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

        # Проверяем, выполнен ли уже квест
        if user_result.state == "выполнен":
            await callback.answer("Этот квест уже выполнен!")
            return

        # Проверяем ответ
        if callback.data == correct_answers_qw2[current_question]:
            correct_count += 1
            user_result.result += 1  # Увеличиваем result в БД
            await callback.answer('Верный ответ!')
        else:
            await callback.answer('Ответ неверный.')

        # Обновляем состояние квеста
        if current_question == len(correct_answers_qw2):
            user_result.state = "выполнен"  # Квест выполнен

        # Сохраняем изменения в БД
        await session.commit()

    # Обновляем состояние FSM
    await state.update_data(correct_count=correct_count)

    # Переход к следующему вопросу
    current_question += 1
    if current_question > len(correct_answers_qw2):
        # Все вопросы пройдены
        await callback.message.answer(
            f"Все вопросы пройдены! 🎉\nВерных ответов: {correct_count} из {len(correct_answers_qw2)}")

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
        # Определяем папку для следующего вопроса
        folder_name = correct_answers_qw2[current_question]

        # Формируем абсолютный путь к файлам (с учетом папки handlers)
        x = randint(1, 4)
        y = randint(1, 4)
        relative_path1 = f"handlers/media/photo/Zone/{folder_name}/{x}.jpg"
        relative_path2 = f"handlers/media/photo/Zone/{folder_name}/{y}.jpg"
        photo_path1 = BASE_DIR / relative_path1
        photo_path2 = BASE_DIR / relative_path2

        # Проверяем, существуют ли файлы
        if not photo_path1.exists() or not photo_path2.exists():
            await callback.message.answer("Файлы с изображениями не найдены.")
            return

        # Отправляем два фото как медиагруппу
        album_builder = MediaGroupBuilder(caption=f"Квест 2: Вопрос {current_question}\n"
                                                  "Определи на какой локации сделаны фото\n"
                                                  f"Верных ответов: {correct_count} из {len(correct_answers_qw2)}")  # Используем correct_answers_qw2
        album_builder.add(type="photo", media=FSInputFile(str(photo_path1)))
        album_builder.add(type="photo", media=FSInputFile(str(photo_path2)))

        photo_messages = await callback.message.answer_media_group(media=album_builder.build())

        # Сохраняем ID всех сообщений из медиагруппы
        photo_message_ids = [msg.message_id for msg in photo_messages]

        # Отправляем текст с вопросом и клавиатурой
        question_message = await callback.message.answer(
            "выбери нужный вариант из кнопок",
            reply_markup=quest2_keyboard()
        )

        # Сохраняем ID сообщений в состоянии
        await state.update_data(
            photo_message_ids=photo_message_ids,  # Список ID сообщений с фото
            question_message_id=question_message.message_id,  # ID текстового сообщения
            current_question=current_question
        )

    await callback.answer()

async def quest_3(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(QuestState.waiting_for_answer)
    await state.update_data(current_question=1)

    # Получаем текущий вопрос
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)  # Получаем текущее количество верных ответов


    # Формируем абсолютный путь к файлу (с учетом папки handlers)
    relative_path = f"handlers/media/video/5.Демонстрация.mov"
    video_path = BASE_DIR / relative_path

    # Проверяем, существует ли файл
    if not video_path.exists():
        await callback.message.answer("Файл с видео не найден.")
        return

    # Отправляем фото
    # await callback.message.delete()
    video = FSInputFile(str(video_path))  # Преобразуем Path в строку
    await callback.message.answer_video(
        video,
        caption="Квест 3: \n"
                "Посмотри видео и приступи к выполнению квеста",reply_markup=quest3_keyboard_after_video()
    )

    await callback.answer()

