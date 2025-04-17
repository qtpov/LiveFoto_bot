from aiogram import Router, types, F
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder
from pathlib import Path
import datetime
import logging
import asyncio
from typing import Union
from bot.db.models import UserResult
from bot.db.session import SessionLocal
from bot.keyboards.inline import *
from .states import QuestState
from bot.configurate import settings
from .moderation import give_achievement
from bot.db.crud import update_user_level
from .moderation import give_achievement, get_quest_finish_keyboard

router = Router()
admin_chat_id = settings.ADMIN_ID
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Словари с правильными ответами и сообщениями
correct_answers_qw27 = {1: 2, 2: 1, 3: 3}
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

correct_answers_qw31 = {1: 1, 2: 2, 3: 1}
correct_answers_qw32 = {1: 0, 2: 1}

# Видео file_ids (должны быть заменены на реальные)
VIDEO_FILE_IDS = {
    "assembly": "BAACAgIAAxkBAAIB...",  # Пример file_id для видео сборки (квест 28)
    "lecture": "BAACAgIAAxkBAAIB..."  # Пример file_id для лекции (квест 31)
}


# Общая функция завершения квеста
async def finish_quest(callback: types.CallbackQuery, state: FSMContext,
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
        await finish_quest(callback, state, correct_answers, len(correct_answers_qw27), 27)

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
    try:
        await callback.message.delete()
    except:
        pass

    # Отправляем видео по file_id
    await callback.message.answer_video("BAACAgIAAxkBAAImsGf0B-OgQ_mpwLkKY2RnMiOqG1DbAALqbgACoYqhS7f0qJ4Nuj69NgQ")

    msg = await callback.message.answer(
        "Квест 28: Сборка магнитов\n\nТвоя задача собрать 6 магнитов как можно быстрее. "
        "При нажатии 'СТАРТ' будет запущен таймер в боте. Перед началом попроси коллегу "
        "записать тебя на видео так, чтоб таймер из бота был в кадре видео. Не забудь отработать движения!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_assembly_28")]
        ])
    )

    await state.update_data(
        start_time=None,
        message_id=msg.message_id
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()


@router.callback_query(F.data == "start_assembly_28", QuestState.waiting_for_answer)
async def start_assembly_28(callback: types.CallbackQuery, state: FSMContext):
    # Отправляем таймер на весь экран
    timer_msg = await callback.message.answer(
        "⏱ Таймер запущен!\n\n00:00:00",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ФИНИШ", callback_data="finish_assembly_28")]
        ])
    )

    await state.update_data(
        start_time=datetime.datetime.now(),
        timer_message_id=timer_msg.message_id
    )

    # Запускаем обновление таймера
    asyncio.create_task(update_timer(callback.message.chat.id, timer_msg.message_id, state))
    await callback.answer("Таймер запущен!")

async def update_timer(chat_id: int, message_id: int, state: FSMContext):
    while True:
        user_data = await state.get_data()
        if "start_time" not in user_data or user_data.get("timer_stopped", False):
            break

        duration = datetime.datetime.now() - user_data["start_time"]
        timer_text = f"⏱ Таймер запущен!\n\n{duration}"

        try:
            await callback.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=timer_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="ФИНИШ", callback_data="finish_assembly_28")]
                ])
            )
        except:
            pass

        await asyncio.sleep(1)

@router.callback_query(F.data == "finish_assembly_28", QuestState.waiting_for_answer)
async def finish_assembly_28(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    duration = (datetime.datetime.now() - user_data["start_time"]).total_seconds()

    # Останавливаем таймер
    await state.update_data(timer_stopped=True)

    # Удаляем таймер
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["timer_message_id"])
    except:
        pass

    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=28,
            result=duration,
            state="выполнен"
        )
        session.add(result)
        await session.commit()

    await callback.message.answer(
        f"✅ Поздравляю, новый отличный результат: {duration:.2f} секунд!\n\n"
        "Теперь отправь видео с твоим выполнением задания на модерацию.",
        reply_markup=get_quest_finish_keyboard(1, 1, 28)
    )
    await state.clear()

