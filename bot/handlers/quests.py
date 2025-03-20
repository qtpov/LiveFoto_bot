from aiogram import Router, types, F
from aiogram.types import  FSInputFile
from bot.db.models import UserResult, User, Achievement
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline import *
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from aiogram.utils.media_group import MediaGroupBuilder
from pathlib import Path
from bot.db.crud import update_user_level
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
    5: 'Демонстрация'

}

# Базовый путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent

# Состояния для FSM
class QuestState(StatesGroup):
    waiting_for_answer = State()

# Получение текущего дня пользователя
async def get_current_day(user_id: int):
    async with SessionLocal() as session:
        user = await session.execute(select(User).filter(User.telegram_id == user_id))
        user = user.scalars().first()
        if not user:
            return None
        return user.day

# Функция для создания клавиатуры с кнопками "Переделать" и "Далее"
def get_quest_finish_keyboard(correct_count, total_questions, current_quest_id):
    builder = InlineKeyboardBuilder()
    if correct_count < total_questions:
        builder.add(types.InlineKeyboardButton(
            text="Переделать",
            callback_data=f"retry_quest_{current_quest_id}"
        ))
    else:
        builder.add(types.InlineKeyboardButton(
            text="Далее",
            callback_data=f"next_quest_{current_quest_id}"
        ))
    return builder.as_markup()

# Словарь с ачивками для каждого квеста
achievements_text = {
    1: {
        "name": "🗺️ Я тут всё знаю!",
        "description": "Вы успешно выполнили квест 'Знакомство с локацией'!"
    },
    2: {
        "name": "📸 Лучший ракурс!",
        "description": "Вы успешно выполнили квест 'Места для фоток'!"
    },
    3: {
        "name": "🗂️ Свой среди своих!",
        "description": "Вы успешно выполнили квест 'Знакомство с базой'!"
    },
    4: {
        "name": "✨ Чисто, как в объективе!",
        "description": "Вы успешно выполнили квест 'Чистота на локации'!"
    },
    5: {
        "name": "🎯 Секретные точки!",
        "description": "Вы успешно выполнили квест 'Места для фото 2.0'!"
    },
    6: {
        "name": "🤳  Первый кадр!",
        "description": "Вы успешно выполнили квест 'Фото с клиентом'!"
    },
    7: {
        "name": "✨ Чисто, как в объективе!",
        "description": "Вы успешно выполнили квест 'Чистота на локации'!"
    },
    8: {
        "name": "💰 Знаю, что продать!",
        "description": "Вы успешно выполнили квест 'Товары и цены'!"
    },
    9: {
        "name": "🎓 Маркетолог от природы!",
        "description": "Вы успешно выполнили квест 'Теория продаж'!"
    },
    10: {
        "name": "🤝 Теперь нас больше!",
        "description": "Вы успешно выполнили квест 'Знакомство с коллегами'!"
    },
    10: {
        "name": "👔 Стиль – моё второе имя!",
        "description": "Вы успешно выполнили квест 'Внешний вид'!"
    },
    11: {
        "name": "🗣️ Голос дня!",
        "description": "Вы успешно выполнили квест 'Фидбек'!"
    },

    # Добавьте остальные ачивки по аналогии
}


# Функция для обновления уровня пользователя


# Функция для выдачи ачивки
async def give_achievement(user_id: int, quest_id: int, session):
    # # Проверяем, выполнено ли 100% квеста
    # user_result = await session.execute(
    #     select(UserResult).filter(
    #         UserResult.user_id == user_id,
    #         UserResult.quest_id == quest_id
    #     )
    # )
    # user_result = user_result.scalars().first()


    # Проверяем, есть ли уже такая ачивка у пользователя
    achievement = await session.execute(
        select(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.name == achievements_text[quest_id]["name"]
        )
    )
    achievement = achievement.scalars().first()

    if not achievement:
        # Добавляем ачивку с описанием
        new_achievement = Achievement(
            name=achievements_text[quest_id]["name"],
            description=achievements_text[quest_id]["description"],
            user_id=user_id
        )
        session.add(new_achievement)
        await session.commit()
        return True

    return False

# Функция для завершения квеста
async def finish_quest(callback: types.CallbackQuery, state: FSMContext, correct_count, total_questions, current_quest_id):
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
    user_data = await state.get_data()
    question_message_id = user_data.get("question_message_id")

    await callback.message.delete()

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
        quests_text = "📋 Квесты на сегодня:\n"
        for quest_id, quest_name in quests_today:
            status = "Не выполнен"
            if quest_id in user_results_dict:
                if user_results_dict[quest_id].state == "выполнен":
                    status = "✅ Выполнен"
            quests_text += f"{quest_id}. {quest_name} — {status}\n"

        # Отправляем сообщение с квестами
        await callback.message.edit_text(quests_text, reply_markup=quests_list_keyboard())

# Клавиатура для списка квестов
def quests_list_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Начать квесты",
        callback_data="start_quests_confirm"
    ))
    return builder.as_markup()


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
            await callback.message.answer("Все квесты на сегодня выполнены! 🎉")
            return

        # Начинаем первый невыполненный квест
        await start_quest(callback, state, first_uncompleted_quest)
    await callback.answer()


