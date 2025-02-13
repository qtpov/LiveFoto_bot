from aiogram import Router, types, F
from bot.db.models import Quest
from aiogram.types import FSInputFile
from bot.keyboards.inline import quest1_keyboard

router = Router()

@router.callback_query(F.data == "quests")
async def quests(callback: types.CallbackQuery):
    await callback.message.delete()
    image_from_pc = FSInputFile("bot/media/photo/zaglushka.png")
    result = await callback.message.answer_photo(
        image_from_pc,
        caption='Квест №1'
                '\nВнимательно изучите картинку и выберите снизу под каким номером локация ##1',
        reply_markup=quest1_keyboard()
    )
    await callback.answer()