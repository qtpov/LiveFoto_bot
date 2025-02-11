from .session import SessionLocal
from .models import User, Quest, Achievement, Moderation

def get_user_by_tg_id(telegram_id):
    session = SessionLocal()
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    session.close()
    return user

def add_user(telegram_id, full_name, age, gender):
    session = SessionLocal()
    user = User(telegram_id=telegram_id, full_name=full_name, age=age, gender=gender)
    session.add(user)
    session.commit()
    session.close()
    return user

#  Выдать ачивку
def give_achievement(user_id, name, description):
    session = SessionLocal()
    achievement = Achievement(user_id=user_id, name=name, description=description)
    session.add(achievement)
    session.commit()
    session.close()
