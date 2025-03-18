from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select
from bot.db.session import SessionLocal
from bot.db.models import User
from bot.keyboards.inline import reg_keyboard, go_profile_keyboard

router = Router()

class Registration(StatesGroup):
    name = State()
    age = State()
    gender = State()

@router.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    async with SessionLocal() as session:
        user = await session.execute(select(User).filter(User.telegram_id == user_id))
        user = user.scalars().first()

    if not user:
        await message.answer(
            f'Здравствуйте {message.from_user.full_name}!\nДля продолжения необходимо пройти регистрацию,'
            f' для продолжения нажмите кнопку снизу', reply_markup=reg_keyboard())
    else:
        await message.answer(f"С возвращением, {user.full_name}!",reply_markup=go_profile_keyboard())


# # Обработчик для файлов и медиа
# @router.message()
# async def handle_files(message: types.Message):
#     if message.document:
#         file_id = message.document.file_id
#         await message.answer(f"File ID документа: {file_id}")
#     elif message.photo:
#         file_id = message.photo[-1].file_id  # Берем последний элемент, так как он самый большой
#         await message.answer(f"File ID фото: {file_id}")
#     elif message.video:
#         file_id = message.video.file_id
#         await message.answer(f"File ID видео: {file_id}")
#     elif message.audio:
#         file_id = message.audio.file_id
#         await message.answer(f"File ID аудио: {file_id}")
#     elif message.voice:
#         file_id = message.voice.file_id
#         await message.answer(f"File ID голосового сообщения: {file_id}")
#     elif message.sticker:
#         file_id = message.sticker.file_id
#         await message.answer(f"File ID стикера: {file_id}")
#     else:
#         await message.answer("Этот тип медиа не поддерживается.")

