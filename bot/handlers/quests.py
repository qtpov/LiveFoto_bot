from aiogram import Router, types, F
from aiogram.types import  FSInputFile
from bot.db.models import UserResult, User, Achievement
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline import *
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from aiogram.utils.media_group import MediaGroupBuilder,InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pathlib import Path
from .moderation import give_achievement, get_quest_finish_keyboard
from bot.db.crud import update_user_level, update_user_day
import datetime
from random import shuffle, randint
import os
from .states import QuestState
from bot.configurate import settings
from .quests_day2 import *
from .quests_day3 import *

router = Router()

admin_chat_id = settings.ADMIN_ID


# Словарь с правильными ответами для каждого вопроса
correct_answers = {
    1: "base",
    2: "stand",
    3: "entrance",
    4: "food-court",
    5: "toilet"
}

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

correct_answers_qw3 = {
    1: 'Сборка техники',
    2: 'Фотографирование',
    3: 'Ретушь',
    4: 'Печать',
    5: 'Презентация'

}

# Базовый путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent



# Обработчик нажатия на кнопку "Переделать"
@router.callback_query(F.data.startswith("retry_quest_"))
async def retry_quest(callback: types.CallbackQuery, state: FSMContext):
    quest_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    # Обновляем статус квеста в базе данных
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == user_id,
                UserResult.quest_id == quest_id
            )
        )
        user_result = user_result.scalars().first()

        if user_result:
            user_result.state = "не выполнен"
            user_result.attempt +=1
            user_result.result = 0  # Обнуляем счетчик верных ответов
            await session.commit()

    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    photo_message_ids = user_data.get("photo_message_ids", [])
    question_message_id = user_data.get("question_message_id")

    await callback.message.delete()

    # Обновляем состояние и начинаем квест заново
    await state.update_data(current_question=1, correct_count=0)
    await globals()[f"quest_{quest_id}"](callback, state)
    await callback.answer()


# Обработчик нажатия на кнопку "Далее"
@router.callback_query(F.data.startswith("next_quest_"))
async def next_quest(callback: types.CallbackQuery, state: FSMContext):
    current_quest_id = int(callback.data.split("_")[-1])
    current_day = await get_current_day(callback.from_user.id)
    quests_today = quests_by_day.get(current_day, [])
    next_quest_id = None

    # Удаляем сообщение с результатами
    try:
        user_data = await state.get_data()
        question_message_id = user_data.get("question_message_id")
        await callback.message.delete()
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Находим следующий невыполненный квест
    for quest_id, _ in quests_today:
        if quest_id > current_quest_id:
            next_quest_id = quest_id
            break

    if next_quest_id:
        # Явно сбрасываем состояние и устанавливаем новые параметры
        await state.clear()
        await state.update_data(
            current_quest_id=next_quest_id,
            current_question=1,
            correct_count=0
        )
        await state.set_state(QuestState.waiting_for_answer)

        # Запускаем новый квест
        await globals()[f"quest_{next_quest_id}"](callback, state)
        await track_quest_time(callback.from_user.id, next_quest_id, is_start=True, state=state)
    else:
        await callback.message.answer("🔥 Вау, ты прошёл все квесты! Смотри-ка, сколько у тебя ачивок — настоящий чемпион! 🏆🎉\n"
                                      "Но расслабляться рано — впереди ещё МИНИ-ИГРЫ для прокачки и БАЗА ЗНАНИЙ для апгрейда навыков.\n"
                                      "Жми, выбирай, прокачивайся дальше — приключения только начинаются! 🚀📸",
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                          [InlineKeyboardButton(text="👉 ПРОФИЛЬ",
                                                                callback_data="profile")],
                                          [InlineKeyboardButton(text="👉 МИНИ-ИГРЫ",
                                                                callback_data="games")],
                                          [InlineKeyboardButton(text="👉 БАЗА ЗНАНИЙ",
                                                                callback_data="knowledge")]
                                      ])
                                      )
        await state.clear()

    await callback.answer()

# Функция для вывода списка квестов
async def show_today_quests(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    current_day = await get_current_day(user_id)

    if not current_day:
        await callback.message.answer("Ты ещё не зарегистрирован! Напиши /start.")
        return

    async with SessionLocal() as session:
        # Получаем квесты на сегодня
        quests_today = quests_by_day.get(current_day, [])
        user_results = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == user_id,
                UserResult.quest_id.in_([quest[0] for quest in quests_today])
            )
        )
        user_results = user_results.scalars().all()
        user_results_dict = {result.quest_id: result for result in user_results}

        # Формируем текст с квестами и их статусами
        quests_text = "📜 Квесты на сегодня:\n"
        for quest_id, quest_name in quests_today:
            status = "ещё нет"
            if quest_id in user_results_dict:
                if user_results_dict[quest_id].state == "выполнен":
                    status = "✅"
                if user_results_dict[quest_id].state == "на модерации":
                    status = "🕒 На модерации"
            quests_text += f"{quest_id}. {quest_name} — {status}\n"
        quests_text += '👉 Готов/а квестить?'
        # Отправляем сообщение с квестами
        await callback.message.edit_text(quests_text, reply_markup=quests_list_keyboard())


# Обработчик кнопки "Квесты"
@router.callback_query(F.data == "quests")
async def handle_quests_button(callback: types.CallbackQuery, state: FSMContext):
    # Показываем список квестов на сегодня
    await show_today_quests(callback, state)
    await callback.answer()


# Общая функция для запуска квестов
async def start_quest(callback: types.CallbackQuery, state: FSMContext, quest_id: int):
    await state.set_state(QuestState.waiting_for_answer)
    await state.update_data(current_question=1, correct_count=0, current_quest_id=quest_id)

    await track_quest_time(callback.from_user.id, quest_id, is_start=True, state=state)

    await globals()[f"quest_{quest_id}"](callback, state)

# Обработчик кнопки "Начать квесты"
@router.callback_query(F.data == "start_quests_confirm")
async def start_quests_confirm(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    current_day = await get_current_day(user_id)

    if not current_day:
        await callback.message.answer("Ты ещё не зарегистрирован! Напиши /start.")
        return

    async with SessionLocal() as session:
        quests_today = quests_by_day.get(current_day, [])
        user_results = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == user_id,
                UserResult.quest_id.in_([quest[0] for quest in quests_today])
            )
        )
        user_results = user_results.scalars().all()
        user_results_dict = {result.quest_id: result for result in user_results}

        # Находим первый невыполненный квест
        first_uncompleted_quest = None
        for quest_id, _ in quests_today:
            if quest_id not in user_results_dict or user_results_dict[quest_id].state != "выполнен":
                first_uncompleted_quest = quest_id
                break

        if first_uncompleted_quest is None:
            await callback.message.answer(
                "🔥 Вау, ты прошёл все квесты! Смотри-ка, сколько у тебя ачивок — настоящий чемпион! 🏆🎉\n"
                "Но расслабляться рано — впереди ещё МИНИ-ИГРЫ для прокачки и БАЗА ЗНАНИЙ для апгрейда навыков.\n"
                "Жми, выбирай, прокачивайся дальше — приключения только начинаются! 🚀📸",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="👉 ПРОФИЛЬ",
                                          callback_data="profile")],
                    [InlineKeyboardButton(text="👉 МИНИ-ИГРЫ",
                                          callback_data="games")],
                    [InlineKeyboardButton(text="👉 БАЗА ЗНАНИЙ",
                                          callback_data="knowledge")]
                ])
                )
            return

        # Начинаем первый невыполненный квест
        await start_quest(callback, state, first_uncompleted_quest)
    await callback.answer()

# Квест 1
async def quest_1(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)

    # # Удаляем предыдущее сообщение, если оно есть
    # if "photo_message_id" in user_data:
    #     await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=user_data["photo_message_id"])
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")


    photo_path = BASE_DIR / "handlers/media/photo/map1.jpg"
    if not photo_path.exists():
        await callback.message.answer("Файл с изображением не найден.")
        return

    photo = FSInputFile(str(photo_path))


    # Отправляем новое сообщение с фото
    message = await callback.message.answer_photo(
        photo,
        caption=f"🎮 Квест 1: Вопрос {current_question}\n"
                f"Взгляни на карту и ответь: Что находится под номером {current_question}? 🤔👇",
        reply_markup=quest1_keyboard()
    )
    await state.update_data(photo_message_id=message.message_id)

    await callback.answer()

# Квест 2 - Добавлены уникальные описания
quest2_descriptions = {
    1: "Угадай, где сделано это яркое фото 🎉\nВыбирай снизу, не зевай 👇",
    2: "Где тут наш герой зависает в шариках? 🎯\nПора применить детективный скилл 🔎",
    3: "Две пушки — это уже серьёзно 😎\nГде проходила перестрелка?",
    4: "Красный трон, королевская подача 💅\nГде снимок?",
    5: "Милота уровня 💯\nВ какой зоне тусит малыш?",
    6: "Снова она, королева батутов 🏃‍♀️\nГде сделан этот кадр?",
    7: "Деньги, власть, корона... всё при нём 🤑\nА ты узнаешь локацию?",
    8: "Тот случай, когда и в трубе, и в шариках кайфово 😄\nГде фоткались?",
    9: "Нежность, яркие цвета, мини-качели — где это? 🧸\nТы уже шаришь 💡",
    10: "Паук, супергерои и рождественский вайб 🎄\nГде снимали эту крутую серию?"
}
async def quest_2(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)

    # Инициализируем список использованных фото, если его нет
    if "used_photos" not in user_data:
        await state.update_data(used_photos={})

    # Удаляем предыдущие сообщения, если они есть
    try:
        photo_message_ids = user_data.get("photo_message_ids", [])
        question_message_id = user_data.get("question_message_id")
        await callback.message.delete()
        for message_id in photo_message_ids:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    folder_name = correct_answers_qw2[current_question]
    photo_dir = BASE_DIR / f"handlers/media/photo/Zone/{folder_name}"

    # Получаем список всех доступных фото
    all_photos = list(photo_dir.glob("*.jpg"))
    if len(all_photos) < 2:
        raise ValueError(f"Недостаточно фотографий в папке {folder_name} (нужно минимум 2)")

    # Получаем список уже использованных фото для этой папки
    used_photos = user_data.get("used_photos", {}).get(folder_name, [])

    # Выбираем только те фото, которые еще не использовались
    available_photos = [p for p in all_photos if p.name not in used_photos]

    # Если доступных фото меньше 2, сбрасываем историю для этой папки
    if len(available_photos) < 2:
        available_photos = all_photos
        used_photos = []

    # Выбираем 2 случайных фото
    shuffle(available_photos)
    selected_photos = available_photos[:2]

    # Обновляем список использованных фото
    used_photos.extend([p.name for p in selected_photos])
    updated_used_photos = user_data.get("used_photos", {})
    updated_used_photos[folder_name] = used_photos
    await state.update_data(used_photos=updated_used_photos)

    # Проверяем существование файлов
    if not all(p.exists() for p in selected_photos):
        await callback.message.answer("Файлы с изображениями не найдены.")
        return

    # Создаем медиагруппу
    album_builder = MediaGroupBuilder(
        caption=f"📸 Квест 2: Вопрос {current_question}\n{quest2_descriptions[current_question]}"
    )
    for photo_path in selected_photos:
        album_builder.add(type="photo", media=FSInputFile(str(photo_path)))

    # Отправляем медиагруппу
    photo_messages = await callback.message.answer_media_group(media=album_builder.build())
    photo_message_ids = [msg.message_id for msg in photo_messages]

    question_message = await callback.message.answer(
        "Выбери нужный вариант из кнопок",
        reply_markup=quest2_keyboard()
    )

    # Сохраняем ID всех сообщений для последующего удаления
    await state.update_data(
        photo_message_ids=photo_message_ids,
        question_message_id=question_message.message_id
    )
    await callback.answer()



