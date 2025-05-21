from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types
from aiogram.dispatcher import FSMContext
from api_client import ask_gpt
from database import *
import os


# Главное меню
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🖐️ Хиромантия"))
    kb.add(KeyboardButton("🌟 Гороскоп"))
    kb.add(KeyboardButton("🪐 Натальная карта"))
    kb.add(KeyboardButton("🆓 Бесплатный доступ"))
    kb.add(KeyboardButton("💳 Оформить подписку"))
    return kb

def subscribe_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1 день — 100₽", callback_data="pay_day"),
        InlineKeyboardButton("7 дней — 350₽", callback_data="pay_week"),
        InlineKeyboardButton("30 дней — 1350₽", callback_data="pay_month")
    )
    return kb

def horoscope_type_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("На сегодня", callback_data="horo_today"),
        InlineKeyboardButton("На неделю", callback_data="horo_week"),
        InlineKeyboardButton("На месяц", callback_data="horo_month"),
        InlineKeyboardButton("На год", callback_data="horo_year")
    )
    return kb



async def start(message: types.Message, state: FSMContext):
    await message.answer(
        "Добро пожаловать в AI-Провидец!\nВыберите услугу:",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda m: m.text == "🆓 Бесплатный доступ")
async def free_trial(message: types.Message):
    user_id = message.from_user.id
    access = await check_access(pool, user_id)
    if access == "trial":
        await set_trial_used(pool, user_id)
        await message.answer("Бесплатный пробный доступ активирован! Теперь выберите услугу.", reply_markup=main_menu())
    else:
        await message.answer("Пробный доступ уже использован. Оформите подписку.", reply_markup=subscribe_menu())

@dp.message_handler(lambda m: m.text == "💳 Оформить подписку")
async def pay_options(message: types.Message):
    await message.answer("Выберите период подписки:", reply_markup=subscribe_menu())



# ========== Хиромантия ==========
async def chiromancy_start(message: types.Message, state: FSMContext):
    await state.set_state(Chiromancy.waiting_left.state)
    await message.answer("Пришлите фото ЛЕВОЙ ладони")

async def chiromancy_left(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(left_hand=file_id)
    await state.set_state(Chiromancy.waiting_right.state)
    await message.answer("Теперь пришлите фото ПРАВОЙ ладони")

async def chiromancy_right(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    data = await state.get_data()
    left_file_id = data.get("left_hand")

    prompt = (
        "Ты профессиональный хиромант с 30-летним стажем. Дай глубокий индивидуальный анализ по двум изображениям ладоней клиента. "
        "Проанализируй линии жизни, сердца, ума, судьбы, здоровья, детей, брака. "
        "Отдельно опиши: прошлое, настоящее, будущее, здоровье, финансы, любовь, судьбу и долголетие. "
        "Пиши с теплотой, подробно, без шаблонов, ориентируясь на уникальность каждого пользователя."
        "\n[Здесь должно быть описание двух фото ладоней, ссылки или base64 файлов]"
    )
    # todo: скачать фото, приложить base64/ссылки для анализа в промпте если требуется.
    answer = await ask_gpt(prompt)
    await message.answer(answer)
    await state.finish()

# ========== Гороскоп ==========
async def horoscope_start(message: types.Message, state: FSMContext):
    await state.set_state(Horoscope.waiting_birthdate.state)
    await message.answer("Введите вашу дату рождения в формате ДД.ММ.ГГГГ")

@dp.message_handler(state=Horoscope.waiting_birthdate)
async def horoscope_birthdate(message: types.Message, state: FSMContext):
    await state.update_data(birthdate=message.text)
    await message.answer("Выберите период гороскопа:", reply_markup=horoscope_type_menu())

@dp.callback_query_handler(lambda c: c.data.startswith("horo_"), state="*")
async def horoscope_period(callback_query: types.CallbackQuery, state: FSMContext):
    period = callback_query.data.replace("horo_", "")
    data = await state.get_data()
    date = data.get("birthdate")
    periods = {
        "today": "на сегодня",
        "week": "на неделю",
        "month": "на месяц",
        "year": "на год"
    }
    prompt = (
        f"Ты профессиональный астролог. Составь персональный астрологический прогноз {periods[period]} на основе даты рождения {date}. "
        "Учитывай знак зодиака, транзиты, лунные фазы и аспекты. "
        "Дай подробный прогноз. Пиши как эксперт, с живыми примерами, без обобщений."
    )
    answer = await ask_gpt(prompt)
    await callback_query.message.answer(answer)
    await state.finish()


# ========== Натальная карта ==========
async def natal_start(message: types.Message, state: FSMContext):
    await state.set_state(NatalChart.waiting_birthdate.state)
    await message.answer("Введите вашу дату рождения в формате ДД.ММ.ГГГГ")

async def natal_birthdate(message: types.Message, state: FSMContext):
    await state.update_data(birthdate=message.text)
    await state.set_state(NatalChart.waiting_time.state)
    await message.answer("Введите время рождения (например: 14:30) или '-' если неизвестно.")

async def natal_time(message: types.Message, state: FSMContext):
    await state.update_data(birthtime=message.text)
    await state.set_state(NatalChart.waiting_city.state)
    await message.answer("Введите город рождения.")

async def natal_city(message: types.Message, state: FSMContext):
    data = await state.get_data()
    date = data.get("birthdate")
    time = data.get("birthtime")
    city = message.text

    prompt = (
        f"Ты профессиональный астролог. Составь полный разбор натальной карты по дате {date}, времени {time}, городу {city}. "
        "Проанализируй личность, карму, сильные и слабые стороны, финансы, любовь, предназначение. "
        "Укажи аспекты, дома, планеты. Пиши с уважением, экспертно, в развернутой форме."
    )
    answer = await ask_gpt(prompt)
    await message.answer(answer)
    await state.finish()
