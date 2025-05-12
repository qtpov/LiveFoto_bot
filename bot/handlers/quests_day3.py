from aiogram import Router, types, F
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder
from pathlib import Path
import datetime
import logging
from sqlalchemy.future import select
import asyncio
from typing import Union
from bot.db.models import UserResult
from bot.db.session import SessionLocal
from bot.keyboards.inline import *
from .states import QuestState
from bot.configurate import settings
from bot.db.crud import update_user_level
from .moderation import give_achievement, get_quest_finish_keyboard
from .quests_day2 import finish_quest
from bot.db.models import User


router = Router()
admin_chat_id = settings.ADMIN_ID
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Словари с правильными ответами и сообщениями
correct_answers_qw27 = {1: 2, 2: 1, 3: 2}
feedback_messages_qw27 = {
    1: {
        "correct": "Прекрасный загар и верный ответ",
        "wrong": "Модель получила ожог, ответ не верный"
    },
    2: {
        "correct": "Сертификат о лазерной коррекции, ответ верный",
        "wrong": "Собака поводырь бежит на помощь, ответ неверный"
    },
    3: {
        "correct": "Прям супермен, ответ верный",
        "wrong": "Возможно это не инвалид, ответ неверный"
    }
}

correct_answers_qw32 = {1: 1, 2: 0, 3:1}


def create_options_keyboard(options: list[str], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=str(i+1), callback_data=f"{prefix}_{i}")
    builder.adjust(2)
    return builder.as_markup()

def create_options_keyboard_text(options: list[str], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=opt, callback_data=f"{prefix}_{i}")  # Используем текст опции вместо номера
    builder.adjust(2)  # Располагаем кнопки по 2 в ряду
    return builder.as_markup()


# Общая функция завершения квеста
async def finish_quest3(callback: types.CallbackQuery, state: FSMContext,
                       correct_count: int, total_questions: int, quest_id: int):
    user_data = await state.get_data()

    # Удаляем предыдущие сообщения
    try:
        if "message_ids" in user_data:
            for msg_id in user_data["message_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except Exception as e:
        logging.error(f"Error deleting messages: {e}")

    # Сохраняем результат в БД
    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=quest_id,
            result=correct_count,
            state="выполнен"
        )
        session.add(result)

        # Выдаем ачивку если все ответы верные
        if correct_count == total_questions:
            await give_achievement(callback.from_user.id, quest_id, session)

        await session.commit()

    # Сообщение пользователю
    await callback.message.answer(
        f"Вы ответили правильно на {correct_count} из {total_questions} вопросов!",
        reply_markup=get_quest_finish_keyboard(correct_count, total_questions, quest_id)
    )
    await state.clear()


# Квест 27 - Правильное фото
async def quest_27(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)

    # Удаляем предыдущие сообщения
    try:
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Error deleting message: {e}")

    # Список фото для всех вопросов (должны быть заменены на реальные)
    questions = [
        {
            "text": "Какое фото пересвечено?",
            "media": [
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png",
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png",
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png"
            ]
        },
        {
            "text": "Какое фото имеет расфокусировку?",
            "media": [
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png",
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png",
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png"
            ]
        },
        {
            "text": "На каком фото обрезаны конечности?",
            "media": [
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png",
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png",
                BASE_DIR / "bot/handlers/media/photo/zaglushka.png"
            ]
        }
    ]

    # Создаем медиагруппу
    album_builder = MediaGroupBuilder()
    for i, photo in enumerate(questions[current_question - 1]["media"], 1):
        album_builder.add_photo(media=FSInputFile(photo), caption=f"Вариант {i}")

    # Отправляем медиагруппу и вопрос
    messages = await callback.message.answer_media_group(media=album_builder.build())
    message_ids = [m.message_id for m in messages]

    question_msg = await callback.message.answer(
        questions[current_question - 1]["text"],
        reply_markup=create_options_keyboard(["1", "2", "3"], "quest27")
    )
    message_ids.append(question_msg.message_id)

    # Сохраняем данные
    await state.update_data(
        current_question=current_question,
        message_ids=message_ids,
        correct_answers=user_data.get("correct_answers", 0)
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()


@router.callback_query(F.data.startswith("quest27_"), QuestState.waiting_for_answer)
async def handle_quest27_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data["current_question"]
    selected = int(callback.data.split("_")[1])
    is_correct = selected == correct_answers_qw27[current_question]

    # Обновляем счетчик
    correct_answers = user_data.get("correct_answers", 0) + int(is_correct)

    # Удаляем предыдущие сообщения
    for msg_id in user_data.get("message_ids", []):
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except:
            pass

    # Показываем результат с соответствующим сообщением
    feedback = feedback_messages_qw27[current_question]["correct"] if is_correct else \
    feedback_messages_qw27[current_question]["wrong"]
    await callback.message.answer(feedback)

    # Переход к следующему вопросу или завершение
    if current_question < len(correct_answers_qw27):
        next_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее →", callback_data="next_question_27")]
        ])
        await callback.message.answer("Переходим к следующему вопросу:", reply_markup=next_button)
        await state.update_data(
            correct_answers=correct_answers
        )
    else:
        await finish_quest3(callback, state, correct_answers, len(correct_answers_qw27), 27)

    await callback.answer()


@router.callback_query(F.data == "next_question_27", QuestState.waiting_for_answer)
async def next_question_27(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    await state.update_data(
        current_question=user_data.get("current_question", 1) + 1
    )
    await quest_27(callback, state)


# Квест 28 - Собери все
async def quest_28(callback: types.CallbackQuery, state: FSMContext):
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

    # Отправляем теорию и видео
    await callback.message.answer_video("BAACAgIAAxkBAAImsGf0B-OgQ_mpwLkKY2RnMiOqG1DbAALqbgACoYqhS7f0qJ4Nuj69NgQ")

    message = await callback.message.answer(
        "⚡ Квест 28: Сборка магнитов\n\n"
        "Твоя задача собрать 6 магнитов как можно быстрее,"
        " при нажатии “СТАРТ” будет запущен таймер в боте. "
        "Перед началом попроси коллегу записать тебя на видео так, "
        "чтоб таймер из бота был в кадре видео. "
        "Не забудь отработать движения!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_quest28")]
        ])
    )

    await state.update_data(
        question_message_id=message.message_id,
        timer_started=False,
        timer_active=False,
        quest_completed=False
    )
    await callback.answer()


@router.callback_query(F.data == "start_quest28")
async def start_quest28(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Запускаем таймер с начальным значением 00:00:00
    start_time = datetime.datetime.now()
    timer_msg = await callback.message.answer(
        "⏱️ Таймер запущен! Соберите 6 магнитов как можно быстрее.\n"
        "Прошедшее время: 00:00:00",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ФИНИШ", callback_data="finish_quest28")]
        ])
    )

    await state.update_data(
        start_time=start_time.isoformat(),
        timer_message_id=timer_msg.message_id,
        timer_active=True,
        quest_completed=False
    )

    # Запускаем асинхронную задачу для обновления таймера
    asyncio.create_task(update_quest28_timer(callback.bot, callback.message.chat.id, timer_msg.message_id, state))
    await state.set_state(QuestState.waiting_for_finish_quest28)

    await callback.answer("Таймер запущен!")


async def update_quest28_timer(bot, chat_id: int, message_id: int, state: FSMContext):
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ФИНИШ", callback_data="finish_quest28")]
    ])

    last_time_str = None  # храним последнее отображенное время

    while True:
        user_data = await state.get_data()

        if not user_data.get("timer_active", False) or user_data.get("quest_completed", False):
            break

        start_time = datetime.datetime.fromisoformat(user_data["start_time"])
        duration = (datetime.datetime.now() - start_time).total_seconds()

        total_seconds = int(duration)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Обновляем только если время изменилось
        if time_str != last_time_str:
            message_text = (
                f"⏱️ Таймер запущен! Соберите 6 магнитов как можно быстрее.\n"
                f"Прошедшее время: {time_str}"
            )

            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message_text,
                    reply_markup=reply_markup
                )
                last_time_str = time_str
            except Exception as e:
                print(f"Ошибка при обновлении таймера: {e}")
                if "message is not modified" not in str(e):  # игнорируем эту ошибку
                    break

        await asyncio.sleep(0.1)  # уменьшаем задержку для более точного времени


