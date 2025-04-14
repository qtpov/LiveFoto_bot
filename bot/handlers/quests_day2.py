from aiogram import Router, types, F
from aiogram.types import FSInputFile
from bot.db.models import UserResult, User, Achievement
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline import *
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from aiogram.utils.media_group import MediaGroupBuilder, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pathlib import Path
from .moderation import give_achievement, get_quest_finish_keyboard
from bot.db.crud import update_user_level, update_user_day
import datetime
import json
import logging
import asyncio
from typing import Union
from random import shuffle, randint
import os
from .states import QuestState
from bot.configurate import settings

router = Router()

admin_chat_id = settings.ADMIN_ID

# Базовый путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent

# Словарь с распределением квестов по дням
quests_by_day = {
    1: [
        (1, "Знакомство с локацией"),
        (2, "Места для фото"),
        (3, "Знакомство с Базой"),
        (4, "Чистота на локация"),
        (5, "Места для фото 2.0"),
        (6, "Фото с клиентом"),
        (7, "Товары и цены"),
        (8, "Теория продаж"),
        (9, "Знакомство с коллегами"),
        (10, "Внешний вид"),
        (11, "Фидбек")
    ],
    2: [
        (12, "Привыкни к аппарату"),
        (13, "Фотограф"),
        (14, "Зоны фотографирования"),
        (15, "1000 и 1 поза"),
        (16, "Дожми до результата"),
        (17, "В здоровом теле здоровый дух"),
        (18, "Практика фотографирования"),
        (19, "Алгоритм действий"),
        (20, "Время и кадры"),
        (21, "Знакомство с коллегами"),
        (22, "Этапы продаж"),
        (23, "Подошел, сфоткал, победил"),
        (24, "5 продаж"),
        (25, "Сила отказов"),
        (26, "Фидбек")
    ],
    3: [
        (27, "Правильное фото"),
        (28, "Собери всё"),
        (29, "ФотоОхотник"),
        (30, "Полный цикл"),
        (31, "Ценность кадра"),
        (32, "Ценности компании"),
        (33, "Клиент"),
        (34, "Фидбек")
    ],
}


# Получение текущего дня пользователя
async def get_current_day(user_id: int):
    async with SessionLocal() as session:
        user = await session.execute(select(User).filter(User.telegram_id == user_id))
        user = user.scalars().first()
        if not user:
            return None
        return user.day


# Функция для завершения квеста
async def finish_quest(callback: types.CallbackQuery, state: FSMContext, correct_count, total_questions,
                       current_quest_id):
    user_data = await state.get_data()

    # Удаляем все сообщения, связанные с текущим квестом
    try:
        photo_message_ids = user_data.get("photo_message_ids", [])
        video_message_ids = user_data.get("video_message_ids", [])
        question_message_id = user_data.get("question_message_id")

        for message_id in photo_message_ids + video_message_ids:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Проверяем, выполнено ли 100% квеста и выдаем ачивку, если это так
    if correct_count == total_questions:
        async with SessionLocal() as session:
            achievement_given = await give_achievement(callback.from_user.id, current_quest_id, session)
            if achievement_given:
                message_text = (
                    f"Квест завершен! 🎉\nВерных ответов: {correct_count} из {total_questions}\n"
                    f"Поздравляем! Вы получили ачивку за выполнение квеста на 100%!"
                )
            else:
                message_text = f"Квест завершен! 🎉\nВерных ответов: {correct_count} из {total_questions}"
    else:
        message_text = f"Есть ошибки, попробуй заново\nВерных ответов: {correct_count} из {total_questions}"

    # Отправляем новое сообщение с результатами
    message = await callback.message.answer(
        message_text,
        reply_markup=get_quest_finish_keyboard(correct_count, total_questions, current_quest_id)
    )

    # Сохраняем ID нового сообщения
    await state.update_data(question_message_id=message.message_id)


# Квест 12 - Привыкни к аппарату
async def quest_12(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Список видео с описаниями
    video_steps = [
        {
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "Квест 12. Привыкни к аппарату\n🔧 Настройка ISO, выдержки и диафрагмы"
        },
        {
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "📷 Кнопка отключения главного дисплея"
        },
        {
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "⚙️ Настройка фокусировки (one shot)"
        },
        {
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "🔄 Настройка формата файла (RAW)"
        },
        {
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "⚡ Настройка вспышки и синхронизаторов"
        }
    ]

    # Сохраняем данные о видео в state
    await state.update_data(
        video_steps=video_steps,
        current_step=0,
        video_message_ids=[],
        test_mode=False
    )

    # Начинаем показ первого видео
    await show_next_video_step_12(callback, state)
    await callback.answer()


async def show_next_video_step_12(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_step = user_data.get("current_step", 0)
    video_steps = user_data.get("video_steps", [])
    video_message_ids = user_data.get("video_message_ids", [])

    # Удаляем предыдущее сообщение с кнопкой, если оно есть
    if "step_message_id" in user_data:
        try:
            await callback.bot.delete_message(callback.message.chat.id, user_data["step_message_id"])
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Проверяем, есть ли еще видео для показа
    if current_step < len(video_steps):
        step_data = video_steps[current_step]

        # Отправляем видео с описанием
        sent_message = await callback.message.answer_photo(
            step_data["file_id"],
            caption=step_data["description"],
            parse_mode="Markdown"
        )#заменить на видео
        video_message_ids.append(sent_message.message_id)

        # Создаем клавиатуру (Далее или Приступить к тесту для последнего шага)
        if current_step < len(video_steps) - 1:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее →", callback_data="next_video_step_12")]
            ])
            action_text = "Нажмите 'Далее' для продолжения"
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Приступить к тесту", callback_data="start_quest12_test")]
            ])
            action_text = "После просмотра всех видео нажмите 'Приступить к тесту'"

        # Отправляем сообщение с кнопкой
        step_message = await callback.message.answer(
            action_text,
            reply_markup=keyboard
        )

        # Обновляем состояние
        await state.update_data(
            current_step=current_step + 1,
            video_message_ids=video_message_ids,
            step_message_id=step_message.message_id
        )
    else:
        # Все видео показаны, можно начинать тест
        await start_quest12_test(callback, state)


@router.callback_query(F.data == "next_video_step_12")
async def handle_next_video_step_12(callback: types.CallbackQuery, state: FSMContext):
    await show_next_video_step_12(callback, state)
    await callback.answer()


