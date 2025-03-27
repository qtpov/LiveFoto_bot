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
from bot.db.crud import update_user_level
import datetime
from random import randint
import os
from .states import QuestState
from bot.configurate import settings

router = Router()

adadmin_chat_id = settings.ADMIN_ID

@router.callback_query(F.data =="go_admin_panel")
async def retry_quest(callback: types.CallbackQuery):
    await callback.message.edit_text('Панель Администратора\n\nВыберите действие',reply_markup=admin_panel_keyboard())

@router.callback_query(F.data == "list_intern")
async def list_intern(callback: types.CallbackQuery):
    await callback.message.edit_text('Тут пока ничего нет', reply_markup=go_admin_panel_keyboard())

@router.callback_query(F.data =="get_analytics")
async def get_analytics(callback: types.CallbackQuery):
    await callback.message.edit_text('Тут пока ничего нет',reply_markup=go_admin_panel_keyboard())