# @router.callback_query(F.data == "quests")
# async def start_quests(callback: types.CallbackQuery, state: FSMContext):
#     user_id = callback.from_user.id
#     current_day = await get_current_day(user_id)
#
#     if not current_day:
#         await callback.message.answer("Ты ещё не зарегистрирован! Напиши /start.")
#         return
#
#     async with SessionLocal() as session:
#         quests_today = quests_by_day.get(current_day, [])
#         user_results = await session.execute(
#             select(UserResult).filter(
#                 UserResult.user_id == user_id,
#                 UserResult.quest_id.in_([quest[0] for quest in quests_today])
#             )
#         )
#         user_results = user_results.scalars().all()
#         user_results_dict = {result.quest_id: result for result in user_results}
#
#         first_uncompleted_quest = None
#         for quest_id, _ in quests_today:
#             if quest_id not in user_results_dict or user_results_dict[quest_id].state != "выполнен":
#                 first_uncompleted_quest = quest_id
#                 break
#
#         if first_uncompleted_quest is None:
#             await callback.message.answer("Все квесты на сегодня выполнены! 🎉")
#             return
#
#         await start_quest(callback, state, first_uncompleted_quest)
#     await callback.answer()

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
        caption=f"Квест 1: Вопрос {current_question}\n"
                f"Перед тобой карта парка, выбери кнопкой внизу, что находится под номером {current_question}",
        reply_markup=quest1_keyboard()
    )
    await state.update_data(photo_message_id=message.message_id)

    await callback.answer()

# Квест 2
async def quest_2(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_question = user_data.get("current_question", 1)
    correct_count = user_data.get("correct_count", 0)

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
    photo_path1 = BASE_DIR / f"handlers/media/photo/Zone/{folder_name}/1.jpg"
    photo_path2 = BASE_DIR / f"handlers/media/photo/Zone/{folder_name}/2.jpg"

    if not photo_path1.exists() or not photo_path2.exists():
        await callback.message.answer("Файлы с изображениями не найдены.")
        return

    album_builder = MediaGroupBuilder(caption=f"Квест 2: Вопрос {current_question}\n"
                                            "Определи на какой локации сделаны фото\n"
                                            f"Верных ответов: {correct_count} из {len(correct_answers_qw2)}")
    album_builder.add(type="photo", media=FSInputFile(str(photo_path1)))
    album_builder.add(type="photo", media=FSInputFile(str(photo_path2)))

    # Отправляем новую медиагруппу
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

    # Список file_id видео
    file_ids = [
        "BAACAgIAAxkBAAIQbGfZ6i6PSqfFkwEviKkeTzjSIq07AAIcdQACA47RSsKNwE8ZB6jMNgQ",
        "BAACAgIAAxkBAAIQb2fZ7BlHovx8Xp1lXQULoPC9TQodAAIqdQACA47RStHyr_i86-BDNgQ",
        "BAACAgIAAxkBAAIQcWfZ7JauvtWMaVmGZURQAzGYZKcgAAItdQACA47RSmhTstArUV9lNgQ",
        "BAACAgIAAxkBAAIQc2fZ7KUbwPbvvLzZkvlXEpkreZBEAAIudQACA47RSlZ0vju21gr_NgQ",
        "BAACAgIAAxkBAAIQdWfZ7_pGQdK3VOE928wyF3OS2NOLAAI2dQACA47RSpceq4CXeMQSNgQ",
    ]

    # Создаём медиагруппу
    album_builder = MediaGroupBuilder()

    # Добавляем видео в медиагруппу по их file_id
    for file_id in file_ids:
        album_builder.add(type="video", media=file_id)

    try:
        # Отправляем медиагруппу
        sent_messages = await callback.message.answer_media_group(media=album_builder.build())
        video_message_ids = [msg.message_id for msg in sent_messages]

        # Отправляем сообщение с клавиатурой
        question_message = await callback.message.answer(
            "Квест 3: \nПосмотри видео и приступи к выполнению квеста",
            reply_markup=quest3_keyboard_after_video()
        )

        # Сохраняем ID всех сообщений для последующего удаления
        await state.update_data(
            video_message_ids=video_message_ids,
            question_message_id=question_message.message_id
        )

        # Переводим состояние в waiting_for_answer
        await state.set_state(QuestState.waiting_for_answer)

    except Exception as e:
        print(f"Ошибка при отправке медиагруппы: {e}")
        await callback.message.answer("Произошла ошибка при отправке видео. Попробуйте ещё раз.")

    await callback.answer()



# Квест 4
# Верные цифры для квеста 4
correct_numbers_qw4 = {1, 2, 3, 4, 5}

# Состояния для FSM
class Quest4State(StatesGroup):
    waiting_for_clean_photo = State()
    waiting_for_items_photo = State()
    waiting_for_dirty_photo = State()
    waiting_for_selection = State()

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
        caption="Чистая локация. Нажмите 'Далее', чтобы продолжить.",
        reply_markup=quest4_keyboard_after_clear()
    )

    # Сохраняем ID сообщения для последующего удаления
    await state.update_data(photo_message_ids=[message.message_id])
    await state.set_state(Quest4State.waiting_for_clean_photo)
    await callback.answer()

