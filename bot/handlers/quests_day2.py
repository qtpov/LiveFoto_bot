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
        (12, "Привыкни к аппарату"),
        (13, "Фотограф"),
        (14, "Зоны фотографирования"),
        (15, "1000 и 1 поза"),
        (16, "Силует"),
        (17, "Дожми до результата"),
        (18, "В здоровом теле здоровый дух"),
        (19, "Практика фотографирования"),
        (20, "Алгоритм действий"),
        (21, "Время и кадры"),
        (22, "Знакомство с коллегами"),
        (23, "Этапы продаж"),
        (24, "Подошел, сфоткал, победил"),
        (25, "5 продаж"),
        (26, "Сила отказов"),
        (27, "Фидбек")
    ],
    3: [
        (28, "Правильное фото"),
        (29, "Собери всё"),
        (30, "ФотоОхотник"),
        (31, "Полный цикл"),
        (32, "Ценность кадра"),
        (33, "Ценности компании"),
        (34, "Клиент"),
        (35, "Фидбек")
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
        message_text = f"Квест завершен! 🎉\nВерных ответов: {correct_count} из {total_questions}"

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
            "description": "🔧 Настройка ISO, выдержки и диафрагмы"
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
        message_text = "✅ Фото получено. Отправьте следующее фото или нажмите 'Пропустить'."
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
            caption=f"{caption}\n\nЗадание {photo['task']}" if i == 1 else f"Задание {photo['task']}"
        ))

    if len(media) > 1:
        await callback.bot.send_media_group(admin_chat_id, media)
    else:
        await callback.bot.send_photo(admin_chat_id, media[0].media, caption=media[0].caption)

    # Дополнительная информация для модератора
    await callback.bot.send_message(
        admin_chat_id,
        f"Фото от {user.full_name} для квеста 13 готовы к проверке.",
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
        message_text += " Отправьте следующее фото или нажмите 'Пропустить зону'."
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
        # # 1. Шаблоны для мальчиков (1 медиагруппа)
        # media_boy_templates = MediaGroupBuilder()
        # for i, template in enumerate(boy_templates):
        #     if i == 0:
        #         media_boy_templates.add_photo(media=template["file_id"], caption=f"{caption}\n\nШаблоны для мальчиков:")
        #     else:
        #         media_boy_templates.add_photo(media=template["file_id"])
        # await message.bot.send_media_group(admin_chat_id, media=media_boy_templates.build())

        # 2. Фото мальчиков (может потребоваться несколько медиагрупп)
        for i in range(0, len(boy_photos), 10):  # Разбиваем по 10 фото
            media_boy_photos = MediaGroupBuilder()
            for photo in boy_photos[i:i+10]:
                media_boy_photos.add_photo(media=photo["file_id"], caption=f"Фото мальчика")
            await message.bot.send_media_group(admin_chat_id, media=media_boy_photos.build())

        # # 3. Шаблоны для девочек (1 медиагруппа)
        # media_girl_templates = MediaGroupBuilder()
        # for i, template in enumerate(girl_templates):
        #     if i == 0:
        #         media_girl_templates.add_photo(media=template["file_id"], caption="Шаблоны для девочек:")
        #     else:
        #         media_girl_templates.add_photo(media=template["file_id"])
        # await message.bot.send_media_group(admin_chat_id, media=media_girl_templates.build())

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
# Квест 16 - Дожми до результата
async def quest_16(callback: types.CallbackQuery, state: FSMContext):
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
        "💬 Квест 16: Дожми до результата\n\n"
        "Вам нужно убедить виртуального клиента согласиться на фотосессию.\n"
        "Выберите наиболее подходящие ответы в диалоге.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать диалог", callback_data="start_quest16")]
        ])
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step=1,
        correct_answers=0,
        total_questions=5  # 5 шагов в диалоге
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

    # Начинаем первый шаг диалога
    await ask_quest16_question(callback, state)
    await callback.answer()

