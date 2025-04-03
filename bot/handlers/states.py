# states.py
from aiogram.fsm.state import StatesGroup, State


class QuestState(StatesGroup):
    # Общие состояния
    waiting_for_answer = State()
    waiting_for_moderation = State()
    waiting_for_comment = State()

    # Состояния для квеста 4
    waiting_for_clean_photo = State()
    waiting_for_items_photo = State()
    waiting_for_dirty_photo = State()
    waiting_for_selection = State()

    # Состояния для квестов с фото
    waiting_for_photos_quest5 = State()  # Для квеста 5
    waiting_for_photos_quest6 = State()  # Для квеста 6
    waiting_for_photo_quest13 = State()  # Для квеста 13
    waiting_for_photo_quest14 = State()

    # Состояния для квеста 9
    waiting_for_colleagues_count = State()
    waiting_for_colleague_position = State()
    waiting_for_colleague_surname = State()
    waiting_for_colleague_name = State()
    waiting_for_colleague_telegram = State()

    # Состояния для квеста 10
    waiting_for_hair = State()
    waiting_for_face = State()
    waiting_for_badge = State()
    waiting_for_shirt = State()
    waiting_for_pants = State()
    waiting_for_shoes = State()

    # Состояния для квеста 11
    waiting_for_hr_rating = State()
    waiting_for_interview = State()
    waiting_for_improvement = State()
    waiting_for_reason = State()
    waiting_for_app_rating = State()
    waiting_for_location_rating = State()
    waiting_for_base = State()
    waiting_for_product = State()
    waiting_for_sales = State()
    waiting_for_team = State()
    waiting_for_uniform = State()
    waiting_for_uniform_suggestions = State()