from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder




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

def quest3_keyboard_after_video():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Приступить", callback_data="complete_video_qw3")]
    ])


def quest4_keyboard_after_clear():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Далее", callback_data="next_to_items")]
    ])

def quest4_keyboard_after_trash():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Приступить", callback_data="start_selection")]
    ])

# Клавиатура для выбора цифр
def quest4_keyboard(selected_numbers: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for number in range(1, 11):
        text = f"{number} ✅" if number in selected_numbers else str(number)
        buttons.append(InlineKeyboardButton(text=text, callback_data=f"select_{number}"))

    # Разбиваем кнопки на строки по 3 или 4 кнопки
    keyboard = []
    for i in range(0, len(buttons), 3):  # По 3 кнопки в строке
        keyboard.append(buttons[i:i + 3])

    # Добавляем кнопку "Готово" в отдельную строку
    keyboard.append([InlineKeyboardButton(text="Готово", callback_data="done")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def quest3_keyboard(question_number: int):
    """
    Возвращает клавиатуру для вопроса по его номеру.
    """
    keyboards = {
        1: [
            [InlineKeyboardButton(text="Прогулка", callback_data="Прогулка")],
            [InlineKeyboardButton(text="Печать", callback_data="Печать")],
            [InlineKeyboardButton(text="Сборка техники", callback_data="Сборка техники")]
        ],
        2: [
            [InlineKeyboardButton(text="Фотографирование", callback_data="Фотографирование")],
            [InlineKeyboardButton(text="Ретушь", callback_data="Ретушь")],
            [InlineKeyboardButton(text="Печать", callback_data="Печать")]
        ],
        3: [
            [InlineKeyboardButton(text="Обед на локации", callback_data="Обед на локации")],
            [InlineKeyboardButton(text="Демонстрация", callback_data="Демонстрация")],
            [InlineKeyboardButton(text="Ретушь", callback_data="Ретушь")]
        ],
        4: [
            [InlineKeyboardButton(text="Сборка техники", callback_data="Сборка техники")],
            [InlineKeyboardButton(text="Печать", callback_data="Печать")],
            [InlineKeyboardButton(text="Просмотр роликов", callback_data="Просмотр роликов")]
        ],
        5: [
            [InlineKeyboardButton(text="Демонстрация", callback_data="Демонстрация")],
            [InlineKeyboardButton(text="Отчет дня", callback_data="Отчет дня")],
            [InlineKeyboardButton(text="Ожидание", callback_data="Ожидание")]
        ],
    }
    return InlineKeyboardMarkup(inline_keyboard=keyboards.get(question_number, []))



def quest5_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Готово", callback_data="start_qw5")]
        #[InlineKeyboardButton(text="Профиль", callback_data="profile")]
    ])

def quest5_finish_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Готово",
        callback_data="finish_quest5"
    ))
    return builder.as_markup()

def quest6_finish_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Готово",
        callback_data="finish_quest6"
    ))
    return builder.as_markup()

def moderation_keyboard(user_id: int, quest_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"accept_{user_id}_{quest_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_{user_id}_{quest_id}"
                )
            ]
        ]
    )




# Добавим в inline.py

def quest6_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить фото", callback_data="start_qw6")]
    ])

def quest7_keyboard(options):
    buttons = []
    for option in options:
        buttons.append([InlineKeyboardButton(
            text=option,
            callback_data=f"qw7_answer_{option}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def quest7_next_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Далее", callback_data="next_qw7")]
    ])

def quest8_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Приступить к тесту", callback_data="start_quest8_test")]
    ])

def quest8_keyboard(options):
    buttons = []
    for option in options:
        # Используем хэш вместо сокращения текста
        callback_data = f"qw8_{hash(option)}"
        buttons.append([InlineKeyboardButton(
            text=option,
            callback_data=callback_data
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def quest9_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_quest9")]
    ])

def quest9_position_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фотограф", callback_data="qw9_position_фотограф")],
        [InlineKeyboardButton(text="Старший смены", callback_data="qw9_position_старший смены")],
        [InlineKeyboardButton(text="Администратор локации", callback_data="qw9_position_администратор локации")]
    ])

# Добавьте в конец inline.py

def quest10_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Приступить", callback_data="start_quest10")]
    ])

def quest10_hair_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Растрёпанная", callback_data="hair_messy")],
        [InlineKeyboardButton(text="Грязная", callback_data="hair_dirty")],
        [InlineKeyboardButton(text="Нормальная", callback_data="hair_normal")],
        [InlineKeyboardButton(text="Шапка", callback_data="hair_hat")],
        [InlineKeyboardButton(text="Кепка", callback_data="hair_cap")],
        [InlineKeyboardButton(text="Поварской колпак", callback_data="hair_chef")]
    ])

