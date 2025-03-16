from aiogram import types
from ..db.session import SessionLocal
from ..db.models import  Moderation



async def review_quest(call: types.CallbackQuery, quest_id: int, approved: bool):
    session = SessionLocal()
    quest = session.query(Task).filter_by(id=quest_id).first()
    if not quest:
        await call.message.answer("Задание не найдено.")
        return

    status = "approved" if approved else "rejected"
    moderation = Moderation(quest_id=quest_id, status=status, moderator_id=call.from_user.id)
    session.add(moderation)

    if approved:
        quest.status = "completed"
    else:
        quest.status = "rejected"

    session.commit()
    await call.message.answer(f"Задание {'принято' if approved else 'отклонено'}.")
    session.close()
