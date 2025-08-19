from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.keyboards.inline import go_profile_keyboard

router = Router()


class OwnGame(StatesGroup):
    waiting_for_category = State()
    waiting_for_question = State()
    selecting_answers = State()
    answer_check = State()


# Обновленные вопросы с разделенными вариантами
QUESTIONS = {
    "100": [
        {
            "type": "single",
            "question": "В какой программе мы обрабатываем фотографии?",
            "answer": "Лайтрум",
            "options": ["Лайтрум", "Фотошоп", "Корел Дро", "Paint"]
        },
        {
            "type": "multi",
            "question": "Выберите 4 вида продукции компании",
            "correct_answers": ["Магнит", "Рамка", "Брелок", "Фотография без рамки", "Электронный кадр"],
            "options": [
                "Магнит", "Рамка", "Брелок", "Фотография без рамки",
                "Электронный кадр", "Футболка", "Кружка", "Пазл"
            ],
            "required": 4  # Сколько нужно выбрать
        }
    ],
    "200": [
        {
            "type": "single",
            "question": "Сколько кадров надо делать на ребенка?",
            "answer": "Не менее 5",
            "options": ["Не менее 5", "1-2", "10-15", "Столько, сколько получится"]
        },
        {
            "type": "multi",
            "question": "Выберите элементы пакетного предложения",
            "correct_answers": [
                "Набор продукции по выгодной цене",
                "Комплект из нескольких товаров",
                "Специальное предложение"
            ],
            "options": [
                "Набор продукции по выгодной цене",
                "Комплект из нескольких товаров",
                "Специальное предложение",
                "Бесплатный подарок",
                "Скидка 50%"
            ],
            "required": 3
        }
    ],
    "300": [
        {
            "type": "multi",
            "question": "Назови три показателя продаж",
            "correct_answers": [
                "Конверсия кадров",
                "Конверсия продаж",
                "Средний чек"
            ],
            "options": [
                "Количество смен в месяц",
                "Конверсия кадров",
                "Конверсия продаж",
                "Средний чек",
                "Количество брака"
            ],
            "required": 3
        },
        {
            "type": "multi",
            "question": "назови три базовые настройки фотоаппарата",
            "correct_answers": [
                "Диафрагма",
                "Выдержка",
                "ISO"
            ],
            "options": [
                "Дата и время на камере",
                "Диафрагма",
                "Выдержка",
                "ISO",
                "Яркость экрана"
            ],
            "required": 3
        },
    ]
}