@router.callback_query(F.data == "finish_quest28", QuestState.waiting_for_finish_quest28)
async def finish_quest28(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    if user_data.get("quest_completed", False):
        await callback.answer()
        return

    await state.update_data(timer_active=False, quest_completed=True)

    try:
        if "timer_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["timer_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщения с таймером: {e}")

    start_time = datetime.datetime.fromisoformat(user_data["start_time"])
    duration = (datetime.datetime.now() - start_time).total_seconds()
    hours, remainder = divmod(int(duration), 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Сохраняем время выполнения в state, чтобы использовать при модерации
    await state.update_data(quest28_time=duration, quest28_time_str=time_str)

    # Запрашиваем видео у пользователя
    await callback.message.answer(
        f"✅ Отлично! Ваше время: {time_str}\n\n"
        "Пожалуйста, отправьте видео с выполнением задания. "
        "Убедитесь, что на видео виден процесс сборки и таймер из бота."
    )

    # Устанавливаем состояние ожидания видео
    await state.set_state(QuestState.waiting_for_quest28_video)
    await callback.answer()


# Обработчик для получения видео
@router.message(F.video, QuestState.waiting_for_quest28_video)
async def process_quest28_video(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    time_str = user_data.get("quest28_time_str", "00:00:00")
    duration = user_data.get("quest28_time", 0)

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == message.from_user.id,
                UserResult.quest_id == 28
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=message.from_user.id,
                quest_id=28,
                state="на модерации",
                attempt=1,
                result=duration
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            user_result.result = duration
            user_result.attempt += 1

        await session.commit()

    # Формируем сообщение для модератора
    username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    caption = (
        f"⚡ Квест 28 - Сборка магнитов\n"
        f"👤 Автор: {message.from_user.full_name} ({username})\n"
        f"⏱ Время выполнения: {time_str}\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Пересылаем видео модератору
    await message.bot.send_video(
        admin_chat_id,
        message.video.file_id,
        caption=caption,
        reply_markup=moderation_keyboard(message.from_user.id, 28)
    )

    # Сообщение пользователю
    await message.answer(
        "🎥 Видео отправлено на модерацию. Вы получите уведомление, когда модератор проверит вашу работу.\n"
    )

    await state.clear()

@router.message(QuestState.waiting_for_quest28_video)
async def wrong_quest28_content(message: types.Message):
    await message.answer("Пожалуйста, отправьте видео с выполнением задания.")

# Квест 29 - Фотоохота
async def quest_29(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="СТАРТ", callback_data="start_photo_hunt_29")],
        [InlineKeyboardButton(text="Рекомендации по работе в фотозоне", callback_data="show_recommendations_29")]
    ])

    msg = await callback.message.answer(
        "Квест 29: Фотоохота\n\n"
        "Твоя задача принести как можно больше фотографий за 15 минут.\n"
        "Обрати внимание, что кадры должны быть интересными и разнообразными.\n"
        "Если ты не успеешь вернуться и выгрузить фотографии за это время, задание будет провалено.\n"
        "Будь уверен в себе и всё получится!",
        reply_markup=keyboard
    )

    await state.update_data(
        timer_start=None,
        photos=[],
        message_id=msg.message_id,
        timer_message_id=None,
        timer_active=False,
        quest_completed=False
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()


@router.callback_query(F.data == "show_recommendations_29", QuestState.waiting_for_answer)
async def show_recommendations_29(callback: types.CallbackQuery, state: FSMContext):
    recommendations = (
        "📌 Рекомендации по работе в фотозоне:\n\n"
        "1. Настройки:\nОбязательно проверь настройки фото-техники перед выходом в фотозону.\n\n"
        "2. Смотри вокруг:\nИщи интересные ракурсы, фоны, составляй красивую композицию в кадре.\n\n"
        "3. Комфорт и доверие:\nУстанови доверительные отношения с детьми и родителями.\n\n"
        "4. Спонтанные моменты:\nНе забывай запечатлевать спонтанные моменты, а не только постановочные.\n\n"
        "5. Взаимодействие:\nОбщайтесь с детьми во время съемки. Игровые задания помогут вызвать искренние улыбки и смех.\n\n"
        "6. Динамика семьи:\nОбращайте внимание на взаимодействие между родителями и детьми.\n\n"
        "7. Разнообразие кадров:\nДелайте разнообразные снимки: крупные планы, общие планы и разные группы.\n\n"
        "8. Терпение:\nБудьте терпеливы и гибки. Дети могут не всегда сотрудничать.\n\n"
        "9. Адаптивность:\nАдаптируйся под текущий трафик."
    )

    await callback.message.edit_text(
        recommendations,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Вернуться к квесту", callback_data="back_to_quest_29")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_quest_29", QuestState.waiting_for_answer)
async def back_to_quest_29(callback: types.CallbackQuery, state: FSMContext):
    await quest_29(callback, state)


@router.callback_query(F.data == "start_photo_hunt_29", QuestState.waiting_for_answer)
async def start_photo_hunt_29(callback: types.CallbackQuery, state: FSMContext):
    # Отправляем сообщение с таймером
    timer_msg = await callback.message.answer(
        "⏱ Осталось времени: 15:00",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТОП", callback_data="stop_photo_hunt_29")]
        ])
    )

    start_time = datetime.datetime.now()
    await state.update_data(
        timer_start=start_time.isoformat(),
        timer_message_id=timer_msg.message_id,
        timer_active=True,
        photos=[],
        photos_submitted=False,
        quest_completed=False
    )

    # Запускаем асинхронную задачу для обновления таймера
    asyncio.create_task(update_quest29_timer(callback.bot, callback.message.chat.id, timer_msg.message_id, state))
    await callback.answer("Таймер запущен! У вас 15 минут.")


async def update_quest29_timer(bot, chat_id: int, message_id: int, state: FSMContext):
    last_time_str = None

    while True:
        user_data = await state.get_data()

        if not user_data.get("timer_active", False) or user_data.get("quest_completed", False):
            break

        start_time = datetime.datetime.fromisoformat(user_data["timer_start"])
        remaining = (15 * 60) - (datetime.datetime.now() - start_time).total_seconds()

        if remaining <= 0:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="⏱ Время вышло!",
                reply_markup=None
            )
            await bot.send_message(
                chat_id=chat_id,
                text="⏰ Не успел! Попробуй еще раз!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
                ])
            )
            await state.update_data(timer_active=False)
            break

        mins, secs = divmod(int(remaining), 60)
        time_str = f"{mins:02d}:{secs:02d}"

        if time_str != last_time_str:
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"⏱ Осталось времени: {time_str}",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="СТОП", callback_data="stop_photo_hunt_29")]
                    ])
                )
                last_time_str = time_str
            except Exception as e:
                if "message is not modified" not in str(e):
                    print(f"Ошибка при обновлении таймера: {e}")
                    break

        await asyncio.sleep(0.5)


@router.message(F.photo, QuestState.waiting_for_answer)
async def handle_quest29_photo(message: types.Message, state: FSMContext):

    user_data = await state.get_data()

    # Проверяем, что это квест 29 (идет фотоохота)
    if not user_data.get("timer_active", False):
        await message.answer("Сначала начните квест, нажав кнопку 'СТАРТ'.")
        return

    # Сохраняем фото (берем самое высокое качество)
    photos = user_data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.delete()



@router.callback_query(F.data == "stop_photo_hunt_29", QuestState.waiting_for_answer)
async def stop_photo_hunt_29(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    # Останавливаем таймер
    await state.update_data(timer_active=False)

    try:
        # Удаляем сообщение с таймером
        if "timer_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["timer_message_id"])
    except:
        pass

    # Проверяем время выполнения
    start_time = datetime.datetime.fromisoformat(user_data["timer_start"])
    duration = (datetime.datetime.now() - start_time).total_seconds()

    if duration > 15 * 60:  # 15 минут
        await callback.message.answer(
            "⏰ Время вышло! Попробуйте еще раз.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
            ])
        )
        return

    photos = user_data.get("photos", [])

    if photos:
        # Если есть фото, предлагаем отправить их на модерацию
        await callback.message.answer(
            f"📸 Вы собрали {len(photos)} фото! Отправьте их на проверку.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Отправить на модерацию", callback_data="submit_photos_29")]
            ])
        )
    else:
        # Если фото нет, спрашиваем причину
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нет людей", callback_data="no_people_29")],
            [InlineKeyboardButton(text="Все отказались", callback_data="all_refused_29")],
            [InlineKeyboardButton(text="Свой вариант", callback_data="custom_reason_29")]
        ])

        await callback.message.answer(
            "Почему вы не сделали фото?",
            reply_markup=keyboard
        )

    await callback.answer()


