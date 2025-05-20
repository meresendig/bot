from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from fsm import Chiromancy, Horoscope, NatalChart
from api_client import ask_gpt
from database import *
import datetime

# Главное меню
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🖐️ Хиромантия"))
    kb.add(KeyboardButton("🌟 Гороскоп"))
    kb.add(KeyboardButton("🪐 Натальная карта"))
    return kb

async def start(message: types.Message, state: FSMContext):
    await message.answer("Добро пожаловать в AI-Провидец!\nВыберите услугу:", reply_markup=main_menu())

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

async def horoscope_birthdate(message: types.Message, state: FSMContext):
    date = message.text
    prompt = (
        f"Ты профессиональный астролог. Составь персональный астрологический прогноз на основе даты рождения {date}. "
        "Учитывай знак зодиака, транзиты, лунные фазы и аспекты. Дай подробный прогноз на: сегодня, неделю и месяц. "
        "Пиши как эксперт, с живыми примерами, без обобщений."
    )
    answer = await ask_gpt(prompt)
    await message.answer(answer)
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
