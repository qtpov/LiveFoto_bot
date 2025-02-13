from aiogram import Router, types,F
#from ..db.session import get_db
from ..db.models import Quest

router = Router()


@router.message(F.text == "Квесты")
async def quests(message: types.Message):
    # db = get_db()
    # quests = db.query(Quest).filter_by(user_id=message.from_user.id, status="active").all()
    #
    # if not quests:
    #     await message.answer("Сегодня у тебя нет активных квестов.")
    #     return
    #
    # text = "📜 *Доступные квесты:*\n\n"
    # for quest in quests:
    #     text += f"✅ {quest.title} - {quest.description}\n"
    text += f"✅квесты"
    await message.answer(text, parse_mode="Markdown")