@router.callback_query(F.data == "submit_photos_29")
async def submit_photos_29(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos = user_data.get("photos", [])

    if not photos:
        await callback.message.answer(
            "Вы не отправили ни одной фотографии. Хотите попробовать еще раз?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
            ])
        )
        return

    # Просто запрашиваем фидбек, не сохраняя фото в БД
    await callback.message.answer(
        "Фотографии готовы к отправке. Какие были трудности?"
    )
    # ,
    # reply_markup = InlineKeyboardMarkup(inline_keyboard=[
    #     [InlineKeyboardButton(text="Пропустить", callback_data="skip_feedback_29")]
    # ])
    await state.set_state(QuestState.waiting_feedback_text)
    await callback.answer()

@router.message(QuestState.waiting_feedback_text)
async def handle_feedback_text(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photos = user_data.get("photos", [])
    feedback_text = message.text

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == message.from_user.id,
                UserResult.quest_id == 29
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=message.from_user.id,
                quest_id=29,
                state="на модерации",
                attempt=1,
                result=len(photos)
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            user_result.result = len(photos)
            user_result.attempt += 1

        await session.commit()

    # Отправляем фото и фидбек модератору
    username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"

    caption = (
        f"📸 Квест 29 - Фотоохота\n"
        f"👤 Автор: {message.from_user.full_name} ({username})\n"
        f"📷 Количество фото: {len(photos)}\n"
        f"💬 Фидбек: {feedback_text}\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Если есть фото - отправляем их с подписью
    if photos:
        try:
            # Остальные фото  отправляем группой
            if len(photos) > 1:
                album = MediaGroupBuilder()
                for photo in photos:
                    album.add_photo(media=photo)
                await message.bot.send_media_group(admin_chat_id, media=album.build())
        except Exception as e:
            logging.error(f"Ошибка отправки фото: {e}")
    else:
        # Если фото нет - просто отправляем текст
        await message.bot.send_message(admin_chat_id, caption)

    # Добавляем кнопки модерации
    await message.bot.send_message(
        admin_chat_id,
        caption,
        reply_markup=moderation_keyboard(message.from_user.id, 29)
    )

    await message.answer(
        "✅ Спасибо! Ваши фото и комментарии отправлены на проверку."
    )
    await state.clear()


@router.callback_query(F.data == "skip_feedback_29", QuestState.waiting_feedback_text)
async def skip_feedback_29(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos = user_data.get("photos", [])

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.message.from_user.id,
                UserResult.quest_id == 29
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=message.from_user.id,
                quest_id=29,
                state="на модерации",
                attempt=1,
                result=len(photos)
            )
            session.add(user_result)
        else:
            user_result.state = "на модерации"
            user_result.result = len(photos)
            user_result.attempt += 1

        await session.commit()

    # Отправляем данные модератору без фидбека
    username = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"

    caption = (
        f"📸 Квест 29 - Фотоохота\n"
        f"👤 Автор: {callback.from_user.full_name} ({username})\n"
        f"📷 Количество фото: {len(photos)}\n"
        f"💬 Фидбек: не предоставлен\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    if photos:
        try:


            if len(photos) > 1:
                album = MediaGroupBuilder()
                for photo in photos:
                    album.add_photo(media=photo)
                await callback.bot.send_media_group(admin_chat_id, media=album.build())
        except Exception as e:
            logging.error(f"Ошибка отправки фото: {e}")
    else:
        await callback.bot.send_message(admin_chat_id, caption)

    await callback.bot.send_message(
        admin_chat_id,
        caption,
        reply_markup=moderation_keyboard(callback.from_user.id, 29)
    )

    await callback.message.answer(
        "✅ Ваши фото отправлены на проверку!"
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "no_people_29")
async def no_people_29(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Не переживай, они обязательно придут! Как только будешь готов нажимай 'Заново' и отправляйся в фотозону!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "all_refused_29")
async def all_refused_29(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Не стоит расстраиваться! Почитай рекомендации по работе в фотозоне, они обязательно помогут!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Рекомендации", callback_data="show_recommendations_29")],
            [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "custom_reason_29")
async def custom_reason_29(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Напиши, почему ты не принес фотографии:",
        reply_markup=None
    )
    await state.set_state(QuestState.waiting_custom_reason)
    await callback.answer()


@router.message(QuestState.waiting_custom_reason)
async def handle_custom_reason(message: types.Message, state: FSMContext):
    await state.update_data(custom_reason=message.text)
    await message.answer(
        "Не стоит расстраиваться! Почитай рекомендации по работе в фотозоне, они обязательно помогут!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Рекомендации", callback_data="show_recommendations_29")],
            [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
        ])
    )
    await state.set_state(QuestState.waiting_for_answer)


@router.callback_query(F.data == "restart_quest_29")
async def restart_quest_29(callback: types.CallbackQuery, state: FSMContext):
    await quest_29(callback, state)

# Квест 30 - Полный цикл
async def quest_30(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    try:
        await callback.message.delete()
    except:
        pass
    async with SessionLocal() as session:
        # Получаем пользователя по telegram_id
        user = await session.execute(select(User).filter(User.telegram_id == user_id))
        user = user.scalars().first()

        if not user:
            await message_or_callback.answer("Ты ещё не зарегистрирован! Напиши /start.")
            return
        steps = [
            {
                "text": "Привет! На связи ***! Я расскажу тебе, как ловко забирать деньги из карманов наших клиентов и при этом не угодить за решетку!",
                "button": "Круто!"
            },
            {
                "text": "Для начала давай определимся, что ты должен выглядеть опрятно, ведь встречают по одежке!",
                "button": "Я красавчик" if user.gender == "Мужской" else "Я красавица"
            },
            {
                "text": "А еще ты должен быть уверен в себе! Представь, что ты не просто фотограф, а скажем...\n"
                        "Владелец этого парка! Да что там парка... Целого торгового центра! Да у тебя сеть этих торговых центов!\n"
                        "Да что там сеть, ты ВЛАДЕЛЕЦ МИРА!!!! Разве владелец мира будет переживать и бояться подойти к родителям и их детям? Конечно, нет!",
                "button": "Это всё про меня!"
            },
            {
                "text": "Поэтому просто поверь в себя и людям сложно будет тебе отказать! Уверенность это 50% успеха и чем больше ты практикуешься, тем больше начинаешь верить в себя!\n"
                        "Вот ты уже опрятный и уверенный! Отправляйся в фотозону, ослепля всех своей улыбкой. и не забудь вспышку и фотоаппарат!",
                "button": "Но что же дальше?"
            },
            {
                "text": "А дальше ты должен понять, что продажа начинается задолго до того, как готова продукция.\n"
                        "Она начинается с работы в фотозоне. То, как ты подходишь к детям и их родителям, то, как ты улыбаешься, взаимодействуешь, играешься с ребенком... "
                        "Все это уже продажа. Продажа тебя как специалиста, продажа твоих неимоверно крутых услуг!",
                "button": "Я проф фотограф"
            },
            {
                "text": "Не забывай улыбаться, но делай это искренне! Получай кайф от процесса!\n"
                        "Не стесняйся, подходи к родителям и заводи диалог.\n"
                        "Скажи: 'Здравствуйте, как зовут малыша/принцессу/супермена?'\n"
                        "При этом смотри в глаза родителю и не забывай улыбаться!",
                "button": "я знаю имя ребёнка"
            },
            {
                "text": "Когда ты узнал имя ребенка приступай к фотосессии. Не забывай, что для ребенка она должна быть игрой, иначе ему может наскучить.\n"
                        "Поэтому вы можете побегать, поиграть с предметами, которые есть в фотозоне, покривляться и посмеяться вместе с ребенком!",
                "button": "кадры в игре готовы"
            },
            {
                "text": "Помни, что даже если мама и папа ребенка не видит твоих стараний, то их замечают родители других детей. И когда ты подойдешь к ним, они будут более настроены на фотосессию.\n"
                        "Уточняйте у детей или родителей есть ли в парке брат/сестра ребенка, которого вы собираетесь фотографировать. Если есть, обязательно собери всех вместе.\n"
                        "Совместные кадры пользуются большим спросом, а это значит, что тебе стоит собирать в кадре всю семью, включая родителей!",
                "button": "Семейные кадры готовы"
            },
            {
                "text": "После того, как ты пофотографировал гостей, не забудь сказать, где и ЧЕРЕЗ СКОЛЬКО они могут посмотреть свои фотографии.\n"
                        "Отправляйся на базу и напечатай фотографии.\n"
                        "Прямые продажи более эффективны, поэтому не стоит ими пренебрегать! Взял фотки и вперед!",
                "button": "фото готовы к продажи"
            },
            {
                "text": "Помни про УВЕРЕННОСТЬ! Не стесняйся презентовать фотографии и подмечай яркие моменты на фотографиях. Похвали крутую улыбку или интересную позу.\n"
                        "Цену озвучивай от большего к меньшему и тогда, когда тебя о ней спросили. До того, как принес фотографии, от вопроса цены уходи. Сначала сделал и принес фотографии, и только потом цены.",
                "button": "Как же это сделать?"
            },
            {
                "text": "Ответь: 'У нас много разной продукции, разных размеров. Я сделаю варианты, все расскажу и покажу!' Обычно после этого повторного вопроса не поступает.\n"
                        "Вернемся к продаже. Как только провели презентацию и гость выбрал фотографии, старайся продать еще!\n"
                        "Сделай выгодное предложение используя акции, еще раз подметь интересные кадры и убеди человека, что кадры крутые и надо взять еще!",
                "button": "я гуру продаж"
            },
            {
                "text": "После этого спроси о способе оплаты, например: 'Хорошо, у вас карта или наличные?'\n"
                        "Если ты не задашь этот вопрос, деньги можешь не получить!\n"
                        "Нельзя откладывать продукцию, чтобы человек оплатил ее при выходе. За это время он может запросто передумать! Поэтому всегда старайся получить деньги сразу.\n"
                        "Да, ты можешь отложить продукцию, которую выбрал клиент, но оплатить надо заранее.\n"
                        "Скажи так: 'Хорошо, я отложу, и вы заберете на выходе. Но оплатить надо сразу, чтобы фотографии не разобрали. Сейчас я принесу вам терминал.'",
                "button": "Вуаля!"
            },
            {
                "text": "Ты сделал продажу! Повторяй все эти действия до тех пор, пока не заработаешь себе на безбедную старость!\n"
                        "Загрузи в бот фотографии которые ты продал. можешь выгрузить их из лайтрум, коллеги подскажут как это сделать.",
                "button": "Завершить"
            }
        ]

    msg = await callback.message.answer(
        steps[0]["text"],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=steps[0]["button"], callback_data="next_step_30")]
        ])
    )

    await state.update_data(
        current_step=0,
        message_id=msg.message_id,
        steps=steps,
        sold_photos=[]  # Для хранения фото проданных работ
    )
    await state.set_state(QuestState.waiting_full_cycle_step)
    await callback.answer()


