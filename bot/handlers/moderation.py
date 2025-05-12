from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from .states import QuestState
from bot.db.session import SessionLocal
from bot.db.crud import update_user_level
from bot.db.models import Achievement, UserResult
from sqlalchemy.future import select
from .states import QuestState
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder

moderation_router = Router()



# Словарь с ачивками для каждого квеста
achievements_text = {
    # День 1
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
        "name": "🤳 Первый кадр!",
        "description": "Вы успешно выполнили квест 'Фото с клиентом'!"
    },
    7: {
        "name": "💰 Знаю, что продать!",
        "description": "Вы успешно выполнили квест 'Товары и цены'!"
    },
    8: {
        "name": "🎓 Маркетолог от природы!",
        "description": "Вы успешно выполнили квест 'Теория продаж'!"
    },
    9: {
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

    # День 2
    12: {
        "name": "📷 Я – камера, я – объектив!",
        "description": "Вы успешно выполнили квест 'Привыкни к аппарату'!"
    },
    13: {
        "name": "🖼️ Настоящий профи!",
        "description": "Вы успешно выполнили квест 'Фотограф'!"
    },
    14: {
        "name": "📌 Лучший фон найден!",
        "description": "Вы успешно выполнили квест 'Зоны фотографирования'!"
    },
    15: {
        "name": "🤩 Модельный агент!",
        "description": "Вы успешно выполнили квест '1000 и 1 поза'!"
    },
    16: {
        "name": "💪 До победного!",
        "description": "Вы успешно выполнили квест 'Дожми до результата'!"
    },
    17: {
        "name": "🏋️ Энергия на максимум!",
        "description": "Вы успешно выполнили квест 'В здоровом теле здоровый дух'!"
    },
    18: {
        "name": "📷 Мастер кадра!",
        "description": "Вы успешно выполнили квест 'Практика фотографирования'!"
    },
    19: {
        "name": "🔄 Всё по плану!",
        "description": "Вы успешно выполнили квест 'Алгоритм действий'!"
    },
    20: {
        "name": "⏳ Ловлю момент!",
        "description": "Вы успешно выполнили квест 'Время и кадры'!"
    },
    21: {
        "name": "🤗 Свой в доску!",
        "description": "Вы успешно выполнили квест 'Знакомство с коллегами'!"
    },
    22: {
        "name": "🛍️ Поэтапный успех!",
        "description": "Вы успешно выполнили квест 'Этапы продаж'!"
    },
    23: {
        "name": "⚡ Молниеносный мастер!",
        "description": "Вы успешно выполнили квест 'Подошёл, сфоткал, победил'!"
    },
    24: {
        "name": "💵 Первый кешбек!",
        "description": "Вы успешно выполнили квест '5 продаж'!"
    },
    25: {
        "name": "🚀 Каждое «нет» ведёт к «да»!",
        "description": "Вы успешно выполнили квест 'Сила отказов'!"
    },
    26: {
        "name": "📊 Разбор полётов!",
        "description": "Вы успешно выполнили квест 'Фидбек'!"
    },

    # День 3
    27: {
        "name": "✅ Золотое сечение!",
        "description": "Вы успешно выполнили квест 'Правильное фото'!"
    },
    28: {
        "name": "🎯 Рабочий механизм!",
        "description": "Вы успешно выполнили квест 'Собери всё'!"
    },
    29: {
        "name": "🦅 Охотник за удачными моментами!",
        "description": "Вы успешно выполнили квест 'ФотоОхотник'!"
    },
    30: {
        "name": "🔄 От кадра до продажи!",
        "description": "Вы успешно выполнили квест 'Полный цикл'!"
    },
    31: {
        "name": "💎 Фото на миллион!",
        "description": "Вы успешно выполнили квест 'Ценность кадра'!"
    },
    32: {
        "name": "🏅 Верю в миссию!",
        "description": "Вы успешно выполнили квест 'Ценности компании'!"
    },
    33: {
        "name": "😊 Клиент всегда доволен!",
        "description": "Вы успешно выполнили квест 'Клиент'!"
    },
    34: {
        "name": "🏆 Растём и развиваемся!",
        "description": "Вы успешно выполнили квест 'Фидбек'!"
    }
}


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

