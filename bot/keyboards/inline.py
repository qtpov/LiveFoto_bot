from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

#клавиатура действий в профиле
def profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Квесты", callback_data="quests"),
         InlineKeyboardButton(text="Ачивки", callback_data="achievements")],
        [InlineKeyboardButton(text="Мини-игры", callback_data="games")],
        [InlineKeyboardButton(text="База знаний", callback_data="knowledge")]
    ])
#клавиатура вбора пола
def gender_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="M", callback_data="Male"),
         InlineKeyboardButton(text="Ж", callback_data="Female")]
    ])
#клавиатура для прехода после анкеты
def form_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Прошел", callback_data="completed_form")]
    ])
#клавиатура перехода в профиль
def go_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Профиль", callback_data="profile")]
    ])

#клавиатура 1 квеста
def quest1_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="pos_1"),
         InlineKeyboardButton(text="2", callback_data="pos_2")],
        [InlineKeyboardButton(text="3", callback_data="pos_3"),
        InlineKeyboardButton(text="4", callback_data="pos_4")]
    ])