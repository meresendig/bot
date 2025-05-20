from aiogram import types
from aiogram.types import LabeledPrice
import datetime
from database import *

PRICES = {
    "day": 10000,   # 100.00 RUB
    "week": 35000,  # 350.00 RUB
    "month": 135000 # 1350.00 RUB
}

def get_invoice(period):
    label = {
        "day": "Подписка на 1 день",
        "week": "Подписка на 7 дней",
        "month": "Подписка на 30 дней"
    }[period]
    return [LabeledPrice(label, PRICES[period])]

async def process_payment(callback_query, period, pool):
    user_id = callback_query.from_user.id
    now = datetime.datetime.now()
    if period == "day":
        until = now + datetime.timedelta(days=1)
    elif period == "week":
        until = now + datetime.timedelta(weeks=1)
    else:
        until = now + datetime.timedelta(days=30)
    await set_paid_until(pool, user_id, until)
    await callback_query.message.answer(f"Оплата прошла успешно! Доступ до {until.strftime('%d.%m.%Y %H:%M')}.")

async def check_access(pool, user_id):
    user = await get_user(pool, user_id)
    now = datetime.datetime.now()
    if not user:
        await add_user(pool, user_id)
        return "trial"
    if not user["trial_used"]:
        return "trial"
    if user["paid_until"] and user["paid_until"] > now:
        return "paid"
    return "no_access"