@router.callback_query(F.data == "next_step_30", QuestState.waiting_full_cycle_step)
async def next_step_30(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_step = user_data["current_step"] + 1
    steps = user_data["steps"]

    if current_step >= len(steps):
        await callback.message.delete()
        # Создаем новое сообщение с запросом фото
        msg = await callback.message.answer(
            'Пожалуйста, отправьте фотографии проданных работ (необходимо отправить хотя бы одно фото):',
            reply_markup=None
        )
        await state.update_data(photo_request_msg_id=msg.message_id)
        await state.set_state(QuestState.waiting_sold_photos)
    else:
        await callback.message.edit_text(
            steps[current_step]["text"],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=steps[current_step]["button"],
                                      callback_data="next_step_30")]
            ])
        )
        await state.update_data(current_step=current_step)
    await callback.answer()


@router.message(F.photo, QuestState.waiting_sold_photos)
async def handle_sold_photos(message: types.Message, state: FSMContext, bot):
    user_data = await state.get_data()
    sold_photos = user_data.get("sold_photos", [])
    msg_id = user_data.get("photo_request_msg_id")

    # Сохраняем самое качественное фото (последнее в списке)
    sold_photos.append(message.photo[-1].file_id)

    await state.update_data(sold_photos=sold_photos)
    await message.delete()

    # Редактируем существующее сообщение вместо создания нового
    if msg_id:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg_id,
                text=f'Получено {len(sold_photos)} фото. Отправьте еще или нажмите "Далее" для продолжения.',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Далее", callback_data="finish_photos_upload")]
                ])
            )
        except:
            # Если не удалось отредактировать (например, сообщение слишком старое)
            msg = await message.answer(
                f'Получено {len(sold_photos)} фото. Отправьте еще или нажмите "Далее" для продолжения.',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Далее", callback_data="finish_photos_upload")]
                ])
            )
            await state.update_data(photo_request_msg_id=msg.message_id)

@router.callback_query(F.data == "finish_photos_upload", QuestState.waiting_sold_photos)
async def finish_photos_upload(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    sold_photos = user_data.get("sold_photos", [])

    if not sold_photos:
        await callback.answer("Необходимо отправить хотя бы одно фото!", show_alert=True)
        return

    # Удаляем сообщение с запросом фото
    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "Теперь укажи, на какую сумму ты осуществил продажу:",
        reply_markup=None
    )
    await state.set_state(QuestState.waiting_sales_amount)
    await callback.answer()


@router.message(QuestState.waiting_sales_amount)
async def handle_sales_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        user_data = await state.get_data()
        sold_photos = user_data.get("sold_photos", [])

        # Сохраняем в БД
        async with SessionLocal() as session:
            result = UserResult(
                user_id=message.from_user.id,
                quest_id=30,
                result=amount,
                state="выполнен"
            )
            session.add(result)
            await session.commit()

        # Отправляем модератору
        username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
        caption = (
            f"💰 Квест 30 - Продажи\n"
            f"👤 Автор: {message.from_user.full_name} ({username})\n"
            f"💵 Сумма продажи: {amount} руб.\n"
            f"📷 Фото: {len(sold_photos)} шт.\n"
            f"🕒 Время: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        if sold_photos:
            try:
                if len(sold_photos) > 1:
                    # Для нескольких фото - отправляем альбом с подписью
                    album = MediaGroupBuilder(caption=caption)
                    for photo in sold_photos:
                        album.add_photo(media=photo)
                    await message.bot.send_media_group(admin_chat_id, media=album.build())
                else:
                    # Для одного фото - отправляем с подписью
                    await message.bot.send_photo(
                        admin_chat_id,
                        photo=sold_photos[0],
                        caption=caption
                    )
            except Exception as e:
                logging.error(f"Ошибка отправки фото: {e}")
                # Если не удалось отправить фото, отправляем хотя бы текст
                await message.bot.send_message(admin_chat_id, caption)
        else:
            await message.bot.send_message(admin_chat_id, caption)

        await message.answer(
            f"✅ Отлично! Ты продал на сумму {amount} рублей!\n\n"
            "Чем больше делаешь - тем больше опыта. Чем больше опыта - тем лучше будет получаться.\n"
            "Чем лучше получается - тем больше денег заработаешь!\n\n"
            "Учись, пробуй, кайфуй и достигай! Я в тебя верю!",
            reply_markup=get_quest_finish_keyboard(1, 1, 30)
        )
        await state.clear()

    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректную сумму (например: 1500 или 2500.50)")


# Квест 31 - Ценность кадра (полная версия)
async def quest_31(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    # Отправляем видео лекции
    video = 'BAACAgIAAxkBAAI8AAFoBT0VOrqDcfK7aqqN0F0Qk1U1iwACWHMAAhrqKUhJ5wHKxUey8DYE'
    video_msg = await callback.message.answer_video(video)

    # Кнопка "Далее" после видео
    msg = await callback.message.answer(
        "Лекция о ценности кадра завершена",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее", callback_data="start_quiz_31")]
        ])
    )

    await state.update_data(
        video_message_id=video_msg.message_id,
        message_id=msg.message_id,
        current_question=1,
        correct_answers=0
    )
    await callback.answer()


@router.callback_query(F.data == "start_quiz_31")
async def start_quiz_31(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
        if "video_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["video_message_id"])
    except:
        pass

    # Начинаем тест
    await callback.message.answer(
        "Предлагаю пройти небольшой тест по просмотренной лекции, за что будешь щедро вознагражден баллами.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать тест", callback_data="next_question_31")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "next_question_31")
