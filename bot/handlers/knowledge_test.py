from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.keyboards.inline import go_profile_keyboard
import datetime
from bot.configurate import settings
from typing import Union

class KnowledgeTest(StatesGroup):
    answering_questions = State()

router = Router()

admin_chat_id = settings.ADMIN_ID

@router.callback_query(F.data.startswith("knowledge_answer_"))
async def handle_knowledge_answer(callback: CallbackQuery, state: FSMContext):
    answer_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    current = data.get("current_question", 0)

    # Сохраняем ответ
    answers = data.get("answers", {})
    answers[current] = answer_index
    await state.update_data(answers=answers, current_question=current + 1)

    await callback.answer("Ответ сохранён")
    await process_knowledge_question(callback, state)

@router.callback_query(F.data == "knowledge_next_question")
async def handle_next_question(callback: CallbackQuery, state: FSMContext):
    await process_knowledge_question(callback, state)


@router.message(KnowledgeTest.answering_questions, F.text)
async def handle_text_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("waiting_for_text_answer", False):
        return

    current = data.get("current_question", 0)
    answers = data.get("answers", {})
    answers[current] = message.text
    await state.update_data(
        answers=answers,
        current_question=current + 1,
        waiting_for_text_answer=False
    )

    # Передаем message напрямую, а не создаем fake callback
    await process_knowledge_question(message, state)

async def start_knowledge_test(callback: CallbackQuery, state: FSMContext):
    questions = [
        "Насколько вы чувствуете себя уверенно в выполнении основных задач фотографа?",
        "Какие задания или навыки вызывали у вас наибольшие трудности?",
        "Что вы сделали для преодоления этих трудностей?",
        "Готовы ли вы взять на себя ответственность за выполнение рабочих задач без постоянного контроля?",
        "Какие три основных шага вы предпримете, чтобы улучшить свои навыки в процессе работы?"
    ]

    await state.set_state(KnowledgeTest.answering_questions)
    await state.update_data(current_question=0, answers={})

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Начать тест",
        callback_data="knowledge_next_question"
    ))

    await callback.message.edit_text(
        "Дружище, ты справился(-сь) со всеми заданиями! Пройди последний вопрос на сегодня.\n\n"
        "Отправимся в увлекательное путешествие со мной дальше!\n\n"
        "Готовы начать тест?",
        reply_markup=builder.as_markup()
    )


async def process_knowledge_question(update: Union[Message, CallbackQuery], state: FSMContext):
    # Получаем message и chat_id в зависимости от типа update
    if isinstance(update, CallbackQuery):
        message = update.message
        chat_id = message.chat.id
    else:  # Message
        message = update
        chat_id = message.chat.id

    data = await state.get_data()
    current = data.get("current_question", 0)
    answers = data.get("answers", {})

    questions = [
        {
            "text": "Насколько вы чувствуете себя уверенно в выполнении основных задач фотографа (съемка, обработка, взаимодействие с клиентами, продажа продукции)?",
            "options": [
                "Полностью уверен",
                "Уверен, но с помощью",
                "Требуется поддержка",
                "Не уверен"
            ],
            "type": "choice"
        },
        {
            "text": "Какие задания или навыки вызывали у вас наибольшие трудности? (Краткий ответ)",
            "type": "text"
        },
        {
            "text": "Что вы сделали для преодоления этих трудностей? Удалось ли вам справиться самостоятельно или с помощью наставника? (Развернутый ответ)",
            "type": "text"
        },
        {
            "text": "Готовы ли вы взять на себя ответственность за выполнение рабочих задач без постоянного контроля? Почему? (Развернутый ответ)",
            "type": "text"
        },
        {
            "text": "Какие три основных шага вы предпримете, чтобы улучшить свои навыки в процессе работы, если вас примут в команду? (Краткий ответ)",
            "type": "text"
        }
    ]

    if current >= len(questions):
        await finish_knowledge_test(message, state)
        return

    question = questions[current]

    if question["type"] == "choice":
        builder = InlineKeyboardBuilder()
        for i, option in enumerate(question["options"]):
            builder.add(types.InlineKeyboardButton(
                text=option,
                callback_data=f"knowledge_answer_{i}"
            ))
        builder.adjust(1)

        if isinstance(update, CallbackQuery):
            await message.edit_text(
                f"Вопрос {current + 1}/{len(questions)}:\n\n{question['text']}",
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer(
                f"Вопрос {current + 1}/{len(questions)}:\n\n{question['text']}",
                reply_markup=builder.as_markup()
            )
    else:
        if isinstance(update, CallbackQuery):
            await message.edit_text(
                f"Вопрос {current + 1}/{len(questions)}:\n\n{question['text']}\n\n"
                "Напишите ваш ответ в чат."
            )
        else:
            await message.answer(
                f"Вопрос {current + 1}/{len(questions)}:\n\n{question['text']}\n\n"
                "Напишите ваш ответ в чат."
            )
        await state.update_data(waiting_for_text_answer=True)


async def finish_knowledge_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", {})
    user = message.from_user

    # Формируем читаемый отчет для модерации
    username = f"@{user.username}" if user.username else f"ID: {user.id}"

    questions_data = [
        {
            "text": "1. Насколько вы чувствуете себя уверенно в выполнении основных задач фотографа?",
            "options": [
                "Полностью уверен",
                "Уверен, но требуется небольшая помощь",
                "Частично уверен, требуется значительная поддержка",
                "Не уверен"
            ]
        },
        {
            "text": "2. Какие задания или навыки вызывали у вас наибольшие трудности?",
            "type": "text"
        },
        {
            "text": "3. Что вы сделали для преодоления этих трудностей?",
            "type": "text"
        },
        {
            "text": "4. Готовы ли вы взять на себя ответственность?",
            "type": "text"
        },
        {
            "text": "5. Какие три шага для улучшения навыков?",
            "type": "text"
        }
    ]

    report_text = (
        f"📝 Тест знаний - Срез знаний\n"
        f"👤 Пользователь: {user.full_name} ({username})\n"
        f"🕒 Время прохождения: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        "Ответы:\n"
    )

    # Форматируем ответы в читаемый вид
    for i, answer in answers.items():
        question = questions_data[int(i)]
        report_text += f"\n{question['text']}:\n"

        if question.get("type") == "text":
            report_text += f"➡ {answer}\n"
        else:
            # Для вопросов с вариантами преобразуем индекс в текст
            if isinstance(answer, int) and 0 <= answer < len(question["options"]):
                report_text += f"➡ {question['options'][answer]}\n"
            else:
                report_text += f"➡ Неизвестный формат ответа\n"

    # Отправляем отчет модератору
    await message.bot.send_message(
        admin_chat_id,
        report_text
    )

    # Сообщение пользователю
    await message.answer(
        "✅ Тест завершен!",
        reply_markup=go_profile_keyboard()
    )

    await state.clear()
