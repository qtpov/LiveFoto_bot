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