async def next_question_31(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)

    questions = [
        {
            "text": "1. Что такое 'ценность кадра' в фотографии?\n\n"
                    "A) Количество пикселей\n"
                    "B) Эмоции и смысл\n"
                    "C) Цена камеры\n"
                    "D) Тип объектива",
            "options": ["A", "B", "C", "D"],
            "correct": 1  # B
        },
        {
            "text": "2. Какое правило помогает выстроить композицию?\n\n"
                    "A) Золотое сечение\n"
                    "B) Центральное размещение\n"
                    "C) Правило третей\n"
                    "D) Параллельные линии",
            "options": ["A", "B", "C", "D"],
            "correct": 2  # C
        },
        {
            "text": "3. Что может сильно изменить атмосферу кадра?\n\n"
                    "A) Одежда модели\n"
                    "B) Погода\n"
                    "C) Свет\n"
                    "D) Цвет волос",
            "options": ["A", "B", "C", "D"],
            "correct": 2  # C
        },
        {
            "text": "4. Какие кадры считаются более живыми?\n\n"
                    "A) Без людей\n"
                    "B) Только пейзажи\n"
                    "C) С эмоциями\n"
                    "D) С предметами",
            "options": ["A", "B", "C", "D"],
            "correct": 2  # C
        },
        {
            "text": "5. Что важно при постобработке?\n\n"
                    "A) Яркие фильтры\n"
                    "B) Добавить текст\n"
                    "C) Сохранять естественность\n"
                    "D) Усилить резкость",
            "options": ["A", "B", "C", "D"],
            "correct": 2  # C
        }
    ]

    if current_question <= len(questions):
        msg = await callback.message.edit_text(
            questions[current_question - 1]["text"],
            reply_markup=create_quiz_keyboard(questions[current_question - 1]["options"], "quest31")
        )
        await state.update_data(
            current_question=current_question,
            message_id=msg.message_id,
            questions=questions
        )
    await callback.answer()


@router.callback_query(F.data.startswith("quest31_"), QuestState.waiting_for_answer)
async def handle_quest31_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data["current_question"]
    questions = user_data["questions"]
    selected = int(callback.data.split("_")[1])

    is_correct = selected == questions[current_question - 1]["correct"]
    correct_answers = user_data.get("correct_answers", 0) + int(is_correct)

    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
    except:
        pass

    res = "✅ Верно!" if is_correct else "❌ Неверно!"
    if current_question < len(questions):
        await state.update_data(
            current_question=current_question + 1,
            correct_answers=correct_answers
        )
        await callback.message.answer(
            f"{res}\nПереходим к следующему вопросу:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее", callback_data="next_question_31")]
            ])
        )
    else:
        # Все вопросы пройдены
        total_questions = len(questions)
        is_completed = correct_answers == total_questions

        async with SessionLocal() as session:
            # Проверяем существующую запись
            user_result = await session.execute(
                select(UserResult)
                .filter(
                    UserResult.user_id == callback.from_user.id,
                    UserResult.quest_id == 31
                )
            )
            user_result = user_result.scalars().first()

            if not user_result:
                # Создаем новую запись
                user_result = UserResult(
                    user_id=callback.from_user.id,
                    quest_id=31,
                    result=correct_answers,
                    state="выполнен" if is_completed else "не выполнен",
                    attempt=1 if not is_completed else 0  # Первая попытка только если не выполнен
                )
                session.add(user_result)
            else:
                # Обновляем существующую запись
                user_result.result = correct_answers
                user_result.state = "выполнен" if is_completed else "не выполнен"
                if not is_completed:
                    user_result.attempt += 1  # Увеличиваем только при неудаче
            if is_completed:
                await give_achievement(callback.from_user.id, 31, session)

            await session.commit()

        if is_completed:
            await callback.message.answer(
                "Ты отлично разбираешься в ценности кадра!",
                reply_markup=get_quest_finish_keyboard(correct_answers, total_questions, 31)
            )
        else:
            await callback.message.answer(
                f"Тебе стоит поработать над пониманием ценности кадра ({correct_answers}/{total_questions} верных ответов)",
                reply_markup=get_quest_finish_keyboard(correct_answers, total_questions, 31)
            )

    await callback.answer()

@router.callback_query(F.data == "restart_quest_31")
async def restart_quest_31(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        current_question=1,
        correct_answers=0
    )
    await next_question_31(callback, state)


@router.callback_query(F.data == "finish_quest_31")
async def finish_quest_31(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Квест завершен!",
        reply_markup=get_quest_finish_keyboard(1, 1, 31)
    )
    await state.clear()
    await callback.answer()


def create_quiz_keyboard(options: list[str], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=opt.split(")")[0], callback_data=f"{prefix}_{i}")
    builder.adjust(2)
    return builder.as_markup()


# Квест 32 - Ценности компании
async def quest_32(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    msg = await callback.message.answer(
        "Квест 32: Ценности компании\nИзучите ценности и пройдите тест",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать игру", callback_data="start_game_32")]]
        ))

    await state.update_data(
        current_scenario=0,
        message_id=msg.message_id,
        first_attempt_errors=0  # Для отслеживания ошибок при первом прохождении
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()

@router.callback_query(F.data == "start_game_32", QuestState.waiting_for_answer)
async def start_game_32(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    scenarios = [
        {
            "text": (
                "Ситуация 1: коллега показывает в сторону семьи, которая стоит в очереди на аттракцион, он кладет "
                "руку в карман, достает купюру 5000 руб. и предлагает разделить найденные деньги, которые выпали у семьи.\n\n"
                "Варианты ответов:\n"
                "1. Напомнить коллеге о ценностях компании\n"
                "2. Проконтролировать, чтоб коллега вернул деньги\n"
                "3. Разделить деньги с командой"
            ),
            "options": ["1", "2", "3"],  # Только номера вариантов
            "correct": 1,  # Индекс правильного ответа (начиная с 0)
            "feedback": [
                "Это похвально, коллега вспомнил о ценностях, но так и не вернул деньги.",
                "Отлично, у нас лояльный клиент и крутые коллеги!",
                "Можно заказать пиццу на команду, но что если коллеги найдут твои деньги?"
            ]
        },
        {
            "text": (
                "Ситуация 2: ты сидишь и выполняешь работу, подходит коллега и просит помочь выполнить задачу, которую поручили ему.\n\n"
                "Варианты ответов:\n"
                "1. Согласиться\n"
                "2. Отказаться"
            ),
            "options": ["1", "2"],
            "correct": 0,
            "feedback": [
                "Ты хороший командный игрок!",
                "Ты не обязан, но нужна ли тебе будет помощь в будущем?"
            ]
        },
        {
            "text": (
                "Ситуация 3: Два сотрудника ведут диалог:\n"
                "Первый: «Какие у тебя планы на ближайшие 3 месяца?»\n"
                "Второй: «Хочу накопить 100 000р и смогу чилить целый месяц дома, а потом снова куда-нибудь устроюсь. А у тебя?»\n"
                "Первый: «Я слышал про внутреннее обучение в компании и возможность карьерного роста, очень хочу попробовать. Для меня важнее закрепиться на одном месте и развиваться в интересном для меня направлении»\n\n"
                "Варианты ответов:\n"
                "1. Чилить\n"
                "2. Расти и развиваться"
            ),
            "options": ["1", "2"],
            "correct": 1,
            "feedback": [
                "Хорошего отдыха!",
                "Фотограф, администратор, управляющий - так и до президента недалеко!"
            ]
        }
    ]

    msg = await callback.message.answer(
        scenarios[0]["text"],
        reply_markup=create_numbered_options_keyboard(scenarios[0]["options"], "quest32")
    )

    await state.update_data(
        scenarios=scenarios,
        current_scenario=0,
        message_id=msg.message_id,
        correct_answers=0,
        is_first_attempt=True
    )

def create_numbered_options_keyboard(options, prefix):
    """Создает клавиатуру с кнопками-номерами вариантов"""
    keyboard = []
    row = []
    for i, option in enumerate(options):
        row.append(InlineKeyboardButton(text=option, callback_data=f"{prefix}_{i}"))
        if len(row) == 2:  # По 2 кнопки в ряду
            keyboard.append(row)
            row = []
    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data.startswith("quest32_"), QuestState.waiting_for_answer)
async def handle_quest32_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_scenario = user_data["current_scenario"]
    scenarios = user_data["scenarios"]
    selected = int(callback.data.split("_")[1])

    is_correct = selected == scenarios[current_scenario]["correct"]
    correct_answers = user_data.get("correct_answers", 0) + int(is_correct)

    # Сохраняем количество ошибок только в state
    if user_data.get("is_first_attempt", True) and not is_correct:
        first_attempt_errors = user_data.get("first_attempt_errors", 0) + 1
        await state.update_data(first_attempt_errors=first_attempt_errors)

    # Удаляем предыдущие сообщения
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
    except:
        pass

    # Отправляем feedback и сразу удаляем предыдущее сообщение с вопросом
    feedback_msg = await callback.message.answer(scenarios[current_scenario]["feedback"][selected])

    if current_scenario + 1 < len(scenarios):
        # Обновляем данные и переходим к следующему сценарию
        await state.update_data(
            correct_answers=correct_answers,
            feedback_message_id=feedback_msg.message_id
        )

        # Кнопка "Далее" с удалением предыдущего feedback
        next_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее →", callback_data="next_scenario_32")]
        ])
        next_msg = await callback.message.answer("Переходим к следующей ситуации:", reply_markup=next_button)

        await state.update_data(next_message_id=next_msg.message_id)
    else:
        # Все сценарии пройдены
        total_scenarios = len(scenarios)
        is_completed = correct_answers == total_scenarios

        async with SessionLocal() as session:
            # Сохраняем результат в БД
            user_result = await session.execute(
                select(UserResult)
                .filter(
                    UserResult.user_id == callback.from_user.id,
                    UserResult.quest_id == 32
                )
            )
            user_result = user_result.scalars().first()

            if not user_result:
                user_result = UserResult(
                    user_id=callback.from_user.id,
                    quest_id=32,
                    result=correct_answers,
                    state="выполнен" if is_completed else "не выполнен",
                    attempt=1
                )
                session.add(user_result)
            else:
                user_result.result = correct_answers
                user_result.state = "выполнен" if is_completed else "не выполнен"
                user_result.attempt += 1

            # Выдаем ачивку если все ответы верные
            if is_completed:
                await give_achievement(callback.from_user.id, 32, session)

            await session.commit()

        # Удаляем предыдущий feedback если есть
        if "feedback_message_id" in user_data:
            try:
                await callback.bot.delete_message(callback.message.chat.id, user_data["feedback_message_id"])
            except:
                pass

        if is_completed:
            completion_msg = await callback.message.answer(
                "Мы рады, что ты придерживаешься наших ценностей!",
                reply_markup=get_quest_finish_keyboard(correct_answers, total_scenarios, 32)
            )
        else:
            completion_msg = await callback.message.answer(
                "Ценностями компании LiveFoto являются: честность, ответственность, работа в команде и саморазвитие. Попробуй ещё раз!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Начать заново", callback_data="restart_quest_32")]
                ])
            )

        await state.update_data(
            is_first_attempt=False,
            completion_message_id=completion_msg.message_id
        )

    await callback.answer()