async def ask_quest16_question(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_step = user_data.get("current_step", 1)

    # Вопросы и варианты ответов
    questions = {
        1: {
            "text": "Клиент: 'Я не уверен, что хочу фотографироваться...'\n\nВаш ответ:",
            "options": [
                "Просто попробуйте, это бесплатно!",
                "Я понимаю ваши сомнения. Могу показать примеры фото других детей?",
                "Все фотографируются, вам тоже нужно!",
                "Хорошо, тогда до свидания."
            ],
            "correct": 1
        },
        2: {
            "text": "Клиент: 'Мой ребенок не любит фотографироваться'\n\nВаш ответ:",
            "options": [
                "Наши фотографы умеют работать с такими детьми",
                "Все дети у нас фотографируются без проблем",
                "Может быть, вы просто не умеете его фотографировать?",
                "Давайте попробуем, это займет всего минуту"
            ],
            "correct": 0
        },
        3: {
            "text": "Клиент: 'А зачем мне эти фото?'\n\nВаш ответ:",
            "options": [
                "Чтобы вспоминать этот день",
                "Это отличный подарок бабушкам и дедушкам",
                "Все покупают, и вам надо",
                "Наши фото - это память на всю жизнь"
            ],
            "correct": 3
        },
        4: {
            "text": "Клиент: 'Мне кажется, это дорого...'\n\nВаш ответ:",
            "options": [
                "У нас есть скидки при покупке нескольких фото",
                "Это не дорого для таких качественных фото",
                "Вы можете посмотреть фото и потом решить",
                "Стоимость начинается от 500 рублей"
            ],
            "correct": 2
        },
        5: {
            "text": "Клиент: 'Хорошо, давайте попробуем'\n\nВаш ответ:",
            "options": [
                "Отлично! Давайте начнем",
                "Я же говорил, что вы согласитесь",
                "Наконец-то!",
                "Сейчас позову фотографа"
            ],
            "correct": 0
        }
    }

    # Отправляем текущий вопрос
    question_data = questions[current_step]
    message = await callback.message.answer(
        question_data["text"],
        reply_markup=quest16_keyboard(question_data["options"])
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_question_data=question_data
    )
    await state.set_state(QuestState.waiting_for_answer_quest16)

@router.callback_query(F.data.startswith("qw16_"), QuestState.waiting_for_answer_quest16)
async def handle_quest16_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_step = user_data.get("current_step", 1)
    correct_answers = user_data.get("correct_answers", 0)
    total_questions = user_data.get("total_questions", 5)
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

    # Переходим к следующему вопросу или завершаем квест
    current_step += 1
    if current_step > total_questions:
        await finish_quest16(callback, state, correct_answers, total_questions)
    else:
        await state.update_data(current_step=current_step)
        await callback.message.delete()
        await ask_quest16_question(callback, state)

    await callback.answer()

async def finish_quest16(callback: types.CallbackQuery, state: FSMContext, correct_count: int,
                         total_questions: int):
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
                result=correct_count
            )
            session.add(user_result)
        else:
            user_result.state = "выполнен"
            user_result.result = correct_count

        await session.commit()

    # Отправляем результат пользователю
    await callback.message.delete()
    message = await callback.message.answer(
        f"✅ Квест 16 завершен!\n"
        f"Правильных ответов: {correct_count} из {total_questions}",
        reply_markup=get_quest_finish_keyboard(correct_count, total_questions, 16)
    )

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
                    "Повторите 5 раз влево, затем 5 раз вправо.",
            "video": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ"
        },
        2: {
            "text": "2. Вращение плечами\n\n"
                    "Согните руки в локтях, положите кисти на плечи.\n"
                    "Делайте круговые движения плечами: 5 раз вперёд, 5 раз назад.",
            "video": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ"
        },
        3: {
            "text": "3. Поднятие ног к груди\n\n"
                    "Поднимите правую ногу, согнув её в колене, и подтяните к груди руками.\n"
                    "Задержитесь на секунду, затем опустите.\n"
                    "Повторите 3 раза для каждой ноги.",
            "video": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ"
        }
    }

    # Отправляем видео упражнения
    exercise_data = exercises[current_exercise]
    sent_message = await callback.message.answer_video(
        exercise_data["video"],
        caption=exercise_data["text"]
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

        await session.commit()

    # Отправляем результат пользователю
    message = await callback.message.answer(
        "✅ Квест 17 завершен!\n"
        "Все упражнения выполнены. Отличная работа!",
        reply_markup=get_quest_finish_keyboard(3, 3, 17)
    )

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
            "file_id": "AgACAgIAAxkBAAImGWfz4xzgScJdAAGcPSyjQMhfLErttwACYPExG5DcoUu5t7Q2nJC8jgEAAwIAA3kAAzYE",
            "description": "Пример 1: Семейное фото с ребенком"
        },
        {
            "file_id": "AgACAgIAAxkBAAImF2fz4xQAAfkQvZDwrTsEp4HksUCM9wACX_ExG5DcoUtTVN7oo4PozgEAAwIAA3kAAzYE",
            "description": "Пример 2: Ребенок с игрушкой"
        },
        {
            "file_id": "AgACAgIAAxkBAAImD2fz4nfoKsDftnMib1kmgO3XS_gSAAJZ8TEbkNyhS3Vp4OVknUyAAQADAgADeQADNgQ",
            "description": "Пример 3: Групповое фото детей"
        },
        {
            "file_id": "AgACAgIAAxkBAAImFWfz4ws0LZRuuMap6gaKW3k1GjTNAAJe8TEbkNyhSwX5urMKlVD-AQADAgADeQADNgQ",
            "description": "Пример 4: Ребенок в движении"
        },
        {
            "file_id": "AgACAgIAAxkBAAImG2fz4yq_LS4V_tuyNEoEIGMmWCD1AAJh8TEbkNyhSz7tTj8yAeKUAQADAgADeQADNgQ",
            "description": "Пример 5: Эмоциональный портрет"
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

async def request_photo_18(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos_remaining = user_data.get("photos_remaining", 5)

    message = await callback.message.answer(
        f"📷 Квест 18: Практика фото\n\n"
        f"Осталось сделать: {photos_remaining} фото\n"
        "Повторите один из показанных ранее примеров и отправьте фото.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_photo_18")]
        ])
    )

    await state.update_data(
        question_message_id=message.message_id
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
        await finish_quest18(callback.message, state)
    else:
        await callback.message.delete()
        await request_photo_18(callback, state)

    await callback.answer()

async def finish_quest18(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_photos = user_data.get("user_photos", [])

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == message.from_user.id,
                UserResult.quest_id == 18
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=message.from_user.id,
                quest_id=18,
                state="на модерации",
                attempt=1,
                result=len(user_photos)
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            user_result.result = len(user_photos)

        await session.commit()

    # Формируем сообщение для модератора
    user = message.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 18 - Практика фото\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Отправляем фото модератору
    media = MediaGroupBuilder()
    for i, photo in enumerate(user_photos):
        if i == 0:
            media.add_photo(media=photo, caption=caption)
        else:
            media.add_photo(media=photo)

    await message.bot.send_media_group(admin_chat_id, media=media.build())

    # Дополнительная информация для модератора
    await message.bot.send_message(
        admin_chat_id,
        f"Фото от {user.full_name} для квеста 18 готовы к проверке.\n"
        f"Отправлено фото: {len(user_photos)}",
        reply_markup=moderation_keyboard(message.from_user.id, 18)
    )

    # Сообщение пользователю
    await message.answer(
        "✅ Все фото отправлены на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )
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
            "photo": "AgACAgIAAxkBAAImGWfz4xzgScJdAAGcPSyjQMhfLErttwACYPExG5DcoUu5t7Q2nJC8jgEAAwIAA3kAAzYE"
        },
        2: {
            "text": "2. Вставляем новую флешку в картридер",
            "photo": "AgACAgIAAxkBAAImF2fz4xQAAfkQvZDwrTsEp4HksUCM9wACX_ExG5DcoUtTVN7oo4PozgEAAwIAA3kAAzYE"
        },
        3: {
            "text": "3. Мышкой «обводим» место где появилась флешка",
            "photo": "AgACAgIAAxkBAAImD2fz4nfoKsDftnMib1kmgO3XS_gSAAJZ8TEbkNyhS3Vp4OVknUyAAQADAgADeQADNgQ"
        },
        # ... остальные шаги аналогично
        18: {
            "text": "18. Обводим кнопку «Печать» и запускаем импорт",
            "photo": "AgACAgIAAxkBAAImG2fz4yq_LS4V_tuyNEoEIGMmWCD1AAJh8TEbkNyhSz7tTj8yAeKUAQADAgADeQADNgQ"
        }
    }

    # Отправляем текущий шаг
    step_data = steps.get(current_step, {})
    if not step_data:
        # Все шаги показаны, переходим к тесту
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

        await session.commit()

    # Отправляем результат пользователю
    message = await callback.message.answer(
        f"✅ Квест 19 завершен!\n"
        f"Правильных ответов: {correct_answers} из {total_questions}",
        reply_markup=get_quest_finish_keyboard(correct_answers, total_questions, 19)
    )

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
        user_photos=[]
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
    await start_quest20_timer(callback, state)
    await callback.answer()

async def start_quest20_timer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    start_time = user_data.get("start_time", datetime.datetime.now())
    end_time = start_time + datetime.timedelta(minutes=10)
    photos_taken = user_data.get("photos_taken", 0)
    required_photos = user_data.get("required_photos", 10)

    while datetime.datetime.now() < end_time and photos_taken < required_photos:
        # Обновляем таймер каждую минуту
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
        except:
            pass

        await asyncio.sleep(1)  # Обновляем каждую секунду
        user_data = await state.get_data()
        photos_taken = user_data.get("photos_taken", 0)

    # Время вышло или все фото сделаны
    await finish_quest20(callback.message, state)

@router.message(F.photo, QuestState.waiting_for_photo_quest20)
async def handle_photo_quest20(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photos_taken = user_data.get("photos_taken", 0)
    user_photos = user_data.get("user_photos", [])

    # Добавляем фото в список
    user_photos.append(message.photo[-1].file_id)
    photos_taken += 1

    await state.update_data(
        photos_taken=photos_taken,
        user_photos=user_photos
    )

    # Проверяем, все ли фото собраны
    if photos_taken >= user_data.get("required_photos", 10):
        await finish_quest20(message, state)

    await message.delete()

@router.callback_query(F.data == "finish_quest20_early")
async def finish_quest20_early(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos_taken = user_data.get("photos_taken", 0)

    if photos_taken == 0:
        await callback.answer("Нельзя завершить без ни одного фото", show_alert=True)
        return

    await finish_quest20(callback.message, state)
    await callback.answer()

async def finish_quest20(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_photos = user_data.get("user_photos", [])
    photos_taken = len(user_photos)
    required_photos = user_data.get("required_photos", 10)

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == message.from_user.id,
                UserResult.quest_id == 20
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=message.from_user.id,
                quest_id=20,
                state="на модерации",
                attempt=1,
                result=photos_taken
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            user_result.result = photos_taken

        await session.commit()

    # Формируем сообщение для модератора
    user = message.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 20 - Время и Кадры\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"Сделано фото: {photos_taken}/{required_photos}"
    )

    # Отправляем фото модератору
    media = MediaGroupBuilder()
    for i, photo in enumerate(user_photos):
        if i == 0:
            media.add_photo(media=photo, caption=caption)
        else:
            media.add_photo(media=photo)

    await message.bot.send_media_group(admin_chat_id, media=media.build())

    # Дополнительная информация для модератора
    await message.bot.send_message(
        admin_chat_id,
        f"Фото от {user.full_name} для квеста 20 готовы к проверке.",
        reply_markup=moderation_keyboard(message.from_user.id, 20)
    )

    # Сообщение пользователю
    await message.answer(
        f"✅ Квест завершен! Сделано фото: {photos_taken}/{required_photos}\n"
        "Фото отправлены на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()



# Обработчик для всех остальных ответов
@router.callback_query(QuestState.waiting_for_answer)
async def handle_other_answers(callback: types.CallbackQuery):
    # Уведомляем пользователя, что ответ неверный
    await callback.answer("Ответ неверный. Попробуйте ещё раз!")