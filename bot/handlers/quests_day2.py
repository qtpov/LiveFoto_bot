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
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "🔼 Кадр сверху вниз:\nСнимите вертикально, чтобы в кадре был только ребёнок и шарики, будто он в море из шариков"
        },
        {
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "📐 Кадр под углом 45°:\nСнимите сбоку под углом, акцентируя внимание на взаимодействии ребёнка с шарами"
        },
        {
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "👶 Кадр на уровне глаз ребёнка:\nСнимите горизонтально, чтобы передать мир глазами ребёнка"
        },
        {
            "file_id": "AgACAgIAAxkBAAIiQmfq5liYmQZwzE13hjT7jre2xq4LAAI89DEb86JZS5r1n5ZAZwXuAQADAgADeAADNgQ",
            "description": "🌊 Кадр 'моря из шариков':\nСнимите сверху с широким углом, чтобы захватить максимальное количество шаров"
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
        total_zones=4  # Всего 4 зоны для съемки
    )
    await request_shot_14(callback, state)
    await callback.answer()


async def request_shot_14(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_zone = user_data.get("current_zone", 1)
    total_zones = user_data.get("total_zones", 4)
    sample_shots = user_data.get("sample_shots", [])

    # Определяем описание для текущей зоны
    zone_descriptions = {
        1: "🔼 Сделайте кадр сверху вниз",
        2: "📐 Сделайте кадр под углом 45°",
        3: "👶 Сделайте кадр на уровне глаз ребёнка",
        4: "🌊 Сделайте кадр 'моря из шариков'"
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

    if current_zone < user_data.get("total_zones", 4):
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
    total_zones = user_data.get("total_zones", 4)

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


# Квест 14 - Зоны фотографирования
async def quest_15(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('пока все', reply_markup=go_profile_keyboard())



# Обработчик для всех остальных ответов
@router.callback_query(QuestState.waiting_for_answer)
async def handle_other_answers(callback: types.CallbackQuery):
    # Уведомляем пользователя, что ответ неверный
    await callback.answer("Ответ неверный. Попробуйте ещё раз!")