# Показываем фото "предметы, которые не должны находиться на локации"
@router.callback_query(F.data == "next_to_items", Quest4State.waiting_for_clean_photo)
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
    media_group = MediaGroupBuilder(caption="Предметы, которые не должны находиться на локации.")

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
        "Нажмите 'Приступить', чтобы начать.",
        reply_markup=quest4_keyboard_after_trash()
    )

    # Сохраняем ID всех сообщений для последующего удаления
    await state.update_data(
        photo_message_ids=photo_message_ids,
        question_message_id=question_message.message_id
    )
    await state.set_state(Quest4State.waiting_for_items_photo)
    await callback.answer()

# Показываем фото "грязной локации" и клавиатуру для выбора цифр
@router.callback_query(F.data == "start_selection", Quest4State.waiting_for_items_photo)
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
        caption="Выбери цифры, которые НЕ соответствуют 'Чистой локации'."
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
    await state.set_state(Quest4State.waiting_for_selection)
    await callback.answer()

# Обработчик выбора цифр
@router.callback_query(F.data.startswith("select_"), Quest4State.waiting_for_selection)
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
@router.callback_query(F.data == "done", Quest4State.waiting_for_selection)
async def handle_done(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    user_data = await state.get_data()
    selected_numbers = user_data.get("selected_numbers", set())

    # Проверяем выбранные цифры
    correct_selected = selected_numbers.intersection(correct_numbers_qw4)
    correct_count = len(correct_selected)  # Количество правильных ответов
    total_questions = len(correct_numbers_qw4)  # Общее количество вопросов

    # Сохраняем результат в базу данных
    async with SessionLocal() as session:
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
                state="не выполнен",
                attempt=1,
                result=correct_count
            )
            session.add(user_result)
        else:
            user_result.result = correct_count
            if correct_count == total_questions:
                user_result.state = "выполнен"

        await session.commit()
        # Обновляем уровень пользователя
        await update_user_level(callback.from_user.id, session)

    # Вызываем общую функцию завершения квеста
    await finish_quest(callback, state, correct_count, total_questions, 4)  # 4 — ID квеста
    await callback.answer()



# Обработчик ответов для квеста 1
@router.callback_query(F.data.in_(correct_answers.values()), QuestState.waiting_for_answer)
async def handle_quest1_answer(callback: types.CallbackQuery, state: FSMContext):
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

    # Обновляем состояние FSM
    await state.update_data(correct_count=correct_count)

    # Переход к следующему вопросу или завершение квеста
    current_question += 1
    if current_question > len(correct_answers):
        await callback.message.delete()
        await finish_quest(callback, state, correct_count, len(correct_answers), current_quest_id)
    else:
        await state.update_data(current_question=current_question)
        await quest_1(callback, state)  # Запускаем следующий вопрос

    await callback.answer()

# Обработчик ответов для квеста 2
@router.callback_query(F.data.in_(correct_answers_qw2.values()), QuestState.waiting_for_answer)
async def handle_quest2_answer(callback: types.CallbackQuery, state: FSMContext):
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

        if callback.data == correct_answers_qw2[current_question]:
            correct_count += 1
            user_result.result += 1
            await callback.answer('Верный ответ!')
        else:
            await callback.answer('Ответ неверный.')

        if current_question == len(correct_answers_qw2):
            user_result.state = "выполнен"

        await session.commit()

    await state.update_data(correct_count=correct_count)

    current_question += 1
    if current_question > len(correct_answers_qw2):
        await callback.message.delete()
        await finish_quest(callback, state, correct_count, len(correct_answers_qw2), current_quest_id)
        await update_user_level(callback.from_user.id, session)
    else:
        await state.update_data(current_question=current_question)
        await quest_2(callback, state)

    await callback.answer()

# Обработчик ответов для квеста 3
@router.callback_query(F.data == "complete_video_qw3", QuestState.waiting_for_answer)
async def start_quest3_questions(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    # Удаляем оба сообщения (медиагруппу и сообщение с кнопкой "Приступить")
    try:
        video_message_ids = user_data.get("video_message_ids", [])
        question_message_id = user_data.get("question_message_id")

        for message_id in video_message_ids:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        if question_message_id:
            await callback.bot.delete_message(callback.message.chat.id, question_message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")

    # Начинаем с первого вопроса
    await state.update_data(current_question=1, correct_count=0)
    await ask_quest3_question(callback, state)

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
    question_text = f"Квест 3: Вопрос {current_question}\nВыбери правильный вариант:"
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


# Обработчик для всех остальных ответов
@router.callback_query(QuestState.waiting_for_answer)
async def handle_other_answers(callback: types.CallbackQuery):
    # Уведомляем пользователя, что ответ неверный
    await callback.answer("Ответ неверный. Попробуйте ещё раз!")
