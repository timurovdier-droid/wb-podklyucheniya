from aiogram.fsm.state import State, StatesGroup


class Flow(StatesGroup):
    city = State()
    apply_phone = State()
    apply_warn = State()
    apply_photo = State()
    apply_cars = State()
    apply_plate = State()
    brand_rules = State()
    brand_name = State()
    brand_phone = State()
    brand_model = State()
    brand_year = State()
    brand_color = State()
    brand_plate = State()
