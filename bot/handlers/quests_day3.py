from aiogram import Router, types, F
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
import datetime
import logging
from pathlib import Path
import os
from typing import List, Dict, Union

# Импорты из вашего проекта
from bot.db.models import UserResult
from bot.db.session import SessionLocal
from bot.keyboards.inline import *
from .states import QuestState
from bot.configurate import settings
from .moderation import give_achievement
from bot.db.crud import update_user_level

router = Router()
admin_chat_id = settings.ADMIN_ID
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Путь к корню проекта


# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================

def build_media_group(files: List[Union[str, Path]], captions: List[str] = None) -> MediaGroupBuilder:
    """Создает медиагруппу из файлов"""
    builder = MediaGroupBuilder()
    for i, file in enumerate(files):
        caption = str(i + 1) if captions is None else captions[i]
        if str(file).endswith(('.jpg', '.jpeg', '.png')):
            builder.add_photo(media=FSInputFile(file), caption=caption)
        elif str(file).endswith('.mp4'):
            builder.add_video(media=FSInputFile(file), caption=caption)
    return builder


def create_options_keyboard(options: List[str], prefix: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с вариантами ответов"""
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options, start=1):
        builder.button(text=str(i), callback_data=f"{prefix}_{i}")
    builder.adjust(3)  # 3 кнопки в ряд
    return builder.as_markup()


async def finish_quest(callback: types.CallbackQuery, state: FSMContext, correct_count: int,
                       total_questions: int, quest_id: int) -> None:
    """Завершает квест и сохраняет результаты"""
    user_data = await state.get_data()

    # Удаляем предыдущие сообщения
    try:
        for msg_id in user_data.get("message_ids", []):
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except Exception as e:
        logging.error(f"Error deleting messages: {e}")

    # Сохраняем результат в БД
    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=quest_id,
            result=correct_count,
            state="completed"
        )
        session.add(result)

        # Выдаем ачивку если все ответы верные
        if correct_count == total_questions:
            await give_achievement(callback.from_user.id, quest_id, session)

        await session.commit()

    # Отправляем отчет администратору
    report = (f"📊 Результат квеста {quest_id}\n"
              f"👤 Пользователь: {callback.from_user.full_name}\n"
              f"✅ Правильных ответов: {correct_count}/{total_questions}")

    await callback.bot.send_message(admin_chat_id, report)

    # Сообщение пользователю
    await callback.message.answer(
        f"Вы ответили правильно на {correct_count} из {total_questions} вопросов!",
        reply_markup=get_quest_finish_keyboard(correct_count, total_questions, quest_id)
    )

    await state.clear()


# ====================== КВЕСТ 27 - ПРАВИЛЬНОЕ ФОТО ======================

async def quest_27(callback: types.CallbackQuery, state: FSMContext):
    """Квест на определение правильно экспонированных фотографий"""
    questions = [
        {
            "text": "Какое фото пересвечено?",
            "media": [
                BASE_DIR / "handlers/media/photo/zaglushka.png",
                BASE_DIR / "handlers/media/photo/zaglushka.png",
                BASE_DIR / "handlers/media/photo/zaglushka.png"
            ],
            "correct": 2,
            "feedback": {
                "correct": "Прекрасный загар и верный ответ!",
                "wrong": "Модель получила ожог, ответ не верный"
            }
        },
        {
            "text": "Какое фото слишком темное?",
            "media": [
                BASE_DIR / "handlers/media/photo/zaglushka.png",
                BASE_DIR / "handlers/media/photo/zaglushka.png",
                BASE_DIR / "handlers/media/photo/zaglushka.png"
            ],
            "correct": 1,
            "feedback": {
                "correct": "Отличное зрение! Это действительно темное фото",
                "wrong": "Нет, это фото нормальной яркости"
            }
        },
        {
            "text": "Какое фото имеет правильную экспозицию?",
            "media": [
                BASE_DIR / "handlers/media/photo/zaglushka.png",
                BASE_DIR / "handlers/media/photo/zaglushka.png",
                BASE_DIR / "handlers/media/photo/zaglushka.png"
            ],
            "correct": 3,
            "feedback": {
                "correct": "Идеально! Это фото с правильной экспозицией",
                "wrong": "К сожалению, это не самый удачный вариант"
            }
        }
    ]

    try:
        # Отправляем первую медиагруппу
        media_group = build_media_group(questions[0]["media"])
        messages = await callback.message.answer_media_group(media=media_group.build())
        message_ids = [m.message_id for m in messages]

        # Отправляем первый вопрос с кнопками
        question_msg = await callback.message.answer(
            questions[0]["text"],
            reply_markup=create_options_keyboard(["1", "2", "3"], "quest27")
        )
        message_ids.append(question_msg.message_id)

        # Сохраняем данные в state
        await state.update_data(
            questions=questions,
            current_question=0,
            message_ids=message_ids,
            correct_answers=0
        )
        await state.set_state(QuestState.waiting_photo_answer)

    except Exception as e:
        logging.error(f"Error in quest_27: {e}")
        await callback.message.answer("Произошла ошибка при загрузке фотографий")


@router.callback_query(F.data.startswith("quest27_"), QuestState.waiting_photo_answer)
async def handle_quest27_answer(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик ответов для квеста 27"""
    user_data = await state.get_data()
    current_q = user_data["current_question"]
    questions = user_data["questions"]

    selected = int(callback.data.split("_")[1])
    is_correct = selected == questions[current_q]["correct"]

    # Удаляем предыдущие сообщения
    for msg_id in user_data["message_ids"]:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except TelegramBadRequest:
            pass

    # Показываем результат
    feedback = questions[current_q]["feedback"]
    result_text = feedback["correct"] if is_correct else feedback["wrong"]
    await callback.message.answer(result_text)

    # Обновляем счетчик правильных ответов
    new_data = {"correct_answers": user_data["correct_answers"] + int(is_correct)}

    # Переход к следующему вопросу или завершение
    if current_q + 1 < len(questions):
        next_q = current_q + 1
        media_group = build_media_group(questions[next_q]["media"])
        messages = await callback.message.answer_media_group(media=media_group.build())

        question_msg = await callback.message.answer(
            questions[next_q]["text"],
            reply_markup=create_options_keyboard(["1", "2", "3"], "quest27")
        )

        new_data.update({
            "current_question": next_q,
            "message_ids": [m.message_id for m in messages] + [question_msg.message_id]
        })
        await state.update_data(**new_data)
    else:
        await finish_quest(callback, state, new_data["correct_answers"], len(questions), 27)


# ====================== КВЕСТ 28 - СОБЕРИ ВСЕ ======================

async def quest_28(callback: types.CallbackQuery, state: FSMContext):
    """Квест на сборку магнитов за минимальное время"""
    try:
        video_path = BASE_DIR / "assets/quest28/assembly_video.mp4"
        video = FSInputFile(video_path)

        msg = await callback.message.answer_video(
            video=video,
            caption="Твоя задача собрать 6 магнитов как можно быстрее. Нажми СТАРТ для начала.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="СТАРТ", callback_data="start_assembly_28")]
            ])
        )

        await state.update_data(
            start_time=None,
            message_id=msg.message_id
        )
        await state.set_state(QuestState.waiting_assembly_start)

    except Exception as e:
        logging.error(f"Error in quest_28: {e}")
        await callback.message.answer("Произошла ошибка при загрузке видео")


