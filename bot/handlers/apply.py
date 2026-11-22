import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InputMediaPhoto, Message, ReplyKeyboardRemove

from bot import db
from bot.brand_rules import is_phone, is_plate, normalize_phone, normalize_plate
from bot.config import settings
from bot.handlers.menu import example_path
from bot.keyboards import back_keyboard, continue_keyboard, menu_keyboard, phone_keyboard
from bot.notify import deliver
from bot.states import Flow
from bot.texts import (
    BTN_CONTINUE,
    CAR_EXAMPLES,
    CAR_PROMPT,
    PHOTO_STEPS,
    accepted_apply,
    apply_phone_again,
    apply_warning,
    ask_plate,
    cars_need_four,
    cars_ok,
    cars_progress,
    need_photo,
    plate_again,
    sending,
    send_failed,
    with_contacts,
)

router = Router()

_albums: dict[str, dict] = {}


async def _ask_step(message: Message, step: int) -> None:
    filename, prompt = PHOTO_STEPS[step]
    sample = example_path(filename)
    caption = with_contacts(prompt)
    if sample:
        await message.answer_photo(FSInputFile(sample), caption=caption, reply_markup=back_keyboard())
    else:
        await message.answer(caption, reply_markup=back_keyboard())


async def _ask_cars(message: Message) -> None:
    await message.answer(with_contacts(CAR_PROMPT), reply_markup=back_keyboard())
    media: list[InputMediaPhoto] = []
    for index, (filename, caption) in enumerate(CAR_EXAMPLES):
        sample = example_path(filename)
        if sample:
            media.append(
                InputMediaPhoto(
                    media=FSInputFile(sample),
                    caption=with_contacts(caption) if index == 0 else None,
                )
            )
    if media:
        await message.answer_media_group(media)
        return
    legacy = example_path("car.jpg")
    if legacy:
        await message.answer_photo(FSInputFile(legacy), caption=with_contacts("Namuna"))


async def _finish_cars(message: Message, state: FSMContext, file_ids: list[str]) -> None:
    await state.update_data(car_photos=file_ids)
    await state.set_state(Flow.apply_plate)
    await message.answer(cars_ok())
    await message.answer(ask_plate(), reply_markup=back_keyboard())


async def _after_phone(message: Message, state: FSMContext, phone: str, full_name: str) -> None:
    await state.update_data(phone=phone, full_name=full_name, step=0, photos=[])
    await state.set_state(Flow.apply_warn)
    await message.answer(apply_warning(), reply_markup=ReplyKeyboardRemove())
    voice = example_path("warning.ogg") or _voice()
    if voice:
        await message.answer_voice(FSInputFile(voice))
    await message.answer("Davom etish uchun tugmani bosing.", reply_markup=continue_keyboard())


@router.message(Flow.apply_phone, F.contact)
async def take_phone(message: Message, state: FSMContext) -> None:
    contact = message.contact
    if contact is None or not contact.phone_number:
        await message.answer(apply_phone_again(), reply_markup=phone_keyboard())
        return
    if contact.user_id and message.from_user and contact.user_id != message.from_user.id:
        await message.answer(apply_phone_again(), reply_markup=phone_keyboard())
        return
    name = " ".join(part for part in [contact.first_name, contact.last_name] if part).strip()
    if not name and message.from_user:
        name = message.from_user.full_name
    phone = normalize_phone(contact.phone_number)
    await _after_phone(message, state, phone, name)


@router.message(Flow.apply_phone, F.text)
async def take_phone_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not is_phone(text):
        await message.answer(apply_phone_again(), reply_markup=phone_keyboard())
        return
    name = message.from_user.full_name if message.from_user else ""
    await _after_phone(message, state, normalize_phone(text), name)


def _voice():
    path = settings.assets_dir / "warning.ogg"
    if path.exists() and path.stat().st_size > 0:
        return path
    return None


@router.message(Flow.apply_phone)
async def take_phone_invalid(message: Message) -> None:
    await message.answer(apply_phone_again(), reply_markup=phone_keyboard())


@router.message(Flow.apply_warn, F.text == BTN_CONTINUE)
async def continue_docs(message: Message, state: FSMContext) -> None:
    await state.set_state(Flow.apply_photo)
    await state.update_data(step=0, photos=[])
    await message.answer("Hujjat rasmlarini yuboring.", reply_markup=back_keyboard())
    await _ask_step(message, 0)


