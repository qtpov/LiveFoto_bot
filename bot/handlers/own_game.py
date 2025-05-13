from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


class OwnGame(StatesGroup):
    waiting_for_category = State()
    waiting_for_answer = State()


QUESTIONS = {
    "100": [
        {
            "question": "В какой программе мы обрабатываем фотографии?",
            "answer": "Лайтрум",
            "options": [
                "Лайтрум",
                "Фотошоп",
                "Корел Дро",
                "xxx"
            ]
        },
        {
            "question": "Назови 4 вида продукции",
            "answer": "Магнит, рамка, брелок, фотография без рамки, электронный кадр",
            "options": [
                "Магнит, рамка, брелок, фотография без рамки, электронный кадр",
                "xxx",
                "xxx",
                "xxx"
            ]
        }
    ],
    "200": [
        {
            "question": "Сколько кадров надо делать на ребенка?",
            "answer": "Не менее 5",
            "options": [
                "Не менее 5",
                "1-2",
                "10-15",
                "xxx"
            ]
        },
        {
            "question": "Что такое пакетное предложение?",
            "answer": "Набор продукции, которую мы предлагаем клиенту в одном комплекте по выгодной цене",
            "options": [
                "Набор продукции, которую мы предлагаем клиенту в одном комплекте по выгодной цене",
                "xxx",
                "xxx",
                "xxx"
            ]
        }
    ],
    "300": [
        {
            "question": "Назови три показателя продаж",
            "answer": "Конверсия кадров, конверсия продаж, средний чек",
            "options": [
                "Конверсия кадров, конверсия продаж, средний чек",
                "xxx",
                "xxx",
                "xxx"
            ]
        },
        {
            "question": "Назови три базовые настройки фотоаппарата",
            "answer": "Диафрагма, выдержка, ИСО",
            "options": [
                "Диафрагма, выдержка, ИСО",
                "xxx",
                "xxx",
                "xxx"
            ]
        }
    ]
}

router = Router()


@router.callback_query(F.data.startswith("own_category_"))
async def handle_category_select(callback: CallbackQuery, state: FSMContext):
    await select_category(callback, state)


@router.callback_query(F.data.startswith("own_question_"))
async def handle_question_select(callback: CallbackQuery, state: FSMContext):
    await ask_own_question(callback, state)


@router.callback_query(F.data.startswith("own_answer_"))
async def handle_answer_select(callback: CallbackQuery, state: FSMContext):
    await check_answer(callback, state)


async def start_own_game(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for points in ["100", "200", "300"]:
        builder.add(types.InlineKeyboardButton(
            text=f"Вопросы за {points}",
            callback_data=f"own_category_{points}"
        ))
    builder.add(types.InlineKeyboardButton(
            text=f"Назад",
            callback_data=f"profile"
        ))
    builder.adjust(1)

    await callback.message.edit_text(
        "Выберите категорию вопросов:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(OwnGame.waiting_for_category)


async def select_category(callback: CallbackQuery, state: FSMContext):
    points = callback.data.split("_")[-1]
    questions = QUESTIONS[points]

    builder = InlineKeyboardBuilder()
    for i, q in enumerate(questions):
        builder.add(types.InlineKeyboardButton(
            text=f"Вопрос {i + 1}",
            callback_data=f"own_question_{points}_{i}"
        ))
    builder.add(types.InlineKeyboardButton(
        text="Назад к выбору категории",
        callback_data="game_own"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        f"Выберите вопрос из категории {points}:",
        reply_markup=builder.as_markup()
    )


async def ask_own_question(callback: CallbackQuery, state: FSMContext):
    _, _, points, index = callback.data.split("_")
    question_data = QUESTIONS[points][int(index)]

    await state.set_state(OwnGame.waiting_for_answer)
    await state.update_data(current_question=question_data, points=points)

    builder = InlineKeyboardBuilder()
    for i, option in enumerate(question_data["options"]):
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"own_answer_{i}"
        ))
    builder.adjust(1)

    await callback.message.edit_text(
        f"Вопрос за {points}:\n\n{question_data['question']}\n\n"
        "Выберите правильный ответ:",
        reply_markup=builder.as_markup()
    )


async def check_answer(callback: CallbackQuery, state: FSMContext):
    answer_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    question = data.get("current_question", {})
    points = data.get("points", "")

    if question["options"][answer_index] == question["answer"]:
        await callback.answer("Правильно! ✅", show_alert=True)
    else:
        await callback.answer(f"Неправильно! ❌ Правильный ответ: {question['answer']}", show_alert=True)

    # Возвращаемся к выбору категории
    await start_own_game(callback, state)