@router.callback_query(F.data == "start_assembly_28", QuestState.waiting_assembly_start)
async def start_assembly_28(callback: types.CallbackQuery, state: FSMContext):
    """Начало выполнения квеста 28"""
    start_time = datetime.datetime.now()

    # Обновляем кнопку на ФИНИШ
    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ФИНИШ", callback_data="finish_assembly_28")]
        ])
    )

    await state.update_data(start_time=start_time)
    await callback.answer("Таймер запущен! Собирайте магниты!")


@router.callback_query(F.data == "finish_assembly_28", QuestState.waiting_assembly_start)
async def finish_assembly_28(callback: types.CallbackQuery, state: FSMContext):
    """Завершение квеста 28 с сохранением времени"""
    user_data = await state.get_data()
    end_time = datetime.datetime.now()
    duration = end_time - user_data["start_time"]

    # Сохраняем результат
    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=28,
            result=duration.total_seconds(),
            state="completed"
        )
        session.add(result)
        await session.commit()

    # Отправляем отчет администратору
    report = (f"⏱ Результат квеста 28\n"
              f"👤 Пользователь: {callback.from_user.full_name}\n"
              f"⏱ Время: {duration.total_seconds():.2f} сек")

    await callback.bot.send_message(admin_chat_id, report)

    # Сообщение пользователю
    await callback.message.answer(
        f"Поздравляю! Ваше время: {duration.total_seconds():.2f} секунд\n"
        "Отправьте видео выполнения на модерацию.",
        reply_markup=get_quest_finish_keyboard(1, 1, 28)  # Всегда успешное завершение
    )

    await state.clear()