@router.callback_query(F.data == "start_quest12_test")
async def start_quest12_test(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "step_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["step_message_id"])
        if "video_message_ids" in user_data:
            for msg_id in user_data["video_message_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем тест
    await state.update_data(
        test_mode=True,
        current_question=1,
        correct_count=0,
        total_questions=11  # Всего 11 вопросов в тесте
    )
    await ask_quest12_question(callback, state)
    await callback.answer()


# Словарь с правильными ответами для квеста 12
correct_answers_qw12 = {
    1: "режим фокусировки",
    2: "диафрагма",
    3: "выдержка",
    4: "ISO",
    5: "кнопку включения",
    6: "колесо режимов",
    7: "кнопку спуска затвора",
    8: "доп дисплей",
    9: "кнопка включения",
    10: "стрелки изменение импульса",
    11: "кнопка срабатывания вспышки"
}


async def ask_quest12_question(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)

    # Удаляем предыдущее сообщение, если оно есть
    if "question_message_id" in user_data:
        try:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Определяем, какую картинку и вопрос показывать
    if 1 <= current_question <= 4:
        # Вопросы 1-4 - дисплей фотоаппарата
        photo_path = BASE_DIR / "handlers/media/photo/zaglushka.png"
        question_text = f"Квест 12: Вопрос {current_question}/11\nЧто мы можем поменять под цифрой {current_question}?"
    elif 5 <= current_question <= 8:
        # Вопросы 5-8 - верхняя часть с кнопками
        photo_path = BASE_DIR / "handlers/media/photo/zaglushka.png"
        question_text = f"Квест 12: Вопрос {current_question}/11\nЧто мы можем поменять под цифрой {current_question - 4}?"
    else:
        # Вопросы 9-11 - экран вспышки
        photo_path = BASE_DIR / "handlers/media/photo/zaglushka.png"
        question_text = f"Квест 12: Вопрос {current_question}/11\nЧто мы можем поменять под цифрой {current_question - 8}?"

    # Варианты ответов для текущего вопроса
    options = {
        1: ["ISO", "выдержка", "диафрагма", "режим фокусировки"],
        2: ["ISO", "выдержка", "диафрагма", "режим фокусировки"],
        3: ["ISO", "диафрагма", "выдержка", "режим фокусировки"],
        4: ["режим фокусировки", "диафрагма", "выдержка", "ISO"],
        5: ["колесо режимов", "кнопку спуска затвора", "доп дисплей", "кнопку включения"],
        6: ["кнопку включения", "колесо режимов", "кнопку спуска затвора", "доп дисплей"],
        7: ["кнопку включения", "колесо режимов", "кнопку спуска затвора", "доп дисплей"],
        8: ["доп дисплей", "кнопку включения", "колесо режимов", "кнопку спуска затвора"],
        9: ["кнопка включения", "стрелки изменение импульса", "кнопка срабатывания вспышки"],
        10: ["кнопка включения", "кнопка срабатывания вспышки", "стрелки изменение импульса"],
        11: ["кнопка включения", "стрелки изменение импульса", "кнопка срабатывания вспышки"]
    }

    # Добавляем кнопку "Подсказка"
    options[current_question].append("подсказка")

    # Отправляем фото с вопросом
    photo = FSInputFile(photo_path)
    message = await callback.message.answer_photo(
        photo,
        caption=question_text,
        reply_markup=quest12_keyboard(options[current_question])
    )

    # Сохраняем ID сообщения для последующего удаления
    await state.update_data(
        question_message_id=message.message_id,
        current_question_options=options[current_question]
    )


@router.callback_query(F.data.startswith("qw12_"), QuestState.waiting_for_answer)
async def handle_quest12_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)
    total_questions = user_data.get("total_questions", 11)
    current_quest_id = 12

    selected_answer = callback.data.split("_")[1]

    # Обработка подсказки
    if selected_answer == "подсказка":
        # Определяем путь к изображению с подсказкой
        if 1 <= current_question <= 4:
            hint_path = BASE_DIR / "handlers/media/photo/zaglushka.png"
        elif 5 <= current_question <= 8:
            hint_path = BASE_DIR / "handlers/media/photo/zaglushka.png"
        else:
            hint_path = BASE_DIR / "handlers/media/photo/zaglushka.png"

        # Отправляем подсказку
        hint_photo = FSInputFile(hint_path)
        await callback.message.delete()
        message = await callback.message.answer_photo(
            hint_photo,
            caption="Подсказка",
            reply_markup=quest12_back_to_question_keyboard()
        )

        await state.update_data(hint_message_id=message.message_id)
        await callback.answer()
        return

    # Проверяем ответ
    is_correct = selected_answer == correct_answers_qw12[current_question]

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

        if is_correct:
            correct_count += 1
            user_result.result += 1
            await callback.answer('Верный ответ!')
        else:
            await callback.answer('Ответ неверный.')

        # Если все вопросы пройдены, отмечаем квест как выполненный
        if current_question == total_questions:
            user_result.state = "выполнен" if correct_count == total_questions else "не выполнен"

        await session.commit()

    # Обновляем состояние FSM
    await state.update_data(correct_count=correct_count)

    # Переход к следующему вопросу или завершение квеста
    current_question += 1
    if current_question > total_questions:
        await callback.message.delete()
        await finish_quest(callback, state, correct_count, total_questions, current_quest_id)
    else:
        await state.update_data(current_question=current_question)
        await ask_quest12_question(callback, state)

    await callback.answer()


@router.callback_query(F.data == "back_to_question_12")
async def back_to_question_12(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем сообщение с подсказкой
    user_data = await state.get_data()
    try:
        if "hint_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["hint_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Возвращаемся к текущему вопросу
    await ask_quest12_question(callback, state)
    await callback.answer()


# Квест 13 - Фотограф
async def quest_13(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Отправляем инструкцию
    message = await callback.message.answer(
        "📷 Квест 13: Фотограф\n\n"
        "Ознакомься ещё раз с настройками фотоаппарата. "
        "Вы можете пересмотреть видео из базы знаний.",
        reply_markup=quest13_watch_again_keyboard()
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_task=1,
        photos=[]
    )
    await callback.answer()


@router.callback_query(F.data == "watch_again_13")
async def watch_again_13(callback: types.CallbackQuery, state: FSMContext):
    # Показываем видео с настройками еще раз
    video_file_id = "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ"

    await callback.message.delete()
    sent_message = await callback.message.answer_photo(
        video_file_id,
        caption="🔧 Настройки фотоаппарата"
    )#заменить на видео

    # Отправляем кнопку для продолжения
    message = await callback.message.answer(
        "После просмотра видео нажмите 'Продолжить'",
        reply_markup=quest13_continue_keyboard()
    )

    await state.update_data(
        video_message_id=sent_message.message_id,
        question_message_id=message.message_id
    )
    await callback.answer()


@router.callback_query(F.data == "continue_quest13")
async def continue_quest13(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "video_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["video_message_id"])
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем первый этап задания
    await send_quest13_task(callback, state)
    await callback.answer()


async def send_quest13_task(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_task = user_data.get("current_task", 1)

    tasks = {
        1: {
            "text": "📷 Задание 1/3:\n"
                    "Сделай фото портрет по грудь коллеги в тёмном месте.\n"
                    "Требования:\n"
                    "- ISO ~800\n"
                    "- Диафрагма открыта максимально для объектива\n"
                    "- Выдержка 100-150\n\n"
                    "Фотографию загрузите в Lightroom и отправьте скриншот из режима редактирования.",
            "keyboard": quest13_task_keyboard()
        },
        2: {
            "text": "📷 Задание 2/3:\n"
                    "Сделай фото портрет по грудь коллеги в светлом месте (напротив окна, под лампочкой и т.д.).\n"
                    "Требования:\n"
                    "- ISO 100-400\n"
                    "- Диафрагма минимальная\n"
                    "- Выдержка стандартная\n\n"
                    "Фотографию загрузите в Lightroom и отправьте скриншот из режима редактирования.",
            "keyboard": quest13_task_keyboard()
        },
        3: {
            "text": "📷 Задание 3/3:\n"
                    "Сделать снимок 3-6 человек (коллег, клиентов и т.д.).\n"
                    "Требования:\n"
                    "- Диафрагма 4.5-10F\n"
                    "- Правильная экспозиция\n\n"
                    "Фотографию загрузите в Lightroom и отправьте скриншот из режима редактирования.",
            "keyboard": quest13_finish_tasks_keyboard()
        }
    }

    message = await callback.message.answer(
        tasks[current_task]["text"],
        reply_markup=tasks[current_task]["keyboard"]
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_task=current_task
    )
    await state.set_state(QuestState.waiting_for_photo_quest13)


@router.callback_query(F.data == "next_task_13")
async def next_task_13(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_task = user_data.get("current_task", 1) + 1

    await state.update_data(current_task=current_task)
    await callback.message.delete()
    await send_quest13_task(callback, state)
    await callback.answer()


@router.message(F.photo, QuestState.waiting_for_photo_quest13)
async def handle_photo_quest13(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photos = user_data.get("photos", [])
    current_task = user_data.get("current_task", 1)

    # Добавляем фото в список
    photos.append({
        "task": current_task,
        "file_id": message.photo[-1].file_id
    })

    await state.update_data(photos=photos)

    # Удаляем предыдущее сообщение с заданием
    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    # Отправляем подтверждение получения фото
    if current_task < 3:
        message_text = "✅ Фото получено. Отправьте следующее фото или нажмите 'Пропустить' чтобы перейти к следующему этапу."
        keyboard = quest13_skip_keyboard()
    else:
        message_text = "✅ Все фото получены. Нажмите 'Завершить', чтобы отправить на модерацию."
        keyboard = quest13_finish_tasks_keyboard()

    question = await message.answer(
        message_text,
        reply_markup=keyboard
    )

    await state.update_data(question_message_id=question.message_id)
    await message.delete()


@router.callback_query(F.data == "skip_task_13")
async def skip_task_13(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_task = user_data.get("current_task", 1)

    if current_task < 3:
        await state.update_data(current_task=current_task + 1)
        await callback.message.delete()
        await send_quest13_task(callback, state)
    else:
        await callback.answer("Это последнее задание, пропустить нельзя", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "finish_quest13")
async def finish_quest13(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos = user_data.get("photos", [])

    if not photos:
        await callback.answer("Вы не отправили ни одного фото!", show_alert=True)
        return

    # Удаляем сообщение с кнопкой
    try:
        await callback.message.delete()
    except:
        pass

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 13
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=13,
                state="на модерации",
                attempt=1,
                result=0
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            await update_user_level(callback.from_user.id, session)

        await session.commit()

    # Формируем сообщение для модератора
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 13 - Фотограф\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Отправляем фото модератору
    media = []
    for i, photo in enumerate(photos, 1):
        media.append(InputMediaPhoto(
            media=photo["file_id"],
            caption=f"Задание {photo['task']}" if i == 1 else f"Задание {photo['task']}"
        ))

    if len(media) > 1:
        await callback.bot.send_media_group(admin_chat_id, media)
    else:
        await callback.bot.send_photo(admin_chat_id, media[0].media, caption=media[0].caption)

    # Дополнительная информация для модератора
    await callback.bot.send_message(
        admin_chat_id,
        caption,
        reply_markup=moderation_keyboard(callback.from_user.id, 13)
    )

    # Сообщение пользователю
    await callback.message.answer(
        "✅ Все фото отправлены на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()
    await callback.answer()


# Квест 14 - Зоны фотографирования
async def quest_14(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")


    # Примеры кадров для разных зон (замените на реальные file_id)
    sample_shots = [
        {
            "file_id": "AgACAgIAAxkBAAImGWfz4xzgScJdAAGcPSyjQMhfLErttwACYPExG5DcoUu5t7Q2nJC8jgEAAwIAA3kAAzYE",
            "description": "🔼 Кадр сверху вниз:"
        },
        {
            "file_id": "AgACAgIAAxkBAAImF2fz4xQAAfkQvZDwrTsEp4HksUCM9wACX_ExG5DcoUtTVN7oo4PozgEAAwIAA3kAAzYE",
            "description": "📐 Кадр под углом 45°:\nСнимите сбоку под углом, акцентируя внимание на взаимодействии ребёнка с шарами"
        },
        {
            "file_id": "AgACAgIAAxkBAAImD2fz4nfoKsDftnMib1kmgO3XS_gSAAJZ8TEbkNyhS3Vp4OVknUyAAQADAgADeQADNgQ",
            "description": "👶 Кадр на уровне глаз ребёнка:\nСнимите горизонтально, чтобы передать мир глазами ребёнка"
        },
        {
            "file_id": "AgACAgIAAxkBAAImFWfz4ws0LZRuuMap6gaKW3k1GjTNAAJe8TEbkNyhSwX5urMKlVD-AQADAgADeQADNgQ",
            "description": "🌊 Кадр 'моря из шариков':\nСнимите сверху с широким углом, чтобы захватить максимальное количество шаров"
        },
        {
            "file_id": "AgACAgIAAxkBAAImG2fz4yq_LS4V_tuyNEoEIGMmWCD1AAJh8TEbkNyhSz7tTj8yAeKUAQADAgADeQADNgQ",
            "description": "🌊 Кадр : "
        }
    ]

    # Сохраняем данные о кадрах в state
    await state.update_data(
        sample_shots=sample_shots,
        current_shot=0,
        shot_message_ids=[],
        user_shots=[]
    )

    # Начинаем показ первого кадра
    await show_next_sample_shot_14(callback, state)
    await callback.answer()


async def show_next_sample_shot_14(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_shot = user_data.get("current_shot", 0)
    sample_shots = user_data.get("sample_shots", [])
    shot_message_ids = user_data.get("shot_message_ids", [])

    # Удаляем предыдущее сообщение с кнопкой
    if "shot_message_id" in user_data:
        try:
            await callback.bot.delete_message(callback.message.chat.id, user_data["shot_message_id"])
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Проверяем, есть ли еще кадры для показа
    if current_shot < len(sample_shots):
        shot_data = sample_shots[current_shot]

        # Отправляем пример кадра с описанием
        sent_message = await callback.message.answer_photo(
            shot_data["file_id"],
            caption=shot_data["description"],
            parse_mode="Markdown"
        )
        shot_message_ids.append(sent_message.message_id)

        # Создаем клавиатуру (Далее или Начать съемку для последнего шага)
        if current_shot < len(sample_shots) - 1:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее →", callback_data="next_sample_shot_14")]
            ])
            action_text = "Нажмите 'Далее' для просмотра следующего примера"
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Начать съемку", callback_data="start_shooting_14")]
            ])
            action_text = "После просмотра всех примеров нажмите 'Начать съемку'"

        # Отправляем сообщение с кнопкой
        shot_message = await callback.message.answer(
            action_text,
            reply_markup=keyboard
        )

        # Обновляем состояние
        await state.update_data(
            current_shot=current_shot + 1,
            shot_message_ids=shot_message_ids,
            shot_message_id=shot_message.message_id
        )
    else:
        # Все примеры показаны, можно начинать съемку
        await start_shooting_14(callback, state)


@router.callback_query(F.data == "next_sample_shot_14")
async def handle_next_sample_shot_14(callback: types.CallbackQuery, state: FSMContext):
    await show_next_sample_shot_14(callback, state)
    await callback.answer()


@router.callback_query(F.data == "start_shooting_14")
async def start_shooting_14(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "shot_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["shot_message_id"])
        if "shot_message_ids" in user_data:
            for msg_id in user_data["shot_message_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем процесс съемки
    await state.update_data(
        shooting_mode=True,
        current_zone=1,
        total_zones=5  # Всего 5 зон для съемки
    )
    await request_shot_14(callback, state)
    await callback.answer()


async def request_shot_14(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_zone = user_data.get("current_zone", 1)
    total_zones = user_data.get("total_zones", 5)
    sample_shots = user_data.get("sample_shots", [])

    # Определяем описание для текущей зоны
    zone_descriptions = {
        1: "🔼 Сделайте кадр сверху вниз",
        2: "📐 Сделайте кадр под углом 45°",
        3: "👶 Сделайте кадр на уровне глаз ребёнка",
        4: "🌊 Сделайте кадр 'моря из шариков'",
        5: "Сделайте кадр "
    }

    # Отправляем напоминание о текущей зоне
    message = await callback.message.answer(
        f"📷 Зона {current_zone}/{total_zones}\n"
        f"{zone_descriptions[current_zone]}\n\n"
        "Сфотографируйте этот кадр на экране монитора и отправьте фото.",
        reply_markup=quest14_skip_zone_keyboard() if current_zone < total_zones else quest14_finish_shooting_keyboard()
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_zone=current_zone
    )
    await state.set_state(QuestState.waiting_for_photo_quest14)


@router.message(F.photo, QuestState.waiting_for_photo_quest14)
async def handle_photo_quest14(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_shots = user_data.get("user_shots", [])
    current_zone = user_data.get("current_zone", 1)

    # Добавляем фото в список
    user_shots.append({
        "zone": current_zone,
        "file_id": message.photo[-1].file_id
    })

    await state.update_data(user_shots=user_shots)

    # Удаляем предыдущее сообщение с заданием
    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    # Отправляем подтверждение получения фото
    message_text = f"✅ Фото для зоны {current_zone} получено."

    if current_zone < user_data.get("total_zones", 5):
        message_text += " Отправьте следующее фото или нажмите 'Пропустить зону' чтобы перейти к следующей зоне"
        keyboard = quest14_skip_zone_keyboard()
    else:
        message_text += " Все фото получены. Нажмите 'Завершить', чтобы отправить на модерацию."
        keyboard = quest14_finish_shooting_keyboard()

    question = await message.answer(
        message_text,
        reply_markup=keyboard
    )

    await state.update_data(question_message_id=question.message_id)
    await message.delete()


@router.callback_query(F.data == "skip_zone_14")
async def skip_zone_14(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_zone = user_data.get("current_zone", 1) + 1
    total_zones = user_data.get("total_zones", 5)

    if current_zone <= total_zones:
        await state.update_data(current_zone=current_zone)
        await callback.message.delete()
        await request_shot_14(callback, state)
    else:
        await callback.answer("Это последняя зона, пропустить нельзя", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "finish_quest14")
async def finish_quest14(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_shots = user_data.get("user_shots", [])

    if not user_shots:
        await callback.answer("Вы не отправили ни одного фото!", show_alert=True)
        return

    # Удаляем сообщение с кнопкой
    try:
        await callback.message.delete()
    except:
        pass

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 14
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=14,
                state="на модерации",
                attempt=1,
                result=0
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"

        await session.commit()

    # Формируем сообщение для модератора
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 14 - Зоны фотографирования\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Отправляем фото модератору с кнопками для модерации
    media = []
    for i, shot in enumerate(user_shots, 1):
        media.append(InputMediaPhoto(
            media=shot["file_id"],
            caption=f"{caption}\n\nЗона {shot['zone']}" if i == 1 else f"Зона {shot['zone']}"
        ))

    if len(media) > 1:
        await callback.bot.send_media_group(admin_chat_id, media)
    else:
        await callback.bot.send_photo(admin_chat_id, media[0].media, caption=media[0].caption)

    # Дополнительная информация для модератора с кнопками принятия/отклонения
    await callback.bot.send_message(
        admin_chat_id,
        f"Фото от {user.full_name} для квеста 14 готовы к проверке.\n"
        "Проверьте соответствие ТЗ и настройки фотоаппарата.",
        reply_markup=moderation_keyboard(callback.from_user.id, 14)
    )

    # Сообщение пользователю
    await callback.message.answer(
        "✅ Все фото отправлены на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()
    await callback.answer()



# Квест 15 - 1000 Поз

# Шаблоны для мальчиков (замените на реальные file_id)
boy_templates = [
    {
        "file_id": "AgACAgIAAxkBAAImumf0CMKeb1EmvwUSaNHq_Am45Hl0AAKD6TEboYqpS1GqOoFJKbDOAQADAgADeQADNgQ",
        "description": "Шаблон 1 для мальчика"
    },
    {
        "file_id": "AgACAgIAAxkBAAImuWf0CMI5CygJwWhGx-SPxPRLYTbIAAKC6TEboYqpS8IMk-x-A6TmAQADAgADeQADNgQ",
        "description": "Шаблон 2 для мальчика"
    },
    {
        "file_id": "AgACAgIAAxkBAAInC2f0HKHHoLHSmwgZNC7jX92sCrwmAAIe6jEboYqpSzl14XAUmplRAQADAgADeQADNgQ",
        "description": "Шаблон 3 для мальчика"
    },
    {
        "file_id": "AgACAgIAAxkBAAImu2f0CMKjAAHX5dUdnypW6dnUaDs-OAAChOkxG6GKqUsvgjpI0UdWbAEAAwIAA3kAAzYE",
        "description": "Шаблон 4 для мальчика"
    },
    {
        "file_id": "AgACAgIAAxkBAAImuGf0CMILgx0cjgnFpxYlLjhKClxiAAKB6TEboYqpS6vJVCHqe6SpAQADAgADeQADNgQ",
        "description": "Шаблон 5 для мальчика"
    }
]

# Шаблоны для девочек (замените на реальные file_id)
girl_templates = [
    {
        "file_id": "AgACAgIAAxkBAAImtmf0CMKtybZPkUaWxS-UoNyyFzPvAAJ_6TEboYqpSyd4njHKEhhQAQADAgADeQADNgQ",
        "description": "Шаблон 1 для девочки"
    },
    {
        "file_id": "AgACAgIAAxkBAAIms2f0CMKwnpMtCoCHOnwQa8Mky4oLAAJ86TEboYqpS9AocbO25De_AQADAgADeQADNgQ",
        "description": "Шаблон 2 для девочки"
    },
    {
        "file_id": "AgACAgIAAxkBAAImtGf0CMJdxOERd2Br5yzwtdkbPho1AAJ96TEboYqpSwbIoi6yi23BAQADAgADeQADNgQ",
        "description": "Шаблон 3 для девочки"
    },
    {
        "file_id": "AgACAgIAAxkBAAInE2f0Hvz20n4-dn4dw57DKw70Kie4AAIl6jEboYqpSynEAAE1X9OqcwEAAwIAA3kAAzYE",
        "description": "Шаблон 4 для девочки"
    },
    {
        "file_id": "AgACAgIAAxkBAAInFWf0Hwn8xb7GZ-00g0e8JuV4KRmhAAIn6jEboYqpSwliqOYlEqw6AQADAgADeQADNgQ",
        "description": "Шаблон 5 для девочки"
    }
]



async def quest_15(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Видео гайд по позированию
    video_guide = {
        "file_id": "BAACAgIAAxkBAAImsGf0B-OgQ_mpwLkKY2RnMiOqG1DbAALqbgACoYqhS7f0qJ4Nuj69NgQ",
        "description": "🎬 Видео-гайд по позированию детей"
    }

    # Отправляем видео гайд
    sent_message = await callback.message.answer_video(
        video_guide["file_id"],
        caption=video_guide["description"],
        parse_mode="Markdown"
    )

    # Отправляем кнопку для продолжения
    message = await callback.message.answer(
        "После просмотра видео нажмите 'Начать задание'",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать задание", callback_data="start_quest15")]
        ])
    )

    await state.update_data(
        video_message_id=sent_message.message_id,
        question_message_id=message.message_id,
        current_gender="boy",  # Начинаем с мальчиков
        boy_photos=[],
        girl_photos=[]
    )
    await callback.answer()


@router.callback_query(F.data == "start_quest15")
async def start_quest15(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "video_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["video_message_id"])
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем задание
    await request_quest15_photo(callback, state)
    await callback.answer()

async def request_quest15_photo(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_gender = user_data.get("current_gender", "boy")
    boy_photos = user_data.get("boy_photos", [])
    girl_photos = user_data.get("girl_photos", [])

    # Удаляем предыдущие сообщения с шаблонами и заданиями
    if "template_message_ids" in user_data:
        try:
            for msg_id in user_data["template_message_ids"]:
                await message_or_callback.bot.delete_message(
                    message_or_callback.message.chat.id if isinstance(message_or_callback, types.CallbackQuery) else message_or_callback.chat.id,
                    msg_id
                )
        except Exception as e:
            print(f"Ошибка при удалении сообщений с шаблонами: {e}")

    # Определяем текст задания и шаблоны
    if current_gender == "boy":
        remaining = 5 - len(boy_photos)
        gender_text = "мальчика"
        templates = boy_templates
    else:
        remaining = 5 - len(girl_photos)
        gender_text = "девочки"
        templates = girl_templates

    # Отправляем шаблон для текущего пола
    template = templates[len(boy_photos if current_gender == "boy" else girl_photos)]

    # Определяем объект сообщения в зависимости от типа входящего объекта
    if isinstance(message_or_callback, types.CallbackQuery):
        message = message_or_callback.message
    else:
        message = message_or_callback

    # Создаем медиагруппу с шаблоном
    media = MediaGroupBuilder()
    media.add_photo(media=template["file_id"], caption=f"Шаблон для {gender_text}: {template['description']}")

    # Отправляем медиагруппу и сохраняем ID сообщений
    sent_messages = await message.answer_media_group(media=media.build())
    template_message_ids = [msg.message_id for msg in sent_messages]

    message_text = (
        f"📷 Квест 15: 1000 Поз\n\n"
        f"Отправьте {remaining} фото {gender_text} по шаблону.\n"
        "Фото должны быть сделаны в соответствии с показанным примером."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_quest15_photo")]
    ])

    sent_message = await message.answer(
        message_text,
        reply_markup=keyboard
    )

    await state.update_data(
        question_message_id=sent_message.message_id,
        current_gender=current_gender,
        current_template=template,
        template_message_ids=template_message_ids  # Сохраняем ID сообщений с шаблонами
    )
    await state.set_state(QuestState.waiting_for_photo_quest15)

@router.message(F.photo, QuestState.waiting_for_photo_quest15)
async def handle_photo_quest15(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    current_gender = user_data.get("current_gender", "boy")
    boy_photos = user_data.get("boy_photos", [])
    girl_photos = user_data.get("girl_photos", [])
    current_template = user_data.get("current_template", {})

    # Добавляем фото в соответствующий список
    if current_gender == "boy":
        boy_photos.append({
            "file_id": message.photo[-1].file_id,
            "template": current_template["file_id"]
        })
    else:
        girl_photos.append({
            "file_id": message.photo[-1].file_id,
            "template": current_template["file_id"]
        })

    await state.update_data(
        boy_photos=boy_photos,
        girl_photos=girl_photos
    )

    # Удаляем предыдущие сообщения (шаблоны и задание)
    try:
        if "template_message_ids" in user_data:
            for msg_id in user_data["template_message_ids"]:
                await message.bot.delete_message(message.chat.id, msg_id)
        if "question_message_id" in user_data:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Проверяем, все ли фото собраны
    if len(boy_photos) >= 5 and len(girl_photos) >= 5:
        # Все фото собраны, завершаем квест
        await finish_quest15(message, state)
    else:
        # Если для текущего пола собрано 5 фото, переключаемся на другой
        if (current_gender == "boy" and len(boy_photos) >= 5) or (current_gender == "girl" and len(girl_photos) >= 5):
            next_gender = "girl" if current_gender == "boy" else "boy"
            await state.update_data(current_gender=next_gender)
            await request_quest15_photo(message, state)
        else:
            # Запрашиваем еще фото для текущего пола
            await request_quest15_photo(message, state)

    await message.delete()

@router.callback_query(F.data == "skip_quest15_photo")
async def skip_quest15_photo(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_gender = user_data.get("current_gender", "boy")
    boy_photos = user_data.get("boy_photos", [])
    girl_photos = user_data.get("girl_photos", [])

    # Если для текущего пола нет фото, не позволяем пропустить
    if (current_gender == "boy" and len(boy_photos) == 0) or (current_gender == "girl" and len(girl_photos) == 0):
        await callback.answer("Нельзя пропустить без хотя бы одного фото", show_alert=True)
        return

    # Удаляем предыдущие сообщения (шаблоны и задание)
    try:
        if "template_message_ids" in user_data:
            for msg_id in user_data["template_message_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Переключаемся на другой пол или завершаем, если все собрано
    if len(boy_photos) >= 5 and len(girl_photos) >= 5:
        await finish_quest15(callback.message, state)
    else:
        next_gender = "girl" if current_gender == "boy" else "boy"
        await state.update_data(current_gender=next_gender)
        await request_quest15_photo(callback, state)

    await callback.answer()

async def finish_quest15(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    boy_photos = user_data.get("boy_photos", [])
    girl_photos = user_data.get("girl_photos", [])

    # Удаляем сообщение с заданием, если оно есть
    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == message.from_user.id,
                UserResult.quest_id == 15
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=message.from_user.id,
                quest_id=15,
                state="на модерации",
                attempt=1,
                result=len(boy_photos) + len(girl_photos)
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            user_result.result = len(boy_photos) + len(girl_photos)

        await session.commit()

    # Формируем сообщение для модератора
    user = message.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 15 - 1000 Поз\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"Мальчики: {len(boy_photos)} фото\n"
        f"Девочки: {len(girl_photos)} фото"
    )

    # Отправляем шаблоны и фото модератору в нескольких медиагруппах
    try:

        # 2. Фото мальчиков (может потребоваться несколько медиагрупп)
        for i in range(0, len(boy_photos), 10):  # Разбиваем по 10 фото
            media_boy_photos = MediaGroupBuilder()
            for photo in boy_photos[i:i+10]:
                media_boy_photos.add_photo(media=photo["file_id"], caption=f"Фото мальчика")
            await message.bot.send_media_group(admin_chat_id, media=media_boy_photos.build())


        # 4. Фото девочек (может потребоваться несколько медиагрупп)
        for i in range(0, len(girl_photos), 10):  # Разбиваем по 10 фото
            media_girl_photos = MediaGroupBuilder()
            for photo in girl_photos[i:i+10]:
                media_girl_photos.add_photo(media=photo["file_id"], caption=f"Фото девочки ")
            await message.bot.send_media_group(admin_chat_id, media=media_girl_photos.build())

    except Exception as e:
        print(f"Ошибка при отправке медиагруппы: {e}")
        # Если не удалось отправить медиагруппу, отправляем по одному фото
        await message.bot.send_message(admin_chat_id, caption)
        for photo in boy_photos:
            await message.bot.send_photo(admin_chat_id, photo["file_id"])
        for photo in girl_photos:
            await message.bot.send_photo(admin_chat_id, photo["file_id"])

    # Дополнительная информация для модератора
    await message.bot.send_message(
        admin_chat_id,
        caption,
        reply_markup=moderation_keyboard(message.from_user.id, 15)
    )

    # Сообщение пользователю
    await message.answer(
        "✅ Все фото отправлены на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()


# Квест 16 - Дожми до результата (финальная версия)
async def quest_16(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Сценарии из Excel файла
    scenarios = {
        1: {
            "name": "Мама с сыном в бассейне",
            "description": "Ситуация: мама с сыном играют в бассейне с шариками, из окна весенний свет",
            "dialogs": [
                {
                    "photographer": "Выберите, как начать диалог:",
                    "client": "",
                    "options": [
                        "Здравствуйте, меня зовут..., как красиво отражаются солнечные лучи! Садитесь скорее рядышком, обалденные кадры получатся!",
                        "Здравствуйте, можно вас сфотографировать?",
                        "Здравствуйте, меня зовут..., будете фотографироваться?",
                        "Здравствуйте"
                    ],
                    "responses": {
                        0: {"client": "Здравствуйте, даже не знаю...", "feedback": ""},
                        1: {"client": "нет, спасибо",
                            "feedback": 'Не стоит задавать вопрос, на который можно ответить "да" или "нет". Если клиент заведомом не заинтересован в продукте, то ответ 100% будет "нет".'},
                        2: {"client": "нет, спасибо",
                            "feedback": 'Не стоит задавать вопрос, на который можно ответить "да" или "нет". Если клиент заведомом не заинтересован в продукте, то ответ 100% будет "нет".'},
                        3: {"client": "до свидания", "feedback": "Нужно быть общительнее, развивай коммуникативные навыки, чтобы уметь сразу зацепить клиента диалогом."}
                    },
                    "correct": 0
                },
                {
                    "photographer": "Выберите вариант ответа фотографа:",
                    "client": "Здравствуйте, даже не знаю...",
                    "options": [
                        "Нельзя упускать такой момент, очень красивый свет, садитесь ближе к сыну, как, кстати Вас зовут?",
                        "Не хотите? ну ладно",
                        "Я могу подойти позже",
                        "Мы вам магниты сделаем, они стоят 500 рублей"
                    ],
                    "responses": {
                        0: {"client": "Елена, а сына Артём", "feedback": ""},
                        1: {"client": "", "feedback": "Никогда не сдавайся на первом отказе! Ты только что упустил возможность сделать классные кадры."},
                        2: {"client": "Не надо, спасибо", "feedback": "Заинтересованность клиента угасла в моменте, жаль, кадры сделать не получится."},
                        3: {"client": "Ой, нет, спасибо, мы не планировали покупать магниты", "feedback": "Теперь клиент думает только о том, что ему придётся что-то купить, а это не самое приятная мысль."}
                    },
                    "correct": 0
                },
                {
                    "photographer": "Артём, скорее обними маму крепко и покажи как ты её любишь! Готово, потрясающий кадр!",
                    "client": "Елена, а сына Артём",
                    "options":['далее'],
                    "responses": {
                        0: {"client": "", "feedback": "У тебя получились чудесные семейные кадры в солнечных лучах. Мама растрогана от чувств после крепких объятий и поцелуя сына. И именно ты создал для них эти эмоции, а так же сделала шикарные кадры момента - от покупки таких фотографий Елене будет сложно устоять."},

                    },
                    "correct": 0
                }
            ]
        },
        2: {
            "name": "Семья в детском центре",
            "description": "Ситуация: семья из мамы, папы и дочки отдыхают в детском центре",
            "dialogs": [
                {
                    "photographer": "Выберите вариант ответа фотографа:",
                    "client": "",
                    "options": [
                        "Здравствуйте, меня зовут ..., скорее вставайте все вместе, потрясающий ракурс для вашей семейной фотографии!",
                        "Можно я девочку сфотографирую?",
                        "Здравствуйте, как вас зовут?",
                        "Здравствуйте, фотографироваться будем?"
                    ],
                    "responses": {
                        0: {"client": "Здравствуйте, у нас уже много дочку фотографировали, а мы не любим фотографироваться...", "feedback": ""},
                        1: {"client": "Не надо её фотографировать, у неё много фотографий", "feedback": "Не стоит предлагать фотографировать только ребенка, когда есть вся семья."},
                        2: {"client": "Сергей \n 📷Фотограф: Давайте вас сфотографирую? \n 👤 Клиент: Нет, спасибо ", "feedback": "Не стоит задавать вопрос, на который можно ответить 'да' или 'нет'."},
                        3: {"client": "Нет", "feedback": "Нужно быть общительнее, развивай коммуникативные навыки, чтобы уметь сразу зацепить клиента диалогом."}
                    },
                    "correct": 0
                },
                {
                    "photographer": "Выберите вариант ответа фотографа:",
                    "client": "Здравствуйте, у нас уже много дочку фотографировали, а мы не любим фотографироваться...",
                    "options": [
                        "Семейные фотографии очень ценны, я подскажу как вам красиво встать и получится кадр, каких у вас еще не было, только представьте как вас будет радовать эта фотография годами! Как вас зовут?",
                        "Хорошо",
                        "Если не любите фотографироваться, я могу сфотографировать только дочку",
                        "Мне надо сделать кадры для плана"
                    ],
                    "responses": {
                        0: {"client": "Мария, Сергей, а дочку Вика", "feedback": ""},
                        1: {"client": "", "feedback": "Никогда не сдавайся на первом отказе! Ты только что упустил возможность сделать классные кадры."},
                        2: {"client": "Не надо, спасибо, у неё куча фотографий", "feedback": "Заинтересованность клиента угасла в моменте, жаль, кадры сделать не получится."},
                        3: {"client": "Не хотим, спасибо", "feedback": "Теперь клиент думает только о том, что вам нужно выполнить план, а не о ценности фотографии."}
                    },
                    "correct": 0
                },
                {
                    "photographer": "Выберите вариант ответа фотографа:",
                    "client": "Мария, Сергей, а дочку Вика",
                    "options": [
                        "Сергей, берите на руки Викторию, Мария, а вы встаньте слегка за могучую спину Сергея и за руку возьмите Викторию, как же вы шикарно смотритесь все вместе! Кадр готов, молодцы!"
                    ],
                    "responses": {
                        0: {"client": "", "feedback": "У тебя получились классные семейные кадры, глядя на которые мама увидит себя в психологически комфортном месте - за спиной своего супруга, а папа держит на руках любимую дочку. Обязательно попробуй поставить семью в разные позы и не забудь сделать им отдельные портреты, тем самым увеличив раскадровку и заинтересовав семью в процессе фотосъёмки."}
                    },
                    "correct": 0
                }
            ]
        },
        3: {
            "name": "Две девочки в бассейне",
            "description": "Ситуация: две девочки плещутся в детском бассейне",
            "dialogs": [
                {
                    "photographer": "Выберите вариант как начать диалог:",
                    "client": "",
                    "options": [
                        "Привет, девчонки! Как настроение? Я (имя), а вас как зовут?",
                        "Фотографироваться будете?",
                        "Привет, как вас зовут?",
                        "Привет, давайте вас сфотографирую?"
                    ],
                    "responses": {
                        0: {"client": "Привет! \nЯ, Алина.\n А я, Вика", "feedback": ""},
                        1: {"client": "Нет.", "feedback": "Не стоит задавать вопрос, на который можно ответить 'да' или 'нет'."},
                        2: {"client": "Привет! Я, Алина. А я, Вика \n 📷Фотограф: Хотите сфотографироваться? \n 👤 Клиент: Нет, спасибо ", "feedback": 'Не стоит задавать вопрос, на который можно ответить "да" или "нет". Если клиент заведомом не заинтересован в продукте, то ответ 100% будет "нет".'},
                        3: {"client": "Не надо, мы стесняемся", "feedback": "Не стоит задавать вопрос, на который можно ответить 'да' или 'нет'."}
                    },
                    "correct": 0
                },
                {
                    "photographer": "Выберите вариант ответа фотографа:",
                    "client": "Привет! Я, Алина. А я, Вика",
                    "options": [
                        "У вас одинаковые прически, как прикольно! Дайте я угадаю, вы, наверное, подружки…нет, стоп, вы сестренки! Верно?",
                        "Хотите сфоткаться?",
                    ],
                    "responses": {
                        0: {"client": "Даааааа!", "feedback": ""},
                        1: {"client": "Нет, не хотим", "feedback": "Не стоит задавать вопрос, на который можно ответить 'да' или 'нет'."}
                    },
                    "correct": 0
                },
                {
                    "photographer": "Выберите вариант ответа фотографа:",
                    "client": "Даааааа!",
                    "options": [
                        "Видите, я настоящий волшебник, могу все отгадать. А еще я умею делать самые красивые фотографии в мире. Давайте проверим это? Ну-ка обнимитесь быстренько! Класс, ну красотки! А теперь покажите как сильно вы любите друг друга! Ну вообще, крутышки! Смотрите, как здорово получается. А теперь девчонки, расскажите, с кем вы сюда пришли отдыхать? Наверное, с родителями?",
                        "Круто, можно вас сфотографирую?"
                    ],
                    "responses": {
                        0: {"client": "Да, там мама и папа. Вон, в джакузи", "feedback": ""},
                        1: {"client": "Не надо, мы стесняемся", "feedback": "Девочки такие девочки. Стоит поискать к ним подход."},

                    },
                    "correct": 0
                },
                {
                    "photographer": "Выберите вариант ответа фотографа:",
                    "client": "Да, там мама и папа. Вон, в джакузи",
                    "options": [
                        "Так побежали скорее к ним, надо вас всех вместе обязательно сфотографировать!"
                    ],
                    "responses": {
                        0: {"client": "", "feedback": "Отличное продолжение диалога! Теперь можно перейти к родителям"}
                    },
                    "correct": 0
                },
                {
                    "photographer": "Здравствуйте, Меня зовут (имя), мы подружились с Викой и Алиной, они настоящие модели! А теперь ну-ка посмотрите все на меня, вы сегодня самая красивая семья в нашем аквапарке!",
                    "client": "Да нас не надо фотографировать, мы же не дети. Их вот фоткайте, раз им нравится так",
                    "options": [
                        "Ой, я забыл упомянуть, я же настоящий волшебник! Правда, девчонки? Я помогу вернуться вам в детство. А ну-ка, покажите какой вы сильный папа! Ну супер-герой же! Девочки, а как же обнять любимую маму? Молодцы! Самое время для брызг! Много брызг!",
                        "Ну хорошо. Девчонки, побежали дальше фотографироваться!",
                        "Да девочек я уже фотографировал. Могу подойти к вам позже.",
                        "Я их уже пофоткал. Хорошего вам отдыха!"
                    ],
                    "responses": {
                        0: {"client": "\n 📷Фотограф: Вы чудесная семья! А теперь, давайте устроим вам настоящую лав-стори. Когда вы в последний раз фотографировались вместе? Поцелуйте даму своего сердца в щечку. Милота! А теперь приобнимитесь, ну супер. Смотрите, какие потрясающие у вас снимки. Ну я же говорил, что я волшебник. А теперь идемте под зонтик, там получаются индивидуальные фотографии как с обложки 'Вог'...", "feedback": 'Далее фотограф работает с каждым членом семьи индивидуально. Таким образом, создается раскадровка семьи'},
                        1: {"client": "Да мы уже нафоткались, не надо больше", "feedback": "У девчонок уже есть фотографий, а самые ценные - семейные фотографии сделать не получилось, а ведь платить за всё будут родители, а захотят ли платить за фотографий, на которых их нет?"},
                        2: {"client": "Не стоит, спасибо", "feedback": "Заинтересованность клиента угасла в моменте, жаль, кадры сделать не получится."},
                        3: {"client": "", "feedback": "У девчонок уже есть фотографий, а самые ценные - семейные фотографии сделать не получилось, а ведь платить за всё будут родители, а захотят ли платить за фотографий, на которых их нет?"}
                    },
                    "correct": 0
                }
            ]
        }
    }

    # Отправляем инструкцию
    message = await callback.message.answer(
        "💬 Квест 16: Дожми до результата\n\n"
        "Вам нужно убедить виртуального клиента согласиться на фотосессию.\n"
        "Выберите наиболее подходящие ответы в диалоге.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать диалог", callback_data="start_quest16")]
        ])
    )

    # Устанавливаем начальное состояние
    await state.update_data(
        question_message_id=message.message_id,
        scenarios=scenarios,
        current_scenario=1,
        current_dialog=-1,  # Для показа описания сценария
        correct_answers=0,
        total_questions=sum(len(scenario["dialogs"]) for scenario in scenarios.values())
    )
    await callback.answer()



@router.callback_query(F.data == "start_quest16")
async def start_quest16(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем первый сценарий
    await show_quest16_scenario(callback, state)
    await callback.answer()


async def show_quest16_scenario(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_scenario = user_data.get("current_scenario", 1)
    current_dialog = user_data.get("current_dialog", -1)
    scenarios = user_data.get("scenarios", {})

    # Проверяем, существует ли текущий сценарий
    if current_scenario not in scenarios:
        await finish_quest16(callback, state)
        return

    # Показываем описание сценария
    if current_dialog == -1:
        scenario = scenarios[current_scenario]
        message = await callback.message.answer(
            f"📌 Сценарий: {scenario['name']}\n\n"
            f"{scenario['description']}\n\n"
            "Нажмите 'Продолжить' чтобы начать диалог",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Продолжить", callback_data="next_quest16_dialog")]
            ])
        )
        await state.update_data(
            current_dialog=0,  # Устанавливаем для перехода к первому диалогу
            question_message_id=message.message_id
        )
        return

    # Получаем текущий сценарий
    scenario = scenarios[current_scenario]

    # Проверяем, существует ли текущий диалог
    if current_dialog >= len(scenario["dialogs"]):
        await finish_quest16(callback, state)
        return

    # Показываем текущий диалог
    dialog = scenario["dialogs"][current_dialog]

    message_text = f"📌 Сценарий: {scenario['name']}\n\n"
    if dialog["client"]:
        message_text += f"👤 Клиент: {dialog['client']}\n\n"
    message_text += f"📷 Фотограф: {dialog['photographer']}\n\n"
    message_text += "Варианты ответов:\n"

    for i, option in enumerate(dialog["options"], 1):
        message_text += f"\n{i}. {option}"

    # Создаем клавиатуру с цифрами (по 2 кнопки в строке)
    keyboard = []
    options = dialog["options"]
    for i in range(0, len(options), 2):
        row = []
        for j in range(2):
            if i + j < len(options):
                row.append(InlineKeyboardButton(text=str(i + j + 1), callback_data=f"qw16_{i + j}"))
        if row:
            keyboard.append(row)

    message = await callback.message.answer(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_dialog_data=dialog
    )


@router.callback_query(F.data == "next_quest16_dialog")
async def next_quest16_dialog(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Устанавливаем current_dialog=0 для перехода к первому диалогу
    await state.update_data(current_dialog=0)
    await show_quest16_scenario(callback, state)
    await callback.answer()


@router.callback_query(F.data.startswith("qw16_"))
async def handle_quest16_answer(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    user_data = await state.get_data()
    current_scenario = user_data.get("current_scenario", 1)
    current_dialog = user_data.get("current_dialog", 0)
    correct_answers = user_data.get("correct_answers", 0)
    dialog = user_data.get("current_dialog_data", {})
    scenarios = user_data.get("scenarios", {})

    selected_answer = int(callback.data.split("_")[1])
    response = dialog["responses"].get(selected_answer, {})

    # Отправляем ответ клиента и обратную связь
    messages = []
    if response.get("client"):
        messages.append(f"👤 Клиент: {response['client']}")
    if response.get("feedback"):
        messages.append(f"📌 Совет: {response['feedback']}")

    # Проверяем правильность ответа
    is_correct = selected_answer == dialog["correct"]

    if messages:
        reply_markup = None
        if not is_correct:
            # Добавляем кнопку "Попробовать снова" при неверном ответе
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова",
                                      callback_data=f"retry_quest16_{current_scenario}_{current_dialog}")]
            ])

            await callback.message.answer(
                "\n\n".join(messages),
                reply_markup=reply_markup
            )

    if is_correct:
        correct_answers += 1
        await callback.answer("✅ Верный ответ!")

        # Переходим к следующему диалогу или сценарию
        scenario = scenarios[current_scenario]
        if current_dialog + 1 < len(scenario["dialogs"]):
            await state.update_data(
                correct_answers=correct_answers,
                current_dialog=current_dialog + 1
            )
        else:
            await state.update_data(
                correct_answers=correct_answers,
                current_scenario=current_scenario + 1,
                current_dialog=0
            )

        await show_quest16_scenario(callback, state)
    else:
        await callback.answer("❌ Неверный ответ")


@router.callback_query(F.data.startswith("retry_quest16_"))
async def retry_quest16_dialog(callback: types.CallbackQuery, state: FSMContext):
    # Парсим параметры из callback_data
    _, _, scenario_num, dialog_num = callback.data.split("_")
    current_scenario = int(scenario_num)
    current_dialog = int(dialog_num)

    # Устанавливаем текущий диалог для повторного прохождения
    await state.update_data(
        current_scenario=current_scenario,
        current_dialog=current_dialog
    )

    # Удаляем сообщение с ошибкой
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Показываем диалог снова
    await show_quest16_scenario(callback, state)
    await callback.answer()


async def finish_quest16(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    correct_answers = user_data.get("correct_answers", 0)
    total_questions = user_data.get("total_questions", 0)

    # Сохраняем результат в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 16
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=16,
                state="выполнен",
                attempt=1,
                result=correct_answers
            )
            session.add(user_result)
        else:
            user_result.state = "выполнен"
            user_result.result = correct_answers
        if correct_answers == total_questions:
            achievement_given = await give_achievement(callback.from_user.id, 16, session)
            if achievement_given:
                # Отправляем результат пользователю
                message = await callback.message.answer(
                    f"✅ Квест 16 завершен!\n"
                    f"Правильных ответов: {correct_answers} из {total_questions}\n"
                    f"Поздравляем! Вы получили ачивку за выполнение квеста на 100%!",
                    reply_markup=get_quest_finish_keyboard(correct_answers, total_questions, 16)
                )
            else:
                message = await callback.message.answer(
                    f"✅ Квест 16 завершен!\n"
                    f"Правильных ответов: {correct_answers} из {total_questions}",
                    reply_markup=get_quest_finish_keyboard(correct_answers, total_questions, 16)
                )
        else:
            message_text = f"Есть ошибки, попробуй заново\nВерных ответов: {correct_count} из {total_questions}"
        await session.commit()


    await state.update_data(question_message_id=message.message_id)
    await state.clear()


# Квест 17 - В здоровом теле здоровый дух
async def quest_17(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Отправляем инструкцию
    message = await callback.message.answer(
        "🏋️ Квест 17: В здоровом теле здоровый дух\n\n"
        "Выполните упражнения вместе с командой. Нажмите 'Начать' для первого упражнения.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать", callback_data="start_quest17")]
        ])
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_exercise=1,
        exercises_completed=0,
        total_exercises=3
    )
    await callback.answer()

@router.callback_query(F.data == "start_quest17")
async def start_quest17(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем первое упражнение
    await show_quest17_exercise(callback, state)
    await callback.answer()

async def show_quest17_exercise(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_exercise = user_data.get("current_exercise", 1)

    # Описания упражнений
    exercises = {
        1: {
            "text": "1. Вращение головой\n\n"
                    "Встаньте прямо, опустите руки.\n"
                    "Медленно вращайте головой по кругу: влево, вниз, вправо, назад.\n"
                    "Повторите 5 раз влево, затем 5 раз вправо."
        },
        2: {
            "text": "2. Вращение плечами\n\n"
                    "Согните руки в локтях, положите кисти на плечи.\n"
                    "Делайте круговые движения плечами: 5 раз вперёд, 5 раз назад."
        },
        3: {
            "text": "3. Поднятие ног к груди\n\n"
                    "Поднимите правую ногу, согнув её в колене, и подтяните к груди руками.\n"
                    "Задержитесь на секунду, затем опустите.\n"
                    "Повторите 3 раза для каждой ноги."
        }
    }

    # Отправляем видео упражнения
    exercise_data = exercises[current_exercise]
    sent_message = await callback.message.answer(
        exercise_data["text"]
    )

    # Отправляем кнопку подтверждения выполнения
    message = await callback.message.answer(
        "После выполнения упражнения нажмите 'Выполнено'",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Выполнено", callback_data="complete_exercise_17")]
        ])
    )

    await state.update_data(
        exercise_message_id=sent_message.message_id,
        question_message_id=message.message_id,
        current_exercise_data=exercise_data
    )

@router.callback_query(F.data == "complete_exercise_17")
async def complete_exercise_17(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_exercise = user_data.get("current_exercise", 1)
    exercises_completed = user_data.get("exercises_completed", 0)
    total_exercises = user_data.get("total_exercises", 3)

    # Увеличиваем счетчик выполненных упражнений
    exercises_completed += 1
    await state.update_data(exercises_completed=exercises_completed)

    # Удаляем предыдущие сообщения
    try:
        if "exercise_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["exercise_message_id"])
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Переходим к следующему упражнению или завершаем квест
    current_exercise += 1
    if current_exercise > total_exercises:
        await finish_quest17(callback, state)
    else:
        await state.update_data(current_exercise=current_exercise)
        await show_quest17_exercise(callback, state)

    await callback.answer()

async def finish_quest17(callback: types.CallbackQuery, state: FSMContext):
    # Сохраняем результат в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 17
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=17,
                state="выполнен",
                attempt=1,
                result=3  # Максимальный результат
            )
            session.add(user_result)
        else:
            user_result.state = "выполнен"
            user_result.result = 3

        achievement_given = await give_achievement(callback.from_user.id, 17, session)
        if achievement_given:
            # Отправляем результат пользователю
            message = await callback.message.answer(
                "✅ Квест 17 завершен!\n"
                     "Все упражнения выполнены. Отличная работа!\n",
                f"Поздравляем! Вы получили ачивку за выполнение квеста на 100%!",
                reply_markup=get_quest_finish_keyboard(3, 3, 17)
            )
        else:
            message = await callback.message.answer(
                "✅ Квест 17 завершен!\n"
                "Все упражнения выполнены. Отличная работа!",
                reply_markup=get_quest_finish_keyboard(3, 3, 17)
            )
        await session.commit()

    await state.update_data(question_message_id=message.message_id)
    await state.clear()

# Квест 18 - Практика фото
async def quest_18(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Примеры фото для повторения
    sample_photos = [
        {
            "file_id": "AgACAgIAAxkBAAIrbWf5LHu7chklaPEzghX2SefEPx7UAAIU7TEbqNnQSyy7MWZcfmySAQADAgADeQADNgQ",
            "description": "Квест 18. Практика фотографирования\nПовтори эти семейные фотографии\nПример 1: Семейное фото с ребенком"
        },
        {
            "file_id": "AgACAgIAAxkBAAIrb2f5LH3S888TQLJcnNLTdKNYsMISAAIV7TEbqNnQS5W61jMENwZJAQADAgADeQADNgQ",
            "description": "Пример 2: Семейное фото"
        },
        {
            "file_id": "AgACAgIAAxkBAAIra2f5LHiKo5n9ZScWmtL5SSrUy8MhAAIT7TEbqNnQS0yH5ir93oj7AQADAgADeQADNgQ",
            "description": "Пример 3: Групповое фото детей"
        },
        {
            "file_id": "AgACAgIAAxkBAAIrZ2f5K7YkzWckYuKzc_f56qb-lnldAAIJ7TEbqNnQS8DoPTAr4KEwAQADAgADeQADNgQ",
            "description": "Пример 4: Групповое фото детей"
        },
        {
            "file_id": "AgACAgIAAxkBAAIraWf5LHaZ9-72VM7YaelXj5IKlzzcAAIS7TEbqNnQSzOIe7IQ5Se4AQADAgADeQADNgQ",
            "description": "Пример 5: Групповое фото детей"
        }
    ]

    # Сохраняем данные о примерах в state
    await state.update_data(
        sample_photos=sample_photos,
        current_photo=0,
        photo_message_ids=[],
        user_photos=[]
    )

    # Начинаем показ первого примера
    await show_next_sample_photo_18(callback, state)
    await callback.answer()

async def show_next_sample_photo_18(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_photo = user_data.get("current_photo", 0)
    sample_photos = user_data.get("sample_photos", [])
    photo_message_ids = user_data.get("photo_message_ids", [])

    # Удаляем предыдущее сообщение с кнопкой
    if "photo_message_id" in user_data:
        try:
            await callback.bot.delete_message(callback.message.chat.id, user_data["photo_message_id"])
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Проверяем, есть ли еще фото для показа
    if current_photo < len(sample_photos):
        photo_data = sample_photos[current_photo]

        # Отправляем пример фото с описанием
        sent_message = await callback.message.answer_photo(
            photo_data["file_id"],
            caption=photo_data["description"],
            parse_mode="Markdown"
        )
        photo_message_ids.append(sent_message.message_id)

        # Создаем клавиатуру (Далее или Начать съемку для последнего шага)
        if current_photo < len(sample_photos) - 1:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее →", callback_data="next_sample_photo_18")]
            ])
            action_text = "Нажмите 'Далее' для просмотра следующего примера"
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Начать съемку", callback_data="start_shooting_18")]
            ])
            action_text = "После просмотра всех примеров нажмите 'Начать съемку'"

        # Отправляем сообщение с кнопкой
        photo_message = await callback.message.answer(
            action_text,
            reply_markup=keyboard
        )

        # Обновляем состояние
        await state.update_data(
            current_photo=current_photo + 1,
            photo_message_ids=photo_message_ids,
            photo_message_id=photo_message.message_id
        )
    else:
        # Все примеры показаны, можно начинать съемку
        await start_shooting_18(callback, state)

@router.callback_query(F.data == "next_sample_photo_18")
async def handle_next_sample_photo_18(callback: types.CallbackQuery, state: FSMContext):
    await show_next_sample_photo_18(callback, state)
    await callback.answer()

@router.callback_query(F.data == "start_shooting_18")
async def start_shooting_18(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "photo_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["photo_message_id"])
        if "photo_message_ids" in user_data:
            for msg_id in user_data["photo_message_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем процесс съемки
    await state.update_data(
        shooting_mode=True,
        photos_remaining=5  # Нужно сделать 5 фото
    )
    await request_photo_18(callback, state)
    await callback.answer()


async def request_photo_18(update: Union[types.Message, types.CallbackQuery], state: FSMContext):
    user_data = await state.get_data()
    photos_remaining = user_data.get("photos_remaining", 5)

    # Обработка разных типов входящих данных
    if isinstance(update, types.CallbackQuery):
        # Для CallbackQuery - отвечаем на колбек и получаем сообщение
        await update.answer()
        message = update.message
    else:
        # Для Message - используем само сообщение
        message = update

    # Отправляем новое сообщение с инструкциями
    sent_message = await message.answer(
        f"📷 Квест 18: Практика фото\n\n"
        f"Осталось сделать: {photos_remaining} фото\n"
        "Повторите один из показанных ранее примеров и отправьте фото.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_photo_18")]
        ]))

    # Сохраняем ID сообщения в состоянии
    await state.update_data(
        question_message_id=sent_message.message_id,
        last_chat_id=message.chat.id  # Сохраняем chat_id для последующего удаления
    )
    await state.set_state(QuestState.waiting_for_photo_quest18)

@router.message(F.photo, QuestState.waiting_for_photo_quest18)
async def handle_photo_quest18(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photos_remaining = user_data.get("photos_remaining", 5)
    user_photos = user_data.get("user_photos", [])

    # Добавляем фото в список
    user_photos.append(message.photo[-1].file_id)
    photos_remaining -= 1

    await state.update_data(
        user_photos=user_photos,
        photos_remaining=photos_remaining
    )

    # Удаляем предыдущее сообщение с заданием
    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    # Проверяем, все ли фото собраны
    if photos_remaining <= 0:
        await finish_quest18(message, state)
    else:
        await request_photo_18(message, state)

    await message.delete()

@router.callback_query(F.data == "skip_photo_18")
async def skip_photo_18(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos_remaining = user_data.get("photos_remaining", 5)
    user_photos = user_data.get("user_photos", [])

    # Не позволяем пропустить, если нет ни одного фото
    if len(user_photos) == 0:
        await callback.answer("Нельзя пропустить без хотя бы одного фото", show_alert=True)
        return

    photos_remaining -= 1
    await state.update_data(photos_remaining=photos_remaining)

    if photos_remaining <= 0:
        await finish_quest18(callback, state)
    else:
        await callback.message.delete()
        await request_photo_18(callback, state)

    await callback.answer()

async def finish_quest18(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    # Универсальная обработка входящего объекта
    if isinstance(message, types.CallbackQuery):
        user = message.from_user
        chat_id = message.message.chat.id
        bot = message.bot
        message = message.message  # Получаем объект Message
    else:
        user = message.from_user
        chat_id = message.chat.id
        bot = message.bot

    user_data = await state.get_data()
    user_photos = user_data.get("user_photos", [])

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == user.id,
                UserResult.quest_id == 18
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=user.id,
                quest_id=18,
                state="на модерации",
                attempt=1,
                result=len(user_photos)
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            user_result.result = len(user_photos)
            user_result.attempt += 1

        await session.commit()

    # Формируем сообщение для модератора
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 18 - Практика фото\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Отправляем фото модератору
    if user_photos:
        media = MediaGroupBuilder()
        for i, photo in enumerate(user_photos):
            if i == 0:
                media.add_photo(media=photo, caption=caption)
            else:
                media.add_photo(media=photo)

        try:
            await bot.send_media_group(admin_chat_id, media=media.build())
        except Exception as e:
            print(f"Ошибка при отправке медиагруппы: {e}")

    # Дополнительная информация для модератора
    await bot.send_message(
        admin_chat_id,
        f"Фото от {user.full_name} для квеста 18 готовы к проверке.\n"
        f"Отправлено фото: {len(user_photos)}",
        reply_markup=moderation_keyboard(user.id, 18)
    )

    # Сообщение пользователю
    await bot.send_message(
        chat_id,
        "✅ Все фото отправлены на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )

    # Очищаем состояние
    await state.clear()

# Квест 19 - Алгоритм действий
async def quest_19(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Отправляем инструкцию
    message = await callback.message.answer(
        "🖨️ Квест 19: Алгоритм действий\n\n"
        "Сейчас мы вместе научимся выводить фото на печать.\n"
        "Нажмите 'Начать выполнение' для просмотра инструкции.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать выполнение", callback_data="start_quest19")]
        ])
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step=1,
        correct_answers=0,
        total_steps=18,
        test_questions_answered=0,
        total_test_questions=5
    )
    await callback.answer()


@router.callback_query(F.data == "start_quest19")
async def start_quest19(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем показ инструкции
    await show_quest19_step(callback, state)
    await callback.answer()


async def show_quest19_step(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_step = user_data.get("current_step", 1)

    # Шаги инструкции
    steps = {
        1: {
            "text": "1. Открываем вкладку Импорт",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        2: {
            "text": "2. Вставляем новую флешку в картридер",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        3: {
            "text": "3. Мышкой «обводим» место где появилась флешка",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        4: {
            "text": "4. Выбираем флешку, обводим место где открылись все фотографии",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        5: {
            "text": "5. Показываем как выбрать место куда сохранять фотографии",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        6: {
            "text": "6. Обводим кнопку Импорт, нажимаем её",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        7: {
            "text": "7. Обводим полоску загрузки фотографий",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        8: {
            "text": "8. Обводим и открываем вкладку «обработка» или «редактирование»",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        9: {
            "text": "9. Обводим снизу все фотки какие мы импортировали, выбираем первую",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        10: {
            "text": "10. Слева обводим окошко с пресетами, выбираем какой-нибудь не автоматически применённый, потом возвращаем на автоматически применённый",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        11: {
            "text": "11. Обводим окошко с настройками баланса белого, экспозиции и т.д.",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        12: {
            "text": "12. Редактируем фотографию, не спеша, по возможности используя по больше инструментов",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        13: {
            "text": "13. Редактируем остальные фотографии. Тут я просто ускорю весь процесс, главное левые окна не открывайте",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        14: {
            "text": "14. Обводим и Открываем окно Печать",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        15: {
            "text": "15. Обводим окно с шаблонами печати и выбираем шаблон на 6 магнитов или фотку А5\А4",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        16: {
            "text": "16. Выбираем фотографии для шаблона",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        17: {
            "text": "17. Обводим кнопку «печать…», нажимаем её",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        },
        18: {
            "text": "18. Обводим кнопку «Печать» и запускаем импорт",
            "photo": "AgACAgIAAxkBAAIsJGf5XoKFaUbeIPNrGjmMSnvaZanuAALb7jEbqNnQS0I4Tz8mVhJ-AQADAgADeAADNgQ"
        }
    }

    # Отправляем текущий шаг
    step_data = steps.get(current_step, {})
    if not step_data:
        # Все шаги показаны, отправляем теоретическое сообщение
        theory_message = await callback.message.answer(
            "Теория: Алгоритм вывода на печать\n\n"
            "1. Открываем вкладку Импорт\n"
            "2. Вставляем новую флешку в картридер\n"
            "3. Мышкой «обводим» место где появилась флешка\n"
            "4. Выбираем флешку, обводим место где открылись все фотографии\n"
            "5. Показываем как выбрать место куда сохранять фотографии\n"
            "6. Обводим кнопку Импорт, нажимаем её\n"
            "7. Обводим полоску загрузки фотографий\n"
            "8. Обводим и открываем вкладку «обработка» или «редактирование»\n"
            "9. Обводим снизу все фотки какие мы импортировали, выбираем первую\n"
            "10. Слева обводим окошко с пресетами, выбираем какой-нибудь не автоматически применённый, потом возвращаем на автоматически применённый\n"
            "11. Обводим окошко с настройками баланса белого, экспозиции и т.д.\n"
            "12. Редактируем фотографию, не спеша, по возможности используя по больше инструментов\n"
            "13. Редактируем остальные фотографии. Тут я просто ускорю весь процесс, главное левые окна не открывайте\n"
            "14. Обводим и Открываем окно Печать\n"
            "15. Обводим окно с шаблонами печати и выбираем шаблон на 6 магнитов или фотку А5\А4\n"
            "16. Выбираем фотографии для шалона\n"
            "17. Обводим кнопку «печать…», нажимаем её\n"
            "18. Обводим кнопку «Печать» и запускаем импорт"
        )

        # Сохраняем ID теоретического сообщения для последующего удаления
        await state.update_data(theory_message_id=theory_message.message_id)

        # Переходим к тесту
        await start_quest19_test(callback, state)
        return

    sent_message = await callback.message.answer_photo(
        step_data["photo"],
        caption=step_data["text"]
    )

    # Отправляем кнопку для продолжения
    message = await callback.message.answer(
        "Нажмите 'Далее' для продолжения",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее →", callback_data="next_quest19_step")]
        ])
    )

    await state.update_data(
        step_message_id=sent_message.message_id,
        question_message_id=message.message_id
    )

@router.callback_query(F.data == "next_quest19_step")
async def next_quest19_step(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_step = user_data.get("current_step", 1) + 1

    # Удаляем предыдущие сообщения
    try:
        if "step_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["step_message_id"])
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Обновляем текущий шаг и показываем следующий
    await state.update_data(current_step=current_step)
    await show_quest19_step(callback, state)
    await callback.answer()

async def start_quest19_test(callback: types.CallbackQuery, state: FSMContext):
    # Начинаем тестовые вопросы
    await state.update_data(current_question=1)
    await ask_quest19_question(callback, state)

async def ask_quest19_question(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)

    # Вопросы теста
    questions = {
        1: {
            "text": "1. Какое действие выполняется в первую очередь?",
            "options": [
                "Вставляем флешку в картридер",
                "Открываем вкладку «Импорт»",
                "Обводим место, где появились фотографии",
                "Выбираем шаблон для печати"
            ],
            "correct": 1
        },
        2: {
            "text": "2. Что нужно сделать сразу после вставки флешки?",
            "options": [
                "Обвести место, где появилась флешка",
                "Открыть вкладку «Редактирование»",
                "Выбрать шаблон на 6 магнитов",
                "Сразу нажать «Печать»"
            ],
            "correct": 0
        },
        3: {
            "text": "3. Какое действие выполняется перед редактированием первой фотографии?",
            "options": [
                "Обводим полоску загрузки фотографий",
                "Выбираем первую фотографию в списке импортированных",
                "Выбираем пресет и сразу применяем его",
                "Нажимаем «Печать»"
            ],
            "correct": 1
        },
        4: {
            "text": "4. Какое из следующих действий выполняется во время редактирования?",
            "options": [
                "Выбор места для сохранения фотографий",
                "Применение пресетов и настройка параметров изображения",
                "Обводка полосы загрузки фотографий",
                "Вставьте флешку в картридер"
            ],
            "correct": 1
        },
        5: {
            "text": "5. Какой шаг выполняется перед печатью фотографий?",
            "options": [
                "Выбираем фотографии для шаблона печати",
                "Обводим кнопку «Импорт» и нажимаем её",
                "Открываем вкладку «Редактирование»",
                "Выбираем флешку с фотографиями"
            ],
            "correct": 0
        }
    }

    # Отправляем текущий вопрос
    question_data = questions.get(current_question, {})
    if not question_data:
        # Все вопросы пройдены, завершаем квест
        await finish_quest19(callback, state)
        return

    message = await callback.message.answer(
        question_data["text"],
        reply_markup=quest19_keyboard(question_data["options"])
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_question_data=question_data
    )
    await state.set_state(QuestState.waiting_for_answer_quest19)

@router.callback_query(F.data.startswith("qw19_"), QuestState.waiting_for_answer_quest19)
async def handle_quest19_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_answers = user_data.get("correct_answers", 0)
    question_data = user_data.get("current_question_data", {})

    selected_answer = int(callback.data.split("_")[1])
    is_correct = selected_answer == question_data["correct"]

    # Обновляем счетчик правильных ответов
    if is_correct:
        correct_answers += 1
        await callback.answer("Верный ответ!")
    else:
        await callback.answer("Неверный ответ. Попробуйте еще раз.")
        return  # Не переходим к следующему вопросу при неверном ответе

    # Сохраняем результат
    await state.update_data(correct_answers=correct_answers)

    # Переходим к следующему вопросу
    current_question += 1
    await state.update_data(current_question=current_question)
    await callback.message.delete()
    await ask_quest19_question(callback, state)

    await callback.answer()

async def finish_quest19(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    correct_answers = user_data.get("correct_answers", 0)
    total_questions = 5

    # Удаляем теоретическое сообщение
    try:
        if "theory_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["theory_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении теоретического сообщения: {e}")

    # Сохраняем результат в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 19
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=19,
                state="выполнен",
                attempt=1,
                result=correct_answers
            )
            session.add(user_result)
        else:
            user_result.state = "выполнен"
            user_result.result = correct_answers

        if correct_answers == total_questions:
            achievement_given = await give_achievement(callback.from_user.id, 19, session)
            if achievement_given:
                # Отправляем результат пользователю
                message = await callback.message.answer(
                    f"✅ Квест 19 завершен!\n"
                    f"Правильных ответов: {correct_answers} из {total_questions}\n"
                    f"Поздравляем! Вы получили ачивку за выполнение квеста на 100%!",
                    reply_markup=get_quest_finish_keyboard(correct_answers, total_questions, 19)
                )
            else:
                message = await callback.message.answer(
                    f"✅ Квест 19 завершен!\n"
                    f"Правильных ответов: {correct_answers} из {total_questions}",
                    reply_markup=get_quest_finish_keyboard(correct_answers, total_questions, 19)
                )
        else:
            message_text = f"Есть ошибки, попробуй заново\nВерных ответов: {correct_count} из {total_questions}"


        await session.commit()


    await state.update_data(question_message_id=message.message_id)
    await state.clear()

# Квест 20 - Время и Кадры
async def quest_20(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
        if "timer_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["timer_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Отправляем теорию
    message = await callback.message.answer(
        "⏱️ Квест 20: Время и Кадры\n\n"
        "Процесс \"Импорт\"\n"
        "Что такое \"Импорт\"?\n"
        "Это процесс, когда ты фотографируешь детей и их родителей в детских зонах и приносишь лучшие снимки на базу для печати и продажи.\n\n"
        "Три главных правила успешного импорта:\n"
        "1. Тайминг ⏳ — приносите фотографии каждые 10 минут.\n"
        "2. Количество 📸 — в среднем ты должен приносить от 15 до 30 лучших снимков за один заход.\n"
        "3. Качество 🌟 — каждое фото должно быть чётким, хорошо освещённым, передавать эмоции.\n\n"
        "Нажмите 'Начать выполнение' для старта задания.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать выполнение", callback_data="start_quest20")]
        ])
    )

    await state.update_data(
        question_message_id=message.message_id,
        timer_started=False,
        photos_taken=0,
        required_photos=10  # Нужно сделать 10 фото
    )
    await callback.answer()

@router.callback_query(F.data == "start_quest20")
async def start_quest20(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Запускаем таймер
    await state.update_data(
        timer_started=True,
        start_time=datetime.datetime.now(),
        user_photos=[],
        timer_active=True
    )

    # Отправляем сообщение с таймером
    message = await callback.message.answer(
        "⏱️ Таймер запущен! У вас есть 10 минут.\n"
        "Сделайте 10 фото разных детей в различных позах.\n"
        "Оставшееся время: 10:00",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Завершить досрочно", callback_data="finish_quest20_early")]
        ])
    )

    # Запускаем задание
    await state.update_data(
        timer_message_id=message.message_id,
        question_message_id=message.message_id
    )
    await state.set_state(QuestState.waiting_for_photo_quest20)
    asyncio.create_task(start_quest20_timer(callback, state))
    await callback.answer()


async def start_quest20_timer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    start_time = user_data.get("start_time", datetime.datetime.now())
    end_time = start_time + datetime.timedelta(minutes=10)
    photos_taken = user_data.get("photos_taken", 0)
    required_photos = user_data.get("required_photos", 10)
    timer_active = user_data.get("timer_active", True)

    while datetime.datetime.now() < end_time and photos_taken < required_photos and timer_active:
        remaining = end_time - datetime.datetime.now()
        minutes, seconds = divmod(remaining.seconds, 60)

        message_text = (
            f"⏱️ Таймер запущен! У вас есть 10 минут.\n"
            f"Сделайте {required_photos} фото разных детей в различных позах.\n"
            f"Оставшееся время: {minutes:02d}:{seconds:02d}\n"
            f"Сделано фото: {photos_taken}/{required_photos}"
        )

        try:
            await callback.bot.edit_message_text(
                message_text,
                chat_id=callback.message.chat.id,
                message_id=user_data["timer_message_id"],
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Завершить досрочно", callback_data="finish_quest20_early")]
                ])
            )
        except Exception as e:
            print(f"Ошибка при обновлении таймера: {e}")
            break

        await asyncio.sleep(1)
        user_data = await state.get_data()
        photos_taken = user_data.get("photos_taken", 0)
        timer_active = user_data.get("timer_active", True)

    if timer_active:
        await finish_quest20(callback, state)

@router.message(F.photo, QuestState.waiting_for_photo_quest20)
async def handle_photo_quest20(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if user_data.get("quest_completed", False):
        await message.delete()
        return

    photos_taken = user_data.get("photos_taken", 0)
    user_photos = user_data.get("user_photos", [])
    required_photos = user_data.get("required_photos", 10)

    # Если уже собрано достаточно фото, игнорируем новые
    if photos_taken >= required_photos:
        await message.delete()
        return

    # Добавляем фото в список
    user_photos.append(message.photo[-1].file_id)
    photos_taken += 1

    await state.update_data(
        photos_taken=photos_taken,
        user_photos=user_photos
    )

    # Проверяем, все ли фото собраны
    if photos_taken >= required_photos:
        await finish_quest20(message, state)

    await message.delete()


@router.callback_query(F.data == "finish_quest20_early")
async def finish_quest20_early(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos_taken = user_data.get("photos_taken", 0)

    if photos_taken == 0:
        await callback.answer("Нельзя завершить без ни одного фото", show_alert=True)
        return

    await state.update_data(timer_active=False)
    await finish_quest20(callback, state)
    await callback.answer()


async def finish_quest20(event: Union[types.Message, types.CallbackQuery], state: FSMContext):
    # Проверяем, не завершен ли уже квест
    user_data = await state.get_data()
    if user_data.get("quest_completed", False):
        return

    # Помечаем квест как завершенный
    await state.update_data(quest_completed=True)

    # Универсальная обработка входящего объекта
    if isinstance(event, types.CallbackQuery):
        user = event.from_user
        chat_id = event.message.chat.id
        bot = event.bot
        message = event.message  # Получаем объект Message
    else:
        user = event.from_user
        chat_id = event.chat.id
        bot = event.bot

    user_photos = user_data.get("user_photos", [])
    required_photos = user_data.get("required_photos", 10)
    photos_taken = len(user_photos)

    # Удаляем сообщение с таймером если оно есть
    try:
        if "timer_message_id" in user_data:
            await bot.delete_message(chat_id, user_data["timer_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщения с таймером: {e}")

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == user.id,
                UserResult.quest_id == 20
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=user.id,
                quest_id=20,
                state="на модерации",
                attempt=1,
                result=photos_taken
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            user_result.result = photos_taken
            user_result.attempt += 1

        await session.commit()

    # Формируем сообщение для модератора
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 20 - Время и Кадры\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"Сделано фото: {photos_taken}/{required_photos}"
    )

    # Отправляем фото модератору (разбиваем на группы по 10 фото)
    if user_photos:
        try:
            # Разбиваем фото на группы по 10
            for i in range(0, len(user_photos), 10):
                photo_group = user_photos[i:i + 10]
                media = MediaGroupBuilder()

                for j, photo in enumerate(photo_group):
                    if i == 0 and j == 0:  # Добавляем подпись только к первому фото первой группы
                        media.add_photo(media=photo, caption=caption)
                    else:
                        media.add_photo(media=photo)

                await bot.send_media_group(admin_chat_id, media=media.build())
        except Exception as e:
            print(f"Ошибка при отправке медиагруппы: {e}")
            await bot.send_message(
                admin_chat_id,
                f"⚠️ Ошибка при отправке фото от {user.full_name} для квеста 20"
            )

    # Отправляем кнопки модерации только если есть хотя бы одно фото
    if photos_taken > 0:
        await bot.send_message(
            admin_chat_id,
            f"Фото от {user.full_name} для квеста 20 готовы к проверке.\n"
            f"Отправлено фото: {photos_taken}/{required_photos}",
            reply_markup=moderation_keyboard(user.id, 20)
        )
    else:
        await bot.send_message(
            admin_chat_id,
            f"⚠️ Пользователь {user.full_name} завершил квест 20 без фото"
        )

    # Сообщение пользователю
    await bot.send_message(
        chat_id,
        f"✅ Квест завершен! Сделано фото: {photos_taken}/{required_photos}\n"
        "Фото отправлены на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )

    # Очищаем состояние
    await state.clear()


# Квест 21 - Знакомство с коллегами (копия из прошлого дня)
async def quest_21(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Запрашиваем количество коллег
    message = await callback.message.answer(
        "Квест 21: Знакомство с коллегами\n"
        "Сколько коллег работает с вами на смене? (Введите число)",
        reply_markup=quest9_cancel_keyboard()
    )

    await state.update_data(
        question_message_id=message.message_id,
        colleagues_data=[],
        current_colleague=1
    )
    await state.set_state(QuestState.waiting_for_colleagues_count_21)
    await callback.answer()


@router.message(QuestState.waiting_for_colleagues_count_21)
async def handle_colleagues_count_21(message: types.Message, state: FSMContext):
    try:
        colleagues_count = int(message.text)
        if colleagues_count < 1 or colleagues_count > 20:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число (от 1 до 20).")
        return

    await message.delete()
    user_data = await state.get_data()
    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    await state.update_data(colleagues_count=colleagues_count)
    await ask_colleague_info_21(message, state)


async def ask_colleague_info_21(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    current_colleague = user_data.get("current_colleague", 1)
    colleagues_count = user_data.get("colleagues_count", 1)

    if current_colleague > colleagues_count:
        # Всех коллег опросили, отправляем на модерацию
        await send_colleagues_to_moderation_21(message, state)
        return

    # Запрашиваем информацию о коллеге
    question = await message.answer(
        f"Коллега {current_colleague} из {colleagues_count}:\n"
        "1. Выберите должность:",
        reply_markup=quest21_position_keyboard()
    )

    await state.update_data(
        question_message_id=question.message_id,
        current_colleague=current_colleague
    )
    await state.set_state(QuestState.waiting_for_colleague_position_21)


@router.callback_query(F.data.startswith("qw21_position_"), QuestState.waiting_for_colleague_position_21)
async def handle_colleague_position_21(callback: types.CallbackQuery, state: FSMContext):
    position = callback.data.split("_")[-1]

    await callback.message.delete()
    await state.update_data(current_position=position)

    # Запрашиваем фамилию
    surnames = ["Алиева", "Белюкова", "Бережной", "Бугрышева", "Глухов", "Горкунов",
                "Захарова", "Шептун", "Денисламова", "Денисов", "Дорофеев", "Дорохина",
                "Дмитриев", "Иванов", "Камаев", "Киршина", "Кочетов", "Ильин",
                "Ирназаров", "Косарева", "Маликова", "Мартенс", "Никифорова",
                "Пучкина", "Мухаметчина", "Першукова", "Рахманова", "Семенов",
                "Скрябина", "Лясс", "Томилова", "Уоррен", "Чудновская", "Хаов", "Эрлих"]

    builder = InlineKeyboardBuilder()
    for surname in surnames:
        builder.button(text=surname, callback_data=f"qw21_surname_{surname}")
    builder.adjust(3)

    question = await callback.message.answer(
        "2. Выберите фамилию коллеги:",
        reply_markup=builder.as_markup()
    )

    await state.update_data(question_message_id=question.message_id)
    await state.set_state(QuestState.waiting_for_colleague_surname_21)
    await callback.answer()


@router.callback_query(F.data.startswith("qw21_surname_"), QuestState.waiting_for_colleague_surname_21)
async def handle_colleague_surname_21(callback: types.CallbackQuery, state: FSMContext):
    surname = callback.data.split("_", 2)[-1]

    await callback.message.delete()
    await state.update_data(current_surname=surname)

    # Запрашиваем имя
    question = await callback.message.answer(
        "3. Введите имя коллеги:",
        reply_markup=quest21_cancel_keyboard()
    )

    await state.update_data(question_message_id=question.message_id)
    await state.set_state(QuestState.waiting_for_colleague_name_21)
    await callback.answer()


@router.message(QuestState.waiting_for_colleague_name_21)
async def handle_colleague_name_21(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Пожалуйста, введите имя.")
        return

    await message.delete()
    user_data = await state.get_data()
    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    await state.update_data(current_name=name)

    # Запрашиваем телеграм
    question = await message.answer(
        "4. Введите имя пользователя в Telegram (например, @username):",
        reply_markup=quest21_cancel_keyboard()
    )

    await state.update_data(question_message_id=question.message_id)
    await state.set_state(QuestState.waiting_for_colleague_telegram_21)


@router.message(QuestState.waiting_for_colleague_telegram_21)
async def handle_colleague_telegram_21(message: types.Message, state: FSMContext):
    telegram = message.text.strip()
    if not telegram:
        await message.answer("Пожалуйста, введите имя пользователя.")
        return

    await message.delete()
    user_data = await state.get_data()
    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    # Сохраняем данные о коллеге
    colleagues_data = user_data.get("colleagues_data", [])
    colleagues_data.append({
        "position": user_data.get("current_position"),
        "surname": user_data.get("current_surname"),
        "name": user_data.get("current_name"),
        "telegram": telegram
    })

    # Переходим к следующему коллеге
    current_colleague = user_data.get("current_colleague", 1) + 1
    await state.update_data(
        colleagues_data=colleagues_data,
        current_colleague=current_colleague
    )

    await ask_colleague_info_21(message, state)


async def send_colleagues_to_moderation_21(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    colleagues_data = user_data.get("colleagues_data", [])

    # Формируем сообщение для модератора
    report_text = "📋 Отчет по квесту 21 (Знакомство с коллегами):\n\n"
    report_text += f"👤 Сотрудник: {message.from_user.full_name} (@{message.from_user.username or 'нет'})\n"
    report_text += f"📅 Дата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    report_text += "Список коллег:\n"

    for i, colleague in enumerate(colleagues_data, 1):
        report_text += (
            f"{i}. {colleague['surname']} {colleague['name']}\n"
            f"   Должность: {colleague['position']}\n"
            f"   Telegram: {colleague['telegram']}\n\n"
        )

    # Отправляем модератору
    await message.bot.send_message(
        admin_chat_id,
        report_text,
        reply_markup=moderation_keyboard(message.from_user.id, 21)
    )

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == message.from_user.id,
                UserResult.quest_id == 21
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=message.from_user.id,
                quest_id=21,
                state="на модерации",
                attempt=1,
                result=0
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"

        await session.commit()

    # Сообщаем пользователю
    await message.answer(
        "✅ Данные о коллегах отправлены на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()


@router.callback_query(F.data == "cancel_quest21")
async def cancel_quest21(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Квест отменен")
    await callback.answer()


# Квест 22 - Этапы продаж
async def quest_22(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Этапы продаж
    stages = [
        {
            "number": 1,
            "name": "Подготовка",
            "description": "Самый первый этап продаж, он начинается ещё до выхода в фотозону. Суть его сводится к максимальному сбору информации, то есть какое количество семей зашло, какого возраста дети, сколько детей в семье(один или есть братья/сёстры), и ресурсов, которые могут пригодиться при общении с клиентом, а именно эмоциональный настрой сотрудника, мотивация на продажу и немаловжно - внешний вид, который должен соответсвовать регламентам компнаии."
        },
        {
            "number": 2,
            "name": "Вступление в контакт",
            "description": "Вступление в контакт – это начало диалога с потенциальным клиентом. Правильно установленный контакт подразумевает собой:\n- Хорошее первое впечатление\n- Привлечение внимания клиента\n- Представление себя\nЕсли Вы понравились, то понравятся Ваши фотографии и наоборот. Ошибка продавцов/фотографов на этапе вхождения в контакт в том, что вы пытаетесь вести себя неестественно. Вся эта неискренность, шансов на удачу не прибавляет, а только отпугивает людей."
        },
        {
            "number": 3,
            "name": "Фотографирование",
            "description": "Фотографирование – это процесс съемки, запечатления объекта, в нашем случае это семьи, дети, родители и их эмоции, памятные моменты (например, дни рождения) на фотокамеру. На данном этапе важно поддерживать диалог с клиентом, что позволит не уйти клиенту в собственные мысли, а так же поддержание диалога напрямую влияет на результат съёмки. И самое главное не забывать про качество и разнообразие кадров! В процессе фотографирования вы можете выявлять потребности клиента, это пригодится вам в дальнейшиъ этапах. Вы должны делать такие фотографии, чтобы сами хотели приобрести, и которые клиенты(родители) не смогут сделать сами на свои смартфоны."
        },
        {
            "number": 4,
            "name": "Обработка импорта",
            "description": "Обработка импорта – процесс загрузки фотографий с флеш-карты в программу компьютера Lightroom, импортирование их в папку фотографов, редактирование во вкладке «коррекция». Не менее важный этап: нужно следить за работой фотографа, указывать на ошибки и следить за их исправлением, также исправлять некоторые недочёты уже в самом Лайтруме и доводить фотографию до шикарного результата."
        },
        {
            "number": 5,
            "name": "Печать продукции",
            "description": "Печать продукции - это процесс перенесения отредактированных кадров с Lightroom на бумажный носитель (фотобумага) и преобразование готовых фотографий в нашу продукцию. Важно следить за качеством печати и состоянием продукции (например, чтобы не были позарапаны стёкла на рамках). Здесь важно не забывать делать упор на ту, продукцию, в которой клиент больше заинтересован, а это можно было выявить на этапе фотографирования при выявлении потребностей, например клиент озвучивает, что часто бывает в парке и у него уже есть магниты, в этом случае важно сделать упор на печать той продукции, которой у него еще нет, дополнительная и оригинальная продукция."
        },
        {
            "number": 6,
            "name": "Презентация продукции на стенде",
            "description": "Презентация товара - важнейший этап, который демонстрирует нашу продукцию и мотивирует на покупку. На стенде должны быть прайс, табличка о запрете съёмки и вся продукция, чтобы продавец мог рассказать и показать все возможные вариантые. Важно не хаотично и как попало презентовать продукцию, а аккуратно и красиво разложить, чтобы еще издалека стенд привлекал покупателя. Для хорошей презентации понадобится:\n- Знание продукта\n- Правильная манера и способ донесения информации до покупателя\n- Умение выявлять скрытые потребности клиента"
        },
        {
            "number": 7,
            "name": "Объявление цены",
            "description": "Объявление цены - этап, когда требуется озвучить цену на имеющуюся продукцию, чаще всего вопрос о стоимости возникает у покупателя, а продавец должен грамотно ответить на этот вопрос, рассказывая о достоинствах продукции. Начинать озвучивать цены нужно с самой большой цены и двигаться к самой маленькой. Не делайте паузу после объявления цены. Ведь это самый дискомфортный момент в продажах. Здесь эмоции спадают и начинается прощания с деньгами. И если клиент колеблется, то в этот момент ему проще всего отказать и перестать далее слушать. Чтобы избежать этого, используйте технику «Проезд». Назовите цену и без паузы продолжайте поддерживать общение или задайте какой-то уместный вопрос, выявляющий потребности или наталкивающий на покупку."
        },
        {
            "number": 8,
            "name": "Работа с возражениями",
            "description": "Работа с возражениями - это отработка аргументами над отказами от клиента. Многие считают, что работа с возражениями, это противостояние продавца и клиента. Некоторые называют этот этап — борьба с возражениями и видимо как-то действительно борются с клиентами. Но это смешно, ведь клиенты никому ничего не должны. На самом деле работа с возражениями — это не борьба, а банальное прояснение. Прояснение того, какое конкретное сомнение кроется за сказанным возражением. А далее Вам всего лишь нужно привести аргумент, который поможет это сомнение снять. Работу со всеми возражениями, можно свести к одному вопросу: «Скажите пожалуйста, почему Вы считаете, что…». А далее основная задача продавца снять сомнение исходя из возражения."
        },
        {
            "number": 9,
            "name": "Завершение продажи",
            "description": "Завершение продажи - это согласие клиента на покупку и проведение самой оплаты. Ошибка в том, что многие продавцы либо вообще не используют техники завершения продаж и упускают клиента, либо завершают продажи, когда это неуместно. На самом деле есть простые вопросы, которые позволят Вам понять степень готовности клиента к покупке. К примеру:\n- Как Вам фотографии в целом?\n- Вам же эти фотографии упаковать? (здесь нужно указать на выбранные фото и сделать жест «согласия» головой, кивать)\n- У Вас оплата картой или наличными?\n- Какие фотографии Вам упаковать?"
        },
        {
            "number": 10,
            "name": "Увеличение чека",
            "description": "Увеличение чека - это повышение общей стоимости покупки засчёт предложения альтернативной продукции или скидок согласно регламентированным в компании пакетам акций. После оформления продажи, не забывайте о способах увеличения суммы чека. Самый простой способ увеличить чек, это предложить клиенту другие варианты продукции или «пакеты»."
        },
        {
            "number": 11,
            "name": "Удержание клиента",
            "description": "Удержание клиента - это закладывание базы для осуществления продажи с этим клиентом в перспективе. Как пример:\n- Спросить у покупателя после завершения продажи, какую ещё продукцию он хотел бы видеть в нашем ассортименте\n- Уточнить у родителя, когда день рождение у ребёнка, и предложить провести фотопрогулку\n- Узнать есть ли какие то пожелания или претензии для быстрого исправления и повышения качества наших услуг\n- Предложить подписаться на соц. сети компании, чтобы быть в курсе нововведений и участвовать в розыгрышах\nПомните, привлечение нового клиента обходится примерно в 7 раз дороже продажи старому клиенту."
        },
        {
            "number": 12,
            "name": "Анализ продажи",
            "description": "Анализ продажи - это этап про развитие продавца. Важно провести анализ диалога с клиентом и к какому результату привёл данный диалог - продажа или отказ? Как мог сотрудник еще обработать возражение, чтобы результатом диалога была продажа. Провести небольшой мозговой штурм, а в дальнейшем обязательно применить новые варианты обработки возражений или подход к клиенту при новом взаимодействии с клиентом."
        }
    ]

    # Сохраняем этапы в state
    await state.update_data(
        stages=stages,
        current_stage=0,
        stage_message_ids=[],
        test_mode=False,
        user_answers={},  # Словарь для хранения ответов пользователя
        current_question=1,
        total_questions=12
    )

    # Начинаем показ первого этапа
    await show_next_stage_22(callback, state)
    await callback.answer()


async def show_next_stage_22(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_stage = user_data.get("current_stage", 0)
    stages = user_data.get("stages", [])
    stage_message_ids = user_data.get("stage_message_ids", [])

    # Удаляем предыдущее сообщение с кнопкой
    if "stage_message_id" in user_data:
        try:
            await callback.message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Проверяем, есть ли еще этапы для показа
    if current_stage < len(stages):
        stage_data = stages[current_stage]

        if current_stage == 0:
             sent_message = await callback.message.answer(
                 f"Квест 22: Этапы продаж \n\n"
                 f"В компании LIVEFOTO выделенны 12 этапов продаж, каждый из них важен,потому что ведёт к нужному результату! \n"
                 f"📌 Этап {stage_data['number']}: {stage_data['name']}\n\n"
                 f"{stage_data['description']}",
                 parse_mode="Markdown"
             )
             stage_message_ids.append(sent_message.message_id)
        else:
            sent_message = await callback.message.answer(
                f"📌 Этап {stage_data['number']}: {stage_data['name']}\n\n"
                f"{stage_data['description']}",
                parse_mode="Markdown"
            )
            stage_message_ids.append(sent_message.message_id)

        # Создаем клавиатуру (Далее или Приступить к тесту для последнего шага)
        if current_stage < len(stages) - 1:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее →", callback_data="next_stage_22")]
            ])
            action_text = "Нажмите 'Далее' для продолжения"
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Приступить к тесту", callback_data="start_quest22_test")]
            ])
            action_text = "После просмотра всех этапов нажмите 'Приступить к тесту'"

        # Отправляем сообщение с кнопкой
        stage_message = await callback.message.answer(
            action_text,
            reply_markup=keyboard
        )

        # Обновляем состояние
        await state.update_data(
            current_stage=current_stage + 1,
            stage_message_ids=stage_message_ids,
            stage_message_id=stage_message.message_id
        )
    else:
        # Все этапы показаны, можно начинать тест
        await start_quest22_test(callback, state)


@router.callback_query(F.data == "next_stage_22")
async def handle_next_stage_22(callback: types.CallbackQuery, state: FSMContext):
    await show_next_stage_22(callback, state)
    await callback.answer()


@router.callback_query(F.data == "start_quest22_test")
async def start_quest22_test(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "stage_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["stage_message_id"])
        if "stage_message_ids" in user_data:
            for msg_id in user_data["stage_message_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем тест
    await state.update_data(
        test_mode=True,
        current_question=1,
        user_answers={},
        total_questions=12
    )
    await ask_quest22_question(callback.message, state)
    await callback.answer()

async def ask_quest22_question(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)

    # Удаляем предыдущее сообщение, если оно есть
    if "question_message_id" in user_data:
        try:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Вопросы теста
    questions = {
        1: {
            "text": "1. Подготовка\nЧто важно сделать перед выходом в фотозону?",
            "correct": "Проанализировать сколько семей зашло, какого возраста дети, сколько детей в семье, а так же свой эмоциональный настрой, личную мотивацию и соответсвие внешнего вида регламенту компании"
        },
        2: {
            "text": "2. Вступление в контакт\nЧто подразумевает под собой правильно установленный контакт?",
            "correct": "Хорошее первое впечатление, привлечение внимания, представления себя"
        },
        3: {
            "text": "3. Фотографирование\nПочему важно поддерживать диалог с клиентом во время съемки?",
            "correct": "Это помогает удерживать клиента в интересе и улучшает результат съемки."
        },
        4: {
            "text": "4. Обработка импорта\nЧто включает в себя этап обработки импорта для фотографий?",
            "correct": "Загрузка фотографий в Lightroom и редактирование."
        },
        5: {
            "text": "5. Печать продукции\nНа что необходимо обращать внимание при печати продукции?",
            "correct": "На качество печати и состояние готовой продукции."
        },
        6: {
            "text": "6. Презентация продукции на стенде\nЧто понадобится для хорошений презентации продукции?",
            "correct": "Знание продукта, правильная манера и способ донесения информации до клиента, умение выявлять скрытые потребности клиента"
        },
        7: {
            "text": "7. Объявление цены\nКак правильно озвучивать цену на продукцию?",
            "correct": "Начинать с самой высокой цены и продолжать к самой низкой, без пауз."
        },
        8: {
            "text": "8. Работа с возражениями\nЧто важно помнить при работе с возражениями клиента?",
            "correct": "Это не борьба, а прояснение сомнений клиента и предоставление аргументов для их снятия."
        },
        9: {
            "text": "9. Завершение продажи\nКак можно понять готовность клиента к покупке?",
            "correct": "Задавать вопросы о впечатлениях от фотографий и уточнять способ оплаты."
        },
        10: {
            "text": "10. Увеличение чека\nКак можно увеличить общую стоимость покупки?",
            "correct": "Предложить альтернативные продукты или использовать скидки по регламентированным пакетам акций."
        },
        11: {
            "text": "11. Удержание клиента\nЧто можно сделать для удержания клиента на будущее?",
            "correct": "Спросить о пожеланиях к ассортименту и предложить подписаться на соцсети."
        },
        12: {
            "text": "12. Анализ продажи\nПочему важен анализ диалога с клиентом?",
            "correct": "Это помогает понять, что сработало, а что нет, и улучшить подход в будущем."
        }
    }

    # Проверяем, есть ли еще вопросы
    if current_question > len(questions):
        # Все вопросы пройдены, завершаем квест
        await finish_quest22(update, state)
        return

    # Отправляем текущий вопрос
    question_data = questions.get(current_question, {})
    sent_message = await callback.answer(
        question_data["text"]
    )

    await state.update_data(
        question_message_id=sent_message.message_id,
        current_question_data=question_data
    )
    await state.set_state(QuestState.waiting_for_answer_quest22)


@router.message(QuestState.waiting_for_answer_quest22)
async def handle_quest22_answer(message: types.Message, state: FSMContext):
    user_answer = message.text.strip()
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    question_data = user_data.get("current_question_data", {})
    user_answers = user_data.get("user_answers", {})

    # Сохраняем ответ пользователя с пометкой is_correct=False (по умолчанию)
    user_answers[current_question] = {
        "question": question_data["text"],
        "user_answer": user_answer,
        "correct_answer": question_data["correct"],
        "is_correct": False  # По умолчанию ответ неверный, модератор исправит
    }

    # Удаляем предыдущее сообщение с вопросом
    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    # Переходим к следующему вопросу или завершаем тест
    if current_question < user_data.get("total_questions", 12):
        await state.update_data(
            current_question=current_question + 1,
            user_answers=user_answers
        )
        await ask_quest22_question(message, state)
    else:
        await state.update_data(user_answers=user_answers)
        await finish_quest22(message, state)

    await message.delete()


@router.callback_query(F.data == "next_quest22_question")
async def next_quest22_question(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1) + 1

    # Удаляем сообщение с обратной связью
    try:
        if "feedback_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["feedback_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Переходим к следующему вопросу
    await state.update_data(current_question=current_question)
    await ask_quest22_question(callback.message, state)
    await callback.answer()


async def finish_quest22(update: Union[types.Message, types.CallbackQuery], state: FSMContext):
    try:
        user_data = await state.get_data()
        user_answers = user_data.get("user_answers", {})

        if isinstance(update, types.CallbackQuery):
            user = update.from_user
            chat_id = update.message.chat.id
            bot = update.bot
        else:
            user = update.from_user
            chat_id = update.chat.id
            bot = update.bot

        # Сохраняем ответы в глобальном хранилище (если нужно)
        # Или сразу формируем клавиатуру модерации

        # Формируем текст всех ответов
        answers_text = "📝 Ответы пользователя:\n\n"
        for q_num, answer_data in sorted(user_answers.items(), key=lambda x: int(x[0])):
            answers_text += (
                f"🔹 Вопрос {q_num}:\n{answer_data['question']}\n\n"
                f"✏️ Ответ:\n{answer_data['user_answer']}\n\n"
                f"✅ Правильный ответ:\n{answer_data['correct_answer']}\n"
                f"{'-' * 30}\n\n"
            )

        # Создаем кнопки для модерации
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        # Добавляем кнопки для каждого вопроса
        buttons_row = []
        for q_num in sorted(user_answers.keys(), key=int):
            buttons_row.append(
                InlineKeyboardButton(
                    text=f"Вопрос {q_num}",
                    callback_data=f"select_22_{user.id}_{q_num}"
                )
            )
            # Разбиваем на ряды по 3 кнопки
            if len(buttons_row) == 3:
                keyboard.inline_keyboard.append(buttons_row)
                buttons_row = []

        # Добавляем оставшиеся кнопки
        if buttons_row:
            keyboard.inline_keyboard.append(buttons_row)

        # Кнопка подтверждения
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="✅ Завершить выбор",
                callback_data=f"finish_select_22_{user.id}"
            )
        ])

        # Отправляем модератору
        try:
            # Сначала отправляем текст ответов
            if len(answers_text) > 4000:
                parts = [answers_text[i:i + 4000] for i in range(0, len(answers_text), 4000)]
                for part in parts:
                    await bot.send_message(admin_chat_id, part)
            else:
                await bot.send_message(admin_chat_id, answers_text)

            # Затем отправляем клавиатуру
            await bot.send_message(
                admin_chat_id,
                "Выберите вопросы для переделки:",
                reply_markup=keyboard
            )

            # Уведомляем пользователя
            await bot.send_message(
                chat_id,
                "✅ Ваши ответы отправлены на модерацию",
                reply_markup=types.ReplyKeyboardRemove()
            )

        except Exception as e:
            logging.error(f"Ошибка отправки модератору: {str(e)}")
            await bot.send_message(
                chat_id,
                "⚠️ Ошибка при отправке ответов",
                reply_markup=types.ReplyKeyboardRemove()
            )

    except Exception as e:
        logging.error(f"Ошибка в finish_quest22: {str(e)}")
    finally:
        await state.clear()


# Обработчик для всех остальных ответов
@router.callback_query(QuestState.waiting_for_answer)
async def handle_other_answers(callback: types.CallbackQuery):
    # Уведомляем пользователя, что ответ неверный
    await callback.answer("Ответ неверный. Попробуйте ещё раз!")