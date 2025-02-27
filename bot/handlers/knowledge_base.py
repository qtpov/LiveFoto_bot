
from aiogram import Router, types, F
from bot.keyboards.inline import knowledge_keyboard

router = Router()

@router.callback_query(F.data == "knowledge")
async def send_knowledge_list(callback: types.CallbackQuery):
    await callback.message.edit_text('Выберите тему из кнопок внизу',reply_markup=knowledge_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("zn_"))
async def proces_knowledge(callback: types.CallbackQuery):
    await callback.message.answer('пока пусто')
    await callback.answer()