@router.callback_query(F.data == "next_scenario_32", QuestState.waiting_for_answer)
async def next_scenario_32(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    # Удаляем предыдущие сообщения
    try:
        if "feedback_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["feedback_message_id"])
        if "next_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["next_message_id"])
    except:
        pass

    current_scenario = user_data["current_scenario"] + 1
    scenarios = user_data["scenarios"]

    msg = await callback.message.answer(
        scenarios[current_scenario]["text"],
        reply_markup=create_options_keyboard_text(scenarios[current_scenario]["options"], "quest32")
    )

    await state.update_data(
        current_scenario=current_scenario,
        message_id=msg.message_id,
        feedback_message_id=None,
        next_message_id=None
    )
    await callback.answer()


@router.callback_query(F.data == "restart_quest_32")
async def restart_quest_32(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "completion_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["completion_message_id"])
    except:
        pass

    await state.update_data(
        current_scenario=0,
        correct_answers=0
    )
    await start_game_32(callback, state)


# Квест 33 - Продажи фотографий (полный цикл)
async def quest_33(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    msg = await callback.message.answer(
        "Квест 33: Продажи фотографий\n\n"
        "Необходимо сделать 3 полных процесса от фотографирования клиента до продажи фото.\n\n"
        "Процесс:\n"
        "1. Сфотографируйте клиента\n"
        "2. Предложите фото на продажу\n"
        "3. Загрузите чек при успешной продаже\n\n"
        "После 3 успешных продаж задание будет завершено.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_sales_quest_33")]
        ]))

    await state.update_data(
        successful_sales=0,
        current_step=0,
        photos=[],
        checks=[],
        comments=[],
        message_id=msg.message_id
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()


@router.callback_query(F.data == "start_sales_quest_33", QuestState.waiting_for_answer)
async def start_sales_quest_33(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Есть продажа", callback_data="sale_success_33"))
    builder.row(InlineKeyboardButton(text="Не получилось", callback_data="sale_failed_33"))
    builder.row(InlineKeyboardButton(text="ЗАВЕРШИТЬ", callback_data="finish_sales_quest_33"))

    await callback.message.edit_text(
        "Начните процесс продажи:\n"
        "1. Сфотографируйте клиента\n"
        "2. Предложите фото на продажу\n\n"
        "Как прошла попытка продажи?",
        reply_markup=builder.as_markup()
    )

    await state.update_data(start_time=datetime.datetime.now())
    await callback.answer()


@router.callback_query(F.data == "sale_success_33", QuestState.waiting_for_answer)
async def handle_success_33(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Ты молодец! Поздравляю с продажей!\n\n"
        "1. Загрузи фотографию чека\n"
        "2. Опиши, какую продукцию продал\n\n"
        "Фото чека можно отправить прямо в этот чат.",
        reply_markup=None
    )
    await state.set_state(QuestState.waiting_photo_33)
    await callback.answer()


@router.message(F.photo, QuestState.waiting_photo_33)
async def handle_check_photo_33(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    checks = data.get("checks", [])
    checks.append(photo_id)

    await state.update_data(checks=checks)
    await message.answer(
        "Отлично! Теперь опиши, какую продукцию ты продал (например: 'Фото 10×15 в рамке')."
    )
    await state.set_state(QuestState.waiting_product_desc_33)


@router.message(QuestState.waiting_product_desc_33)
async def handle_product_desc_33(message: types.Message, state: FSMContext):
    comment = message.text
    data = await state.get_data()
    comments = data.get("comments", [])
    comments.append(comment)
    successful_sales = data.get("successful_sales", 0) + 1

    await state.update_data(comments=comments, successful_sales=successful_sales)

    if successful_sales >= 3:
        await finish_sales_quest_33(message, state)
    else:
        builder = InlineKeyboardBuilder()
        next_sale_text = f"Есть {'вторая' if successful_sales == 1 else 'третья'} продажа"
        builder.row(InlineKeyboardButton(text=next_sale_text, callback_data="sale_success_33"))
        builder.row(InlineKeyboardButton(text="Не получилось", callback_data="sale_failed_33"))

        await message.answer(
            f"Отлично! Теперь нужно совершить {'вторую' if successful_sales == 1 else 'третью'} продажу.",
            reply_markup=builder.as_markup()
        )
        await state.set_state(QuestState.waiting_for_answer)


@router.callback_query(F.data == "sale_failed_33", QuestState.waiting_for_answer)
async def handle_failure_33(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    # Добавляем варианты отказов из Excel
    builder.row(InlineKeyboardButton(text="1) У меня был отказ в фото-зоне", callback_data="refusal_photo_zone_33"))
    builder.row(InlineKeyboardButton(text="2) У меня был отказ на стенде", callback_data="refusal_stand_33"))

    await callback.message.edit_text(
        "Давай попробуем решить, почему у тебя не получилось продать. Выбери тип отказа:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(QuestState.handling_refusal_33)
    await callback.answer()


@router.callback_query(F.data.startswith("refusal_"), QuestState.handling_refusal_33)
async def handle_refusal_type_33(callback: types.CallbackQuery, state: FSMContext):
    refusal_type = callback.data

    if refusal_type == "refusal_photo_zone_33":
        builder = InlineKeyboardBuilder()
        # Добавляем варианты из Excel
        reasons = [
            "1) Ребёнок убежал",
            "2) Ребёнок сказал, что ему 'мама не разрешила'",
            "3) Ребёнок сказал, что 'Вы потом фотки нам будете продавать'",
            "4) Ребёнок испугался",
            "5) Ребёнок сказал, что его уже фотографировали",
            "6) 'Нас не надо, у нас уже много здесь фотографировали'",
            "7) Не надо, у нас много фотографий (на телефоне)",
            "8) *с телефона мы так же может распечатать",
            "9) Мы сегодня не нарядные/растрёпанные/некрасивые",
            "10) Религиозные",
            "11) Я не люблю фотографироваться (я же взрослый)",
            "12) 'Я знаю, что у вас дорого'",
            "13) *спрашивают цены",
            "14) Мы на телефон сфоткались",
            "15) Мы недавно были на фотосессии"
        ]
        for i, reason in enumerate(reasons, 1):
            builder.row(InlineKeyboardButton(text=reason, callback_data=f"photo_reason_{i}_33"))

        await callback.message.edit_text(
            "Выбери конкретную причину отказа в фото-зоне:",
            reply_markup=builder.as_markup()
        )

    elif refusal_type == "refusal_stand_33":
        builder = InlineKeyboardBuilder()
        reasons = [
            "1) 'Дорого'",
            "2) 'Я подумаю'",
            "3) 'У нас уже есть ваша продукция'"
        ]
        for i, reason in enumerate(reasons, 1):
            builder.row(InlineKeyboardButton(text=reason, callback_data=f"stand_reason_{i}_33"))

        await callback.message.edit_text(
            "Выбери конкретную причину отказа на стенде:",
            reply_markup=builder.as_markup()
        )

    await callback.answer()


# Обработчики для конкретных причин с советами
@router.callback_query(F.data.startswith("photo_reason_"), QuestState.handling_refusal_33)
async def handle_photo_reason_33(callback: types.CallbackQuery, state: FSMContext):
    reason_num = int(callback.data.split("_")[2])
    advice = ""

    # Советы из Excel для каждой причины
    advice_map = {
        1: [
            "1. Попробуй свести всё в игру 'догонялки' и в процессе делать фотографии",
            "2. Попробуй познакомиться, поиграть без фотоаппарата",
            "3. Попробуй заинтересовать реквизитом"
        ],
        2: [
            "1. Попробуй договориться с ребёнком, что это будет 'Наш маленький секрет'",
            "2. 'А давай мы сделаем маме сюрприз'",
            "3. Попробуй обыграть запрет: 'Мама не разрешила покупать, а фоткаться можно', 'Смотри, все фоткаются'"
        ],
        3: [
            "1. 'Мы сделаем фотографию, вы посмотрите, а дальше решите'",
            "2. 'Да, но фотографии же недорогие, и не обязательно покупать'"
        ],
        4: [
            "1. Попробуй познакомиться, поиграть, если время позволяет, то сначала без фотоаппарата",
            "2. Попробуй через родителей",
            "3. Попробуй заинтересовать чем-то другим (реквизитом), перевести внимание и сделать кадры в моменте"
        ],
        5: [
            "1. Если девочка: 'А тебя в этом же наряде фотографировали?'",
            "2. Узнай красиво/некрасиво фотографировали? И в зависимости от ответа предложи удобный тебе исход",
            "3. 'А я тебя еще не фотографировал'",
            "4. 'А тебя фотографировали с диназоваром/с ёлкой?' (зацепить чем-то необычным на локации)",
            "5. Сделай акцент на ценный момент (соревнования, праздник, день рождения, придумать праздник самостоятельно 'день сладкоежки')",
            "6. Попробуй предложить обмен 'ты фоткаешься, я тебе подарок (чупа-чупс)'"
        ],
        6: [
            "1. Сделай акцент на ценность момента",
            "2. Сделай акцент на наряд ребёнка/взрослого",
            "3. Иной взгляд другой профессионального фотографа",
            "4. 'У нас новая фототехника, получатся другие кадры'",
            "5. Акцент на новую продукцию",
            "6. Акцент на новую фотозону/аттракцион (обновление парка)"
        ],
        7: [
            "1. Профессиональная техника + профессиональный фотограф",
            "2. Фото с телефона обычно не печатаются, риск потери",
            "3. Ценность момента",
            "4. Ценность уже готовой физической продукции (бабушке эл. кадр не подаришь)",
            "5. В кадре нет того, кто фотографирует, нет общего кадра, а сэлфи искажает"
        ],
        8: [
            "1. Затрата времени и денег (найти салон, доехать, распечатать, доехать забрать и т.д.), а у нас уже всё готово"
        ],
        9: [
            "1. Попробуй сделать комплимент про естественную красоту",
            "2. Попробуй сделать комплимент про одежду 'это самое красивое платье, которые я сегодня видел'",
            "3. Попробуй сделать комплимент про 'изюминку' во внешности (такие большие голубые глаза, такая длинная коса, яркие рыжие волосы)"
        ],
        10: [
            "1. Никто не увидит ваши фотографии, только я и вы (фотографии ценного момента для вашей семьи)"
        ],
        11: [
            "1. 'Мы сделаем крутой кадр, вы посмотрите, а дальше решите'",
            "2. Ценность момента",
            "3. 'Давайте вернёмся в детство'",
            "4. Сделать крутой, взрослый кадр (использовать ч/б или иную обработку), мы не только детские фотографы",
            "5. 'Я профессионал, у меня не может получиться плохой кадр' закрыть боль клиента от неудавшейся фотосъёмки (важно быть уверенным в своём опыте)",
            "6. 'Тем более, значит у вас мало фотографий', 'Как я вас понимаю, тоже не люблю фотографироваться и у меня совсем нет фотографий'"
        ],
        12: [
            "1. 'Мы сделаем крутой кадр, вы посмотрите, а дальше решите'",
            "2. 'Да, но...' (приурочить например к празднику, всё равно на подарок потратитесь = закрыть боль клиента с подарком)",
            "3. 'А какую продукцию вы у нас покупали? а как вам? а у нас есть еще другие варианты, даже дешевле, вставайте сделаем крутую фотографмю, потом посмотрите'"
        ],
        13: [
            "1. 'Я не могу вам продать воздух, давайте сфотографируемся, а дальше уже посмотрите'"
        ],
        14: [
            "1. Профессиональная техника + профессиональный фотограф (предложить сфотографироваться и сравнить кадры)",
            "2. Фото с телефона обычно не печатаются, риск потери",
            "3. Ценность уже готовой физической продукции (бабушке эл. кадр не подаришь)",
            "4. В кадре нет того, кто фотографирует, нет общего кадра, а сэлфи искажает",
            "5. Показать пример готовых фотографий для сравнения"
        ],
        15: [
            "1. 'С фотосессии вы получили только эл. кадры, а у нас готовые фотографии, эл. кадры не подарить, а если и решите подарить, то придётся искать где напечатать, дополнительно платить, ехать'",
            "2. Ценность момента",
            "3. Завести диалог о тематике фотосессии и привести к тому, что в парке можно сделать иные по стилю фотографии",
            "4. 'Значит вы умеете классно позировать'"
        ]
    }

    advice = "Советы:\n" + "\n".join(advice_map.get(reason_num, ["Попробуй ещё раз"]))

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Попробую ещё раз", callback_data="start_sales_quest_33"))

    await callback.message.edit_text(
        f"Ситуация: {callback.message.text}\n\n{advice}",
        reply_markup=builder.as_markup()
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()


@router.callback_query(F.data.startswith("stand_reason_"), QuestState.handling_refusal_33)
async def handle_stand_reason_33(callback: types.CallbackQuery, state: FSMContext):
    reason_num = int(callback.data.split("_")[2])
    advice = ""

    advice_map = {
        1: [
            "'Скажите, почему вы считаете что ваши фотографии это дорого?' дальнейший ответ позволит узнать истинное сомнение и обработать его"],
        2: [
            "'Почему вам сложно принять решение сейчас?' дальнейший ответ позволит узнать истинное сомнение и обработать его"],
        3: ["'А какая продукция у вас есть?' дальнейший ответ позволит узнать на какую продукцию сделать упор"]
    }

    advice = "Совет:\n" + "\n".join(advice_map.get(reason_num, ["Попробуй ещё раз"]))

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Попробую ещё раз", callback_data="start_sales_quest_33"))

    await callback.message.edit_text(
        f"Ситуация: {callback.message.text}\n\n{advice}",
        reply_markup=builder.as_markup()
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()


async def finish_sales_quest_33(message: types.Message, state: FSMContext):
    data = await state.get_data()
    checks = data.get("checks", [])
    comments = data.get("comments", [])

    # Сохраняем в БД
    async with SessionLocal() as session:
        result = UserResult(
            user_id=message.from_user.id,
            quest_id=33,
            result=3,  # 3 успешные продажи
            state="на модерации"
        )
        session.add(result)
        await session.commit()

    # Отправляем чеки и комментарии модератору
    username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    caption = (
        f"💰 Квест 33 - Продажи\n"
        f"👤 Автор: {message.from_user.full_name} ({username})\n"
        f"📊 Продажи: 3\n"
        f"📝 Комментарии: {', '.join(comments)}\n"
        f"🕒 Время: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    if checks:
        try:
            # Отправляем все чеки
            album = MediaGroupBuilder()
            for check in checks:
                album.add_photo(media=check)
            await message.bot.send_media_group(admin_chat_id, media=album.build())

            # Отправляем подпись отдельно с кнопками модерации
            await message.bot.send_message(
                admin_chat_id,
                caption,
                reply_markup=moderation_keyboard(message.from_user.id, 33)
            )
        except Exception as e:
            logging.error(f"Ошибка отправки чеков: {e}")
    else:
        await message.bot.send_message(
            admin_chat_id,
            caption,
            reply_markup=moderation_keyboard(message.from_user.id, 33)
        )

    await message.answer(
        "🎉 Ты отлично справился! У тебя хорошие навыки продаж!\n"
        "Задание завершено.",
        reply_markup=get_quest_finish_keyboard(3, 3, 33)
    )
    await state.clear()


@router.callback_query(F.data == "finish_sales_quest_33", QuestState.waiting_for_answer)
async def force_finish_sales_quest_33(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    successful_sales = data.get("successful_sales", 0)

    if successful_sales >= 3:
        await finish_sales_quest_33(callback.message, state)
    else:
        await callback.message.answer(
            f"Вы выполнили только {successful_sales} из 3 необходимых продаж. Продолжить?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Продолжить", callback_data="start_sales_quest_33")],
                [InlineKeyboardButton(text="Завершить досрочно", callback_data="confirm_early_finish_33")]
            ])
        )
        await callback.answer()

    @outer.callback_query(F.data == "confirm_early_finish_33", QuestState.waiting_for_answer)
    async def confirm_early_finish_33(callback: types.CallbackQuery, state: FSMContext):

        data = await state.get_data()
    successful_sales = data.get("successful_sales", 0)

    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=33,
            result=successful_sales,
            state="не выполнен"
        )
        session.add(result)
        await session.commit()

    await callback.message.answer(
        f"Вы завершили задание досрочно. Успешных продаж: {successful_sales}/3",
        reply_markup=get_quest_finish_keyboard(successful_sales, 3, 33)
    )
    await state.clear()
    await callback.answer()


# Квест 34 - Фидбек
async def quest_34(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    msg = await callback.message.answer(
        "Дорогой друг, а теперь ответь пожалуйста на несколько вопросов, "
        "чтобы сделать лучше жизнь тех, кто придёт после тебя:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать помогать", callback_data="start_feedback_34")]
        ]))

    await state.update_data(
        current_question=0,
        message_id=msg.message_id,
        answers={}
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()


@router.callback_query(F.data == "start_feedback_34", QuestState.waiting_for_answer)
async def start_feedback_34(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()

    questions = [
        {
            "text": "1. Как вам понравился формат обучения с элементами игры?",
            "type": "options",
            "options": ["Очень понравился", "Понравился", "Нейтрально", "Не понравился"]
        },
        {
            "text": "2. Какие задания были для вас наиболее интересными и полезными? (Укажите одно или несколько)",
            "type": "text"
        },
        {
            "text": "3. Были ли задания, которые показались слишком сложными или непонятными? Если да, укажите какие и почему.",
            "type": "text"
        },
        {
            "text": "4. Чувствуете ли вы, что освоили основные навыки работы фотографа?",
            "type": "options",
            "options": ["Да, полностью", "Да, но остались вопросы", "Нет, хотелось бы больше практики"]
        },
        {
            "text": "5. Оцените, насколько вы чувствуете себя уверенно в продажах (по шкале от 1 до 5).",
            "type": "options",
            "options": ["1 (совсем неуверенно)", "2", "3", "4", "5 (полностью уверен)"]
        },
        {
            "text": "6. Что из обучающего материала по продажам было самым полезным?",
            "type": "text"
        },
        {
            "text": "7. Какие моменты в процессе работы вызвали трудности (например, съемка, работа с клиентами, использование оборудования)?",
            "type": "text"
        },
        {
            "text": "8. Оцените работу коллектива и наставника (по шкале от 1 до 5).",
            "type": "options",
            "options": ["1 (очень плохо)", "2", "3", "4", "5 (отлично)"]
        },
        {
            "text": "9. Какие ваши впечатления от стажировки? Что можно улучшить?",
            "type": "text"
        },
        {
            "text": "10. Хотели бы вы продолжить работу в компании? Если да, то почему? Если нет, то, что вас остановило?",
            "type": "text"
        }
    ]

    # Start with first question
    question = questions[0]
    if question["type"] == "options":
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"answer_34_0_{i}")]
            for i, opt in enumerate(question["options"])
        ])
    else:
        reply_markup = None

    msg = await callback.message.answer(
        question["text"],
        reply_markup=reply_markup
    )

    await state.update_data(
        questions=questions,
        current_question=0,
        message_id=msg.message_id
    )