# Квест 3
async def quest_3(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    # Удаляем предыдущие сообщения, если они есть
    try:
        video_message_ids = user_data.get("video_message_ids", [])
        question_message_id = user_data.get("question_message_id")
        await callback.message.delete()
        for message_id in video_message_ids:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Список видео с описаниями этапов (file_id, описание)
    video_steps = [
        {
            "file_id": "BAACAgIAAxkBAAIQbGfZ6i6PSqfFkwEviKkeTzjSIq07AAIcdQACA47RSsKNwE8ZB6jMNgQ",
            "description": "🔧 Этап 1: Сборка техники\nТут всё начинается. Камера, вспышка и немного магии ✨"
        },
        {
            "file_id": "BAACAgIAAxkBAAIQb2fZ7BlHovx8Xp1lXQULoPC9TQodAAIqdQACA47RStHyr_i86-BDNgQ",
            "description": "📸 Этап 2: Фотографирование\nПогнали по локации! Как снять крутой кадр и не потерять свет 🙌"
        },
        {
            "file_id": "BAACAgIAAxkBAAIQcWfZ7JauvtWMaVmGZURQAzGYZKcgAAItdQACA47RSmhTstArUV9lNgQ",
            "description": "🛠 Этап 3: Ретушь\nОбработка —  где магия превращается в вау. Как навести красоту в пару кликов? 💻🎨"
        },
        {
            "file_id": "BAACAgIAAxkBAAIQc2fZ7KUbwPbvvLzZkvlXEpkreZBEAAIudQACA47RSlZ0vju21gr_NgQ",
            "description": "🖨 Этап 4: Печать\nХоп — и уже в руках! Как превратить пиксели в реальность 📷📄"
        },
        {
            "file_id": "BAACAgIAAxkBAAIQdWfZ7_pGQdK3VOE928wyF3OS2NOLAAI2dQACA47RSpceq4CXeMQSNgQ",
            "description": "⭐ Этап 5: Презентация\nКак красиво отдать готовую работу и не стушеваться 💁"
        }
    ]

    # Сохраняем данные о видео в state
    await state.update_data(
        video_steps=video_steps,
        current_step=0,
        video_message_ids=[]
    )

    # Начинаем показ первого видео
    await show_next_video_step(callback, state)
    await callback.answer()


async def show_next_video_step(callback: types.CallbackQuery, state: FSMContext):
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
        sent_message = await callback.message.answer_video(
            step_data["file_id"],
            caption=step_data["description"],
            parse_mode="Markdown"
        )
        video_message_ids.append(sent_message.message_id)

        # Создаем клавиатуру (Далее или Приступить к вопросам для последнего шага)
        if current_step < len(video_steps) - 1:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее →", callback_data="next_video_step")]
            ])
            action_text = "\nНажмите 'Далее' для продолжения"
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Приступить к тесту", callback_data="start_quest3_test")]
            ])
            action_text = "\nКвест 3. Запомни правильный порядок действий, нажми 'Приступить к тесту', когда будешь готовы"


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
        await start_quest3_test(callback, state)

@router.callback_query(F.data == "next_video_step")
async def handle_next_video_step(callback: types.CallbackQuery, state: FSMContext):
    await show_next_video_step(callback, state)
    await callback.answer()

