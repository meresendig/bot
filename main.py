import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

import handlers  # Важно: импорт всего модуля (для pool)
from handlers import (
    start, free_trial, pay_options,
    chiromancy_start, chiromancy_left, chiromancy_right,
    horoscope_start, horoscope_birthdate, horoscope_period,
    natal_start, natal_birthdate, natal_time, natal_city
)
from payments import *
from database import get_pool, create_tables, add_user, set_trial_used
from fsm import Chiromancy, Horoscope, NatalChart

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

pool = None

# ====== Регистрация обработчиков меню доступа ======
dp.register_message_handler(start, commands=["start"], state="*")
dp.register_message_handler(free_trial, lambda m: m.text == "🆓 Бесплатный доступ", state="*")
dp.register_message_handler(pay_options, lambda m: m.text == "💳 Оформить подписку", state="*")

# ====== Хиромантия ======
dp.register_message_handler(chiromancy_start, lambda m: m.text == "🖐️ Хиромантия", state="*")
dp.register_message_handler(chiromancy_left, content_types=types.ContentType.PHOTO, state=Chiromancy.waiting_left)
dp.register_message_handler(chiromancy_right, content_types=types.ContentType.PHOTO, state=Chiromancy.waiting_right)

# ====== Гороскоп ======
dp.register_message_handler(horoscope_start, lambda m: m.text == "🌟 Гороскоп", state="*")
dp.register_message_handler(horoscope_birthdate, state=Horoscope.waiting_birthdate)
dp.register_callback_query_handler(horoscope_period, lambda c: c.data.startswith("horo_"), state="*")

# ====== Натальная карта ======
dp.register_message_handler(natal_start, lambda m: m.text == "🪐 Натальная карта", state="*")
dp.register_message_handler(natal_birthdate, state=NatalChart.waiting_birthdate)
dp.register_message_handler(natal_time, state=NatalChart.waiting_time)
dp.register_message_handler(natal_city, state=NatalChart.waiting_city)

# ====== Оплата ======
@dp.message_handler(commands=["pay"])
async def cmd_pay(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("1 день — 100₽", callback_data="pay_day"))
    kb.add(types.InlineKeyboardButton("7 дней — 350₽", callback_data="pay_week"))
    kb.add(types.InlineKeyboardButton("30 дней — 1350₽", callback_data="pay_month"))
    await message.answer("Выберите период подписки:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("pay_"))
async def process_pay_callback(callback_query: types.CallbackQuery):
    period = callback_query.data.replace("pay_", "")
    await bot.send_invoice(
        callback_query.from_user.id,
        title="AI-Провидец Подписка",
        description="Доступ к premium-аналитике",
        provider_token=os.getenv("PAYMENT_TOKEN"),
        currency="RUB",
        prices=get_invoice(period),
        payload=period
    )
    await callback_query.answer()

@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def got_payment(message: types.Message):
    period = message.successful_payment.invoice_payload
    await process_payment(message, period, pool)

# ====== on_startup ======
async def on_startup(_):
    global pool
    pool = await get_pool()
    await create_tables(pool)
    handlers.pool = pool   # Это важно!
    print("Бот запущен")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
