from aiogram import Router, types, F
from aiogram.types import BufferedInputFile, FSInputFile
from bot.db.models import UserResult, User, Achievement
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline import *
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from aiogram.utils.media_group import MediaGroupBuilder,InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
import datetime
import pandas as pd
from io import BytesIO
import logging
import os
from .states import QuestState
from bot.configurate import settings
from sqlalchemy.orm import joinedload

router = Router()

adadmin_chat_id = settings.ADMIN_ID

@router.callback_query(F.data =="go_admin_panel")
async def retry_quest(callback: types.CallbackQuery):
    await callback.message.edit_text('Панель Администратора\n\nВыберите действие',reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "list_intern")
async def list_intern(callback: types.CallbackQuery):
    async with SessionLocal() as session:
        # Получаем пользователей с профилями
        stmt = select(User).options(joinedload(User.profile))
        result = await session.execute(stmt)
        users = result.scalars().all()

        if not users:
            await callback.message.edit_text("Нет зарегистрированных стажеров", reply_markup=go_admin_panel_keyboard())
            return

        builder = InlineKeyboardBuilder()
        for user in users:
            name = user.profile.full_name if user.profile else user.full_name
            builder.button(
                text=f"{name} (ID: {user.telegram_id})",
                callback_data=f"user_detail:{user.telegram_id}"
            )

        builder.button(text="Назад", callback_data="go_admin_panel")
        builder.adjust(1)

        await callback.message.edit_text(
            "Список стажеров:",
            reply_markup=builder.as_markup()
        )


@router.callback_query(F.data.startswith("user_detail:"))
async def user_detail(callback: types.CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    async with SessionLocal() as session:
        # Получаем пользователя с профилем и результатами
        user = await session.execute(
            select(User)
            .options(joinedload(User.profile))
            .where(User.telegram_id == user_id)
        )
        user = user.scalars().first()

        if not user:
            await callback.answer("Пользователь не найден")
            return

        # Получаем результаты пользователя
        results = await session.execute(
            select(UserResult)
            .where(UserResult.user_id == user_id)
        )
        results = results.scalars().all()


        name = user.profile.full_name if user.profile else user.full_name
        text = (
            f"Информация о стажере:\n\n"
            f"ID: {user.telegram_id}\n"
            f"ФИО: {name}\n"
            f"Уровень: {user.level}\n"
            f"День стажировки: {user.day}\n"
            f"Выполнено заданий: {len(results)}\n"
        )

        builder = InlineKeyboardBuilder()
        builder.button(text="Назад", callback_data="list_intern")
        await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "get_analytics")
async def get_analytics(callback: types.CallbackQuery):
    async with SessionLocal() as session:
        # Получаем всех пользователей с профилями
        users = await session.execute(
            select(User)
            .options(joinedload(User.profile))
        )
        users = users.scalars().all()

        # Собираем данные для отчета
        report_data = []
        for user in users:
            # Получаем результаты пользователя
            results = await session.execute(
                select(UserResult)
                .where(UserResult.user_id == user.telegram_id)
            )
            results = results.scalars().all()

            # Рассчитываем среднее время выполнения
            completion_times = [r.completion_time for r in results if r.completion_time is not None]
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0

            # Форматируем время в минуты:секунды
            minutes, seconds = divmod(int(avg_completion_time), 60)
            avg_time_str = f"{minutes}:{seconds:02d}"

            name = user.profile.full_name if user.profile else user.full_name
            report_data.append({
                "ID": user.telegram_id,
                "ФИО": name,
                "Выполнено заданий": len(results),
                "Уровень": user.level,
                "День стажировки": user.day,
                "Среднее время выполнения (м:с)": avg_time_str
            })

        # Создаем Excel файл
        df = pd.DataFrame(report_data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Отчет')

        output.seek(0)
        await callback.message.answer_document(
            BufferedInputFile(
                output.getvalue(),
                filename=f"analytics_report_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
            ),
            caption="Отчет по всем стажерам"
        )
        await callback.answer()