# Квест 29 - Фотоохота
async def quest_29(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    # Создаем клавиатуру с кнопкой рекомендаций
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
        timer_message_id=None
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
            [InlineKeyboardButton(text="СТОП", callback_data="stop_photo_hunt_29")],
            [InlineKeyboardButton(text="Отправить фотографии", callback_data="submit_photos_29")]
        ])
    )

    await state.update_data(
        timer_start=datetime.datetime.now(),
        timer_message_id=timer_msg.message_id,
        photos=[],
        timer_task=asyncio.create_task(
            countdown_timer(callback.message.chat.id, timer_msg.message_id, state, 15 * 60))
    )
    await callback.answer("Таймер запущен! У вас 15 минут.")

async def countdown_timer(chat_id: int, message_id: int, state: FSMContext, seconds: int):
    remaining = seconds
    while remaining > 0:
        user_data = await state.get_data()
        if user_data.get("timer_stopped", False):
            break

        mins, secs = divmod(remaining, 60)
        timer_text = f"⏱ Осталось времени: {mins:02d}:{secs:02d}"

        try:
            await callback.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=timer_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="СТОП", callback_data="stop_photo_hunt_29")],
                    [InlineKeyboardButton(text="Отправить фотографии", callback_data="submit_photos_29")]
                ])
            )
        except:
            pass

        await asyncio.sleep(1)
        remaining -= 1

    # Если время вышло
    if remaining <= 0:
        user_data = await state.get_data()
        if not user_data.get("photos_submitted", False):
            await callback.bot.send_message(
                chat_id=chat_id,
                text="⏰ Время вышло! Вы не успели отправить фотографии.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
                ])
            )
            await state.update_data(timer_stopped=True)

@router.callback_query(F.data == "stop_photo_hunt_29", QuestState.waiting_for_answer)
async def stop_photo_hunt_29(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    duration = (datetime.datetime.now() - user_data["timer_start"]).total_seconds()

    # Останавливаем таймер
    await state.update_data(timer_stopped=True)
    if "timer_task" in user_data:
        user_data["timer_task"].cancel()

    # Удаляем таймер
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["timer_message_id"])
    except:
        pass

    # Проверяем, не вышло ли время
    if duration > 15 * 60:
        await callback.message.answer(
            "⏰ Не успел! Попробуй еще раз!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
            ])
        )
        return

    # Предлагаем варианты завершения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нет людей", callback_data="no_people_29")],
        [InlineKeyboardButton(text="Все отказались", callback_data="all_refused_29")],
        [InlineKeyboardButton(text="Свой вариант", callback_data="custom_reason_29")],
        [InlineKeyboardButton(text="Отправить фотографии", callback_data="submit_photos_29")]
    ])

    await callback.message.answer(
        "Почему ты остановил фотоохоту?",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "restart_quest_29", QuestState.waiting_for_answer)
async def restart_quest_29(callback: types.CallbackQuery, state: FSMContext):
    await quest_29(callback, state)

@router.callback_query(F.data == "no_people_29", QuestState.waiting_for_answer)
async def no_people_29(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Не переживай, они обязательно придут! Как только будешь готов нажимай 'Заново' и отправляйся в фотозону!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "all_refused_29", QuestState.waiting_for_answer)
async def all_refused_29(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Не стоит расстраиваться! Почитай рекомендации по работе в фотозоне, они обязательно помогут!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Рекомендации", callback_data="show_recommendations_29")],
            [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "custom_reason_29", QuestState.waiting_for_answer)
async def custom_reason_29(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Напиши, почему ты не принес фотографии:",
        reply_markup=None
    )
    await state.set_state(QuestState.waiting_photo_feedback)
    await callback.answer()

@router.message(QuestState.waiting_photo_feedback)
async def handle_custom_reason(message: types.Message, state: FSMContext):
    await state.update_data(custom_reason=message.text)
    await message.answer(
        "Спасибо за объяснение! Почитай рекомендации по работе в фотозоне, они обязательно помогут!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Рекомендации", callback_data="show_recommendations_29")],
            [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
        ])
    )
    await state.set_state(QuestState.waiting_for_answer)

