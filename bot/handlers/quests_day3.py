from aiogram import Router, types, F
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
import datetime
import logging
from pathlib import Path
import os

# Импорты из вашего проекта
from bot.db.models import UserResult
from bot.db.session import SessionLocal
from bot.keyboards.inline import get_quest_finish_keyboard
from .states import QuestState
from bot.configurate import settings

router = Router()
admin_chat_id = settings.ADMIN_ID
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Путь к корню проекта


# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================

def build_media_group(files, captions=None):
    """Создает медиагруппу из файлов"""
    builder = MediaGroupBuilder()
    for i, file in enumerate(files):
        caption = str(i + 1) if captions is None else captions[i]
        if str(file).endswith(('.jpg', '.jpeg', '.png')):
            builder.add_photo(media=file, caption=caption)
        elif str(file).endswith('.mp4'):
            builder.add_video(media=file, caption=caption)
    return builder


def create_options_keyboard(options, prefix):
    """Создает клавиатуру с вариантами ответов"""
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options, start=1):
        builder.button(text=str(i), callback_data=f"{prefix}_{i}")
    builder.adjust(3)  # 3 кнопки в ряд
    return builder.as_markup()


# ====================== КВЕСТ 27 - ПРАВИЛЬНОЕ ФОТО ======================

async def quest_27(callback: types.CallbackQuery, state: FSMContext):
    questions = [
        {
            "text": "Какое фото пересвечено?",
            "media": [
                FSInputFile(BASE_DIR / "assets/quest27/photo1.jpg"),
                FSInputFile(BASE_DIR / "assets/quest27/photo2.jpg"),
                FSInputFile(BASE_DIR / "assets/quest27/photo3.jpg")
            ],
            "correct": 2,
            "feedback": {
                "correct": "Прекрасный загар и верный ответ!",
                "wrong": "Модель получила ожог, ответ не верный"
            }
        },
        # Добавьте остальные вопросы аналогично
    ]

    try:
        # Отправляем медиагруппу
        media_group = build_media_group(questions[0]["media"])
        messages = await callback.message.answer_media_group(media=media_group.build())
        message_ids = [m.message_id for m in messages]

        # Отправляем вопрос с кнопками
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
    else:
        await finish_quest27(callback, state, new_data["correct_answers"])
        return

    await state.update_data(**new_data)


async def finish_quest27(callback: types.CallbackQuery, state: FSMContext, correct_answers: int):
    total_questions = 3  # Общее количество вопросов

    # Сохраняем результат в БД
    async with SessionLocal() as session:
        result = UserResult(
            user_id=callback.from_user.id,
            quest_id=27,
            result=correct_answers,
            state="completed"
        )
        session.add(result)
        await session.commit()

    # Отправляем отчет администратору
    report = (f"📊 Результат квеста 27\n"
              f"👤 Пользователь: {callback.from_user.full_name}\n"
              f"✅ Правильных ответов: {correct_answers}/{total_questions}")

    await callback.bot.send_message(admin_chat_id, report)

    # Сообщение пользователю
    await callback.message.answer(
        f"Вы ответили правильно на {correct_answers} из {total_questions} вопросов!",
        reply_markup=get_quest_finish_keyboard(correct_answers, total_questions, 27)
    )

    await state.clear()


# ====================== КВЕСТ 28 - СОБЕРИ ВСЕ ======================

async def quest_28(callback: types.CallbackQuery, state: FSMContext):
    try:
        video = FSInputFile(BASE_DIR / "assets/quest28/assembly_video.mp4")

        msg = await callback.message.answer_video(
            video=video,
            caption="Твоя задача собрать 6 магнитов как можно быстрее. Нажми СТАРТ для начала.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="СТАРТ", callback_data="start_assembly")]
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


@router.callback_query(F.data == "start_assembly", QuestState.waiting_assembly_start)
async def start_assembly(callback: types.CallbackQuery, state: FSMContext):
    start_time = datetime.datetime.now()

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ФИНИШ", callback_data="finish_assembly")]
        ])
    )

    await state.update_data(start_time=start_time)
    await callback.answer("Таймер запущен! Собирайте магниты!")


@router.callback_query(F.data == "finish_assembly", QuestState.waiting_assembly_start)
async def finish_assembly(callback: types.CallbackQuery, state: FSMContext):
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

    # Отправляем отчет
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

# Квест 28 - Собери все
async def quest_28(callback: types.CallbackQuery, state: FSMContext):
    video_url = "video_url_here"

    message = await callback.message.answer_video(
        video_url,
        caption="Твоя задача собрать 6 магнитов как можно быстрее. Нажми СТАРТ для начала.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_assembly")]
        ])
    )

    await state.update_data(
        start_time=None,
        message_id=message.message_id
    )


