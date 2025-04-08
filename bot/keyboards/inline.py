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
#клавиатура админа на старте
def admin_start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Админ-панель", callback_data="go_admin_panel")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")]
    ])

def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Список сотрудников", callback_data="list_intern")],
        [InlineKeyboardButton(text="Получить общую статистику", callback_data="get_analytics")],
        [InlineKeyboardButton(text="Профиль", callback_data="profile")]
    ])

#клавиатура перехода в админ панель
def go_admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="go_admin_panel")]
    ])

# Клавиатура для списка квестов
def quests_list_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать квесты", callback_data="start_quests_confirm")],
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
            [InlineKeyboardButton(text="Презентация", callback_data="Презентация")],
            [InlineKeyboardButton(text="Ретушь", callback_data="Ретушь")]
        ],
        4: [
            [InlineKeyboardButton(text="Сборка техники", callback_data="Сборка техники")],
            [InlineKeyboardButton(text="Печать", callback_data="Печать")],
            [InlineKeyboardButton(text="Просмотр роликов", callback_data="Просмотр роликов")]
        ],
        5: [
            [InlineKeyboardButton(text="Презентация", callback_data="Презентация")],
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

def quest11_finish_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Готово",
        callback_data="next_quest_12"
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

# Раздельные клавиатуры для разных этапов
def quest7_view_next_keyboard():
    """Клавиатура для этапа ознакомления"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Далее", callback_data="next_product_group")]
    ])

def quest7_next_keyboard():
    """Клавиатура для тестового этапа"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Следующий вопрос", callback_data="next_question_test")]
    ])

def quest7_finish_keyboard():
    """Клавиатура для завершения теста"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Завершить тест", callback_data="finish_quest7")]
    ])

def quest8_konspekt_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Конспект", callback_data="quest8_text")]
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
    """Клавиатура для начала квеста 10"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать", callback_data="start_quest10")]
    ])

def quest10_choice_keyboard(step: str):
    """Клавиатура для выбора варианта (1-5) на каждом этапе"""
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(
            text=str(i),
            callback_data=f"qw10_choose_{step}_{i}"
        ))
    builder.adjust(5)
    return builder.as_markup()

def quest10_finish_keyboard():
    """Клавиатура после завершения квеста"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий квест", callback_data="next_quest_11")]
    ])

def quest10_retry_keyboard(step: str):
    """Клавиатура при ошибке выбора (повторить)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"retry_quest10_{step}")]
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


def get_day_finish_keyboard(current_quest_id):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Начать новый день",
        callback_data=f"next_quest_{current_quest_id}"
    ))
    return builder.as_markup()




# Клавиатуры для квеста 12
def quest12_keyboard(options: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for option in options:
        builder.add(InlineKeyboardButton(
            text=option.capitalize(),
            callback_data=f"qw12_{option}"
        ))
    builder.adjust(2)
    return builder.as_markup()

def quest12_back_to_question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Вернуться к вопросу", callback_data="back_to_question_12")]
    ])

# Клавиатуры для квеста 13
def quest13_watch_again_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пересмотреть видео", callback_data="watch_again_13")],
        [InlineKeyboardButton(text="Продолжить", callback_data="continue_quest13")]
    ])

def quest13_continue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить", callback_data="continue_quest13")]
    ])

def quest13_task_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_task_13")]
    ])

def quest13_skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_task_13")]
    ])

def quest13_finish_tasks_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Завершить", callback_data="finish_quest13")]
    ])


def quest14_skip_zone_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить зону", callback_data="skip_zone_14")
    return builder.as_markup()

def quest14_finish_shooting_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Завершить и отправить", callback_data="finish_quest14")
    return builder.as_markup()

def quest16_keyboard(options):
    """Создает клавиатуру для квеста 16 с вариантами ответов"""
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        builder.button(text=option, callback_data=f"qw16_{i}")
    builder.adjust(1)
    return builder.as_markup()