# Функция для выдачи ачивки
async def give_achievement(user_id: int, quest_id: int, session):

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


@moderation_router.callback_query(F.data.startswith(("accept_", "reject_")))
async def handle_moderation(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Разбираем callback_data
        action, user_id_str, quest_id_str = callback.data.split('_')
        user_id = int(user_id_str)
        quest_id = int(quest_id_str)

        # Удаляем сообщение с кнопками
        await callback.message.delete()

        async with SessionLocal() as session:
            # Обновляем статус в БД
            user_result = await session.execute(
                select(UserResult).where(
                    UserResult.user_id == user_id,
                    UserResult.quest_id == quest_id
                )
            )
            user_result = user_result.scalars().first()

            if not user_result:
                await callback.answer("Запись не найдена в базе данных!", show_alert=True)
                return

            if action == "accept":
                # Обновляем статус и результат
                user_result.state = "выполнен"
                user_result.result = 100


                await session.commit()

                # Запрашиваем комментарий
                await state.update_data(
                    target_user_id=user_id,
                    quest_id=quest_id,
                    action="accept"
                )
                await callback.message.answer(
                    "Введите комментарий для пользователя:"
                )
                await state.set_state(QuestState.waiting_for_comment)

            elif action == "reject":
                user_result.state = "не выполнен"

                await session.commit()  # Важно: сохраняем изменения!

                await state.update_data(
                    target_user_id=user_id,
                    quest_id=quest_id,
                    action="reject"
                )
                await callback.message.answer(
                    "Укажите причину отклонения:"
                )
                await state.set_state(QuestState.waiting_for_comment)

    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}")


@moderation_router.message(QuestState.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    comment = message.text

    try:
        if user_data["action"] == "accept":
            # Выдача награды
            async with SessionLocal() as session:
                await give_achievement(user_data["target_user_id"], user_data["quest_id"], session)
                #await update_user_level(user_data["target_user_id"], session)

            await message.bot.send_message(
                user_data["target_user_id"],
                f"✅ Ваш квест {user_data['quest_id']} принят!\nПоздравляем! Вы получили ачивку за выполнение квеста!\nКомментарий: {comment}",
                reply_markup = get_quest_finish_keyboard(100, 100, user_data["quest_id"])
            )

        elif user_data["action"] == "reject":
            await message.bot.send_message(
                user_data["target_user_id"],
                f"❌ Квест {user_data['quest_id']} отклонен\nПричина: {comment}\n\n"
                "Пожалуйста, исправьте и отправьте заново.", reply_markup=get_quest_finish_keyboard(0, 100, user_data["quest_id"])
            )

        await message.answer("Результат отправлен пользователю")
        await state.clear()

    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


#модерация 22 квеста
@moderation_router.callback_query(F.data.startswith("acc_22_"))
async def accept_quest22(callback: types.CallbackQuery):
    try:
        user_id = int(callback.data.split('_')[2])

        # Обновляем статус в БД
        async with SessionLocal() as session:
            user_result = await session.execute(
                select(UserResult).where(
                    UserResult.user_id == user_id,
                    UserResult.quest_id == 22
                )
            )
            user_result = user_result.scalars().first()

            if user_result:
                user_result.state = "выполнен"
                user_result.result = 100  # 100% выполнено

            await session.commit()

            # Даем ачивку
            await give_achievement(user_id, 22, session)

        # Удаляем кнопки и редактируем сообщение
        await callback.message.edit_text(
            "✅ Ответы приняты",
            reply_markup=None
        )

        # Уведомляем пользователя с кнопкой "Далее"
        await callback.bot.send_message(
            user_id,
            "✅ Ваши ответы приняты модератором! Поздравляем с успешным прохождением квеста!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее →", callback_data="next_quest_22")]
            ])
        )

        await callback.answer("Ответы приняты")
    except Exception as e:
        logging.error(f"Ошибка при принятии квеста 22: {e}")
        await callback.answer("⚠️ Ошибка при обработке", show_alert=True)