# ====================== КВЕСТ 29 - ФОТООХОТА ======================

async def quest_29(callback: types.CallbackQuery, state: FSMContext):
    """Квест на выполнение фотосессии за ограниченное время"""
    recommendations = (
        "Рекомендации по работе в фотозоне:\n"
        "1. Проверь настройки фотоаппарата\n"
        "2. Ищи интересные ракурсы\n"
        "3. Установи доверительные отношения\n"
        "4. Лови спонтанные моменты\n"
        "5. Делай разнообразные снимки"
    )

    msg = await callback.message.answer(
        "📷 Фотоохота\n\n"
        "Твоя задача сделать как можно больше качественных фотографий за 15 минут.\n\n"
        "Требования:\n"
        "- Минимум 10 разных кадров\n"
        "- Разные ракурсы и композиции\n"
        "- Хорошая экспозиция и фокус",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Рекомендации", callback_data="show_recommendations_29")],
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_photo_hunt_29")]
        ])
    )

    await state.update_data(
        timer_start=None,
        photos=[],
        message_id=msg.message_id,
        recommendations=recommendations
    )
    await state.set_state(QuestState.waiting_photo_hunt_start)


@router.callback_query(F.data == "show_recommendations_29", QuestState.waiting_photo_hunt_start)
async def show_recommendations_29(callback: types.CallbackQuery, state: FSMContext):
    """Показывает рекомендации для фотоохоты"""
    user_data = await state.get_data()
    await callback.message.answer(user_data["recommendations"])
    await callback.answer()


@router.callback_query(F.data == "start_photo_hunt_29", QuestState.waiting_photo_hunt_start)
async def start_photo_hunt_29(callback: types.CallbackQuery, state: FSMContext):
    """Начинает отсчет времени для фотоохоты"""
    timer_start = datetime.datetime.now()

    # Обновляем сообщение с новыми кнопками
    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТОП", callback_data="stop_photo_hunt_29")],
            [InlineKeyboardButton(text="Нет людей", callback_data="no_people_29")],
            [InlineKeyboardButton(text="Все отказались", callback_data="all_refused_29")]
        ])
    )

    await state.update_data(timer_start=timer_start)
    await callback.answer("Таймер запущен! У вас 15 минут на выполнение задания.")


