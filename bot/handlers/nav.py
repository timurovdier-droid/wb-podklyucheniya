from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers import apply as apply_flow
from bot.keyboards import (
    back_keyboard,
    city_keyboard,
    continue_keyboard,
    menu_keyboard,
    phone_keyboard,
)
from bot.states import Flow
from bot.texts import (
    BTN_BACK,
    PHOTO_STEPS,
    apply_phone,
    apply_warning,
    ask_plate,
    brand_ask_color,
    brand_ask_model,
    brand_ask_name,
    brand_ask_phone,
    brand_ask_plate,
    brand_ask_year,
    brand_rules,
    cars_progress,
    choose_city,
    menu_intro,
    welcome,
)

router = Router()


async def show_city(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    city = data.get("city")
    await state.set_state(Flow.city)
    if city:
        await state.update_data(city=city)
    await message.answer(welcome(), reply_markup=city_keyboard())


async def show_menu(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    city = data.get("city")
    if not city:
        await show_city(message, state)
        return
    await state.set_state(None)
    await state.update_data(city=city)
    await message.answer(menu_intro(city), reply_markup=menu_keyboard())


@router.message(F.chat.type == "private", F.text == BTN_BACK)
async def go_back(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    data = await state.get_data()
    city = data.get("city") or ""

    if current in (None, Flow.city.state):
        if current is None and city:
            await show_city(message, state)
            return
        await show_city(message, state)
        return

    if current == Flow.apply_phone.state:
        await show_menu(message, state)
        return

    if current == Flow.apply_warn.state:
        await state.set_state(Flow.apply_phone)
        await message.answer(apply_phone(city), reply_markup=phone_keyboard())
        return

    if current == Flow.apply_photo.state:
        step = int(data.get("step") or 0)
        photos = list(data.get("photos") or [])
        if step <= 0:
            await state.set_state(Flow.apply_warn)
            await message.answer(apply_warning(), reply_markup=continue_keyboard())
            return
        photos = photos[:-1]
        step -= 1
        await state.update_data(photos=photos, step=step)
        await apply_flow._ask_step(message, step)
        return

    if current == Flow.apply_cars.state:
        cars = list(data.get("car_photos") or [])
        if not cars:
            await state.set_state(Flow.apply_photo)
            step = max(len(PHOTO_STEPS) - 1, 0)
            photos = list(data.get("photos") or [])
            if photos:
                photos = photos[:-1]
            await state.update_data(step=step, photos=photos, car_photos=[])
            await apply_flow._ask_step(message, step)
            return
        cars = cars[:-1]
        await state.update_data(car_photos=cars)
        if cars:
            await message.answer(cars_progress(len(cars)), reply_markup=back_keyboard())
        else:
            await apply_flow._ask_cars(message)
        return

    if current == Flow.apply_plate.state:
        cars = list(data.get("car_photos") or [])
        if cars:
            cars = cars[:-1]
        await state.set_state(Flow.apply_cars)
        await state.update_data(car_photos=cars)
        if cars:
            await message.answer(cars_progress(len(cars)), reply_markup=back_keyboard())
        else:
            await apply_flow._ask_cars(message)
        return

    if current == Flow.brand_rules.state:
        await show_menu(message, state)
        return

    if current == Flow.brand_name.state:
        await state.set_state(Flow.brand_rules)
        await message.answer(brand_rules(city), reply_markup=continue_keyboard())
        return

    if current == Flow.brand_phone.state:
        await state.set_state(Flow.brand_name)
        await message.answer(brand_ask_name(city), reply_markup=back_keyboard())
        return

    if current == Flow.brand_model.state:
        await state.set_state(Flow.brand_phone)
        await message.answer(brand_ask_phone(city), reply_markup=back_keyboard())
        return

    if current == Flow.brand_year.state:
        await state.set_state(Flow.brand_model)
        await message.answer(brand_ask_model(city), reply_markup=back_keyboard())
        return

    if current == Flow.brand_color.state:
        await state.set_state(Flow.brand_year)
        await message.answer(brand_ask_year(city), reply_markup=back_keyboard())
        return

    if current == Flow.brand_plate.state:
        await state.set_state(Flow.brand_color)
        await message.answer(brand_ask_color(city), reply_markup=back_keyboard())
        return

    await show_menu(message, state)