# Квест 29 - Фотоохота
async def quest_29(callback: types.CallbackQuery, state: FSMContext):
    recommendations = """
    Рекомендации по работе в фотозоне:
    1. Проверь настройки фотоаппарата
    2. Ищи интересные ракурсы
    3. Установи доверительные отношения
    4. Лови спонтанные моменты
    5. Делай разнообразные снимки
    """

    message = await callback.message.answer(
        "Твоя задача принести как можно больше фотографий за 15 минут.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Рекомендации", callback_data="show_recommendations")],
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_photo_hunt")]
        ])
    )

    await state.update_data(
        timer_start=None,
        photos=[],
        message_id=message.message_id,
        recommendations=recommendations
    )


# Квест 30 - Полный цикл
async def quest_30(callback: types.CallbackQuery, state: FSMContext):
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

    message = await callback.message.answer(
        steps[0],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Круто!", callback_data="next_step_30")]
        ])
    )

    await state.update_data(
        steps=steps,
        current_step=0,
        message_id=message.message_id,
        sold_amount=0
    )


# Обработчики для квеста 27
@router.callback_query(F.data.startswith("quest27_"), QuestState.waiting_for_photo_answer)
async def handle_photo_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data["current_question"]
    questions = user_data["questions"]

    selected = int(callback.data.split("_")[1])
    is_correct = selected == questions[current_question]["correct"]

    # Удаляем предыдущие фото и вопрос
    for msg_id in user_data["message_ids"]:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except:
            pass

    # Показываем результат
    result_text = questions[current_question]["success"] if is_correct else questions[current_question]["fail"]
    await callback.message.answer(result_text)

    # Переходим к следующему вопросу или завершаем
    if current_question + 1 < len(questions):
        next_question = current_question + 1
        message = await callback.message.answer_media_group([
            InputMediaPhoto(media=questions[next_question]["photo1"], caption="1"),
            InputMediaPhoto(media=questions[next_question]["photo2"], caption="2"),
            InputMediaPhoto(media=questions[next_question]["photo3"], caption="3")
        ])

        question_msg = await callback.message.answer(
            questions[next_question]["text"],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="1", callback_data="quest27_1")],
                [InlineKeyboardButton(text="2", callback_data="quest27_2")],
                [InlineKeyboardButton(text="3", callback_data="quest27_3")]
            ])
        )

        await state.update_data(
            current_question=next_question,
            message_ids=[m.message_id for m in message] + [question_msg.message_id]
        )
    else:
        await finish_quest27(callback, state)


# Обработчики для квеста 28
@router.callback_query(F.data == "start_assembly")
async def start_assembly(callback: types.CallbackQuery, state: FSMContext):
    start_time = datetime.datetime.now()

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="ФИНИШ", callback_data="finish_assembly")]
        ])
    )

    await state.update_data(start_time=start_time)
    await callback.answer("Таймер запущен!")


@router.callback_query(F.data == "finish_assembly")
async def finish_assembly(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    end_time = datetime.datetime.now()
    duration = end_time - user_data["start_time"]

    await callback.message.answer(
        f"Поздравляю новый отличный результат: {duration.total_seconds():.2f} секунд!\n"
        "Отправь видео на модерацию."
    )

    await state.clear()


# Обработчики для квеста 29
@router.callback_query(F.data == "start_photo_hunt")
async def start_photo_hunt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТОП", callback_data="stop_photo_hunt")],
            [InlineKeyboardButton(text="Нет людей", callback_data="no_people")],
            [InlineKeyboardButton(text="Все отказались", callback_data="all_refused")],
            [InlineKeyboardButton(text="Свой вариант", callback_data="custom_reason")]
        ])
    )

    await state.update_data(timer_start=datetime.datetime.now())
    await callback.answer("Таймер запущен! У вас 15 минут")

# Остальные обработчики и функции завершения квестов аналогичны предыдущим примерам

# Квест 31 - Ценность кадра
async def quest_31(callback: types.CallbackQuery, state: FSMContext):
    video_url = "video_lecture_url_here"

    message = await callback.message.answer_video(
        video_url,
        caption="Лекция о ценности кадра в фотографии",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее", callback_data="start_quiz_31")]
        ])
    )

    await state.update_data(
        message_id=message.message_id,
        correct_answers=0
    )

@router.callback_query(F.data == "start_quiz_31")
async def start_quiz_31(callback: types.CallbackQuery, state: FSMContext):
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
        # Остальные вопросы аналогично
    ]

    message = await callback.message.answer(
        questions[0]["text"],
        reply_markup=quest31_keyboard(questions[0])
    )

    await state.update_data(
        questions=questions,
        current_question=0,
        quiz_message_id=message.message_id
    )