@router.callback_query(F.data == "stop_photo_hunt_29", QuestState.waiting_photo_hunt_start)
async def stop_photo_hunt_29(callback: types.CallbackQuery, state: FSMContext):
    """Завершает фотоохоту и сохраняет результаты"""
    user_data = await state.get_data()
    end_time = datetime.datetime.now()
    duration = end_time - user_data["timer_start"]

    if duration.total_seconds() < 60:  # Минимум 1 минута
        await callback.answer("Вы должны потратить хотя бы 1 минуту на выполнение задания!", show_alert=True)
        return

    # Сохраняем результат
    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=29,
            result=duration.total_seconds(),
            state="completed"
        )
        session.add(result)
        await session.commit()

    # Отправляем отчет администратору
    report = (f"📸 Результат квеста 29\n"
              f"👤 Пользователь: {callback.from_user.full_name}\n"
              f"⏱ Время выполнения: {duration.total_seconds() / 60:.1f} мин\n"
              f"📷 Количество фото: {len(user_data.get('photos', []))}")

    await callback.bot.send_message(admin_chat_id, report)

    # Сообщение пользователю
    await callback.message.answer(
        f"Фотоохота завершена!\n"
        f"Время выполнения: {duration.total_seconds() / 60:.1f} минут\n"
        f"Отправьте лучшие фото на модерацию.",
        reply_markup=get_quest_finish_keyboard(1, 1, 29)
    )

    await state.clear()


# ====================== КВЕСТ 30 - ПОЛНЫЙ ЦИКЛ ======================

async def quest_30(callback: types.CallbackQuery, state: FSMContext):
    """Квест на прохождение полного цикла работы с клиентом"""
    steps = [
        "Привет! На связи ***! Я расскажу тебе, как ловко забирать деньги из карманов наших клиентов...",
        "Для начала давай определимся, что ты должен выглядеть опрятно...",
        "А еще ты должен быть уверен в себе! Представь, что ты не просто фотограф...",
        "Вот ты уже опрятный и уверенный! Отправляйся в фотозону...",
        "А дальше ты должен понять, что продажа начинается задолго до того, как готова продукция...",
        "Не забывай улыбаться, но делай это искренне! Получай кайф от процесса!...",
        "Когда ты узнал имя ребенка приступай к фотосессии...",
        "После того, как ты пофотографировал гостей, не забудь сказать, где...",
        "Помни про УВЕРЕННОСТЬ! Не стесняйся презентовать фотографии...",
        "Как только провели презентацию и гость выбрал фотографии, старайся продать еще!...",
        "Ты сделал продажу! Повторяй все эти действия..."
    ]

    msg = await callback.message.answer(
        steps[0],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее →", callback_data="next_step_30")]
        ])
    )

    await state.update_data(
        steps=steps,
        current_step=0,
        message_id=msg.message_id,
        sold_amount=0
    )
    await state.set_state(QuestState.waiting_full_cycle_step)

