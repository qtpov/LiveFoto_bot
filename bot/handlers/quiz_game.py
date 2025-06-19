from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.keyboards.inline import go_profile_keyboard


router = Router()


class QuizGame(StatesGroup):
    waiting_for_answer = State()
    current_question = State()
    score = State()



QUESTIONS = [
    {
        "question": "Для чего нужно проходить задания в приложении?",
        "options": [
            "А) что бы было не скучно",
            "Б) что бы получить ЗП",
            "В) что бы изучить работу и стать суперпрофессионалом",
            "Г) Что бы прокачать своего героя"
        ],
        "correct": 2  # Индекс правильного ответа (0-based)
    },
    {
        "question": "Что нужно сделать первым делом когда утопил фотик?",
        "options": [
            "А) сообщить Админу",
            "Б) вытащить аккумулятор",
            "В) снять объектив",
            "Г) засунуть фотик в рис"
        ],
        "correct": 1
    },
    {
        "question": "Чего не должно быть на Базе?",
        "options": [
            "А) фотографов",
            "Б) детей",
            "В) домашних животных",
            "Г) микросхем"
        ],
        "correct": 2
    },
    {
        "question": "Что из ниже перечисленных вариантов является правилом фотографирования?",
        "options": [
            "А) Всегда нужно рассмешить человека/людей в кадре",
            "Б) Всегда нужно что бы было нечетное кол-во людей в кадре",
            "В) При фотографировании фотоаппарат нужно держать на уровне глаз человека в кадре",
            "Г) При фотографировании фотоаппарат нужно держать так чтобы глаза человека были по середине кадра"
        ],
        "correct": 2
    },
    {
        "question": "Что не является продукцией компании?",
        "options": [
            "А) магниты",
            "Б) 3D стикеры",
            "В) фото на футболке",
            "Г) фоторамки"
        ],
        "correct": 2
    },
    {
        "question": "Что не является этапом продаж?",
        "options": [
            "А) Поиск клиента",
            "Б) указать клиенту, где туалет",
            "В) Приветствие клиента",
            "Г) Общение с клиентом в фотозоне"
        ],
        "correct": 1
    },
    {
        "question": "Что является успешной продажей?",
        "options": [
            "А) когда клиент купил всю продукцию со скидкой и ушел довольный",
            "Б) когда клиент купил самый дорогой товар",
            "В) когда мама из жалости купила один магнитик",
            "Г) когда клиент купил большое количество продукции по пакетному предложению и ушёл довольный"
        ],
        "correct": 3
    },
    {
        "question": "Что не является показателем продаж?",
        "options": [
            "А) возраст ребёнка",
            "Б) количество кадров",
            "В) количество чеков",
            "Г) средний чек"
        ],
        "correct": 0
    },
    {
        "question": "Что не является элементом форменной одежды сотрудника работающего на локации?",
        "options": [
            "А) Футболка",
            "Б) Повязка на волосы",
            "В) Жилетка",
            "Г) Шорты"
        ],
        "correct": 2
    }
]


@router.callback_query(F.data.startswith("quiz_answer_"))
async def handle_quiz_answer(callback: CallbackQuery, state: FSMContext):
    await process_quiz_answer(callback, state)


async def start_quiz_game(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QuizGame.waiting_for_answer)
    await state.update_data(current_question=0, score=0)
    await ask_question(callback.message, state)


async def ask_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question_index = data.get("current_question", 0)

    if question_index >= len(QUESTIONS):
        await finish_quiz(message, state)
        return

    question_data = QUESTIONS[question_index]

    # Формируем текст сообщения с вопросом и вариантами ответов
    question_text = f"Вопрос {question_index + 1}/{len(QUESTIONS)}:\n\n{question_data['question']}\n\n"
    for option in question_data["options"]:
        question_text += f"{option}\n"

    # Создаем кнопки с буквами ответов (А, Б, В, Г)
    builder = InlineKeyboardBuilder()
    for i in range(len(question_data["options"])):
        letter = chr(1040 + i)  # 1040 - код буквы 'А' в Unicode
        builder.add(types.InlineKeyboardButton(
            text=letter,
            callback_data=f"quiz_answer_{i}"
        ))
    builder.adjust(4)  # Размещаем все кнопки в один ряд

    await message.edit_text(
        question_text,
        reply_markup=builder.as_markup()
    )


async def process_quiz_answer(callback: CallbackQuery, state: FSMContext):
    answer_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    question_index = data.get("current_question", 0)
    score = data.get("score", 0)

    if answer_index == QUESTIONS[question_index]["correct"]:
        score += 1
        await callback.answer("Правильно! ✅")
    else:
        correct_index = QUESTIONS[question_index]["correct"]
        correct_letter = chr(1040 + correct_index)  # Преобразуем индекс в букву
        await callback.answer(f"Неправильно! ❌ Правильный ответ: {correct_letter}")

    await state.update_data(
        current_question=question_index + 1,
        score=score
    )
    await ask_question(callback.message, state)


async def finish_quiz(message: types.Message, state: FSMContext):
    data = await state.get_data()
    score = data.get("score", 0)
    total = len(QUESTIONS)

    await message.edit_text(
        f"Викторина завершена!\n\n"
        f"Ваш результат: {score}/{total}\n"
        f"Процент правильных ответов: {int(score / total * 100)}%",
        reply_markup=go_profile_keyboard()
    )
    await state.clear()