def quest10_face_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Чёрный мейкап", callback_data="face_black")],
        [InlineKeyboardButton(text="Синий мейкап", callback_data="face_blue")],
        [InlineKeyboardButton(text="Красный мейкап", callback_data="face_red")],
        [InlineKeyboardButton(text="Грязный", callback_data="face_dirty")],
        [InlineKeyboardButton(text="Сопли", callback_data="face_snot")],
        [InlineKeyboardButton(text="Чистый", callback_data="face_clean")]
    ])

def quest10_badge_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Есть бейдж", callback_data="badge_yes")],
        [InlineKeyboardButton(text="Нет бейджа", callback_data="badge_no")]
    ])

def quest10_shirt_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Футболка LF", callback_data="shirt_lf")],
        [InlineKeyboardButton(text="Футболка с пятнами", callback_data="shirt_dirty")],
        [InlineKeyboardButton(text="Кофта", callback_data="shirt_sweater")],
        [InlineKeyboardButton(text="Дырявая", callback_data="shirt_holey")]
    ])

def quest10_pants_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Брюки", callback_data="pants_trousers")],
        [InlineKeyboardButton(text="Шорты", callback_data="pants_shorts")],
        [InlineKeyboardButton(text="Грязные", callback_data="pants_dirty")],
        [InlineKeyboardButton(text="Скини", callback_data="pants_skinny")],
        [InlineKeyboardButton(text="Широкие", callback_data="pants_wide")],
        [InlineKeyboardButton(text="Рваные", callback_data="pants_torn")]
    ])

def quest10_shoes_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Кроксы", callback_data="shoes_crocs")],
        [InlineKeyboardButton(text="Носки дырявые", callback_data="shoes_holey_socks")],
        [InlineKeyboardButton(text="Носки целые", callback_data="shoes_whole_socks")],
        [InlineKeyboardButton(text="Сандали", callback_data="shoes_sandals")],
        [InlineKeyboardButton(text="Кроссовки", callback_data="shoes_sneakers")]
    ])

def quest10_finish_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Завершить", callback_data="finish_quest10")]
    ])

def quest11_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать фидбек", callback_data="start_quest11")]
    ])

def quest11_rating_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="rating_1")],
        [InlineKeyboardButton(text="2", callback_data="rating_2")],
        [InlineKeyboardButton(text="3", callback_data="rating_3")],
        [InlineKeyboardButton(text="4", callback_data="rating_4")],
        [InlineKeyboardButton(text="5", callback_data="rating_5")]
    ])

def quest11_interview_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Было не совсем понятно, но интересно", callback_data="interview_1")],
        [InlineKeyboardButton(text="Меня классно встретили, все рассказали", callback_data="interview_2")],
        [InlineKeyboardButton(text="Собеседования не было", callback_data="interview_3")],
        [InlineKeyboardButton(text="Было ужасно некомфортно", callback_data="interview_4")]
    ])

def quest11_reason_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Атмосфера на локации", callback_data="reason_1")],
        [InlineKeyboardButton(text="Приятная команда", callback_data="reason_2")],
        [InlineKeyboardButton(text="Хочу стать фотографом", callback_data="reason_3")],
        [InlineKeyboardButton(text="Интересные условия работы", callback_data="reason_4")],
        [InlineKeyboardButton(text="Комфортно (рядом с домом и т.д.)", callback_data="reason_5")]
    ])

def quest11_base_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Столько всего, ничего не понятно", callback_data="base_1")],
        [InlineKeyboardButton(text="Очень удобно, все под рукой", callback_data="base_2")],
        [InlineKeyboardButton(text="База это что?", callback_data="base_3")],
        [InlineKeyboardButton(text="Еще не понял", callback_data="base_4")]
    ])

def quest11_sales_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нет, я не собираюсь продавать", callback_data="sales_1")],
        [InlineKeyboardButton(text="Конечно, нужно грамотно преподносить", callback_data="sales_2")]
    ])

def quest11_team_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Очень некомфортно", callback_data="team_1")],
        [InlineKeyboardButton(text="Классная команда", callback_data="team_2")],
        [InlineKeyboardButton(text="Я почти ни с кем не знаком", callback_data="team_3")]
    ])

def quest11_uniform_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Впщ не нравится", callback_data="uniform_1")],
        [InlineKeyboardButton(text="Прикольная футболка", callback_data="uniform_2")],
        [InlineKeyboardButton(text="Мне все равно", callback_data="uniform_3")],
        [InlineKeyboardButton(text="Есть предложения по изменению", callback_data="uniform_4")]
    ])

def quest11_finish_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить фидбек", callback_data="finish_quest11")]
    ])