# Обработчик ответов для квеста 3
@router.callback_query(F.data == "start_quest3_test", QuestState.waiting_for_answer)
async def start_quest3_test(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    # Удаляем предыдущее сообщение с кнопкой
    if "step_message_id" in user_data:
        try:
            await callback.bot.delete_message(callback.message.chat.id, user_data["step_message_id"])
            for msg in  user_data["video_message_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg)
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Начинаем с первого вопроса
    await state.update_data(current_question=1, correct_count=0)
    await ask_quest3_question(callback, state)
    await callback.answer()

QUEST3_TEST_QUESTIONS = {
    1: "С чего всё начинается? (И нет, не с кофе)",
    2: "Техника собрана. Что дальше? (Спойлер: фоткать себя в зеркало —  не считается)",
    3: "Контент есть. Что теперь? (Фильтр «Вальден» —  не вариант)",
    4: "Всё блестит. Что дальше? (Нет, не TikTok)",
    5: "Финальный штрих. Что делаем? (Сломаться —  не опция)"
}
async def ask_quest3_question(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)

    # Удаляем предыдущее сообщение, если оно есть
    if "question_message_id" in user_data:
        try:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

    # Задаём вопрос
    question_text = f"🧠 Вопрос {current_question}\n{QUEST3_TEST_QUESTIONS[current_question]}"
    message = await callback.message.answer(
        question_text,
        reply_markup=quest3_keyboard(current_question)
    )

    # Сохраняем ID сообщения для последующего удаления
    await state.update_data(question_message_id=message.message_id)
    await callback.answer()

@router.callback_query(F.data.in_(correct_answers_qw3.values()), QuestState.waiting_for_answer)
async def handle_quest3_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)
    current_quest_id = user_data.get("current_quest_id", 3)  # ID квеста 3

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

        # Проверяем ответ пользователя
        if callback.data == correct_answers_qw3[current_question]:
            correct_count += 1
            user_result.result += 1
            await session.commit()  # Сохраняем изменение результата в БД
            await callback.answer('Верный ответ!')
        else:
            await callback.answer('Ответ неверный.')

        # Если все вопросы пройдены, отмечаем квест как выполненный
        if current_question == len(correct_answers_qw3):
            user_result.state = "выполнен"
            await session.commit()  # Финальный коммит после завершения квеста

    # Обновляем состояние FSM
    await state.update_data(correct_count=correct_count)

    # Переход к следующему вопросу или завершение квеста
    current_question += 1
    if current_question > len(correct_answers_qw3):
        await callback.message.delete()
        await finish_quest(callback, state, correct_count, len(correct_answers_qw3), current_quest_id)
        await session.commit()
    else:
        await state.update_data(current_question=current_question)
        await ask_quest3_question(callback, state)  # Задаём следующий вопрос

    await callback.answer()


# Квест 4
# Верные цифры для квеста 4
correct_numbers_qw4 = {1, 2, 3, 4, 5}

# Начало квеста 4
@router.callback_query(F.data == "start_quest4")
async def quest_4(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения, если они есть
    user_data = await state.get_data()
    try:
        photo_message_ids = user_data.get("photo_message_ids", [])
        question_message_id = user_data.get("question_message_id")
        await callback.message.delete()
        for message_id in photo_message_ids:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Показываем фото "чистой локации"
    photo_path = BASE_DIR / "handlers/media/photo/clean_location.jpg"
    clean_photo = FSInputFile(str(photo_path))
    message = await callback.message.answer_photo(
        clean_photo,
        caption="🧼 Чистота — это сила!\nПеред тобой идеальная локация без бардака. Запомни, как она выглядит 💡",
        reply_markup=quest4_keyboard_after_clear()
    )

    # Сохраняем ID сообщения для последующего удаления
    await state.update_data(photo_message_ids=[message.message_id])
    await state.set_state(QuestState.waiting_for_clean_photo)
    await callback.answer()

# Показываем фото "предметы, которые не должны находиться на локации"
@router.callback_query(F.data == "next_to_items", QuestState.waiting_for_clean_photo)
async def show_items_photo(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения, если они есть
    user_data = await state.get_data()
    try:
        photo_message_ids = user_data.get("photo_message_ids", [])
        question_message_id = user_data.get("question_message_id")
        await callback.message.delete()
        for message_id in photo_message_ids:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Создаем медиагруппу
    media_group = MediaGroupBuilder(caption="🧃 Нечистые предметы 👀\n"
                                            "Вот примеры вещей, которые не должны тусить на локации.\n")

    # Добавляем фото в медиагруппу
    for i in range(1, 10):  # Номера от 1 до 9
        photo_path = BASE_DIR / f"handlers/media/photo/мусор/{i}.jpg"
        if photo_path.exists():
            media_group.add_photo(media=FSInputFile(str(photo_path)))
        else:
            print(f"Файл {photo_path} не найден!")

    # Отправляем медиагруппу
    photo_messages = await callback.message.answer_media_group(media=media_group.build())
    photo_message_ids = [msg.message_id for msg in photo_messages]

    # Отправляем кнопку "Приступить"
    question_message = await callback.message.answer(
        "Взгляни и впиши их в память 🧠 Жми «Далее», если готов к проверке",
        reply_markup=quest4_keyboard_after_trash()
    )

    # Сохраняем ID всех сообщений для последующего удаления
    await state.update_data(
        photo_message_ids=photo_message_ids,
        question_message_id=question_message.message_id
    )
    await state.set_state(QuestState.waiting_for_items_photo)
    await callback.answer()

# Показываем фото "грязной локации" и клавиатуру для выбора цифр
@router.callback_query(F.data == "start_selection", QuestState.waiting_for_items_photo)
async def show_dirty_location(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения, если они есть
    user_data = await state.get_data()
    try:
        photo_message_ids = user_data.get("photo_message_ids", [])
        question_message_id = user_data.get("question_message_id")
        await callback.message.delete()
        for message_id in photo_message_ids:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Показываем фото "грязной локации"
    photo_path = BASE_DIR / "handlers/media/photo/dirty_location.jpg"
    dirty_photo = FSInputFile(str(photo_path))
    message = await callback.message.answer_photo(
        dirty_photo,
        caption="🔍 Проверка на чистоту!\nНа фото снова локация.\nТвоя задача: тыкни номера, которые ломают идеальный вайб 😤"
    )

    # Отправляем клавиатуру для выбора цифр
    question_message = await callback.message.answer(
        "Выбери цифры:",
        reply_markup=quest4_keyboard(set())
    )

    # Сохраняем ID всех сообщений для последующего удаления
    await state.update_data(
        photo_message_ids=[message.message_id],
        question_message_id=question_message.message_id
    )
    await state.set_state(QuestState.waiting_for_selection)
    await callback.answer()


# Квест 5
async def quest_5(callback: types.CallbackQuery, state: FSMContext):
    # Очищаем предыдущие фото
    await state.update_data(photos=[], photo_message_id=None)


    user_data = await state.get_data()

    # Удаляем предыдущие сообщения, если они есть
    try:
        photo_message_ids = user_data.get("photo_message_ids", [])
        question_message_id = user_data.get("question_message_id")
        await callback.message.delete()
        for message_id in photo_message_ids:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    photo_path = BASE_DIR / "handlers/media/photo/map2.jpg"
    if not photo_path.exists():
        await callback.message.answer("Файл с изображением не найден.")
        return

    photo = FSInputFile(str(photo_path))

    # Отправляем новое сообщение с фото
    message = await callback.message.answer_photo(
        photo,
        caption="📍 Квест 5: Фото-миссия\n"
                "Перед тобой карта парка 🎢\n"
                "Сделай фото своих коллег на всех фото-точках во время работы.\n"
                "Когда всё будет готово —  жми «Готово» и получи +100 к уважению 😎",
        reply_markup=quest5_keyboard()
    )
    await state.update_data(photo_message_id=message.message_id, photos=[])
    await callback.answer()


# В функции collect_photos (квест 5) изменим состояние:
@router.callback_query(F.data == "start_qw5")
async def collect_photos(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    # Обновляем статус в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 5
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=5,
                state="не выполнен",
                attempt=1,
                result=0
            )
            session.add(user_result)

        if user_result.state == "выполнен":
            await callback.answer("Этот квест уже выполнен!")
            return
        await session.commit()

    await callback.message.answer("Выгрузи все фотки одним сообщением, мы оценим 😎")
    await state.set_state(QuestState.waiting_for_photos_quest5)  # Изменили состояние
    await callback.answer()

# И обработчик фото для квеста 5:
@router.message(F.photo, QuestState.waiting_for_photos_quest5)
async def handle_photos_quest5(message: types.Message, state: FSMContext):
    # Добавляем фото в state
    user_data = await state.get_data()
    photos = user_data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)

    # Если это первое фото - отправляем кнопку "Готово"
    if len(photos) == 1:
        await message.answer(
            "Фото получено. Отправь остальные или нажми 'Готово'",
            reply_markup=quest5_finish_keyboard()
        )



# Квест 6 - Фото с клиентом
async def quest_6(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "photo_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["photo_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    message = await callback.message.answer(
        "📸 Квест 6: Фото с клиентом\n"
        "Попроси коллегу щёлкнуть тебя в моменте — пока ты работаешь с клиентом.\n"
        "Получится и полезно, и в стиле «я на рабочем вайбе» 😎\n"
        "Когда будешь готов(а) — загружай:",
        reply_markup=quest6_keyboard()
    )

    await state.update_data(photo_message_id=message.message_id)
    await callback.answer()


@router.callback_query(F.data == "start_qw6")
async def collect_photo_quest6(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()

    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 6
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=6,
                state="не выполнен",
                attempt=1,
                result=0
            )
            session.add(user_result)

        if user_result.state == "выполнен":
            await callback.answer("Этот квест уже выполнен!")
            return
        await session.commit()

    await callback.message.answer("Пожалуйста, отправьте фото одним сообщением.")
    await state.set_state(QuestState.waiting_for_photos_quest6)
    await callback.answer()


@router.message(F.photo, QuestState.waiting_for_photos_quest6)
async def handle_photos_quest6(message: types.Message, state: FSMContext):
    # Добавляем фото в state
    user_data = await state.get_data()
    photos = user_data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)

    # Если это первое фото - отправляем кнопку "Готово"
    if len(photos) == 1:
        await message.answer(
            "📥 Фотка принята!\n Если есть ещё — кидай\nИли жми «Готово», чтобы всё оформить 🧾",
            reply_markup=quest6_finish_keyboard()
        )


@router.callback_query(F.data == "finish_quest6", QuestState.waiting_for_photos_quest6)
async def send_for_moderation_quest6(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos = user_data.get("photos", [])

    if not photos:
        await callback.answer("Вы не отправили ни одного фото!", show_alert=True)
        return

    # Удаляем сообщение с кнопкой "Готово"
    try:
        await callback.message.delete()
    except:
        pass

    # Обновляем статус в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).where(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 6
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=6,
                state="на модерации",
                attempt=1,
                result=0
            )
            session.add(user_result)

        if user_result:
            user_result.state = "на модерации"
        await session.commit()

    # Получаем информацию о пользователе для подписи
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 6 - Фото с клиентом\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Отправляем фото модератору с подписью к первому фото
    if len(photos) > 1:
        media = []
        # Первое фото с подписью
        media.append(InputMediaPhoto(
            media=photos[0],
            caption=caption
        ))
        # Остальные фото без подписи
        for photo in photos[1:]:
            media.append(InputMediaPhoto(media=photo))

        await callback.bot.send_media_group(admin_chat_id, media)
    else:
        # Если фото одно - отправляем с подписью
        await callback.bot.send_photo(
            admin_chat_id,
            photos[0],
            caption=caption
        )

    # Дополнительная информация для модератора с кнопками
    await callback.bot.send_message(
        admin_chat_id,
        f"Выберите действие для квеста 6 от {user.full_name}:",
        reply_markup=moderation_keyboard(
            user_id=callback.from_user.id,
            quest_id=6
        )
    )

    # Финальное сообщение пользователю
    await callback.message.answer(
        "✅ Фото отправлено на модерацию. Ожидайте проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await track_quest_time(callback.from_user.id, 6, is_start=False, state=state)
    await state.clear()
    await callback.answer()


# Квест 7 - Товары и цены


PRODUCT_GROUPS = {
    "magnets": {
        "name": "📦 Шаг 1/9 — Магниты и брелки\n"
                "Никакой бабушкин холодильник без фотомагнита не обходится!\n"
                "Брелок на память — must-have.\n"
                "Цена? Лайтовая. Погнали дальше!",
        "items": [
            {
                "name": "Магнит 100*100",
                "price": "500 руб.",
                "photo": "products/magnets/magnet_100x100.jpg"
            },
            {
                "name": "Магнит А6",
                "price": "900 руб.",
                "photo": "products/magnets/magnet_a6.jpg"
            },
            {
                "name": "Брелоки 56*40",
                "price": "400 руб.",
                "photo": "products/magnets/brelok.jpg"
            }
        ]
    },
    "photos": {
        "name": "📸 Шаг 2/9 — Фотопечать\n"
                "A6, A5, A4 — выбирай под вайб и кошелёк.\n"
                "На стену, в рамку, в альбом — всё в твоих руках.",
        "items": [
            {
                "name": "Фото А4",
                "price": "700 руб.",
                "photo": "products/photos/photo_a4.jpg"
            }
        ]
    },
    "photos_frame": {
        "name": "🖼 Шаг 3/9 — Фото в рамке\n"
                "Подарок маме, бабушке или себе любимому? ✔\n"
                "Красиво стоит, дорого выглядит.",
        "items": [
            {
                "name": "Фото А4 в рамке",
                "price": "2000 руб.",
                "photo": "products/photos_frame/photo_frame.jpg"
            }

        ]

    },
    "collage": {
        "name": "🧩 Шаг 4/9 — Коллажи\n"
                "Фоточка одна — это скучно. А вот коллаж из лучших моментов — 🔥\n"
                "Больше лиц, больше любви.",
        "items": [
            {
                "name": "Коллаж А4 ",
                "price": "2000 руб.",
                "photo": "products/collage/collage_a4.jpg",
                "description": "Магнит 100×100 — 500 ₽, идеал на холодильник не может быть бесплатным!\n"
                               "Подгоняй дальше, ты почти Разрушитель Прайс-листов 💥 "
            },
            {
                "name": "Коллаж А4 в рамке",
                "price": "1200 руб.",
                "photo": "products/collage/collage_a4_frame.jpg",
                "description": "Фото A4 — 700 ₽. Большой формат для больших эмоций! "
            },
            {
                "name": "Коллаж А5 ",
                "price": "1100 руб.",
                "photo": "products/collage/collage_a5.jpg",
                "description": " "
            },
            {
                "name": "Коллаж А5 в рамке",
                "price": "1100 руб.",
                "photo": "products/collage/collage_a5_frame.jpg",
                "description": " "
            }
        ]

    },
    "budka": {
        "name": "📷 Шаг 5/9 — Фотобудка\n"
                "Три кадра, один смех, и воспоминания на века\n"
                "Идеально для друзей, пар и “мы просто коллеги”.",
        "items": [
            {
                "name": "Фото ",
                "price": "2000 руб.",
                "photo": "products/budka/1.jpg"
            }
        ]

    },
    "suvenir": {
        "name": "🎁 Шаг 6/9 — Сувениры\n"
                "Кружка, что греет душу. Левитирующая рамка — вау-эффект 100%\n"
                "Хотел? Теперь знаешь, где взять.",
        "items": [
            {
                "name": "Кружка",
                "price": "2000 руб.",
                "photo": "products/suvenir/cup.jpg",
                "description": " "
            },
            {
                "name": "Рамка",
                "price": "5000 руб.",
                "photo": "products/suvenir/frame_fly.jpg",
                "description": " "
            },
            {
                "name": "Стикер",
                "price": "1100 руб.",
                "photo": "products/suvenir/sticker.jpg",
                "description": " "
            },
            {
                "name": "Брелок",
                "price": "1100 руб.",
                "photo": "products/suvenir/ny_circle.jpg",
                "description": " "
            },
            {
                "name": "Значек",
                "price": "1100 руб.",
                "photo": "products/suvenir/znak.jpg",
                "description": " "
            }
        ]

    },
    "calendar": {
        "name": "🗓 Шаг 7/9 — Календари\n"
                "Каждый день — с твоим лицом 😎\n"
                "Есть даже в рамке, чтобы как у продюсера в офисе.",
        "items": [
            {
                "name": "Фото ",
                "price": "2000 руб.",
                "photo": "products/calendar/a4.jpg"
            },
            {
                "name": "Фото ",
                "price": "2000 руб.",
                "photo": "products/calendar/a4_frame.jpg"
            }
        ]

    },
    "print": {
        "name": "💾 Шаг 8/9 — Печать с носителя\n"
                "Принёс с флешки — получил фото.\n"
                "Всё просто. Даже дед поймёт.",
        "items": [
            {
                "name": "услуга ",
                "price": "2000 руб.",
                "photo": "products/print/1.jpg"
            },
            {
                "name": "услуга ",
                "price": "2000 руб.",
                "photo": "products/print/2.jpg"
            },
            {
                "name": "услуга ",
                "price": "2000 руб.",
                "photo": "products/print/3.jpg"
            },
            {
                "name": "услуга ",
                "price": "2000 руб.",
                "photo": "products/print/4.jpg"
            },
            {
                "name": "услуга ",
                "price": "2000 руб.",
                "photo": "products/print/5.jpg"
            }
        ]

    },
    "services": {
        "name": "📲 Шаг 9/9 — Доп. услуги\n"
                "Видео, фотопрогулки, электронка — как хочешь, так и забирай.\n"
                "Контент — это валюта, помни об этом 💸\n"
                "Готов к проверке? Не переживай, помощь будет 😎",
        "items": [
            {
                "name": "Фото эл ",
                "price": "2000 руб.",
                "photo": "products/services/el.jpg"
            },
            {
                "name": "Фото ",
                "price": "2000 руб.",
                "photo": "products/services/video.jpg"
            },
            {
                "name": "Фото ",
                "price": "2000 руб.",
                "photo": "products/services/photo.jpg"
            }
        ]

    },
}
    # Добавьте остальные групп
# Словарь с товарами, ценами и описаниями
QUEST7_TEST_QUESTIONS  = {
        1: {
            "name": "Магнит 100×100",
            "photo": BASE_DIR / "handlers/media/photo/products/magnet.jpg",
            "options": ["300", "400", "900", "500"],
            "correct": "500",
            "description0":
'''❌ Неверно!
Магнит — не просто «красотка на холодильник», а супер-кейс для коллекций и подарков. Он стоит 500 рублей, дружок 😉
Жми “Следующий вопрос” и поехали дальше!''',
            "description1":
''' ✅ Верно! Блин, ты в теме!
Магнит 100×100 — 500 ₽, идеал на холодильник не может быть бесплатным!
Подгоняй дальше, ты почти Разрушитель Прайс-листов 💥'''
        },
        2: {
            "name": "Фото A4",
            "photo": BASE_DIR / "handlers/media/photo/products/a4.jpg",
            "options": ["1000", "700", "500", "100"],
            "correct": "700",
            "description0":
'''❌ Упс, мимо!
A4 — это формат «вау», который в альбом не просто влезет, а будет сиять. За него просят 700 руб.
Давай-ка вопрос 3!''',
            "description1":
'''✅ Верно! Бомба!
Фото A4 — 700 ₽. Большой формат для больших эмоций!'''
        },
        3: {
            "name": "Фото в рамке A5",
            "photo": BASE_DIR / "handlers/media/photo/products/a5.jpg",
            "options": ["1200", "1500", "900", "400"],
            "correct": "1200",
            "description0": '''❌ Nope!
Красивые фоторамки не даром: A5-ка в рамке — 1200 рублей.
Не сдаёмся, остаётся ещё много вопросов!''',
            "description1": '''✅ Верно! Отлично!
Фото в рамке A5 — 1200 ₽. Ваши снимки + стильная рамка = ❤'''
        },
        4: {
            "name": "Фото-коллаж A4 в рамке",
            "photo": BASE_DIR / "handlers/media/photo/products/col_a4.jpg",
            "options": ["2500","2100","2200","2400"],
            "correct": "2200",
            "description0": '''❌ Нет-нет!
Этот коллаж — альтернатива альбому, стоит ровно 2100 руб.
Вперёд, к вопросу 5!''',
            "description1": '''✅ Верно! В яблочко!
Фото-коллаж A4 в рамке — 2100 ₽. Коллекция лучших моментов в стиле гика.'''
        },
        5: {
            "name": "Фото в электронном виде",
            "photo": BASE_DIR / "handlers/media/photo/products/el.jpg",
            "options": ["100", "300", "500", "700"],
            "correct": "500",
            "description0": '''❌ Мимо!
Электронка – это твоя аватарка в соц.сети! Универсальный продукт! Цена ее 500 руб., но так же это отличный бонус для повышения чека! 
Вперёд, к вопросу 6!''',
            "description1": '''✅ Верно! Любишь менять фотки на аве?
Фото в электронном виде — 500 ₽. Сохраняй, делись и будь в тренде!'''
        },
        6: {
            "name": "Кружка с фото",
            "photo": BASE_DIR / "handlers/media/photo/products/cup.jpg",
            "options": ["2000", "1000", "1500", "500"],
            "correct": "1000",
            "description0": '''❌ Неверно!
Кружка с фоткой — не просто чашка, а вечный аксессуар. Она стоит 1000 ₽ 😉
Жми «Следующий вопрос» и вперед!''',
            "description1": '''✅ Верно! Двигаешься на уверенном!
Кружка с фото — 1000 ₽. Утро начинается с твоего лица и кофе.'''
        },
        7: {
            "name": "Левитирующая рамка",
            "photo": BASE_DIR / "handlers/media/photo/products/ramka.jpg",
            "options": ["2000", "5000", "5500", "3500"],
            "correct": "5000",
            "description0": '''❌ Упс! Неверно.
Такая рамка – магия для всех — это 5000 ₽, не меньше!
Жмём «Следующий вопрос» 🔥''',
            "description1": '''✅ Верно! На 100%!
Левитирующая рамка — 5000 ₽. Магия гравитации и кадра в одном флаконе.'''
        },
        8: {
            "name": "фото календарь А4 в рамке",
            "photo": BASE_DIR / "handlers/media/photo/products/calendar.jpg",
            "options": ["2100", "2500", "2300", "2000"],
            "correct": "2100",
            "description0": '''❌ Мимо!
Календарь с твоим лицом в крутой рамке — 2100 ₽. Запоминай!
Идём к последнему вопросу!''',
            "description1": '''✅ Верно! Ты явно списываешь…
Фото-календарь A4 в рамке — 2100 ₽. Будь в курсе дат и не забывай про свою истинную любовь — фотоконтент!'''
        },
        9: {
            "name": 'фотопрогулка 1 час "Стандарт"',
            "photo": BASE_DIR / "handlers/media/photo/products/fp.jpg",
            "options": ["4500", "5000", "3000", "3500"],
            "correct": "3500",
            "description0": '''❌ Не верно!
«Стандарт» — это минимум 1 час драйва в праздник и минус 3500 рублей в кошельке клиента.''',
            "description1": '''✅ Верно! Абсолютно!
Фотопрогулка «Стандарт» (1 час) — 3500 ₽. Гарантированный час эпичных кадров и кайфа.'''
        }
    }


async def quest_7(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)

    # Удаляем предыдущие сообщения
    try:
        await callback.message.delete()
        if "photo_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["photo_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    await callback.message.answer('🧠 Сейчас будет жёстко (немного)\n'
                                  '9 шагов. Много инфы. Цены, товары, магниты, рамки, фотобудки и даже левитация 😵‍💫'
                                  'Постарайся запомнить — это пригодится в бою 💪\n'
                                  'Поехали!', reply_markup=quest7_start_keyboard())


@router.callback_query(F.data == "start_quest7")
async def start_quest_7(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)

    # Удаляем предыдущие сообщения
    try:
        await callback.message.delete()
        if "photo_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["photo_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Проверяем, в каком режиме находимся (просмотр товаров или тест)
    if not user_data.get("test_mode", False):
        """Начало квеста - показ товаров по группам"""
        await state.update_data(
            current_group=0,
            test_mode=False
        )
        await show_product_group(callback, state)
    else:
        """Продолжение тестовой части"""
        await ask_test_question(callback, state)

    await callback.answer()


async def show_product_group(callback: types.CallbackQuery, state: FSMContext):
    """Показывает одну группу товаров"""
    user_data = await state.get_data()
    group_keys = list(PRODUCT_GROUPS.keys())
    current_idx = user_data.get("current_group", 0)

    # Удаляем предыдущие сообщения
    try:
        if "media_group_ids" in user_data:
            for msg_id in user_data["media_group_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
    except Exception as e:
        print(f"Ошибка при удалении: {e}")

    group = PRODUCT_GROUPS[group_keys[current_idx]]

    # Создаем медиагруппу
    album_builder = MediaGroupBuilder(
        caption=f"{group['name']}"
    )

    for item in group["items"]:
        photo_path = BASE_DIR / f"handlers/media/photo/{item['photo']}"
        if photo_path.exists():
            album_builder.add_photo(
                media=FSInputFile(str(photo_path))
            )

    # Отправляем группу товаров
    sent_messages = await callback.message.answer_media_group(media=album_builder.build())

    # Кнопка для продолжения
    is_last_group = current_idx == len(group_keys) - 1
    button_text = "✅ Приступить к тесту" if is_last_group else "➡️ Дальше"
    callback_data = "start_quest7_test" if is_last_group else "next_product_group"

    control_message = await callback.message.answer(
        f"Шаг {current_idx + 1}/{len(group_keys)}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
            ]
        ))

    await state.update_data(
        media_group_ids=[m.message_id for m in sent_messages],
        control_message_id=control_message.message_id
    )


@router.callback_query(F.data == "next_product_group")
async def next_product_group(callback: types.CallbackQuery, state: FSMContext):
    """Показывает следующую группу товаров"""
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "media_group_ids" in user_data:
            for msg_id in user_data["media_group_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
        if "control_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["control_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    #await callback.message.delete()

    user_data = await state.get_data()
    current_idx = user_data.get("current_group", 0) + 1
    await state.update_data(current_group=current_idx)
    await show_product_group(callback, state)
    await callback.answer()

@router.callback_query(F.data == "next_question_test")
async def next_test_question(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1) + 1
    total_questions = user_data.get("total_questions", len(QUEST7_TEST_QUESTIONS))

    await callback.message.delete()

    if current_question <= total_questions:
        await state.update_data(current_question=current_question)
        await ask_test_question(callback, state)
    else:
        correct_count = user_data.get("correct_count", 0)
        await finish_quest(callback, state, correct_count, total_questions, 7)

    await callback.answer()


@router.callback_query(F.data == "start_quest7_test")
async def start_quest7_test(callback: types.CallbackQuery, state: FSMContext):
    """Начинает тестовую часть квеста"""
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        if "media_group_ids" in user_data:
            for msg_id in user_data["media_group_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
        if "control_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["control_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    await state.update_data(
        test_mode=True,
        current_question=1,
        correct_count=0,
        total_questions=len(QUEST7_TEST_QUESTIONS)
    )

    # Начинаем тест с первого вопроса
    await ask_test_question(callback, state)
    await callback.answer()


async def ask_test_question(callback: types.CallbackQuery, state: FSMContext):
    """Задает тестовый вопрос"""
    user_data = await state.get_data()
    question_data = QUEST7_TEST_QUESTIONS[user_data["current_question"]]

    # Сохраняем вопрос в state
    await state.update_data(current_product=question_data)

    try:
        # Удаляем предыдущие сообщения
        if "photo_message_id" in user_data:
            try:
                await callback.bot.delete_message(callback.message.chat.id, user_data["photo_message_id"])
            except:
                pass

        # Проверяем путь к фото
        if isinstance(question_data["photo"], Path):
            photo_path = question_data["photo"]
        else:
            photo_path = BASE_DIR / "handlers/media/photo" / question_data["photo"]

        if not photo_path.exists():
            raise FileNotFoundError(f"Фото не найдено: {photo_path}")

        # Отправляем вопрос с фото
        photo = FSInputFile(photo_path)
        message = await callback.message.answer_photo(
            photo,
            caption=f"❓Тест: Вопрос {user_data['current_question']}/{user_data['total_questions']}\n"
                    f"Укажите цену товара: <b>{question_data['name']}</b> \n(пс, можешь смотреть прайс на локации)",parse_mode="HTML",
            reply_markup=quest7_keyboard(question_data["options"])
        )

        await state.update_data(
            current_question_data=question_data,
            photo_message_id=message.message_id
        )

    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        # Если фото не найдено, отправляем текст без фото
        message = await callback.message.answer(
            f"Тест: Вопрос {user_data['current_question']}/{user_data['total_questions']}\n"
            f"Укажите цену товара: {question_data['name']}\n"
            f"⚠️ Фото временно недоступно",
            reply_markup=quest7_keyboard(question_data["options"])
        )
        await state.update_data(
            current_question_data=question_data,
            photo_message_id=message.message_id
        )

    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        await callback.message.answer("Произошла ошибка при загрузке вопроса. Попробуйте еще раз.")
        await state.finish()

@router.callback_query(F.data.startswith("qw7_answer_"), QuestState.waiting_for_answer)
async def handle_quest7_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    # Проверяем наличие необходимых данных
    if not all(key in user_data for key in ['current_question', 'correct_count', 'current_product', 'total_questions']):
        await callback.answer("Ошибка: данные вопроса не найдены. Начните квест заново.")
        await state.clear()
        return

    current_question = user_data["current_question"]
    correct_count = user_data["correct_count"]
    current_product = user_data["current_product"]
    total_questions = user_data["total_questions"]

    # Дополнительная проверка current_product
    if current_product is None:
        await callback.answer("Ошибка: информация о товаре не найдена.")
        return

    selected_answer = callback.data.split("_")[-1]
    is_correct = selected_answer == current_product["correct"]

    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 7
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=7,
                state="не выполнен",
                attempt=1,
                result=0
            )
            session.add(user_result)

        if is_correct:
            correct_count += 1
            user_result.result += 1
            await callback.answer("✅ Верный ответ!")
        else:
            await callback.answer("❌ Неверный ответ!")

        if current_question == total_questions:
            user_result.state = "выполнен" if correct_count == total_questions else "не выполнен"

        await session.commit()

    # Показываем описание товара
    try:
        await callback.message.delete()
    except:
        pass

    if is_correct:
        message = await callback.message.answer(
            f"{current_product['description1']}",
            reply_markup=quest7_next_keyboard()
        )
    else:
        message = await callback.message.answer(
            f"{current_product['description0']}",
            reply_markup=quest7_next_keyboard()
        )

    await state.update_data(
        correct_count=correct_count,
        question_message_id=message.message_id
    )


@router.callback_query(F.data == "next_qw7")
async def next_quest7_question(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1) + 1

    # Обновляем текущий продукт
    if current_question <= len(QUEST7_TEST_QUESTIONS):
        await state.update_data(
            current_question=current_question,
            current_product=QUEST7_TEST_QUESTIONS[current_question]
        )
        await quest_7(callback, state)
    else:
        correct_count = user_data.get("correct_count", 0)
        await finish_quest(callback, state, correct_count, user_data["total_questions"], 7)
        async with SessionLocal() as session:
            await update_user_level(callback.from_user.id, session)
            await session.commit()

# Квест 8 - Теория продаж


questions = {
    1: {
        "text": "🎉 Вопрос 1\n\n"
                "Как начать общение с клиентом, чтобы не выглядеть как спам-бот?",
        "options": [
            "Мчатся сразу к демонстрации товара",
            "Здороваемся и устанавливаем контакт 👋",
            "Сразу говорим про цену 💸",
            "Сразу “убираем” возражения 🗑"
        ],
        "correct": "Здороваемся и устанавливаем контакт 👋",
        "explanation": "Любое взаимодействие начинается с приветствия и установления контакта. Это создает доверительную атмосферу."
    },
    2: {
        "text": "🎯 Вопрос 2\n\n"
                "Что важнее всего на этапе выяснения потребностей?",
        "options": [
            "Узнать, сколько у него денег 💰",
            "Понять истинные желания и болевые точки ✨",
            "Рассказать обо ВСЕХ наших товарах сразу 📢",
            "Спросить, где он работает 🏢"
        ],
        "correct": "Понять истинные желания и болевые точки ✨",
        "explanation": "Ключевая задача - понять реальные потребности клиента, а не навязывать свое видение."
    },
    3: {
        "text": "🔥 Вопрос 3\n\n"
                "При презентации товара куда лучше смотреть?",
        "options": [
            "Сразу на цену и скидки 💵",
            "На выгоды клиента — “что он получает” 🕶",
            "На статистику всех продаж 📈",
            "На время 👋"
        ],
        "correct": "На выгоды клиента — “что он получает” 🕶",
        "explanation": "Важно показать, как продукт решает конкретные проблемы клиента, а не просто перечислять характеристики."
    },
    4: {
        "text": "💥 Вопрос 4\n\n"
                "Зачем вообще работают с возражениями?",
        "options": [
            "Чтобы в любом случае “впарить” товар 🎯",
            "Чтобы быстрее закрыть продажу ✅",
            "Чтобы показать ценность и ответить на сомнения 🛡",
            "Чтобы убрать все “а вдруг?” как пыль с полок 🧹"
        ],
        "correct": "Чтобы показать ценность и ответить на сомнения 🛡",
        "explanation": "Возражения - это возможность прояснить сомнения клиента и показать преимущества продукта."
    },
    5: {
        "text": "🏁 Вопрос 5\n\n"
                "Что нужно сделать после успешной сделки?",
        "options": [
            "Бежать к следующему клиенту 🕷",
            "Проанализировать, что сработало, а что нет 📊",
            "Рассказывать о других товарах 🎥",
            "Давать скидки всем подряд 🏷️"
        ],
        "correct": "Проанализировать, что сработало, а что нет 📊",
        "explanation": "Анализ помогает понять, что сработало хорошо, а что можно улучшить в следующий раз."
    }
}

async def quest_8(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)

    # Удаляем предыдущие сообщения
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Показываем теорию перед первым вопросом
    if current_question == 1 and "theory_shown" not in user_data:
        video_id = 'BAACAgIAAxkBAAIiUGfsEMbuLFe7uVP1NOEazWMhXTpgAAK3agACM69gSzOYodJOm4amNgQ'
        theory_video = await callback.message.answer_video(
            video_id, caption= '*Квест 8: Теория продаж*\n\n'
                               'Зацени видос — там лайфхаки, как делать продажи на автопилоте.\n'
                               'Впитай, как спонтанный мем, и жми *«Конспект»*, чтобы забить важные тезисы в свою базу знаний 📚✨',
            reply_markup=quest8_konspekt_keyboard(), parse_mode='Markdown'
        )
        await state.update_data(theory_video_id=theory_video.message_id, theory_shown=True)
        return

    # Отправляем текущий вопрос с пронумерованными вариантами
    current_q = questions.get(current_question)
    question_text = f"Квест 8: Теория продаж\n{current_q['text']}\n\n"

    # Добавляем пронумерованные варианты ответов
    for i, option in enumerate(current_q["options"], 1):
        question_text += f"{i}. {option}\n"

    question_message = await callback.message.answer(
        question_text,
        reply_markup=quest8_keyboard(len(current_q["options"]))
    )

    await state.update_data(
        question_message_id=question_message.message_id,
        current_question_data=current_q,
        total_questions=len(questions)
    )
    await callback.answer()


@router.callback_query(F.data == "quest8_text")
async def quest8_konspekt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    # Показываем теорию перед первым вопросом
    theory_text = """
    📚 <b>Основы базовой теории продаж</b>

    Продажа — процесс передачи товаров или услуг от продавца к покупателю. Основные элементы теории продаж включают:

    1. <b>Приветствие и установление контакта</b>
    Любое взаимодействие начинается с приветствия и захвата внимания клиента. Постройте доверительные отношения с клиентом, допустим разговор "ни о чём" для создания благоприятной психологической основы взаимодействия. Эффективно работает правило "трёх да" - если клиент в чём-то соглашается с продавцом, можно смело переходить к следующему этапу.

    2. <b>Понимание клиента и определение потребностей</b>
    Выявление истинных желаний клиента, удержание внимания. Знайте целевую аудиторию, её потребности и предпочтения. Данный этап обычно более эффективен, если продавец понимает потребности клиента еще до вступления с ним в контакт.

    3. <b>Презентация продукта</b>  
    На этапе презентации продукта важно хорошо понимать все его преимущества, характеристики в разрезе выгод покупателя. Детально вы должны разбираться в:
    
    - Свойства, характеристики, особенности товара/услуги
    - Преимущества и недостатки
    - Качество
    - Стоимость
    - Что влияет на цену продукта

    4. <b>Обработка возражений</b>  
    Выслушивайте и отвечайте на сомнения клиента, показывая ценность продукта. Важно понимать, что возражения в большинстве случаев мнимые и могут быть с лёгкостью обработаны.

    5. <b>Завершение продажи</b>
    Подводите клиента к принятию решения. Используйте призыв к действию. Также эффективно работает правило "трёх да". Предложите клиенту удобный вариант оплаты. Важно оставить о себе хорошее впечатление, чтобы клиент захотел вернуться.

    6. <b>Анализ продажи</b>
    Проанализируйте проведённую продажу: какие инструменты сработали, какие - нет, как можно было бы еще обработать возражения. Данный пункт про развитие навыков продавца.

    7. <b>Послепродажное обслуживание</b>  
    Поддерживайте связь, чтобы разрешить возможные проблемы и стимулировать повторные продажи.

    💡 <b>Советы:</b>
    - Работа с возражениями начинается до контакта с клиентом
    - Каждое возражение должно иметь минимум один сценарий решения
    - Ответы можно продумать так, чтобы перекрывать возражения клиента ещё до их появления
    - Не спорьте с покупателем, используйте технику "присоединение"
    - В 90% случаев возражения завязаны на стоимости - донесите ценность предложения

    Классическая техника продаж подразумевает выполнение всех обещаний - это основа доверительных отношений. Будьте искренними и проявляйте неподдельную заинтересованность.
    
<b>Много умных словечек? Не переживай, на практике легче! Давай пройдем тест!</b>
<b>Жми «приступить к тесту»</b>
    """
    theory_message = await callback.message.answer(
            theory_text,
            parse_mode="HTML",
            reply_markup=quest8_start_keyboard()
        )
    await state.update_data(theory_message_id=theory_message.message_id, theory_shown=True)



@router.callback_query(F.data == "start_quest8_test")
async def start_quest8_test(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем сообщение с теорией
    user_data = await state.get_data()
    try:
        if "theory_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["theory_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Начинаем тест с первого вопроса
    await state.update_data(current_question=1, correct_count=0)
    await quest_8(callback, state)
    await callback.answer()


@router.callback_query(F.data.startswith("qw8_"), QuestState.waiting_for_answer)
async def handle_quest8_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)
    current_q = user_data.get("current_question_data")
    total_questions = user_data.get("total_questions", 5)

    # Получаем номер выбранного варианта
    selected_number = int(callback.data.split("_")[1])

    # Проверяем, что номер в допустимом диапазоне
    if selected_number < 1 or selected_number > len(current_q["options"]):
        await callback.answer("Неверный номер варианта")
        return

    # Получаем выбранный ответ
    selected_answer = current_q["options"][selected_number - 1]

    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 8
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=8,
                state="не выполнен",
                attempt=1,
                result=0
            )
            session.add(user_result)

        # Проверяем ответ
        is_correct = selected_answer == current_q["correct"]

        if is_correct:
            correct_count += 1
            user_result.result += 1
            await callback.answer("Верный ответ!")
        else:
            await callback.answer("Неверный ответ!")

        if current_question == total_questions:
            user_result.state = "выполнен" if correct_count == total_questions else "не выполнен"

        await session.commit()

    # Переход к следующему вопросу или завершение
    current_question += 1
    if current_question > total_questions:
        await callback.message.delete()
        await finish_quest(callback, state, correct_count, total_questions, 8)
    else:
        await state.update_data(
            current_question=current_question,
            correct_count=correct_count
        )
        await quest_8(callback, state)

    await callback.answer()

# Квест 9 - Знакомство с коллегами
async def quest_9(callback: types.CallbackQuery, state: FSMContext):
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
        "🤜🤛 *Квест 9: Знакомство с коллегами*\n\n"
        "Сколько человек тусит с тобой на смене? Введи цифру:",
        reply_markup=quest9_cancel_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        colleagues_data=[],
        current_colleague=1
    )
    await state.set_state(QuestState.waiting_for_colleagues_count)
    await callback.answer()


@router.message(QuestState.waiting_for_colleagues_count)
async def handle_colleagues_count(message: types.Message, state: FSMContext):
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
    await ask_colleague_info(message, state)


async def ask_colleague_info(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    current_colleague = user_data.get("current_colleague", 1)
    colleagues_count = user_data.get("colleagues_count", 1)

    if current_colleague > colleagues_count:
        # Всех коллег опросили, отправляем на модерацию
        await send_colleagues_to_moderation(message, state)
        return

    # Запрашиваем информацию о коллеге
    question = await message.answer(
        f"👥*Коллега {current_colleague} из {colleagues_count}:*\n\n"
        "Кто он в команде?",
        reply_markup=quest9_position_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=question.message_id,
        current_colleague=current_colleague
    )
    await state.set_state(QuestState.waiting_for_colleague_position)


@router.callback_query(F.data.startswith("qw9_position_"), QuestState.waiting_for_colleague_position)
async def handle_colleague_position(callback: types.CallbackQuery, state: FSMContext):
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
        builder.button(text=surname, callback_data=f"qw9_surname_{surname}")
    builder.adjust(3)

    question = await callback.message.answer(
        "*👤 Фамилия коллеги:*",
        reply_markup=builder.as_markup(), parse_mode='Markdown'
    )

    await state.update_data(question_message_id=question.message_id)
    await state.set_state(QuestState.waiting_for_colleague_surname)
    await callback.answer()


@router.callback_query(F.data.startswith("qw9_surname_"), QuestState.waiting_for_colleague_surname)
async def handle_colleague_surname(callback: types.CallbackQuery, state: FSMContext):
    surname = callback.data.split("_", 2)[-1]

    await callback.message.delete()
    await state.update_data(current_surname=surname)

    # Запрашиваем имя
    question = await callback.message.answer(
        "📝 Имя коллеги:",
        reply_markup=quest9_cancel_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(question_message_id=question.message_id)
    await state.set_state(QuestState.waiting_for_colleague_name)
    await callback.answer()


@router.message(QuestState.waiting_for_colleague_name)
async def handle_colleague_name(message: types.Message, state: FSMContext):
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
        "*💬 Telegram-юзернейм (@username):*",
        reply_markup=quest9_cancel_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(question_message_id=question.message_id)
    await state.set_state(QuestState.waiting_for_colleague_telegram)



@router.message(QuestState.waiting_for_colleague_telegram)
async def handle_colleague_telegram(message: types.Message, state: FSMContext):
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

    await ask_colleague_info(message, state)


async def send_colleagues_to_moderation(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    colleagues_data = user_data.get("colleagues_data", [])

    # Формируем сообщение для модератора
    report_text = "📋 Отчет по квесту 9 (Знакомство с коллегами):\n\n"
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
        reply_markup=moderation_keyboard(message.from_user.id, 9)
    )

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == message.from_user.id,
                UserResult.quest_id == 9
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=message.from_user.id,
                quest_id=9,
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
        "⏳ Данные о коллегах отправлены на модерацию.\n\n"
        "Жди вердикта, скоро выдадим случившихся героев команды 🕵️‍♀️",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await track_quest_time(message.from_user.id, 9, is_start=False, state=state)
    await state.clear()



@router.callback_query(F.data == "cancel_quest9")
async def cancel_quest9(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Квест отменен")
    await callback.answer()




# Обработчик ответов для квеста 1
@router.callback_query(F.data.in_(correct_answers.values()), QuestState.waiting_for_answer)
async def handle_quest1_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)
    current_quest_id = user_data.get("current_quest_id", 1)

    async with SessionLocal() as session:
        try:
            # Получаем или создаем запись о результате
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
                await session.flush()
            elif user_result.state == "выполнен":
                await callback.answer("Этот квест уже выполнен!")
                return

            # Проверяем ответ пользователя
            if callback.data == correct_answers[current_question]:
                correct_count += 1
                user_result.result += 1
                await callback.answer('Верный ответ!')
            else:
                await callback.answer('Ответ неверный.')

            # Если все вопросы пройдены, отмечаем квест как выполненный
            if current_question == len(correct_answers):
                user_result.state = "выполнен"

            await session.commit()

        except IntegrityError as e:
            await session.rollback()
            await callback.answer("Произошла ошибка при сохранении результата. Попробуйте еще раз.")
            return

    # Обновляем состояние FSM
    await state.update_data(correct_count=correct_count)

    # Переход к следующему вопросу или завершение квеста
    current_question += 1
    if current_question > len(correct_answers):
        await callback.message.delete()
        await finish_quest(callback, state, correct_count, len(correct_answers), current_quest_id)
    else:
        await state.update_data(current_question=current_question)
        await quest_1(callback, state)

    await callback.answer()

# Обработчик ответов для квеста 2
@router.callback_query(F.data.in_(correct_answers_qw2.values()), QuestState.waiting_for_answer)
async def handle_quest2_answer(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)
    current_quest_id = user_data.get("current_quest_id", 2)  # ID квеста 2

    async with SessionLocal() as session:
        try:
            # Получаем или создаем запись о результате
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
                await session.flush()
            elif user_result.state == "выполнен":
                await callback.answer("Этот квест уже выполнен!")
                return

            # Проверяем ответ пользователя
            if callback.data == correct_answers_qw2[current_question]:
                correct_count += 1
                user_result.result += 1
                await callback.answer('Верный ответ!')
            else:
                await callback.answer('Ответ неверный.')

            # Если все вопросы пройдены, отмечаем квест как выполненный
            if current_question == len(correct_answers_qw2):
                user_result.state = "выполнен"

            await session.commit()

        except IntegrityError as e:
            await session.rollback()
            await callback.answer("Произошла ошибка при сохранении результата. Попробуйте еще раз.")
            return

    # Обновляем состояние FSM
    await state.update_data(correct_count=correct_count)

    # Переход к следующему вопросу или завершение квеста
    current_question += 1
    if current_question > len(correct_answers_qw2):
        await callback.message.delete()
        await finish_quest(callback, state, correct_count, len(correct_answers_qw2), current_quest_id)
        async with SessionLocal() as session:
            await update_user_level(callback.from_user.id, session)
    else:
        await state.update_data(current_question=current_question)
        await quest_2(callback, state)

    await callback.answer()

# Обработчик выбора цифр квест 4
@router.callback_query(F.data.startswith("select_"), QuestState.waiting_for_selection)
async def handle_number_selection(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    selected_numbers = user_data.get("selected_numbers", set())

    number = int(callback.data.split("_")[1])
    if number in selected_numbers:
        selected_numbers.remove(number)  # Убираем цифру, если она уже выбрана
    else:
        selected_numbers.add(number)  # Добавляем цифру, если она не выбрана

    await state.update_data(selected_numbers=selected_numbers)
    new_keyboard = quest4_keyboard(selected_numbers)
    if callback.message.reply_markup != new_keyboard:
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)

    await callback.answer()

# Обработчик нажатия "Готово" квест 4
@router.callback_query(F.data == "done", QuestState.waiting_for_selection)
async def handle_done(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    user_data = await state.get_data()
    selected_numbers = user_data.get("selected_numbers", set())

    # Получаем правильный набор цифр для квеста 4
    correct_numbers = correct_numbers_qw4  # {1, 2, 3, 4, 5}
    total_questions = len(correct_numbers)

    # Проверяем точное соответствие выбранных цифр
    is_correct = selected_numbers == correct_numbers
    # Количество совпадающих цифр (для статистики)
    correct_count = len(selected_numbers.intersection(correct_numbers))

    # Сохраняем результат в базу данных
    async with SessionLocal() as session:
        # Получаем или создаем запись о результате
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 4  # ID квеста 4
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=4,
                state="выполнен" if is_correct else "не выполнен",
                attempt=1,
                result=correct_count  # Сохраняем фактическое количество верных
            )
            session.add(user_result)
        else:
            # Увеличиваем счетчик попыток только если это новая попытка
            if not is_correct and user_result.state != "выполнен":
                user_result.attempt += 1

            # Обновляем результат
            user_result.result = correct_count

            # Устанавливаем статус "выполнен" если ответ правильный
            if is_correct:
                user_result.state = "выполнен"

        await session.commit()

    # Обновляем уровень только если квест выполнен
    if is_correct:
        await update_user_level(callback.from_user.id, session)

    # Вызываем общую функцию завершения квеста
    await finish_quest(callback, state, correct_count, total_questions, 4)
    await callback.answer()


#завершение квеста 5
@router.callback_query(F.data == "finish_quest5")
async def send_for_moderation(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    photos = user_data.get("photos", [])

    if not photos:
        await callback.answer("Вы не отправили ни одного фото!", show_alert=True)
        return

    # Удаляем сообщение с кнопкой "Готово"
    try:
        await callback.message.delete()
    except:
        pass

    # Обновляем статус в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).where(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 5
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=5,
                state="на модерации",
                attempt=1,
                result=0
            )
            session.add(user_result)

        if user_result:
            user_result.state = "на модерации"
        await session.commit()

    # Получаем информацию о пользователе для подписи
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"ID: {user.id}"
    caption = (
        f"📸 Квест 5 - Фото зоны\n"
        f"👤 Автор: {user.full_name} ({username})\n"
        f"🕒 Время отправки: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Отправляем фото модератору с подписью к первому фото
    if len(photos) > 1:
        media = []
        # Первое фото с подписью
        media.append(InputMediaPhoto(
            media=photos[0],
            caption=caption
        ))
        # Остальные фото без подписи
        for photo in photos[1:]:
            media.append(InputMediaPhoto(media=photo))

        await callback.bot.send_media_group(admin_chat_id, media)
    else:
        # Если фото одно - отправляем с подписью
        await callback.bot.send_photo(
            admin_chat_id,
            photos[0],
            caption=caption
        )

    # Дополнительная информация для модератора с кнопками
    await callback.bot.send_message(
        admin_chat_id,
        f"Выберите действие для квеста 5 от {user.full_name}:",
        reply_markup=moderation_keyboard(
            user_id=callback.from_user.id,
            quest_id=5
        )
    )

    # Финальное сообщение пользователю
    await callback.message.answer(
        "✅ Все фото отправлены на модерацию. Ожидай проверки.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await track_quest_time(callback.from_user.id, 5, is_start=False, state=state)
    await state.clear()
    await callback.answer()



# Квест 10 - Внешний вид
# Добавим в начало файла quests.py
QUEST10_CORRECT_ANSWERS = {
    "Мужской": {
        "head": 4,  # Правильный вариант для головы (мужчина)
        "top": 3,  # Правильный вариант для верха (мужчина)
        "badge": 2,  # Правильный вариант для бейджа (мужчина)
        "bottom": 4,  # Правильный вариант для низа (мужчина)
        "shoes": 4  # Правильный вариант для обуви (мужчина)
    },
    "Женский": {
        "head": 3,  # Правильный вариант для головы (женщина)
        "top": 4,  # Правильный вариант для верха (женщина)
        "badge": 4,  # Правильный вариант для бейджа (женщина)
        "bottom": 3,  # Правильный вариант для низа (женщина)
        "shoes": 4  # Правильный вариант для обуви (женщина)
    }
}

# Добавляем функцию для получения заголовка этапа
def get_step_caption(step: str) -> str:
    captions = {
        "head": "1️⃣ Голова\n\nВыбери, какая причёска и головной убор в тему LiveFoto:",
        "top": "2️⃣ Верх\n\nКрутая футболка с логотипом или что-то отстойное?",
        "badge": "3️⃣ Бейдж\n\nИмя+роль на шее — или пустой холст для «посторонних»?",
        "bottom": "4️⃣ Низ\n\nДжинсы без дыр или «это на вырост»?",
        "shoes": "5️⃣ Обувь\n\nСменка, в которой можно бежать за идеальным кадром:"
    }
    return captions.get(step, "Выберите правильный вариант")

async def quest_10(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "photo_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["photo_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Получаем пол пользователя из базы данных
    async with SessionLocal() as session:
        user = await session.execute(
            select(User).filter(User.telegram_id == callback.from_user.id)
        )
        user = user.scalars().first()
        gender = user.gender if user else None

    if not gender:
        await callback.message.answer("Не удалось определить ваш пол. Пожалуйста, обновите данные профиля.")
        return

    # Сохраняем пол в состоянии
    await state.update_data(
        gender=gender,
        current_step="head",
        correct_count=0,
        total_steps=5
    )

    text = """
👔 *Квест 10: Внешний вид профи*  
Ты — лицо LiveFoto, и первые 3 секунды клиент оценивает тебя по луку. Давай прокачаем скилл *"Dress to impress"*! 🚀  

🔝 *Верх (лето/в помещении):*  
    - Фирменная футболка или толстовка с логотипом LiveFoto  
    - Бейдж с твоим именем и ролью (или общий «Фотограф»)  
    - Чистая причёска, аккуратная борода/усы или гладко выбритое лицо  
    - Шапка/кепка только после согласования (если нужно)  

🔽 *Низ (в помещении):*  
    - Штаны/джинсы/леггинсы без дыр и ярких принтов  
    - Носки однотонные, тёмные  
    - Сменная обувь: кеды, кроссовки или лаконичные слипоны  

💦 *Для аквапарков:*  
    Всё то же, но без кед и толстовок — берём шорты и лотники, чтобы не утонуть в стиле 🌊  

📲 *Готов прокачать лук?* Жми *"Начать"* и пойдём дальше!  
"""
    # Отправляем инструкцию
    message = await callback.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=quest10_start_keyboard()
    )

    await state.update_data(photo_message_id=message.message_id)
    await callback.answer()


@router.callback_query(F.data == "start_quest10")
async def start_quest10(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущее сообщение
    await callback.message.delete()

    # Начинаем первый этап
    user_data = await state.get_data()
    await show_quest10_step(callback, state, user_data["current_step"])
    await callback.answer()


async def show_quest10_step(callback: types.CallbackQuery, state: FSMContext, step: str):
    user_data = await state.get_data()
    gender = user_data.get("gender")

    # Определяем папку с изображениями в зависимости от пола и этапа
    gender_folder = "male" if gender == "Мужской" else "female"
    step_folders = {
        "head": "head",
        "top": "top",
        "badge": "badge",
        "bottom": "bottom",
        "shoes": "shoes"
    }

    photo_dir = BASE_DIR / f"handlers/media/photo/appearance/{gender_folder}/{step_folders[step]}"

    # Получаем список фото и перемешиваем
    try:
        photo_paths = list(photo_dir.glob("*.png"))

        if not photo_paths:
            await callback.message.answer("Изображения для этого этапа не найдены.")
            return

        # Создаем медиагруппу
        album_builder = MediaGroupBuilder(
            caption=get_step_caption(step)
        )

        for i, photo_path in enumerate(photo_paths[:4], 1):  # Берем первые 5 фото
            album_builder.add_photo(
                media=FSInputFile(str(photo_path)),
                caption=f"Вариант {i}"
            )

        # Отправляем медиагруппу
        sent_messages = await callback.message.answer_media_group(media=album_builder.build())

        # Получаем правильный ответ для этого этапа и пола
        correct_answer = QUEST10_CORRECT_ANSWERS[gender][step]

        # Отправляем клавиатуру для выбора
        message = await callback.message.answer(
            get_step_caption(step) + "\nВыбери правильный вариант (1-4):",
            reply_markup=quest10_choice_keyboard(step)
        )

        # Сохраняем данные для последующей проверки
        await state.update_data(
            current_step=step,
            photo_message_ids=[m.message_id for m in sent_messages],
            choice_message_id=message.message_id,
            correct_answer=correct_answer
        )
    except Exception as e:
        print(f"Ошибка при загрузке изображений: {e}")
        await callback.message.answer("Произошла ошибка при загрузке заданий. Попробуйте позже.")
        await state.clear()


@router.callback_query(F.data.startswith("qw10_choose_"))
async def handle_quest10_choice(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    step = parts[2]
    chosen_answer = int(parts[3])

    user_data = await state.get_data()
    correct_answer = user_data.get("correct_answer")
    correct_count = user_data.get("correct_count", 0)

    # Проверяем ответ
    if chosen_answer != correct_answer:
        await callback.answer("❌ Неверный выбор! Попробуйте еще раз.", show_alert=True)
        return

    # Увеличиваем счетчик правильных ответов
    correct_count += 1
    await state.update_data(correct_count=correct_count)

    # Удаляем предыдущие сообщения
    try:
        if "photo_message_ids" in user_data:
            for msg_id in user_data["photo_message_ids"]:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
        if "choice_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["choice_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Определяем следующий этап
    next_steps = ["head", "top", "badge", "bottom", "shoes"]
    current_index = next_steps.index(step)

    if current_index < len(next_steps) - 1:
        # Переходим к следующему этапу
        next_step = next_steps[current_index + 1]
        await state.update_data(current_step=next_step)
        await show_quest10_step(callback, state, next_step)
    else:
        # Все этапы пройдены
        await finish_quest10(callback, state)

    await callback.answer()


async def finish_quest10(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    correct_count = user_data.get("correct_count", 0)
    total_steps = user_data.get("total_steps", 5)
    current_quest_id = 10  # ID текущего квеста

    # Сохраняем результат в БД
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
                state="выполнен",
                attempt=1,
                result=int((correct_count / total_steps) * 100)
            )
            session.add(user_result)
        else:
            user_result.state = "выполнен"
            user_result.result = int((correct_count / total_steps) * 100)

        await session.commit()

    # Используем общую функцию завершения квеста
    await finish_quest(callback, state, correct_count, total_steps, current_quest_id)
    await callback.answer()

# Квест 11 - Фидбек по первому дню
async def quest_11(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем предыдущие сообщения
    user_data = await state.get_data()
    try:
        await callback.message.delete()
        if "question_message_id" in user_data:
            await callback.bot.delete_message(callback.message.chat.id, user_data["question_message_id"])
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем фидбек
    message = await callback.message.answer(
        "🎤 *Квест 11: Фидбек по первому дню*\n\n"
        "Мы знаем, что ты суров, но даже суровые иногда нуждаются в обратке 😉\n"
        "Расскажи, как прошёл твой первый день: честно, с эмодзи и без стеснения!\n\n"
        "1️⃣  Насколько ты понял(а) условия работы после звонка от HR?\n"
        "(1 = вообще не вкурил, 5 = как профи всё в голове)",
        reply_markup=quest11_rating_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        feedback_data={},
        current_step="hr_rating"
    )
    await state.set_state(QuestState.waiting_for_hr_rating)
    await callback.answer()


# Обработчики для каждого вопроса фидбека
@router.callback_query(F.data.startswith("rating_"), QuestState.waiting_for_hr_rating)
async def handle_hr_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])

    await state.update_data(feedback_data={"hr_rating": rating})
    await callback.message.delete()

    message = await callback.message.answer(
        "2️⃣ Как прошёл сам интро-чек (интервью + встреча в локации)?",
        reply_markup=quest11_interview_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step="interview"
    )
    await state.set_state(QuestState.waiting_for_interview)
    await callback.answer()


@router.callback_query(F.data.startswith("interview_"), QuestState.waiting_for_interview)
async def handle_interview(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["interview"] = answer

    await state.update_data(feedback_data=feedback_data)
    await callback.message.delete()

    message = await callback.message.answer(
        "3️⃣ *Что можно прокачать на этапе знакомства?*\n\n"
        "(телефонный HR + очная встреча)\n"
        "Напиши свой инсайт текстом ниже:"
        , parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step="improvement"
    )
    await state.set_state(QuestState.waiting_for_improvement)
    await callback.answer()


@router.message(QuestState.waiting_for_improvement)
async def handle_improvement(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите текст.")
        return

    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["improvement"] = message.text

    await state.update_data(feedback_data=feedback_data)
    await message.delete()

    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    question = await message.answer(
        "4️⃣ *Почему ты решил(а) стать частью команды?*",
        reply_markup=quest11_reason_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=question.message_id,
        current_step="reason"
    )
    await state.set_state(QuestState.waiting_for_reason)


@router.callback_query(F.data.startswith("reason_"), QuestState.waiting_for_reason)
async def handle_reason(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["reason"] = answer

    await state.update_data(feedback_data=feedback_data)
    await callback.message.delete()

    message = await callback.message.answer(
        "5️⃣ *Оцени приложение (1 = жутко неудобно, 5 = бомба бомбой)!*",
        reply_markup=quest11_rating_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step="app_rating"
    )
    await state.set_state(QuestState.waiting_for_app_rating)
    await callback.answer()


@router.callback_query(F.data.startswith("rating_"), QuestState.waiting_for_app_rating)
async def handle_app_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["app_rating"] = rating

    await state.update_data(feedback_data=feedback_data)
    await callback.message.delete()

    message = await callback.message.answer(
        "6️⃣ *Насколько ты теперь шаришь локацию благодаря приложению?*\n"
        "(1 = как в лабиринте без карты, 5 = гугл-карты отдыхают)",
        reply_markup=quest11_rating_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step="location_rating"
    )
    await state.set_state(QuestState.waiting_for_location_rating)
    await callback.answer()


@router.callback_query(F.data.startswith("rating_"), QuestState.waiting_for_location_rating)
async def handle_location_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["location_rating"] = rating

    await state.update_data(feedback_data=feedback_data)
    await callback.message.delete()

    message = await callback.message.answer(
        "*7️⃣ Как тебе рабочее место (база)?*",
        reply_markup=quest11_base_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step="base"
    )
    await state.set_state(QuestState.waiting_for_base)
    await callback.answer()


@router.callback_query(F.data.startswith("base_"), QuestState.waiting_for_base)
async def handle_base(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["base"] = answer

    await state.update_data(feedback_data=feedback_data)
    await callback.message.delete()

    message = await callback.message.answer(
        "8️⃣ *Какая продукция понравилась больше всего и почему?*\n\n"
        "Напиши в свободной форме — мы любим длинные тексты! 🖊"
        , parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step="product"
    )
    await state.set_state(QuestState.waiting_for_product)


@router.message(QuestState.waiting_for_product)
async def handle_product(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите текст.")
        return

    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["product"] = message.text

    await state.update_data(feedback_data=feedback_data)
    await message.delete()

    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    question = await message.answer(
        "9️⃣ Стоит ли знанию техники продаж уделять внимание?",
        reply_markup=quest11_sales_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=question.message_id,
        current_step="sales"
    )
    await state.set_state(QuestState.waiting_for_sales)


@router.callback_query(F.data.startswith("sales_"), QuestState.waiting_for_sales)
async def handle_sales(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["sales"] = answer

    await state.update_data(feedback_data=feedback_data)
    await callback.message.delete()

    message = await callback.message.answer(
        "🔟 *Насколько тебе комфортно в коллективе?*",
        reply_markup=quest11_team_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step="team"
    )
    await state.set_state(QuestState.waiting_for_team)
    await callback.answer()


@router.callback_query(F.data.startswith("team_"), QuestState.waiting_for_team)
async def handle_team(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["team"] = answer

    await state.update_data(feedback_data=feedback_data)
    await callback.message.delete()

    message = await callback.message.answer(
        "Как тебе форма?",
        reply_markup=quest11_uniform_keyboard()
    )

    await state.update_data(
        question_message_id=message.message_id,
        current_step="uniform"
    )
    await state.set_state(QuestState.waiting_for_uniform)
    await callback.answer()


@router.callback_query(F.data.startswith("uniform_"), QuestState.waiting_for_uniform)
async def handle_uniform(callback: types.CallbackQuery, state: FSMContext):
    answer = callback.data.split("_")[1]
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["uniform"] = answer

    if answer == "4":
        # Если выбрано "Есть предложения по изменению"
        await callback.message.delete()
        message = await callback.message.answer(
            "Напиши свои предложения по изменению формы:"
            , parse_mode='Markdown'
        )

        await state.update_data(
            question_message_id=message.message_id,
            current_step="uniform_suggestions"
        )
        await state.set_state(QuestState.waiting_for_uniform_suggestions)
    else:
        await state.update_data(feedback_data=feedback_data)
        await callback.message.delete()

        message = await callback.message.answer(
            "Спасибо за фидбек! Проверь свои ответы и нажми 'Отправить'.",
            reply_markup=quest11_finish_keyboard(), parse_mode='Markdown'
        )

        await state.update_data(
            question_message_id=message.message_id,
            current_step="finish"
        )

    await callback.answer()


@router.message(QuestState.waiting_for_uniform_suggestions)
async def handle_uniform_suggestions(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите текст.")
        return

    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})
    feedback_data["uniform_suggestions"] = message.text

    await state.update_data(feedback_data=feedback_data)
    await message.delete()

    if "question_message_id" in user_data:
        try:
            await message.bot.delete_message(message.chat.id, user_data["question_message_id"])
        except:
            pass

    question = await message.answer(
        "Спасибо за фидбек! Проверь свои ответы и нажми 'Отправить'.",
        reply_markup=quest11_finish_keyboard(), parse_mode='Markdown'
    )

    await state.update_data(
        question_message_id=question.message_id,
        current_step="finish"
    )


@router.callback_query(F.data == "finish_quest11")
async def finish_quest11(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    feedback_data = user_data.get("feedback_data", {})

    # Формируем отчет для модератора
    report_text = "📋 Фидбек по первому дню:\n\n"
    report_text += f"👤 Сотрудник: {callback.from_user.full_name} (@{callback.from_user.username or 'нет'})\n"
    report_text += f"📅 Дата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"

    report_text += f"1. Понятность условий после HR: {feedback_data.get('hr_rating', 'нет ответа')}/5\n"
    report_text += f"2. Впечатления от собеседования: {feedback_data.get('interview', 'нет ответа')}\n"
    report_text += f"3. Что улучшить: {feedback_data.get('improvement', 'нет ответа')}\n"
    report_text += f"4. Причина вступления в команду: {feedback_data.get('reason', 'нет ответа')}\n"
    report_text += f"5. Оценка приложения: {feedback_data.get('app_rating', 'нет ответа')}/5\n"
    report_text += f"6. Ориентация на локации: {feedback_data.get('location_rating', 'нет ответа')}/5\n"
    report_text += f"7. Рабочее место (база): {feedback_data.get('base', 'нет ответа')}\n"
    report_text += f"8. Любимая продукция: {feedback_data.get('product', 'нет ответа')}\n"
    report_text += f"9. Нужно ли изучать технику продаж: {feedback_data.get('sales', 'нет ответа')}\n"
    report_text += f"10. Комфорт в коллективе: {feedback_data.get('team', 'нет ответа')}\n"
    report_text += f"11. Форма: {feedback_data.get('uniform', 'нет ответа')}\n"

    if "uniform_suggestions" in feedback_data:
        report_text += f"12. Предложения по форме: {feedback_data['uniform_suggestions']}\n"

    # Отправляем модератору
    await callback.bot.send_message(
        admin_chat_id,
        report_text
    )

    # Сохраняем в БД
    async with SessionLocal() as session:
        user_result = await session.execute(
            select(UserResult).filter(
                UserResult.user_id == callback.from_user.id,
                UserResult.quest_id == 11
            )
        )
        user_result = user_result.scalars().first()

        if not user_result:
            user_result = UserResult(
                user_id=callback.from_user.id,
                quest_id=11,
                state="выполнен",
                attempt=1,
                result=100
            )
            session.add(user_result)
        else:
            user_result.state = "выполнен"

        await update_user_level(callback.from_user.id, session)

        await update_user_day(callback.from_user.id, session)


        await session.commit()

    # Завершаем квест
    await callback.message.delete()
    await callback.message.answer(
"""🚀 Спасибо за фидбек!

Ты помог(ла) нам стать лучше. За твою откровенность уже летит ачивка в профиль! 🎖
Вместе создаём идеальную фотокоманду!

🎉 Отличная работа в День 1! 🎉
Ты:
    - Ознакомился(лась) с приложением и прокачал(а) навигацию
    - Познакомился(лась) с командой и системой квестов
    - Изучил(а) локацию, разобрал(а) квесты и задания
    - Разобрал(а) товары, цены и теорию продаж
    - Собрал(а) идеальный образ согласно дресс-коду
    - Оставил(а) ценный фидбэк и помог(ла) улучшить процесс
    
Давай взглянем на все твои достижения за первый день и немного передахнем! Кликай на «Профиль». Отдыхай, заряжайся и готовься к новым челленджам! Как будешь готов продолжить, заходи в «Квесты» и покоряй новые вершины!
""",
        reply_markup=go_profile_keyboard()

    )
    await track_quest_time(callback.from_user.id, 11, is_start=False, state=state)


    await state.clear()
    await callback.answer()

