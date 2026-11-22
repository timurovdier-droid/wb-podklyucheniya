from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.config import settings
from bot.texts import (
    BTN_APPLY,
    BTN_BRAND,
    BTN_CONTACT,
    BTN_CONTINUE,
    BTN_OFFICE,
    BTN_PHONE,
)


def city_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=city)] for city in settings.cities],
        resize_keyboard=True,
    )


def menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_APPLY)],
            [KeyboardButton(text=BTN_BRAND)],
            [KeyboardButton(text=BTN_CONTACT), KeyboardButton(text=BTN_OFFICE)],
        ],
        resize_keyboard=True,
    )


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_PHONE, request_contact=True)]],
        resize_keyboard=True,
    )


def continue_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CONTINUE)]],
        resize_keyboard=True,
    )


def office_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Xaritada ochish", url=settings.office_map_url)]
        ]
    )


def status_keyboard(application_id: int, status: str = "new") -> InlineKeyboardMarkup:
    jarayonda = "🟡 Jarayonda" if status == "contacted" else "🟢 Jarayonda"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tayyor", callback_data=f"st:{application_id}:connected")],
            [
                InlineKeyboardButton(text=jarayonda, callback_data=f"st:{application_id}:contacted"),
                InlineKeyboardButton(text="📷 Chala rasm", callback_data=f"st:{application_id}:incomplete"),
            ],
        ]
    )
