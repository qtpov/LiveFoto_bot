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
def reg_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать регистрацию", callback_data="start_profile_form")]
    ])
#клавиатура перехода в профиль
def go_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Профиль", callback_data="profile")]
    ])

def knowledge_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тема 1", callback_data="zn_1")],
        [InlineKeyboardButton(text="Тема 2", callback_data="zn_2")],
        [InlineKeyboardButton(text="Тема 3", callback_data="zn_3")],
        [InlineKeyboardButton(text="Тема 4", callback_data="zn_4")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")]
    ])

def knowledge_theme_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="knowledge")]
    ])


def go_quests_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить", callback_data="start_quest")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")]
    ])


def quest1_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="База", callback_data="base"),
        InlineKeyboardButton(text="Стенд", callback_data="stand")],
        [InlineKeyboardButton(text="Вход в парк", callback_data="entrance"),
         InlineKeyboardButton(text="Фуд-корт", callback_data="food-court")],
        [InlineKeyboardButton(text="Туалет", callback_data="toilet")]
    ])

def quest2_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Автоматы", callback_data="Автоматы"),
        InlineKeyboardButton(text="Батуты", callback_data="Батуты")],
        [InlineKeyboardButton(text="Трон", callback_data="Трон"),
         InlineKeyboardButton(text="Лабиринт", callback_data="Лабиринт")],
        [InlineKeyboardButton(text="Детская", callback_data="Детская")]
    ])


#
# #Создает инлайн-клавиатуру из массива данных каждая отдельно
# def create_inline_keyboard(data, callback_prefix="task_"):
#     """
#     data: Массив данных из базы данных """
#     # Создаем список кнопок
#     buttons = []
#     for item in data:
#         # Предполагаем, что каждый элемент массива имеет поля `id` и `title`
#         button = InlineKeyboardButton(
#             text=item.title,  # Текст кнопки
#             callback_data=f"{callback_prefix}{item.id}"  # Уникальный callback_data
#         )
#         buttons.append([button])  # Каждая кнопка в отдельном списке (одна кнопка на строку)
#
#     # Создаем клавиатуру с кнопками
#     keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
#     return keyboard
#
# #создает клавиатуру по 2 кнопки в строке
# def create_inline_keyboard_2(data, callback_prefix="task_"):
#
#     buttons = []  # Список для хранения строк кнопок
#     row = []      # Временный список для хранения кнопок в текущей строке
#
#     for item in data:
#         # Создаем кнопку
#         button = InlineKeyboardButton(
#             text=item,  # Текст кнопки
#             callback_data=f"{callback_prefix}_{item}"  # Уникальный callback_data
#         )
#         row.append(button)  # Добавляем кнопку в текущую строку
#
#         # Если в строке накопилось 2 кнопки, добавляем строку в buttons
#         if len(row) == 2:
#             buttons.append(row)  # Добавляем строку в buttons
#             row = []  # Очищаем текущую строку
#
#     # Если после цикла в row остались кнопки (например, если количество кнопок нечетное)
#     if row:
#         buttons.append(row)  # Добавляем оставшиеся кнопки в buttons
#
#     # Создаем клавиатуру с кнопками
#     keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
#     return keyboard

from aiogram.utils.keyboard import InlineKeyboardBuilder

def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_edit")
    return builder.as_markup()