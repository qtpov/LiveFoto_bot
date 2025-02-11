from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Квесты", callback_data="quests")],
        [InlineKeyboardButton(text="Мини-игры", callback_data="games")],
        [InlineKeyboardButton(text="Ачивки", callback_data="achievements")],
        [InlineKeyboardButton(text="База знаний", callback_data="knowledge")]
    ])