@router.callback_query(F.data == "submit_photos_29", QuestState.waiting_for_answer)
async def submit_photos_29(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    # Останавливаем таймер
    await state.update_data(timer_stopped=True, photos_submitted=True)
    if "timer_task" in user_data:
        user_data["timer_task"].cancel()

    # Удаляем таймер
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["timer_message_id"])
    except:
        pass

    if not user_data.get("photos"):
        await callback.message.answer(
            "Вы не загрузили ни одной фотографии. Хотите попробовать еще раз?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Заново", callback_data="restart_quest_29")]
            ])
        )
        return

    # Отправляем фотографии на модерацию
    album_builder = MediaGroupBuilder()
    for photo in user_data["photos"]:
        album_builder.add_photo(media=photo)

    await callback.message.answer_media_group(media=album_builder.build())

    # Запрашиваем фидбек
    await callback.message.answer(
        "Фотографии отправлены на модерацию. А пока расскажи, какие были трудности на твоем пути?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_feedback_29")]
        ])
    )

    await state.set_state(QuestState.waiting_feedback_text)

@router.message(QuestState.waiting_feedback_text)
async def handle_feedback_text(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        result = UserResult(
            user_id=message.from_user.id,
            quest_id=29,
            result=len((await state.get_data()).get("photos", [])),
            state="выполнен",
            feedback=message.text
        )
        session.add(result)
        await session.commit()

    await message.answer(
        "✅ Спасибо за обратную связь!",
        reply_markup=get_quest_finish_keyboard(1, 1, 29)
    )
    await state.clear()

@router.callback_query(F.data == "skip_feedback_29", QuestState.waiting_feedback_text)
async def skip_feedback_29(callback: types.CallbackQuery, state: FSMContext):
    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=29,
            result=len((await state.get_data()).get("photos", [])),
            state="выполнен"
        )
        session.add(result)
        await session.commit()

    await callback.message.answer(
        "✅ Фотоохота завершена!",
        reply_markup=get_quest_finish_keyboard(1, 1, 29)
    )
    await state.clear()