@router.callback_query(F.data.startswith("answer_34_"), QuestState.waiting_for_answer)
async def handle_feedback_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_q = int(callback.data.split("_")[2])
    answer_idx = int(callback.data.split("_")[3])

    answers = user_data.get("answers", {})
    answers[current_q] = user_data["questions"][current_q]["options"][answer_idx]

    await state.update_data(answers=answers)
    await callback.message.delete()

    await ask_next_question(callback, state, current_q + 1)
    await callback.answer()


@router.message(QuestState.waiting_for_answer)
async def handle_feedback_text(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    current_q = user_data["current_question"]

    # Check if we're expecting text input for this question
    if user_data["questions"][current_q]["type"] == "text":
        answers = user_data.get("answers", {})
        answers[current_q] = message.text
        await state.update_data(answers=answers)
        await message.delete()

        await ask_next_question(message, state, current_q + 1)
    else:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.")


async def ask_next_question(source: Union[types.CallbackQuery, types.Message], state: FSMContext, next_q: int):
    user_data = await state.get_data()
    questions = user_data["questions"]

    if next_q < len(questions):
        question = questions[next_q]

        if question["type"] == "options":
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=opt, callback_data=f"answer_34_{next_q}_{i}")]
                for i, opt in enumerate(question["options"])
            ])
        else:
            reply_markup = None

        # Handle both CallbackQuery and Message sources
        if isinstance(source, types.CallbackQuery):
            msg = await source.message.answer(
                question["text"],
                reply_markup=reply_markup
            )
        else:  # It's a Message
            msg = await source.answer(
                question["text"],
                reply_markup=reply_markup
            )

        await state.update_data(
            current_question=next_q,
            message_id=msg.message_id
        )
    else:
        await finish_feedback_34(source, state)


