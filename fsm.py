from aiogram.dispatcher.filters.state import StatesGroup, State

class Chiromancy(StatesGroup):
    waiting_left = State()
    waiting_right = State()

class Horoscope(StatesGroup):
    waiting_birthdate = State()

class NatalChart(StatesGroup):
    waiting_birthdate = State()
    waiting_time = State()
    waiting_city = State()
