from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot import db
from bot.brand_rules import brand_block_reason, is_full_name, is_phone, is_plate, normalize_plate, parse_year
from bot.keyboards import back_keyboard, continue_keyboard, menu_keyboard
from bot.notify import deliver
from bot.states import Flow
from bot.texts import (
    BTN_CONTINUE,
    accepted_brand,
    brand_ask_color,
    brand_ask_model,
    brand_ask_name,
    brand_ask_phone,
    brand_ask_plate,
    brand_ask_year,
    brand_color_again,
    brand_name_again,
    brand_phone_again,
    brand_rejected_rules,
    brand_rules,
    brand_year_again,
    plate_again,
    sending,
    send_failed,
)

router = Router()


@router.message(Flow.brand_rules, F.text == BTN_CONTINUE)
async def brand_continue(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(Flow.brand_name)
    await message.answer(brand_ask_name(data.get("city") or ""), reply_markup=back_keyboard())


@router.message(Flow.brand_rules)
async def brand_rules_invalid(message: Message) -> None:
    await message.answer("Davom etish tugmasini bosing.", reply_markup=continue_keyboard())


@router.message(Flow.brand_name, F.text)
async def brand_name(message: Message, state: FSMContext) -> None:
    if not is_full_name(message.text or ""):
        await message.answer(brand_name_again())
        return
    data = await state.get_data()
    await state.update_data(full_name=message.text.strip())
    await state.set_state(Flow.brand_phone)
    await message.answer(brand_ask_phone(data.get("city") or ""), reply_markup=back_keyboard())


@router.message(Flow.brand_phone, F.text)
async def brand_phone(message: Message, state: FSMContext) -> None:
    if not is_phone(message.text or ""):
        await message.answer(brand_phone_again())
        return
    data = await state.get_data()
    await state.update_data(phone=message.text.strip())
    await state.set_state(Flow.brand_model)
    await message.answer(brand_ask_model(data.get("city") or ""), reply_markup=back_keyboard())


@router.message(Flow.brand_phone, F.contact)
async def brand_phone_contact(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number if message.contact else ""
    if not is_phone(phone):
        await message.answer(brand_phone_again())
        return
    data = await state.get_data()
    await state.update_data(phone=phone)
    await state.set_state(Flow.brand_model)
    await message.answer(brand_ask_model(data.get("city") or ""), reply_markup=back_keyboard())


@router.message(Flow.brand_model, F.text)
async def brand_model(message: Message, state: FSMContext) -> None:
    model = (message.text or "").strip()
    if len(model) < 2:
        await message.answer("Modelni to'liq yozing. Masalan: Chevrolet Lacetti.")
        return
    data = await state.get_data()
    await state.update_data(car_model=model)
    await state.set_state(Flow.brand_year)
    await message.answer(brand_ask_year(data.get("city") or ""), reply_markup=back_keyboard())


@router.message(Flow.brand_year, F.text)
async def brand_year(message: Message, state: FSMContext) -> None:
    year = parse_year(message.text or "")
    if year is None:
        await message.answer(brand_year_again())
        return
    data = await state.get_data()
    reason = brand_block_reason(data.get("car_model") or "", year)
    city = data.get("city") or ""
    if reason == "model":
        await message.answer(brand_rejected_rules())
        await state.set_state(Flow.brand_model)
        await message.answer(brand_ask_model(city), reply_markup=back_keyboard())
        return
    if reason == "year":
        await message.answer(brand_rejected_rules())
        await message.answer(brand_ask_year(city), reply_markup=back_keyboard())
        return
    await state.update_data(car_year=str(year))
    await state.set_state(Flow.brand_color)
    await message.answer(brand_ask_color(city), reply_markup=back_keyboard())


@router.message(Flow.brand_color, F.text)
async def brand_color(message: Message, state: FSMContext) -> None:
    color = (message.text or "").strip()
    if len(color) < 2:
        await message.answer(brand_color_again())
        return
    data = await state.get_data()
    await state.update_data(car_color=color)
    await state.set_state(Flow.brand_plate)
    await message.answer(brand_ask_plate(data.get("city") or ""), reply_markup=back_keyboard())


@router.message(Flow.brand_plate, F.text)
async def brand_plate(message: Message, state: FSMContext) -> None:
    if not is_plate(message.text or ""):
        await message.answer(plate_again(), reply_markup=back_keyboard())
        return
    data = await state.get_data()
    user = message.from_user
    await message.answer(sending())
    app = await db.create_application(
        {
            "kind": "brend",
            "user_id": user.id,
            "username": user.username,
            "full_name": data.get("full_name"),
            "phone": data.get("phone"),
            "city": data.get("city"),
            "plate": normalize_plate(message.text),
            "car_model": data.get("car_model"),
            "car_year": data.get("car_year"),
            "car_color": data.get("car_color"),
        }
    )
    delivered = await deliver(message.bot, app)
    await state.set_state(None)
    await state.update_data(city=data.get("city"))
    if delivered:
        await message.answer(accepted_brand(app["code"], data.get("city") or ""), reply_markup=menu_keyboard())
    else:
        await message.answer(send_failed(), reply_markup=menu_keyboard())


@router.message(Flow.brand_name)
@router.message(Flow.brand_phone)
@router.message(Flow.brand_model)
@router.message(Flow.brand_year)
@router.message(Flow.brand_color)
@router.message(Flow.brand_plate)
async def brand_need_text(message: Message) -> None:
    await message.answer("Iltimos, javobni matn ko'rinishida yozing.", reply_markup=back_keyboard())