@router.callback_query(F.data == "next_step_30", QuestState.waiting_full_cycle_step)
async def next_step_30(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик перехода между шагами квеста 30"""
    user_data = await state.get_data()
    current_step = user_data["current_step"] + 1
    steps = user_data["steps"]

    if current_step >= len(steps):
        # Завершаем квест
        await finish_full_cycle_quest(callback, state)
        return

    # Обновляем сообщение с новым шагом
    await callback.message.edit_text(
        steps[current_step],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее →", callback_data="next_step_30")]
        ])
    )

    await state.update_data(current_step=current_step)
    await callback.answer()

    async def finish_full_cycle_quest(callback: types.CallbackQuery, state: FSMContext):
        """Завершение квеста 30"""
        user_data = await state.get_data()

        # Сохраняем результат
        async with SessionLocal() as session:
            result = UserResult(
                user_id=callback.from_user.id,
                quest_id=30,
                result=user_data.get("sold_amount", 0),
                state="completed"
            )
            session.add(result)
            await session.commit()

        # Отправляем отчет администратору
        report = (f"🔄 Результат квеста 30\n"
                  f"👤 Пользователь: {callback.from_user.full_name}\n"
                  f"💰 Продано: {user_data.get('sold_amount', 0)}")

        await callback.bot.send_message(admin_chat_id, report)

        # Сообщение пользователю
        await callback.message.answer(
            "Поздравляю! Ты прошел полный цикл работы с клиентом.\n"
            "Теперь попробуй сделать это в реальных условиях!",
            reply_markup=get_quest_finish_keyboard(1, 1, 30)
        )

        await state.clear()

# ====================== КВЕСТ 31 - ЦЕННОСТЬ КАДРА ======================

async def quest_31(callback: types.CallbackQuery, state: FSMContext):
    """Квест с лекцией и тестом о ценности кадра"""
    try:
        video_path = BASE_DIR / "assets/quest31/lecture.mp4"
        video = FSInputFile(video_path)

        msg = await callback.message.answer_video(
            video=video,
            caption="🎬 Лекция о ценности кадра в фотографии",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Начать тест", callback_data="start_quiz_31")]
            ])
        )

        await state.update_data(
            message_id=msg.message_id,
            correct_answers=0
        )
        await state.set_state(QuestState.waiting_quiz_start)

    except Exception as e:
        logging.error(f"Error in quest_31: {e}")
        await callback.message.answer("Произошла ошибка при загрузке видео")

@router.callback_query(F.data == "start_quiz_31", QuestState.waiting_quiz_start)
async def start_quiz_31(callback: types.CallbackQuery, state: FSMContext):
    """Начинает тест после лекции"""
    questions = [
        {
            "text": "1. Что такое 'ценность кадра' в фотографии?",
            "options": [
                "A) Количество пикселей",
                "B) Эмоции и смысл",
                "C) Цена камеры",
                "D) Тип объектива"
            ],
            "correct": 1
        },
        {
            "text": "2. Какое правило помогает выстроить композицию?",
            "options": [
                "A) Золотое сечение",
                "B) Центральное размещение",
                "C) Правило третей",
                "D) Параллельные линии"
            ],
            "correct": 2
        },
        {
            "text": "3. Что важнее в портретной фотографии?",
            "options": [
                "A) Резкость по всему кадру",
                "B) Передача эмоций",
                "C) Сложный фон",
                "D) Много аксессуаров"
            ],
            "correct": 1
        }
    ]

    # Удаляем предыдущее сообщение
    user_data = await state.get_data()
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
    except:
        pass

    # Отправляем первый вопрос
    msg = await callback.message.answer(
        questions[0]["text"],
        reply_markup=create_quiz_keyboard(questions[0]["options"], "quest31")
    )

    await state.update_data(
        questions=questions,
        current_question=0,
        quiz_message_id=msg.message_id
    )
    await state.set_state(QuestState.waiting_quiz_answer)

def create_quiz_keyboard(options: List[str], prefix: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для теста"""
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        builder.button(text=option.split(")")[0], callback_data=f"{prefix}_{i}")
    builder.adjust(2)
    return builder.as_markup()

@router.callback_query(F.data.startswith("quest31_"), QuestState.waiting_quiz_answer)
async def handle_quiz_answer_31(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик ответов в тесте"""
    user_data = await state.get_data()
    current_q = user_data["current_question"]
    questions = user_data["questions"]
    selected = int(callback.data.split("_")[1])

    is_correct = selected == questions[current_q]["correct"]
    new_data = {"correct_answers": user_data["correct_answers"] + int(is_correct)}

    # Удаляем предыдущее сообщение
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["quiz_message_id"])
    except:
        pass

    # Показываем результат
    result_text = "✅ Верно!" if is_correct else "❌ Неверно!"
    await callback.message.answer(result_text)

    # Переход к следующему вопросу или завершение
    if current_q + 1 < len(questions):
        next_q = current_q + 1
        msg = await callback.message.answer(
            questions[next_q]["text"],
            reply_markup=create_quiz_keyboard(questions[next_q]["options"], "quest31")
        )

        new_data.update({
            "current_question": next_q,
            "quiz_message_id": msg.message_id
        })
        await state.update_data(**new_data)
    else:
        await finish_quest(callback, state, new_data["correct_answers"], len(questions), 31)

# ====================== ОСТАЛЬНЫЕ КВЕСТЫ ДНЯ 3 ======================

# Квест 32 - Ценности компании
async def quest_32(callback: types.CallbackQuery, state: FSMContext):
    """Квест на изучение ценностей компании"""
    values = (
        "Ценности компании LiveFoto:\n\n"
        "1. Честность - мы всегда говорим правду клиентам\n"
        "2. Ответственность - выполняем обещания\n"
        "3. Профессионализм - постоянно развиваемся\n"
        "4. Клиентоориентированность - ставим клиента на первое место\n"
        "5. Командность - работаем вместе для общего результата"
    )

    msg = await callback.message.answer(
        values,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать игру", callback_data="start_game_32")]
        ]))

    await state.update_data(
        message_id=msg.message_id,
        correct_answers=0
    )
    await state.set_state(QuestState.waiting_game_start)

@router.callback_query(F.data == "start_game_32", QuestState.waiting_game_start)
async def start_game_32(callback: types.CallbackQuery, state: FSMContext):
    """Начинает игру на соответствие ценностям"""
    scenarios = [
        {
            "text": "Ситуация 1: Коллега предлагает разделить найденные деньги в фотозоне...",
            "options": [
                "Честность - напомнить о ценностях",
                "Ответственность - проконтролировать",
                "Работа в команде - разделить"
            ],
            "correct": 0
        },
        {
            "text": "Ситуация 2: Клиент просит сделать скидку без причины...",
            "options": [
                "Клиентоориентированность - согласиться",
                "Профессионализм - объяснить цену",
                "Командность - спросить у менеджера"
            ],
            "correct": 1
        }
    ]

    # Удаляем предыдущее сообщение
    user_data = await state.get_data()
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
    except:
        pass

    # Отправляем первый сценарий
    msg = await callback.message.answer(
        scenarios[0]["text"],
        reply_markup=create_quiz_keyboard(scenarios[0]["options"], "quest32")
    )

    await state.update_data(
        scenarios=scenarios,
        current_scenario=0,
        game_message_id=msg.message_id
    )
    await state.set_state(QuestState.waiting_game_answer)

@router.callback_query(F.data.startswith("quest32_"), QuestState.waiting_game_answer)
async def handle_game_answer_32(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик ответов в игре"""
    user_data = await state.get_data()
    current_scenario = user_data["current_scenario"]
    scenarios = user_data["scenarios"]
    selected = int(callback.data.split("_")[1])

    is_correct = selected == scenarios[current_scenario]["correct"]
    new_data = {"correct_answers": user_data["correct_answers"] + int(is_correct)}

    # Удаляем предыдущее сообщение
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["game_message_id"])
    except:
        pass

    # Показываем результат
    result_text = "✅ Верный выбор!" if is_correct else "❌ Это не лучший вариант"
    await callback.message.answer(result_text)

    # Переход к следующему сценарию или завершение
    if current_scenario + 1 < len(scenarios):
        next_scenario = current_scenario + 1
        msg = await callback.message.answer(
            scenarios[next_scenario]["text"],
            reply_markup=create_quiz_keyboard(scenarios[next_scenario]["options"], "quest32")
        )

        new_data.update({
            "current_scenario": next_scenario,
            "game_message_id": msg.message_id
        })
        await state.update_data(**new_data)
    else:
        await finish_quest(callback, state, new_data["correct_answers"], len(scenarios), 32)

# Квест 33 - Клиент (аналогичен квесту 29)
async def quest_33(callback: types.CallbackQuery, state: FSMContext):
    """Квест на взаимодействие с клиентами"""
    msg = await callback.message.answer(
        "👥 Работа с клиентами\n\n"
        "Твоя задача пообщаться с 5 разными клиентами и сделать их фотографии.\n\n"
        "Требования:\n"
        "- Узнай имя каждого клиента\n"
        "- Сделай минимум 3 кадра каждого\n"
        "- Получи разрешение на использование фото",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_client_quest_33")]
        ]))

    await state.update_data(
        message_id=msg.message_id,
        clients=0,
        photos=[]
    )
    await state.set_state(QuestState.waiting_client_start)

