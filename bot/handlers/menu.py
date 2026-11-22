from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from bot.config import settings
from bot.keyboards import city_keyboard, continue_keyboard, menu_keyboard, office_keyboard, phone_keyboard
from bot.states import Flow
from bot.texts import (
    BTN_APPLY,
    BTN_BRAND,
    BTN_CONTACT,
    BTN_OFFICE,
    apply_phone,
    brand_rules,
    choose_city,
    contacts_text,
    office_text,
)

router = Router()


async def _city(state: FSMContext, message: Message) -> str | None:
    data = await state.get_data()
    city = data.get("city")
    if city:
        return city
    await state.set_state(Flow.city)
    await message.answer(choose_city(), reply_markup=city_keyboard())
    return None


@router.message(F.chat.type == "private", F.text == BTN_APPLY)
async def open_apply(message: Message, state: FSMContext) -> None:
    city = await _city(state, message)
    if not city:
        return
    await state.set_state(Flow.apply_phone)
    await state.update_data(photos=[], car_photos=[], step=0)
    await message.answer(apply_phone(city), reply_markup=phone_keyboard())


@router.message(F.chat.type == "private", F.text == BTN_BRAND)
async def open_brand(message: Message, state: FSMContext) -> None:
    city = await _city(state, message)
    if not city:
        return
    await state.set_state(Flow.brand_rules)
    await message.answer(brand_rules(city), reply_markup=continue_keyboard())


@router.message(F.chat.type == "private", F.text == BTN_OFFICE)
async def open_office(message: Message, state: FSMContext) -> None:
    city = await _city(state, message)
    if not city:
        return
    photo = settings.assets_dir / "office.jpg"
    caption = office_text(city)
    if photo.exists():
        await message.answer_photo(
            FSInputFile(photo),
            caption=caption,
            reply_markup=office_keyboard(),
        )
    else:
        await message.answer(caption, reply_markup=office_keyboard())


@router.message(F.chat.type == "private", F.text == BTN_CONTACT)
async def open_contacts(message: Message, state: FSMContext) -> None:
    city = await _city(state, message)
    if not city:
        return
    await message.answer(contacts_text(city), reply_markup=menu_keyboard())


def example_path(name: str) -> Path | None:
    path = settings.assets_dir / "examples" / name
    if path.exists() and path.stat().st_size > 0:
        return path
    return None