async def finish_feedback_34(source: Union[types.CallbackQuery, types.Message], state: FSMContext):
    user_data = await state.get_data()

    # Delete the last question message if it exists
    if "message_id" in user_data:
        try:
            if isinstance(source, types.CallbackQuery):
                await source.bot.delete_message(source.message.chat.id, user_data["message_id"])
            else:  # Message
                await source.bot.delete_message(source.chat.id, user_data["message_id"])
        except Exception as e:
            logging.error(f"Error deleting message: {e}")

    # Prepare report with author info
    username = f"@{source.from_user.username}" if source.from_user.username else f"ID: {source.from_user.id}"
    report = (
        f"📋 Фидбек по обучению\n\n"
        f"👤 Автор: {source.from_user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    )

    # Add questions and answers
    for i, (q, a) in enumerate(zip(user_data["questions"], user_data["answers"].values())):
        report += f"{i + 1}. {q['text']}\n➡️ {a}\n\n"

    # Send to admin
    await source.bot.send_message(admin_chat_id, report)

    # Save to DB
    async with SessionLocal() as session:
        result = UserResult(
            user_id=source.from_user.id,
            quest_id=34,
            result=1,
            state="выполнен"
        )
        session.add(result)
        await session.commit()

    # Respond to user
    if isinstance(source, types.CallbackQuery):
        await source.message.answer(
            "✅ Спасибо за фидбек! Ваши ответы помогут нам стать лучше.",
            reply_markup=get_quest_finish_keyboard(1, 1, 34)
        )
    else:
        await source.answer(
            "✅ Спасибо за фидбек! Ваши ответы помогут нам стать лучше.",
            reply_markup=get_quest_finish_keyboard(1, 1, 34)
        )
    await give_achievement(source.from_user.id, 34, session)

    await state.clear()


# Обработчик для всех остальных ответов
@router.callback_query(QuestState.waiting_for_answer)
async def handle_other_answers(callback: types.CallbackQuery):
    # Уведомляем пользователя, что ответ неверный
    await callback.answer("Ответ неверный. Попробуйте ещё раз!")