# Квест 30 - Полный цикл
async def quest_30(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    steps = [
        {
            "text": "Привет! На связи ***! Я расскажу тебе, как ловко забирать деньги из карманов наших клиентов и при этом не угодить за решетку!",
            "button": "Круто!"
        },
        {
            "text": "Для начала давай определимся, что ты должен выглядеть опрятно, ведь встречают по одежке!",
            "button": "Я красавчик" if user_data.get("gender") == "male" else "Я красавица"
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
        steps=steps
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()

@router.callback_query(F.data == "next_step_30", QuestState.waiting_for_answer)
async def next_step_30(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_step = user_data["current_step"] + 1
    steps = user_data["steps"]

    if current_step >= len(steps):
        # Завершаем квест
        await callback.message.answer(
            "Укажи, на какую сумму ты осуществил продажу:",
            reply_markup=None
        )
        await state.set_state(QuestState.waiting_sales_amount)
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

@router.message(QuestState.waiting_sales_amount)
async def handle_sales_amount(message: types.Message, state: FSMContext):

    try:
        amount = float(message.text)
        async with SessionLocal() as session:
            result = UserResult(
                user_id=message.from_user.id,
                quest_id=30,
                result=amount,
                state="выполнен"
            )
            session.add(result)
            await session.commit()

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
        return

# Квест 31 - Ценность кадра
async def quest_31(callback: types.CallbackQuery, state: FSMContext):

    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)

    try:
        await callback.message.delete()
    except:
        pass

    if current_question == 1:
        video_path = BASE_DIR / "assets/quest31/lecture.mp4"
        video = FSInputFile(video_path)

        video_msg = await callback.message.answer_video(video)
        msg = await callback.message.answer(
            "Просмотрите видео и начните тест",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Начать тест", callback_data="start_quiz_31")]
            ])
        )

        await state.update_data(
            video_message_id=video_msg.message_id,
            message_id=msg.message_id
        )
    else:
        await ask_quest31_question(callback, state)

        await callback.answer()

async def ask_quest31_question(callback: types.CallbackQuery, state: FSMContext):

    user_data = await state.get_data()
    current_question = user_data["current_question"]

    questions = [
        {
            "text": "1. Что такое 'ценность кадра' в фотографии?",
            "options": ["A) Количество пикселей", "B) Эмоции и смысл", "C) Цена камеры", "D) Тип объектива"]
        },
        {
            "text": "2. Какое правило помогает выстроить композицию?",
            "options": ["A) Золотое сечение", "B) Центральное размещение", "C) Правило третей",
                        "D) Параллельные линии"]
        },
        {
            "text": "3. Что важнее в портретной фотографии?",
            "options": ["A) Резкость по всему кадру", "B) Передача эмоций", "C) Сложный фон",
                        "D) Много аксессуаров"]
        }
    ]

    msg = await callback.message.answer(
        questions[current_question - 1]["text"],
        reply_markup=create_quiz_keyboard(questions[current_question - 1]["options"], "quest31")
    )

    await state.update_data(
        message_id=msg.message_id,
        current_question=current_question
    )

@router.callback_query(F.data.startswith("quest31_"), QuestState.waiting_for_answer)
async def handle_quest31_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data["current_question"]
    selected = int(callback.data.split("_")[1])
    is_correct = selected == correct_answers_qw31[current_question]

    correct_answers = user_data.get("correct_answers", 0) + int(is_correct)

    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
    except:
        pass

    await callback.message.answer("✅ Верно!" if is_correct else "❌ Неверно!")

    if current_question < len(correct_answers_qw31):
        await state.update_data(
            current_question=current_question + 1,
            correct_answers=correct_answers
        )
        await ask_quest31_question(callback, state)
    else:
        await finish_quest(callback, state, correct_answers, len(correct_answers_qw31), 31)

    await callback.answer()

# Квест 32 - Ценности компании
async def quest_32(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    msg = await callback.message.answer(
        "Квест 32: Ценности компании\nИзучите ценности и пройдите тест",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать игру", callback_data="start_game_32")]
        ]))

    await state.update_data(
        current_scenario=0,
        message_id=msg.message_id
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()

@router.callback_query(F.data == "start_game_32", QuestState.waiting_for_answer)
async def start_game_32(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()

    scenarios = [
        {
            "text": "Ситуация 1: Коллега предлагает разделить найденные деньги...",
            "options": ["Честность", "Ответственность", "Работа в команде"]
        },
        {
            "text": "Ситуация 2: Клиент просит сделать скидку без причины...",
            "options": ["Клиентоориентированность", "Профессионализм", "Командность"]
        }
    ]

    msg = await callback.message.answer(
        scenarios[0]["text"],
        reply_markup=create_quiz_keyboard(scenarios[0]["options"], "quest32")
    )

    await state.update_data(
        scenarios=scenarios,
        current_scenario=0,
        message_id=msg.message_id,
        correct_answers=0
    )

@router.callback_query(F.data.startswith("quest32_"), QuestState.waiting_for_answer)
async def handle_quest32_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_scenario = user_data["current_scenario"]
    selected = int(callback.data.split("_")[1])
    is_correct = selected == correct_answers_qw32[current_scenario + 1]

    correct_answers = user_data.get("correct_answers", 0) + int(is_correct)

    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
    except:
        pass

    await callback.message.answer("✅ Верный выбор!" if is_correct else "❌ Это не лучший вариант")

    if current_scenario + 1 < len(user_data["scenarios"]):
        await state.update_data(
            current_scenario=current_scenario + 1,
            correct_answers=correct_answers
        )

        msg = await callback.message.answer(
            user_data["scenarios"][current_scenario + 1]["text"],
            reply_markup=create_quiz_keyboard(
                user_data["scenarios"][current_scenario + 1]["options"], "quest32")
        )
        await state.update_data(message_id=msg.message_id)
    else:
        await finish_quest(callback, state, correct_answers, len(user_data["scenarios"]), 32)

    await callback.answer()

# Квест 33 - Клиент
async def quest_33(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    msg = await callback.message.answer(
        "Квест 33: Работа с клиентами\nПообщайтесь с 5 клиентами",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_client_quest_33")]
        ]))

    await state.update_data(
        clients=0,
        photos=[],
        message_id=msg.message_id
    )
    await state.set_state(QuestState.waiting_for_answer)
    await callback.answer()

@router.callback_query(F.data == "start_client_quest_33", QuestState.waiting_for_answer)
async def start_client_quest_33(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ЗАВЕРШИТЬ", callback_data="finish_client_quest_33")]
        ]))

    await state.update_data(start_time=datetime.datetime.now())
    await callback.answer("Квест начат!")