@moderation_router.callback_query(F.data.startswith("rej_22_"))
async def reject_quest22(callback: types.CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split('_')[2])

        # Получаем текст сообщения с ответами (первые 4000 символов)
        original_text = callback.message.text
        if len(original_text) > 4000:
            original_text = original_text[:4000] + "..."

        # Создаем клавиатуру с вопросами для выбора
        buttons = []
        for q_num in range(1, 13):  # 12 вопросов в квесте 22
            buttons.append(
                InlineKeyboardButton(
                    text=f"Вопрос {q_num}",
                    callback_data=f"select_22_{user_id}_{q_num}"
                )
            )

        # Разбиваем кнопки на ряды по 3
        keyboard = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]

        # Добавляем кнопку завершения выбора
        keyboard.append([
            InlineKeyboardButton(
                text="✅ Завершить выбор",
                callback_data=f"finish_select_22_{user_id}"
            )
        ])

        # Редактируем сообщение, добавляя клавиатуру
        await callback.message.edit_text(
            f"{original_text}\n\nВыберите вопросы, которые нужно переделать:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        # Сохраняем данные в state
        await state.update_data(
            target_user_id=user_id,
            original_message_id=callback.message.message_id,
            selected_questions=[]
        )

        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в reject_quest22: {str(e)}")
        await callback.answer("⚠️ Ошибка при обработке", show_alert=True)


@moderation_router.callback_query(F.data.startswith("select_22_"))
async def select_question(callback: types.CallbackQuery, state: FSMContext):
    try:
        _, _, user_id, q_num = callback.data.split('_')
        question_num = int(q_num)

        # Получаем текущие данные из state
        data = await state.get_data()
        selected_questions = data.get("selected_questions", [])

        # Обновляем список выбранных вопросов
        if question_num in selected_questions:
            selected_questions.remove(question_num)
            selected = False
        else:
            selected_questions.append(question_num)
            selected = True

        await state.update_data(selected_questions=selected_questions)

        # Обновляем текст кнопки
        keyboard = callback.message.reply_markup.inline_keyboard
        for row in keyboard:
            for button in row:
                if button.callback_data == callback.data:
                    button.text = f"{'✅ ' if selected else ''}Вопрос {q_num}"

        # Обновляем сообщение
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        await callback.answer()

    except Exception as e:
        logging.error(f"Ошибка выбора вопроса: {str(e)}")
        await callback.answer("⚠️ Ошибка при выборе", show_alert=True)


@moderation_router.callback_query(F.data.startswith("finish_select_22_"))
async def finish_selection(callback: types.CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback.data.split('_')[3])
        data = await state.get_data()
        selected_questions = data.get("selected_questions", [])

        if not selected_questions:
            await callback.answer("Выберите хотя бы один вопрос", show_alert=True)
            return

        # Запрашиваем комментарий
        await callback.message.edit_text(
            "Введите комментарий для пользователя с указанием, что нужно исправить:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_comment")]
            ])
        )

        # Сохраняем данные для следующего шага
        await state.update_data(
            target_user_id=user_id,
            questions_to_redo=selected_questions
        )
        await state.set_state(QuestState.waiting_for_reject_comment)

    except Exception as e:
        logging.error(f"Ошибка завершения выбора: {str(e)}")
        await callback.answer("⚠️ Ошибка обработки", show_alert=True)


@moderation_router.message(QuestState.waiting_for_reject_comment)
async def send_rejection_comment(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = data["target_user_id"]
        questions_to_redo = data.get("questions_to_redo", [])
        comment = message.text

        # Формируем текст с вопросами для переделки
        questions_text = "\n".join([f"• Вопрос {q_num}" for q_num in sorted(questions_to_redo)])

        # Отправляем пользователю
        await message.bot.send_message(
            user_id,
            f"📝 Ваши ответы требуют доработки:\n\n"
            f"Нужно исправить следующие вопросы:\n{questions_text}\n\n"
            f"Комментарий модератора:\n{comment}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔄 Пройти заново",
                    callback_data=f"repeat_quest_22_{'_'.join(map(str, questions_to_redo))}"
                )]
            ])
        )

        await message.answer("✅ Комментарий отправлен пользователю")

        # Удаляем исходное сообщение с кнопками
        original_message_id = data.get("original_message_id")
        if original_message_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=original_message_id)
            except:
                pass

    except Exception as e:
        logging.error(f"Ошибка при отправке комментария: {e}")
        await message.answer("⚠️ Ошибка при отправке комментария")
    finally:
        await state.clear()