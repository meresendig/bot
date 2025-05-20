import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from handlers import *
from payments import *
from database import get_pool, create_tables

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

pool = None

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message, state: FSMContext):
    await add_user(pool, message.from_user.id)
    await start(message, state)

@dp.message_handler(lambda m: m.text == "🖐️ Хиромантия")
async def m_chiromancy(message: types.Message, state: FSMContext):
    access = await check_access(pool, message.from_user.id)
    if access in ("trial", "paid"):
        await chiromancy_start(message, state)
        if access == "trial":
            await set_trial_used(pool, message.from_user.id)
    else:
        await message.answer("Для доступа оформите подписку или используйте пробный доступ.")

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Chiromancy.waiting_left)
async def chiromancy_left_photo(message: types.Message, state: FSMContext):
    await chiromancy_left(message, state)

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Chiromancy.waiting_right)
async def chiromancy_right_photo(message: types.Message, state: FSMContext):
    await chiromancy_right(message, state)

@dp.message_handler(lambda m: m.text == "🌟 Гороскоп")
async def m_horoscope(message: types.Message, state: FSMContext):
    access = await check_access(pool, message.from_user.id)
    if access in ("trial", "paid"):
        await horoscope_start(message, state)
        if access == "trial":
            await set_trial_used(pool, message.from_user.id)
    else:
        await message.answer("Для доступа оформите подписку или используйте пробный доступ.")

@dp.message_handler(state=Horoscope.waiting_birthdate)
async def horoscope_date(message: types.Message, state: FSMContext):
    await horoscope_birthdate(message, state)

@dp.message_handler(lambda m: m.text == "🪐 Натальная карта")
async def m_natal(message: types.Message, state: FSMContext):
    access = await check_access(pool, message.from_user.id)
    if access in ("trial", "paid"):
        await natal_start(message, state)
        if access == "trial":
            await set_trial_used(pool, message.from_user.id)
    else:
        await message.answer("Для доступа оформите подписку или используйте пробный доступ.")

@dp.message_handler(state=NatalChart.waiting_birthdate)
async def natal_birthdate_handler(message: types.Message, state: FSMContext):
    await natal_birthdate(message, state)

@dp.message_handler(state=NatalChart.waiting_time)
async def natal_time_handler(message: types.Message, state: FSMContext):
    await natal_time(message, state)

@dp.message_handler(state=NatalChart.waiting_city)
async def natal_city_handler(message: types.Message, state: FSMContext):
    await natal_city(message, state)

# Команды для оплаты
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

async def on_startup(_):
    global pool
    pool = await get_pool()
    await create_tables(pool)
    print("Бот запущен")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup)