@router.callback_query(F.data == "start_client_quest_33", QuestState.waiting_client_start)
async def start_client_quest_33(callback: types.CallbackQuery, state: FSMContext):
    """Начинает квест с клиентами"""
    # Удаляем предыдущее сообщение
    user_data = await state.get_data()
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
    except:
        pass

    await callback.message.answer(
        "Отлично! Начинаем взаимодействие с клиентами. "
        "Присылай фото и имена клиентов по мере выполнения.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ЗАВЕРШИТЬ", callback_data="finish_client_quest_33")]
        ]))

    await state.update_data(start_time=datetime.datetime.now())
    await callback.answer("Квест начат! Удачи в общении с клиентами!")

@router.callback_query(F.data == "finish_client_quest_33", QuestState.waiting_client_start)
async def finish_client_quest_33(callback: types.CallbackQuery, state: FSMContext):
    """Завершает квест с клиентами"""
    user_data = await state.get_data()

    if user_data.get("clients", 0) < 3:  # Минимум 3 клиента
        await callback.answer("Нужно пообщаться хотя бы с 3 клиентами!", show_alert=True)
        return

    # Сохраняем результат
    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=33,
            result=user_data.get("clients", 0),
            state="completed"
        )
        session.add(result)
        await session.commit()

    # Отправляем отчет администратору
    report = (f"👥 Результат квеста 33\n"
              f"👤 Пользователь: {callback.from_user.full_name}\n"
              f"🔄 Обработано клиентов: {user_data.get('clients', 0)}\n"
              f"📷 Сделано фото: {len(user_data.get('photos', []))}")

    await callback.bot.send_message(admin_chat_id, report)

    # Сообщение пользователю
    await callback.message.answer(
        f"Отличная работа! Ты пообщался с {user_data.get('clients', 0)} клиентами.\n"
        "Отправь лучшие фото на модерацию.",
        reply_markup=get_quest_finish_keyboard(1, 1, 33)
    )

    await state.clear()

