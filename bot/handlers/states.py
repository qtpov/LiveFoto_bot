# states.py
from aiogram.fsm.state import StatesGroup, State

class SalesState(StatesGroup):
    WAITING_PHOTO_33 = State()
    WAITING_PRODUCT_DESC_33 = State()
    HANDLING_REFUSAL_33 = State()

class QuestState(StatesGroup):
    # Общие состояния
    waiting_for_answer = State()
    waiting_for_moderation = State()
    waiting_for_moderation_comment = State()
    waiting_for_comment = State()

    waiting_for_answer_quest16 = State()
    waiting_for_answer_quest19 = State()
    waiting_for_answer_quest22 = State()


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
    waiting_for_photo_quest15 = State()
    waiting_for_photo_quest18 = State()
    waiting_for_photo_quest20 = State()

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

    # Состояния для квеста 21
    waiting_for_colleagues_count_21 = State()
    waiting_for_colleague_position_21 = State()
    waiting_for_colleague_surname_21 = State()
    waiting_for_colleague_name_21 = State()
    waiting_for_colleague_telegram_21 = State()
    waiting_for_retry_answer = State()
    waiting_for_reject_comment = State()

    waiting_for_sale_result_24 = State()
    waiting_for_fail_reason_24 = State()
    waiting_for_continue_24 = State()
    waiting_for_custom_reason_24 = State()

    # Состояния для квеста 26
    waiting_for_answer_26_1 = State()
    waiting_for_answer_26_2 = State()
    waiting_for_answer_26_3 = State()
    waiting_for_answer_26_4 = State()
    waiting_for_answer_26_5 = State()
    waiting_for_answer_26_6 = State()
    waiting_for_answer_26_7 = State()
    waiting_for_answer_26_8 = State()

    # Квест 27 - Правильное фото
    waiting_photo_answer = State()  # Ожидание ответа на вопрос с фото

    # Квест 28 - Собери все
    waiting_assembly_start = State()  # Ожидание старта сборки
    waiting_for_finish_quest28 = State()  # Ожидание завершения сборки
    waiting_for_quest28_video = State()

    # Квест 29 - Фотоохота
    waiting_photo_hunt_start = State()  # Ожидание старта фотоохоты
    waiting_photo_hunt_stop = State()  # Ожидание остановки фотоохоты
    waiting_custom_reason = State()  # Ожидание отправки фото
    waiting_photo_feedback = State()  # Ожидание фидбека по фотоохоте
    waiting_photo_upload = State()

    # Квест 30 - Полный цикл
    waiting_full_cycle_step = State()  # Ожидание следующего шага
    waiting_sales_amount = State()  # Ожидание ввода суммы продаж
    waiting_sold_photos = State()

    # Квест 31 - Ценность кадра
    waiting_quiz_start = State()  # Ожидание старта теста
    waiting_quiz_answer = State()  # Ожидание ответа на вопрос теста

    # Квест 32 - Ценности компании
    waiting_game_start = State()  # Ожидание старта игры
    waiting_scenario_answer = State()  # Ожидание ответа на сценарий

    # Квест 33 - Клиент
    waiting_photo_33 = State()
    waiting_product_desc_33 = State()
    handling_refusal_33 = State()

    # Квест 34 - Фидбек
    waiting_feedback_34 = State()  # Ожидание старта опроса
    waiting_feedback_answer = State()  # Ожидание ответа на вопрос опроса
    waiting_feedback_text = State()  # Ожидание текстового ответа



