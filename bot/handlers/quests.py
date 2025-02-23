from aiogram import Router, types, F
from bot.db.models import Task
from bot.db.crud import get_tasks
from aiogram.types import FSInputFile
from bot.keyboards.inline import create_inline_keyboard,create_inline_keyboard_2
from sqlalchemy.future import select
from bot.db.session import SessionLocal

router = Router()

@router.callback_query(F.data == "quests")
async def show_tasks(callback: types.CallbackQuery):
    # Получаем задания из базы данных
    async with SessionLocal() as db:
        tasks = await get_tasks(db)

        if not tasks:
            await callback.message.answer("Заданий пока нет.")
            return

        # Создаем инлайн-клавиатуру
        keyboard = create_inline_keyboard(tasks, callback_prefix="task_")

        # Отправляем сообщение с клавиатурой
        await callback.message.edit_text("Выберите задание:", reply_markup=keyboard)
    await callback.answer()

    @router.callback_query(F.data.startswith("task_"))
    async def process_task_callback(callback: types.CallbackQuery):
        # Извлекаем ID задания из callback_data
        task_id = int(callback.data.replace("task_", ""))
        async with SessionLocal() as session:
            task = await session.execute(select(Task).filter(Task.id == task_id))
            task = task.scalars().first()

            if not task:
                await callback.message.answer("Заданий не найдено")
                return

            # Здесь можно выполнить действия с выбранным заданием
            await callback.message.edit_text(f"{task.title}"
                                          f"\n{task.description}",reply_markup=create_inline_keyboard_2(task.options, callback_prefix=f"qw_{task_id}"))

        # Подтверждаем обработку callback
        await callback.answer()

    @router.callback_query(F.data.startswith("qw_"))
    async def process_task1_callback(callback: types.CallbackQuery):
        task_id = int(callback.data[3:4])

        async with SessionLocal() as session:
            task = await session.execute(select(Task).filter(Task.id == task_id))
            task = task.scalars().first()

            next_task = await session.execute(select(Task).filter(Task.id == task_id+1))
            next_task = next_task.scalars().first()

            if not task:
                await callback.message.answer("Заданий не найдено")
                return
            await callback.message.answer(callback.data[5:])
            if callback.data[5:] == task.correct_answer:
                await callback.message.edit_text('верный ответ')
                #добавить проверку на последнее задание
                await callback.message.answer(f"{next_task.title}"
                                              f"\n{next_task.description}",
                                              reply_markup=create_inline_keyboard_2(next_task.options,
                                                                                    callback_prefix=f"qw_{task_id+1}"))

            else:
                await callback.message.edit_text('ответ неверный попробуй снова')
                return

        await callback.answer()