@router.message(Flow.apply_warn)
async def warn_invalid(message: Message) -> None:
    await message.answer("Davom etish tugmasini bosing.", reply_markup=continue_keyboard())


@router.message(Flow.apply_photo, F.photo)
async def take_document(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    step = int(data.get("step") or 0)
    photos = list(data.get("photos") or [])
    photos.append(message.photo[-1].file_id)
    step += 1
    await state.update_data(photos=photos, step=step)
    if step < len(PHOTO_STEPS):
        await _ask_step(message, step)
        return
    await state.set_state(Flow.apply_cars)
    await state.update_data(car_photos=[])
    await _ask_cars(message)


@router.message(Flow.apply_photo)
async def document_invalid(message: Message) -> None:
    await message.answer(need_photo(), reply_markup=back_keyboard())


@router.message(Flow.apply_cars, F.photo)
async def take_car(message: Message, state: FSMContext) -> None:
    if message.media_group_id:
        await _buffer_album(message, state)
        return
    data = await state.get_data()
    cars = list(data.get("car_photos") or [])
    cars.append(message.photo[-1].file_id)
    if len(cars) < 4:
        await state.update_data(car_photos=cars)
        await message.answer(cars_progress(len(cars)), reply_markup=back_keyboard())
        return
    await _finish_cars(message, state, cars[:4])


async def _buffer_album(message: Message, state: FSMContext) -> None:
    key = f"{message.from_user.id}:{message.media_group_id}"
    item = _albums.setdefault(key, {"ids": [], "state": state, "message": message, "task": None})
    item["ids"].append(message.photo[-1].file_id)
    item["state"] = state
    item["message"] = message
    task = item.get("task")
    if task is None or task.done():
        item["task"] = asyncio.create_task(_flush_album(key))


async def _flush_album(key: str) -> None:
    await asyncio.sleep(1.2)
    item = _albums.pop(key, None)
    if not item:
        return
    state: FSMContext = item["state"]
    message: Message = item["message"]
    if await state.get_state() != Flow.apply_cars.state:
        return
    ids = item["ids"]
    if len(ids) != 4:
        await state.update_data(car_photos=[])
        await message.answer(cars_need_four(), reply_markup=back_keyboard())
        return
    await _finish_cars(message, state, ids)


@router.message(Flow.apply_cars)
async def cars_invalid(message: Message) -> None:
    await message.answer(cars_need_four(), reply_markup=back_keyboard())


@router.message(Flow.apply_plate, F.text)
async def take_plate(message: Message, state: FSMContext) -> None:
    if not is_plate(message.text or ""):
        await message.answer(plate_again(), reply_markup=back_keyboard())
        return
    data = await state.get_data()
    photos = list(data.get("photos") or [])
    cars = list(data.get("car_photos") or [])
    if len(photos) != len(PHOTO_STEPS) or len(cars) != 4:
        await state.set_state(Flow.apply_photo)
        await state.update_data(step=0, photos=[], car_photos=[])
        await message.answer("Rasmlar to'liq emas. Qaytadan yuboring.")
        await _ask_step(message, 0)
        return
    user = message.from_user
    await message.answer(sending(), reply_markup=ReplyKeyboardRemove())
    app = await db.create_application(
        {
            "kind": "ulanish",
            "user_id": user.id,
            "username": user.username,
            "full_name": data.get("full_name") or user.full_name,
            "phone": data.get("phone"),
            "city": data.get("city"),
            "plate": normalize_plate(message.text),
            "photos": photos + cars,
        }
    )
    delivered = await deliver(message.bot, app)
    await state.set_state(None)
    await state.update_data(city=data.get("city"), photos=[], car_photos=[], step=0)
    if delivered:
        await message.answer(accepted_apply(app["code"], data.get("city") or ""), reply_markup=menu_keyboard())
    else:
        await message.answer(send_failed(), reply_markup=menu_keyboard())


@router.message(Flow.apply_plate)
async def plate_invalid(message: Message) -> None:
    await message.answer(plate_again(), reply_markup=back_keyboard())