# Квест 34 - Фидбек
async def quest_34(callback: types.CallbackQuery, state: FSMContext):
    """Финальный квест с фидбеком"""
    questions = [
        {
            "text": "Как вам понравился формат обучения с элементами игры?",
            "type": "options",
            "options": [
                "Очень понравился",
                "Понравился",
                "Нейтрально",
                "Не понравился"
            ]
        },
        {
            "text": "Какие задания были для вас наиболее интересными и полезными?",
            "type": "text"
        },
        {
            "text": "Что бы вы улучшили в процессе обучения?",
            "type": "text"
        }
    ]

    msg = await callback.message.answer(
        "📝 Фидбек по обучению\n\n"
        "Пожалуйста, ответьте на несколько вопросов о вашем опыте прохождения обучения.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать опрос", callback_data="start_feedback_34")]
        ]))

    await state.update_data(
        message_id=msg.message_id,
        questions=questions,
        current_question=0,
        answers={}
    )
    await state.set_state(QuestState.waiting_feedback_start)

@router.callback_query(F.data == "start_feedback_34", QuestState.waiting_feedback_start)
async def start_feedback_34(callback: types.CallbackQuery, state: FSMContext):
    """Начинает опрос с фидбеком"""
    user_data = await state.get_data()
    question = user_data["questions"][0]

    # Удаляем предыдущее сообщение
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["message_id"])
    except:
        pass

    if question["type"] == "options":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"answer_34_{i}")]
            for i, opt in enumerate(question["options"])
        ])
    else:
        keyboard = None

    msg = await callback.message.answer(
        question["text"],
        reply_markup=keyboard
    )

    await state.update_data(
        feedback_message_id=msg.message_id
    )
    await state.set_state(QuestState.waiting_feedback_answer)

