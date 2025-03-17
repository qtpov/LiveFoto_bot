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