@router.callback_query(F.data == "game_own")
async def start_own_game(callback: CallbackQuery, state: FSMContext):
    """Начало игры, выбор категории"""
    builder = InlineKeyboardBuilder()
    for points in QUESTIONS.keys():
        builder.add(types.InlineKeyboardButton(
            text=f"🟢 Вопросы за {points}",
            callback_data=f"own_category_{points}"
        ))
    builder.add(types.InlineKeyboardButton(
        text="Назад",
        callback_data="profile"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        "🎲 <b>Своя игра</b>\n\n"
        "Выберите категорию вопросов:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(OwnGame.waiting_for_category)


@router.callback_query(F.data.startswith("own_category_"), OwnGame.waiting_for_category)
async def select_category(callback: CallbackQuery, state: FSMContext):
    """Выбор конкретного вопроса из категории"""
    points = callback.data.split("_")[-1]
    questions = QUESTIONS[points]

    builder = InlineKeyboardBuilder()
    for i in range(len(questions)):
        builder.add(types.InlineKeyboardButton(
            text=f"❓ Вопрос {i + 1}",
            callback_data=f"own_question_{points}_{i}"
        ))
    builder.add(types.InlineKeyboardButton(
        text="Назад к категориям",
        callback_data="game_own"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        f"📋 <b>Категория {points}</b>\n\n"
        "Выберите вопрос:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(OwnGame.waiting_for_question)
    await state.update_data(current_category=points)


@router.callback_query(F.data.startswith("own_question_"), OwnGame.waiting_for_question)
async def ask_question(callback: CallbackQuery, state: FSMContext):
    """Отображение вопроса"""
    _, _, points, index = callback.data.split("_")
    question_data = QUESTIONS[points][int(index)]

    await state.update_data(
        current_question=question_data,
        question_points=points,
        question_index=int(index),
        selected_answers=[]
    )

    if question_data["type"] == "single":
        # Обычный вопрос с одним ответом
        question_text = f"🏆 <b>Вопрос за {points}</b>\n\n❔ {question_data['question']}"

        builder = InlineKeyboardBuilder()
        letters = ["А", "Б", "В", "Г"]
        for i, option in enumerate(question_data["options"]):
            builder.add(types.InlineKeyboardButton(
                text=f"{letters[i]}) {option}",
                callback_data=f"own_answer_{i}"
            ))
        builder.adjust(1)

        await callback.message.edit_text(
            question_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(OwnGame.answer_check)
    else:
        # Вопрос с множественным выбором
        question_text = (
            f"🏆 <b>Вопрос за {points}</b>\n\n"
            f"❔ {question_data['question']}\n\n"
            f"Выберите {question_data['required']} варианта(ов):"
        )

        builder = InlineKeyboardBuilder()
        for i, option in enumerate(question_data["options"]):
            builder.add(types.InlineKeyboardButton(
                text=option,
                callback_data=f"own_select_{i}"
            ))
        builder.adjust(1)

        # Кнопка подтверждения выбора
        builder.row(types.InlineKeyboardButton(
            text="✅ Проверить ответ",
            callback_data="own_check_answers"
        ))

        await callback.message.edit_text(
            question_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(OwnGame.selecting_answers)


@router.callback_query(F.data.startswith("own_select_"), OwnGame.selecting_answers)
async def select_answer(callback: CallbackQuery, state: FSMContext):
    """Выбор вариантов для вопросов с множественным выбором"""
    answer_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    question_data = data["current_question"]
    selected = data.get("selected_answers", [])
    option = question_data["options"][answer_index]

    if option in selected:
        selected.remove(option)
    else:
        if len(selected) < question_data["required"]:
            selected.append(option)
        else:
            await callback.answer(f"Можно выбрать не более {question_data['required']} вариантов")
            return

    await state.update_data(selected_answers=selected)

    # Обновляем сообщение с отметкой выбранных вариантов
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(question_data["options"]):
        prefix = "✅ " if opt in selected else ""
        builder.add(types.InlineKeyboardButton(
            text=f"{prefix}{opt}",
            callback_data=f"own_select_{i}"
        ))
    builder.adjust(1)

    builder.row(types.InlineKeyboardButton(
        text=f"✅ Проверить ответ ({len(selected)}/{question_data['required']})",
        callback_data="own_check_answers"
    ))

    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "own_check_answers", OwnGame.selecting_answers)
async def check_multiple_answers(callback: CallbackQuery, state: FSMContext):
    """Проверка ответов для вопросов с множественным выбором"""
    data = await state.get_data()
    question_data = data["current_question"]
    selected = data.get("selected_answers", [])
    correct_answers = question_data["correct_answers"]

    # Проверяем правильность ответов
    correct_selected = sum(1 for ans in selected if ans in correct_answers)
    total_correct = len(correct_answers)

    result_text = (
        f"Ваш выбор: {', '.join(selected) if selected else 'Нет выбора'}\n\n"
        f"Правильных ответов: {correct_selected}/{question_data['required']}\n"
    )

    if correct_selected == question_data["required"] and len(selected) == question_data["required"]:
        result_text += "🎉 <b>Верно!</b> Все ответы правильные!"
    else:
        result_text += (
            f"🔍 <b>Правильные ответы:</b> {', '.join(correct_answers)}\n"
            "Попробуйте ещё раз!"
        )

    builder = InlineKeyboardBuilder()
    if correct_selected == question_data["required"] and len(selected) == question_data["required"]:
        # Если ответ правильный, предлагаем следующий вопрос
        builder.add(types.InlineKeyboardButton(
            text="➡️ Следующий вопрос",
            callback_data=f"game_own"
        ))
    else:
        # Если есть ошибки, предлагаем попробовать снова
        builder.add(types.InlineKeyboardButton(
            text="🔄 Попробовать снова",
            callback_data=f"retry_question"
        ))

    await callback.message.edit_text(
        f"🏆 <b>Результат</b>\n\n{result_text}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(OwnGame.answer_check)


@router.callback_query(F.data.startswith("own_answer_"), OwnGame.answer_check)
async def check_single_answer(callback: CallbackQuery, state: FSMContext):
    """Проверка ответа для вопросов с одним вариантом"""
    answer_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    question_data = data["current_question"]
    selected_option = question_data["options"][answer_index]
    builder = InlineKeyboardBuilder()
    if selected_option == question_data["answer"]:
        result_text = "🎉 <b>Правильно!</b>"
        builder.add(types.InlineKeyboardButton(
            text="➡️ Следующий вопрос",
            callback_data=f"game_own"
        ))
    else:
        result_text = f"❌ <b>Неверно.</b> Правильный ответ: {question_data['answer']}"
        builder.add(types.InlineKeyboardButton(
            text="🔄 Попробовать снова",
            callback_data=f"retry_question"
        ))

    await callback.message.edit_text(
        f"🏆 <b>Результат</b>\n\n{result_text}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "retry_question", OwnGame.answer_check)
async def retry_question(callback: CallbackQuery, state: FSMContext):
    """Повторная попытка ответа на вопрос"""
    data = await state.get_data()
    points = data["question_points"]
    index = data["question_index"]

    # Создаем новый callback с нужными данными
    new_callback = CallbackQuery(
        id=callback.id,
        from_user=callback.from_user,
        chat_instance=callback.chat_instance,
        message=callback.message,
        data=f"own_question_{points}_{index}"
    )

    await ask_question(new_callback, state)


@router.callback_query(F.data == "own_next_question")
async def next_question(callback: CallbackQuery, state: FSMContext):
    """Переход к следующему вопросу"""
    data = await state.get_data()
    points = data["question_points"]
    index = data["question_index"] + 1

    if index < len(QUESTIONS[points]):
        # Создаем новый callback с нужными данными
        new_callback = CallbackQuery(
            id=callback.id,
            from_user=callback.from_user,
            chat_instance=callback.chat_instance,
            message=callback.message,
            data=f"own_question_{points}_{index}"
        )
        await ask_question(new_callback, state)
    else:
        # Если вопросы закончились, возвращаем к выбору категории
        await start_own_game(callback, state)