@router.callback_query(F.data.startswith("answer_34_"), QuestState.waiting_feedback_answer)
async def handle_feedback_answer_34(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик ответов в фидбеке"""
    user_data = await state.get_data()
    current_q = user_data["current_question"]
    questions = user_data["questions"]
    answers = user_data["answers"]

    # Сохраняем ответ
    selected = int(callback.data.split("_")[2])
    answers[current_q] = questions[current_q]["options"][selected]

    # Переход к следующему вопросу
    next_q = current_q + 1
    if next_q >= len(questions):
        await finish_feedback_34(callback, state, answers)
        return

    question = questions[next_q]

    # Удаляем предыдущее сообщение
    try:
        await callback.bot.delete_message(callback.message.chat.id, user_data["feedback_message_id"])
    except:
        pass

    if question["type"] == "options":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"answer_34_{i}")]
            for i, opt in enumerate(question["options"])
        ])
        msg = await callback.message.answer(
            question["text"],
            reply_markup=keyboard
        )
    else:
        msg = await callback.message.answer(
            question["text"] + "\n\nНапишите ваш ответ текстом."
        )

    await state.update_data(
        current_question=next_q,
        answers=answers,
        feedback_message_id=msg.message_id
    )
    await callback.answer()

@router.message(QuestState.waiting_feedback_answer)
async def handle_text_feedback_34(message: types.Message, state: FSMContext):
    """Обработчик текстовых ответов в фидбеке"""
    user_data = await state.get_data()
    current_q = user_data["current_question"]
    questions = user_data["questions"]
    answers = user_data["answers"]

    # Сохраняем ответ
    answers[current_q] = message.text

    # Переход к следующему вопросу
    next_q = current_q + 1
    if next_q >= len(questions):
        await finish_feedback_34(message, state, answers)
        return

    question = questions[next_q]

    # Удаляем предыдущее сообщение
    try:
        await message.bot.delete_message(message.chat.id, user_data["feedback_message_id"])
    except:
        pass

    if question["type"] == "options":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"answer_34_{i}")]
            for i, opt in enumerate(question["options"])
        ])
        msg = await message.answer(
            question["text"],
            reply_markup=keyboard
        )
    else:
        msg = await message.answer(
            question["text"] + "\n\nНапишите ваш ответ текстом."
        )

    await state.update_data(
        current_question=next_q,
        answers=answers,
        feedback_message_id=msg.message_id
    )
    await message.delete()

async def finish_feedback_34(message: Union[types.Message, types.CallbackQuery], state: FSMContext,
                             answers: Dict):
    """Завершает квест с фидбеком"""
    user_data = await state.get_data()

    # Формируем отчет для администратора
    report_text = "📋 Фидбек по обучению:\n\n"
    report_text += f"👤 Сотрудник: {message.from_user.full_name}\n\n"

    for i, (q, a) in enumerate(zip(user_data["questions"], answers.values())):
        report_text += f"{i + 1}. {q['text']}\n"
        report_text += f"➡️ Ответ: {a}\n\n"

    await message.bot.send_message(admin_chat_id, report_text)

    # Сохраняем результат
    async with SessionLocal() as session:
        result = UserResult(
            user_id=message.from_user.id,
            quest_id=34,
            result=1,  # Всегда успешно
            state="completed"
        )
        session.add(result)
        await session.commit()

    # Сообщение пользователю
    await message.answer(
        "Спасибо за ваши ответы! Ваше мнение очень важно для нас.",
        reply_markup=get_quest_finish_keyboard(1, 1, 34)
    )

    await state.clear()