@router.callback_query(F.data == "finish_client_quest_33", QuestState.waiting_for_answer)
async def finish_client_quest_33(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    clients = user_data.get("clients", 0)

    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=33,
            result=clients,
            state="выполнен"
        )
        session.add(result)
        await session.commit()

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Вы пообщались с {clients} клиентами",
        reply_markup=get_quest_finish_keyboard(1, 1, 33)
    )
    await state.clear()

# Квест 34 - Фидбек
async def quest_34(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass

    msg = await callback.message.answer(
        "Квест 34: Фидбек по обучению\nПройдите небольшой опрос",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать опрос", callback_data="start_feedback_34")]
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
            "text": "1. Как вам формат обучения с элементами игры?",
            "type": "options",
            "options": ["Очень понравился", "Понравился", "Нейтрально", "Не понравился"]
        },
        {
            "text": "2. Какие задания были наиболее полезными?",
            "type": "text"
        }
    ]

    msg = await callback.message.answer(
        questions[0]["text"],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"answer_34_0_{i}")]
            for i, opt in enumerate(questions[0]["options"])
        ])
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

    if current_q + 1 < len(user_data["questions"]):
        next_q = current_q + 1
        question = user_data["questions"][next_q]

        if question["type"] == "options":
            msg = await callback.message.answer(
                question["text"],
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=opt, callback_data=f"answer_34_{next_q}_{i}")]
                    for i, opt in enumerate(question["options"])
                ])
            )
        else:
            msg = await callback.message.answer(
                question["text"] + "\n\nНапишите ответ текстом"
            )

        await state.update_data(
            current_question=next_q,
            message_id=msg.message_id
        )
    else:
        await finish_feedback_34(callback, state)

    await callback.answer()

@router.message(QuestState.waiting_for_answer)
async def handle_text_feedback(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    current_q = user_data["current_question"]

    answers = user_data.get("answers", {})
    answers[current_q] = message.text

    await state.update_data(answers=answers)
    await message.delete()

    if current_q + 1 < len(user_data["questions"]):
        next_q = current_q + 1
        question = user_data["questions"][next_q]

        msg = await message.answer(
            question["text"],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=opt, callback_data=f"answer_34_{next_q}_{i}")]
                for i, opt in enumerate(question["options"])
            ]) if question["type"] == "options" else None
        )

        await state.update_data(
            current_question=next_q,
            message_id=msg.message_id if msg else None
        )
    else:
        await finish_feedback_34(message, state)

async def finish_feedback_34(source: Union[types.CallbackQuery, types.Message], state: FSMContext):
    user_data = await state.get_data()

    report = "📋 Фидбек по обучению:\n\n"
    for i, (q, a) in enumerate(zip(user_data["questions"], user_data["answers"].values())):
        report += f"{i + 1}. {q['text']}\n➡️ {a}\n\n"

    await source.bot.send_message(admin_chat_id, report)

    async with SessionLocal() as session:
        result = UserResult(
            user_id=source.from_user.id,
            quest_id=34,
            result=1,
            state="выполнен"
        )
        session.add(result)
        await session.commit()

    await source.answer(
        "✅ Спасибо за фидбек!",
        reply_markup=get_quest_finish_keyboard(1, 1, 34)
    )
    await state.clear()

# Вспомогательные функции
def create_options_keyboard(options: list[str], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, _ in enumerate(options, 1):
        builder.button(text=str(i), callback_data=f"{prefix}_{i}")
    builder.adjust(3)
    return builder.as_markup()

def create_quiz_keyboard(options: list[str], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        builder.button(text=opt.split(")")[0], callback_data=f"{prefix}_{i}")
    builder.adjust(2)
    return builder.as_markup()


# Обработчик для всех остальных ответов
@router.callback_query(QuestState.waiting_for_answer)
async def handle_other_answers(callback: types.CallbackQuery):
    # Уведомляем пользователя, что ответ неверный
    await callback.answer("Ответ неверный. Попробуйте ещё раз!")