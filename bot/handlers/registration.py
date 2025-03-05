from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.db.session import SessionLocal
from bot.db.crud import add_user
from bot.keyboards.inline import go_profile_keyboard
import logging
from datetime import datetime
import re

router = Router()

# Состояния для анкеты
class ProfileForm(StatesGroup):
    full_name = State()
    birth_date = State()
    phone = State()
    address = State()
    vacancy = State()
    desired_salary = State()
    marital_status = State()
    children = State()
    education = State()
    additional_education = State()
    work_experience = State()
    health_restrictions = State()
    criminal_record = State()
    preferred_schedule = State()
    medical_book = State()
    military_service = State()
    start_date = State()
    vacancy_source = State()
    relatives_contacts = State()
    friends_contacts = State()
    personal_data_consent = State()
    gender = State()

# Функция для удаления сообщений
async def delete_previous_messages(bot, chat_id: int, message_id: int):
    """
    Удаляет сообщение с указанным message_id.
    """
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        logging.error(f"Не удалось удалить сообщение: {e}")

# Начало заполнения анкеты
@router.callback_query(F.data == "start_profile_form")
async def start_profile_form(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, введите ваше ФИО:")
    await state.set_state(ProfileForm.full_name)
    await callback.answer()

# Обработка ФИО
@router.message(ProfileForm.full_name)
async def process_full_name(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    if not re.match(r'^[А-Яа-яЁё\s]+$', message.text):
        # Удаляем сообщение с ответом пользователя
        await delete_previous_messages(bot, message.chat.id, message.message_id)

        await message.answer("Ошибка: ФИО должно содержать только кириллицу и пробелы.")
        return

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(full_name=message.text)
    await message.answer("Введите вашу дату рождения (в формате ДД.ММ.ГГГГ):")
    await state.set_state(ProfileForm.birth_date)

# Обработка даты рождения
@router.message(ProfileForm.birth_date)
async def process_birth_date(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    try:
        birth_date = datetime.strptime(message.text, "%d.%m.%Y")
        # Удаляем сообщение с ответом пользователя
        await delete_previous_messages(bot, message.chat.id, message.message_id)

        await state.update_data(birth_date=message.text)
        await message.answer("Введите ваш номер телефона (в формате +7XXXXXXXXXX):")
        await state.set_state(ProfileForm.phone)
    except ValueError:
        await delete_previous_messages(bot, message.chat.id, message.message_id)
        await message.answer("Ошибка: Неверный формат даты рождения. Используйте формат ДД.ММ.ГГГГ.")

# Обработка номера телефона
@router.message(ProfileForm.phone)
async def process_phone(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    if not re.match(r'^\+7\d{10}$', message.text):
        # Удаляем сообщение с ответом пользователя
        await delete_previous_messages(bot, message.chat.id, message.message_id)
        await message.answer("Ошибка: Неверный формат номера телефона. Используйте формат +7XXXXXXXXXX.")
        return

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(phone=message.text)
    await message.answer("Введите ваш фактический адрес проживания:")
    await state.set_state(ProfileForm.address)

# Обработка адреса
@router.message(ProfileForm.address)
async def process_address(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(address=message.text)
    await message.answer("На какую вакансию вы претендуете?")
    await state.set_state(ProfileForm.vacancy)

# Обработка вакансии
@router.message(ProfileForm.vacancy)
async def process_vacancy(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(vacancy=message.text)
    await message.answer("Какой уровень заработной платы вы ожидаете?")
    await state.set_state(ProfileForm.desired_salary)

# Обработка желаемой зарплаты
@router.message(ProfileForm.desired_salary)
async def process_desired_salary(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    if not re.match(r'^\d+$', message.text):
        await delete_previous_messages(bot, message.chat.id, message.message_id)
        await message.answer("Ошибка: Зарплата должна быть числом.")
        return

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(desired_salary=message.text)
    await message.answer("Ваше семейное положение:")
    await state.set_state(ProfileForm.marital_status)

# Обработка семейного положения
@router.message(ProfileForm.marital_status)
async def process_marital_status(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(marital_status=message.text)
    await message.answer("Укажите возраст ваших детей (если есть, в формате числа):")
    await state.set_state(ProfileForm.children)

# Обработка информации о детях
@router.message(ProfileForm.children)
async def process_children(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    if message.text and not re.match(r'^\d+$', message.text):
        await delete_previous_messages(bot, message.chat.id, message.message_id)
        await message.answer("Ошибка: Возраст детей должен быть числом.")
        return

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(children=message.text)
    await message.answer("Укажите ваше образование (ВУЗ, специальность):")
    await state.set_state(ProfileForm.education)

# Обработка образования
@router.message(ProfileForm.education)
async def process_education(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(education=message.text)
    await message.answer("Укажите дополнительное обучение (если есть):")
    await state.set_state(ProfileForm.additional_education)

# Обработка дополнительного образования
@router.message(ProfileForm.additional_education)
async def process_additional_education(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(additional_education=message.text)
    await message.answer("Опишите ваш опыт работы (последние 3 места работы):")
    await state.set_state(ProfileForm.work_experience)

# Обработка опыта работы
@router.message(ProfileForm.work_experience)
async def process_work_experience(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(work_experience=message.text)
    await message.answer("Есть ли у вас ограничения по работе или хронические заболевания?")
    await state.set_state(ProfileForm.health_restrictions)

# Обработка ограничений по здоровью
@router.message(ProfileForm.health_restrictions)
async def process_health_restrictions(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(health_restrictions=message.text)
    await message.answer("Есть ли у вас судимости? Если да, укажите статью:")
    await state.set_state(ProfileForm.criminal_record)

# Обработка судимостей
@router.message(ProfileForm.criminal_record)
async def process_criminal_record(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(criminal_record=message.text)
    await message.answer("Какой график работы вы предпочитаете?")
    await state.set_state(ProfileForm.preferred_schedule)

# Обработка предпочтительного графика работы
@router.message(ProfileForm.preferred_schedule)
async def process_preferred_schedule(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(preferred_schedule=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="medical_book_yes")],
        [InlineKeyboardButton(text="Нет", callback_data="medical_book_no")]
    ])
    await message.answer("Есть ли у вас медицинская книжка (действующая или нет)?", reply_markup=keyboard)
    await state.set_state(ProfileForm.medical_book)

# Обработка медицинской книжки
@router.callback_query(ProfileForm.medical_book, F.data.in_(["medical_book_yes", "medical_book_no"]))
async def process_medical_book(callback: types.CallbackQuery, state: FSMContext, bot):

    medical_book = "Да" if callback.data == "medical_book_yes" else "Нет"
    await state.update_data(medical_book=medical_book)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Служил", callback_data="military_served")],
        [InlineKeyboardButton(text="Не служил", callback_data="military_not_served")],
        [InlineKeyboardButton(text="Запас", callback_data="military_reserve")],
        [InlineKeyboardButton(text="Не имею отношения", callback_data="military_no_relation")]
    ])
    await callback.message.edit_text("Ваше отношение к воинской обязанности:", reply_markup=keyboard)
    await state.set_state(ProfileForm.military_service)
    await callback.answer()

# Обработка воинской обязанности
@router.callback_query(ProfileForm.military_service, F.data.in_(["military_served", "military_not_served", "military_reserve", "military_no_relation"]))
async def process_military_service(callback: types.CallbackQuery, state: FSMContext, bot):

    military_service = {
        "military_served": "Служил",
        "military_not_served": "Не служил",
        "military_reserve": "Запас",
        "military_no_relation": "Не имею отношения"
    }[callback.data]
    await state.update_data(military_service=military_service)
    await callback.message.edit_text("Когда вы готовы приступить к работе? (в формате ДД.ММ.ГГГГ):")
    await state.set_state(ProfileForm.start_date)
    await callback.answer()

# Обработка даты начала работы
@router.message(ProfileForm.start_date)
async def process_start_date(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    try:
        start_date = datetime.strptime(message.text, "%d.%m.%Y")
        # Удаляем сообщение с ответом пользователя
        await delete_previous_messages(bot, message.chat.id, message.message_id)

        await state.update_data(start_date=message.text)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="HH.ru", callback_data="vacancy_source_hh")],
            [InlineKeyboardButton(text="Avito", callback_data="vacancy_source_avito")],
            [InlineKeyboardButton(text="Работа.ру", callback_data="vacancy_source_rabota")],
            [InlineKeyboardButton(text="ВК", callback_data="vacancy_source_vk")],
            [InlineKeyboardButton(text="Друзья/родственники", callback_data="vacancy_source_friends")],
            [InlineKeyboardButton(text="Другое", callback_data="vacancy_source_other")]
        ])
        await message.answer("Откуда вы узнали о вакансии?", reply_markup=keyboard)
        await state.set_state(ProfileForm.vacancy_source)
    except ValueError:
        await delete_previous_messages(bot, message.chat.id, message.message_id)
        await message.answer("Ошибка: Неверный формат даты. Используйте формат ДД.ММ.ГГГГ.")

# Обработка источника вакансии
@router.callback_query(ProfileForm.vacancy_source, F.data.in_(["vacancy_source_hh", "vacancy_source_avito", "vacancy_source_rabota", "vacancy_source_vk", "vacancy_source_friends", "vacancy_source_other"]))
async def process_vacancy_source(callback: types.CallbackQuery, state: FSMContext, bot):

    vacancy_source = {
        "vacancy_source_hh": "HH.ru",
        "vacancy_source_avito": "Avito",
        "vacancy_source_rabota": "Работа.ру",
        "vacancy_source_vk": "ВК",
        "vacancy_source_friends": "Друзья/родственники",
        "vacancy_source_other": "Другое"
    }[callback.data]
    await state.update_data(vacancy_source=vacancy_source)
    await callback.message.edit_text("Укажите контактные данные близких родственников (ФИО, степень родства, дата рождения, телефон):")
    await state.set_state(ProfileForm.relatives_contacts)
    await callback.answer()

# Обработка контактов родственников
@router.message(ProfileForm.relatives_contacts)
async def process_relatives_contacts(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(relatives_contacts=message.text)
    await message.answer("Укажите контакты друзей/знакомых/родственников, которые также ищут работу:")
    await state.set_state(ProfileForm.friends_contacts)

# Обработка контактов друзей
@router.message(ProfileForm.friends_contacts)
async def process_friends_contacts(message: types.Message, state: FSMContext, bot):
    # Удаляем сообщение с вопросом
    await delete_previous_messages(bot, message.chat.id, message.message_id - 1)

    # Удаляем сообщение с ответом пользователя
    await delete_previous_messages(bot, message.chat.id, message.message_id)

    await state.update_data(friends_contacts=message.text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мужской", callback_data="gender_male")],
        [InlineKeyboardButton(text="Женский", callback_data="gender_female")]
    ])
    await message.answer("Пожалуйста, укажите ваш пол:", reply_markup=keyboard)
    await state.set_state(ProfileForm.gender)

# Обработка пола
@router.callback_query(ProfileForm.gender, F.data.in_(["gender_male", "gender_female"]))
async def process_gender(callback: types.CallbackQuery, state: FSMContext, bot):

    gender = "Мужской" if callback.data == "gender_male" else "Женский"
    await state.update_data(gender=gender)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Согласен", callback_data="consent_yes")],
        [InlineKeyboardButton(text="Согласна", callback_data="consent_yes")]
    ])
    await callback.message.edit_text("Cогласие на обработку персональных данных\n"
                                     "В соответствии с п.1 ст.9 закона РФ от 27.-7.2006 №152-ФЗ «О персональных данных»"
                                     " разрешение на обработку моих персональных данных, хранение и использования исключительно"
                                     " для решения вопроса о приеме меня на работу, о моем обучении и продвижении, а так же в других целях"
                                     ", связанных с трудовыми отношениями между мной и Компанией. Я не возражаю против получения"
                                     " моих персональных данных о предыдущих местах работы и периодах трудовой деятельности от третьих лиц."
                                     " Я подтверждаю достоверность всего изложенного выше и не возражаю против проверки данных сведений."
                                     , reply_markup=keyboard)
    await state.set_state(ProfileForm.personal_data_consent)
    await callback.answer()

# Обработка согласия на обработку данных
@router.callback_query(ProfileForm.personal_data_consent, F.data == "consent_yes")
async def process_personal_data_consent(callback: types.CallbackQuery, state: FSMContext, bot):

    await callback.message.delete()
    # Получаем данные из состояния
    data = await state.get_data()

    # Проверяем, есть ли дата рождения
    if "birth_date" not in data:
        await callback.message.answer("Ошибка: Дата рождения не указана.")
        return

    # Рассчитываем возраст на основе даты рождения
    try:
        birth_date = datetime.strptime(data["birth_date"], "%d.%m.%Y")  # Формат ДД.ММ.ГГГГ
        today = datetime.today()
        age = today.year - birth_date.year

        # Корректируем возраст, если день рождения еще не наступил в этом году
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
    except ValueError:
        await callback.message.answer("Ошибка: Неверный формат даты рождения. Используйте формат ДД.ММ.ГГГГ.")
        return

    # Подготавливаем данные для профиля
    profile_data = {
        "full_name": data["full_name"],
        "birth_date": data["birth_date"],
        "phone": data["phone"],
        "address": data["address"],
        "vacancy": data["vacancy"],
        "desired_salary": data["desired_salary"],
        "marital_status": data["marital_status"],
        "children": data["children"],
        "education": data["education"],
        "additional_education": data["additional_education"],
        "work_experience": data["work_experience"],
        "health_restrictions": data["health_restrictions"],
        "criminal_record": data["criminal_record"],
        "preferred_schedule": data["preferred_schedule"],
        "medical_book": data["medical_book"],
        "military_service": data["military_service"],
        "start_date": data["start_date"],
        "vacancy_source": data["vacancy_source"],
        "relatives_contacts": data["relatives_contacts"],
        "friends_contacts": data["friends_contacts"],
        "personal_data_consent": True
    }

    # Сохраняем пользователя и профиль в базу данных
    async with SessionLocal() as session:
        try:
            # Создаем пользователя и профиль
            user = await add_user(
                session,
                telegram_id=callback.from_user.id,
                full_name=data["full_name"],
                age=age,  # Рассчитанный возраст
                gender=data["gender"],  # Пол, который был запрошен ранее
                profile_data=profile_data
            )
            await callback.message.answer("Спасибо! Ваша анкета успешно сохранена.", reply_markup=go_profile_keyboard())
        except ValueError as e:
            await callback.message.answer(f"Ошибка: {e}")
        except Exception as e:
            await callback.message.answer("Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже.")
            logging.error(f"Ошибка при сохранении данных: {e}")

    # Очищаем состояние
    await state.clear()
    await callback.answer()