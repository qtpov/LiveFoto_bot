from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.session import SessionLocal
from bot.db.crud import add_user
import logging
from datetime import datetime
from bot.db.models import UserProfile

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

# Начало заполнения анкеты
@router.callback_query(F.data == "start_profile_form")
async def start_profile_form(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Пожалуйста, введите ваше ФИО:")
    await state.set_state(ProfileForm.full_name)
    await callback.answer()

# Обработка ФИО
@router.message(ProfileForm.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Введите вашу дату рождения (в формате ДД.ММ.ГГГГ):")
    await state.set_state(ProfileForm.birth_date)

# Обработка даты рождения
@router.message(ProfileForm.birth_date)
async def process_birth_date(message: types.Message, state: FSMContext):
    try:
        # Проверяем формат даты
        birth_date = datetime.strptime(message.text, "%d.%m.%Y")  # Формат ДД.ММ.ГГГГ
        await state.update_data(birth_date=message.text)  # Сохраняем дату рождения в состоянии
        await message.answer("Введите ваш номер телефона::")
        await state.set_state(ProfileForm.phone)
    except ValueError:
        await message.answer("Ошибка: Неверный формат даты рождения. Используйте формат ДД.ММ.ГГГГ.")


# Обработка номера телефона
@router.message(ProfileForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите ваш фактический адрес проживания:")
    await state.set_state(ProfileForm.address)

# Обработка адреса
@router.message(ProfileForm.address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("На какую вакансию вы претендуете?")
    await state.set_state(ProfileForm.vacancy)

# Обработка вакансии
@router.message(ProfileForm.vacancy)
async def process_vacancy(message: types.Message, state: FSMContext):
    await state.update_data(vacancy=message.text)
    await message.answer("Какой уровень заработной платы вы ожидаете?")
    await state.set_state(ProfileForm.desired_salary)

# Обработка желаемой зарплаты
@router.message(ProfileForm.desired_salary)
async def process_desired_salary(message: types.Message, state: FSMContext):
    await state.update_data(desired_salary=message.text)
    await message.answer("Ваше семейное положение:")
    await state.set_state(ProfileForm.marital_status)

# Обработка семейного положения
@router.message(ProfileForm.marital_status)
async def process_marital_status(message: types.Message, state: FSMContext):
    await state.update_data(marital_status=message.text)
    await message.answer("Укажите возраст ваших детей (если есть):")
    await state.set_state(ProfileForm.children)

# Обработка информации о детях
@router.message(ProfileForm.children)
async def process_children(message: types.Message, state: FSMContext):
    await state.update_data(children=message.text)
    await message.answer("Укажите ваше образование (ВУЗ, специальность):")
    await state.set_state(ProfileForm.education)

# Обработка образования
@router.message(ProfileForm.education)
async def process_education(message: types.Message, state: FSMContext):
    await state.update_data(education=message.text)
    await message.answer("Укажите дополнительное обучение (если есть):")
    await state.set_state(ProfileForm.additional_education)

# Обработка дополнительного образования
@router.message(ProfileForm.additional_education)
async def process_additional_education(message: types.Message, state: FSMContext):
    await state.update_data(additional_education=message.text)
    await message.answer("Опишите ваш опыт работы (последние 3 места работы):")
    await state.set_state(ProfileForm.work_experience)

# Обработка опыта работы
@router.message(ProfileForm.work_experience)
async def process_work_experience(message: types.Message, state: FSMContext):
    await state.update_data(work_experience=message.text)
    await message.answer("Есть ли у вас ограничения по работе или хронические заболевания?")
    await state.set_state(ProfileForm.health_restrictions)

# Обработка ограничений по здоровью
@router.message(ProfileForm.health_restrictions)
async def process_health_restrictions(message: types.Message, state: FSMContext):
    await state.update_data(health_restrictions=message.text)
    await message.answer("Есть ли у вас судимости? Если да, укажите статью:")
    await state.set_state(ProfileForm.criminal_record)

# Обработка судимостей
@router.message(ProfileForm.criminal_record)
async def process_criminal_record(message: types.Message, state: FSMContext):
    await state.update_data(criminal_record=message.text)
    await message.answer("Какой график работы вы предпочитаете?")
    await state.set_state(ProfileForm.preferred_schedule)

# Обработка предпочтительного графика работы
@router.message(ProfileForm.preferred_schedule)
async def process_preferred_schedule(message: types.Message, state: FSMContext):
    await state.update_data(preferred_schedule=message.text)
    await message.answer("Есть ли у вас медицинская книжка (действующая или нет)?")
    await state.set_state(ProfileForm.medical_book)

# Обработка медицинской книжки
@router.message(ProfileForm.medical_book)
async def process_medical_book(message: types.Message, state: FSMContext):
    await state.update_data(medical_book=message.text)
    await message.answer("Ваше отношение к воинской обязанности (служил, запас и т.п.):")
    await state.set_state(ProfileForm.military_service)

# Обработка воинской обязанности
@router.message(ProfileForm.military_service)
async def process_military_service(message: types.Message, state: FSMContext):
    await state.update_data(military_service=message.text)
    await message.answer("Когда вы готовы приступить к работе?")
    await state.set_state(ProfileForm.start_date)

# Обработка даты начала работы
@router.message(ProfileForm.start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    await state.update_data(start_date=message.text)
    await message.answer("Откуда вы узнали о вакансии? (HH.ru, Avito, Работа.ру, ВК, Друзья/родственники, Другое)")
    await state.set_state(ProfileForm.vacancy_source)

# Обработка источника вакансии
@router.message(ProfileForm.vacancy_source)
async def process_vacancy_source(message: types.Message, state: FSMContext):
    await state.update_data(vacancy_source=message.text)
    await message.answer("Укажите контактные данные близких родственников (ФИО, степень родства, дата рождения, телефон):")
    await state.set_state(ProfileForm.relatives_contacts)

# Обработка контактов родственников
@router.message(ProfileForm.relatives_contacts)
async def process_relatives_contacts(message: types.Message, state: FSMContext):
    await state.update_data(relatives_contacts=message.text)
    await message.answer("Укажите контакты друзей/знакомых/родственников, которые также ищут работу:")
    await state.set_state(ProfileForm.friends_contacts)

# Обработка контактов друзей
@router.message(ProfileForm.friends_contacts)
async def process_friends_contacts(message: types.Message, state: FSMContext):
    await state.update_data(friends_contacts=message.text)
    await message.answer("Пожалуйста, укажите ваш пол (Мужской/Женский):")
    await state.set_state(ProfileForm.gender)


@router.message(ProfileForm.gender)
async def process_gender(message: types.Message, state: FSMContext):
    gender = message.text.strip().lower()
    if gender in ["мужской", "женский"]:
        await state.update_data(gender=gender.capitalize())
        await message.answer("Дайте согласие на обработку персональных данных (напишите 'Согласен' или 'Согласна'):")
        await state.set_state(ProfileForm.personal_data_consent)
    else:
        await message.answer('Пожалуйста, напишите "Мужской" или "Женский".')


# Обработка согласия на обработку данных
@router.message(ProfileForm.personal_data_consent)
async def process_personal_data_consent(message: types.Message, state: FSMContext):
    if message.text.lower() in ["согласен", "согласна"]:
        # Получаем данные из состояния
        data = await state.get_data()

        # Проверяем, есть ли дата рождения
        if "birth_date" not in data:
            await message.answer("Ошибка: Дата рождения не указана.")
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
            await message.answer("Ошибка: Неверный формат даты рождения. Используйте формат ДД.ММ.ГГГГ.")
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
                    telegram_id=message.from_user.id,
                    full_name=data["full_name"],
                    age=age,  # Рассчитанный возраст
                    gender=data["gender"],  # Пол, который был запрошен ранее
                    profile_data=profile_data
                )
                await message.answer("Спасибо! Ваша анкета успешно сохранена.")
            except ValueError as e:
                await message.answer(f"Ошибка: {e}")
            except Exception as e:
                await message.answer("Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже.")
                logging.error(f"Ошибка при сохранении данных: {e}")

        # Очищаем состояние
        await state.clear()
    else:
        await message.answer('Пожалуйста, напишите "Согласен" или "Согласна".')