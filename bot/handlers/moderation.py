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
from aiogram.utils.keyboard import InlineKeyboardBuilder

moderation_router = Router()



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

    # далее день 2
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
                    "Введите комментарий для пользователя:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Отмена", callback_data="cancel_moderation")]
                    ])
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
                    "Укажите причину отклонения:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Отмена", callback_data="cancel_moderation")]
                    ])
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
                await update_user_level(user_data["target_user_id"], session)

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


@moderation_router.callback_query(F.data == "cancel_moderation", QuestState.waiting_for_comment)
async def cancel_moderation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Модерация отменена")
    await callback.answer()