# Квест 32 - Ценности компании
async def quest_32(callback: types.CallbackQuery, state: FSMContext):
    message = await callback.message.answer(
        "Ценности компании — это правила, показывающие, как она работает...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Хочу узнать ценности!", callback_data="show_values_32")]
        ]))

    await state.update_data(
        message_id=message.message_id,
        correct_answers=0
    )

@router.callback_query(F.data == "show_values_32")
async def show_values_32(callback: types.CallbackQuery, state: FSMContext):
    message = await callback.message.answer(
        "Ценностями компании LiveFoto являются: честность, ответственность...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать игру", callback_data="start_game_32")]
        ])
    )

    await state.update_data(
        values_message_id=message.message_id
    )

# Квест 33 - Фотоохота (аналогично квесту 29)
async def quest_33(callback: types.CallbackQuery, state: FSMContext):
    message = await callback.message.answer(
        "Твоя задача сделать как можно больше интересных кадров...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="СТАРТ", callback_data="start_hunting_33")]
        ])
    )

    await state.update_data(
        message_id=message.message_id,
        photos=[]
    )

# Квест 34 - Фидбек
async def quest_34(callback: types.CallbackQuery, state: FSMContext):
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
        # Остальные вопросы аналогично
    ]

    message = await callback.message.answer(
        "Дорогой друг, ответь пожалуйста на несколько вопросов...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать помогать", callback_data="start_feedback_34")]
        ])
    )

    await state.update_data(
        message_id=message.message_id,
        questions=questions,
        current_question=0,
        answers={}
    )

@router.callback_query(F.data == "start_feedback_34")
async def start_feedback_34(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    question = user_data["questions"][0]

    if question["type"] == "options":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"answer_34_{i}")]
            for i, opt in enumerate(question["options"])
        ])
    else:
        keyboard = None

    message = await callback.message.answer(
        question["text"],
        reply_markup=keyboard
    )

    await state.update_data(
        feedback_message_id=message.message_id
    )
    await state.set_state(QuestState.waiting_for_feedback_answer)

# Обработчики для квеста 31
@router.callback_query(F.data.startswith("answer31_"))
async def handle_quiz_answer31(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data["current_question"]
    questions = user_data["questions"]
    selected = int(callback.data.split("_")[1])

    is_correct = selected == questions[current_question]["correct"]

    if is_correct:
        await state.update_data(correct_answers=user_data["correct_answers"] + 1)

    # Показываем следующий вопрос или завершаем
    if current_question + 1 < len(questions):
        next_question = current_question + 1
        await callback.message.edit_text(
            questions[next_question]["text"],
            reply_markup=quest31_keyboard(questions[next_question])
        )
        await state.update_data(current_question=next_question)
    else:
        await finish_quiz31(callback, state)

# Обработчики для квеста 32
@router.callback_query(F.data == "start_game_32")
async def start_game_32(callback: types.CallbackQuery, state: FSMContext):
    scenarios = [
        {
            "text": "Ситуация 1: Коллега предлагает разделить найденные деньги...",
            "options": [
                "Честность — напомнить о ценностях",
                "Ответственность — проконтролировать",
                "Работа в команде — разделить"
            ],
            "correct": 1
        },
        # Остальные сценарии аналогично
    ]

    message = await callback.message.answer(
        scenarios[0]["text"],
        reply_markup=quest32_keyboard(scenarios[0])
    )

    await state.update_data(
        scenarios=scenarios,
        current_scenario=0,
        game_message_id=message.message_id
    )

# Функции завершения квестов
async def finish_quiz31(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    correct = user_data["correct_answers"]
    total = len(user_data["questions"])

    if correct == total:
        await callback.message.answer_animation(
            "success_animation_url",
            caption="Красавчик! Все ответы верные!"
        )
    else:
        await callback.message.answer(
            f"Тебе стоит поработать над {total - correct} вопросами",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Начать заново", callback_data="start_quiz_31")],
                [InlineKeyboardButton(text="Далее", callback_data="next_quest")]
            ])
        )

    await state.clear()

async def finish_quest34(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    # Формируем отчет для администратора
    report_text = "📋 Фидбек по обучению:\n\n"
    report_text += f"👤 Сотрудник: {message.from_user.full_name}\n"

    for i, answer in user_data["answers"].items():
        report_text += f"{i + 1}. {user_data['questions'][i]['text']}\n"
        report_text += f"Ответ: {answer}\n\n"

    await message.bot.send_message(admin_chat_id, report_text)
    await message.answer("Спасибо за ответы!")
    await state.clear()

