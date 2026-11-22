from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import settings
from bot.keyboards import city_keyboard, menu_keyboard
from bot.states import Flow
from bot.texts import choose_city, city_chosen, menu_intro, welcome

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    if message.chat.type != "private":
        return
    await state.clear()
    await state.set_state(Flow.city)
    await message.answer(welcome(), reply_markup=city_keyboard())


@router.message(Command("chatid"))
async def chat_id(message: Message) -> None:
    await message.answer(f"Chat ID: <code>{message.chat.id}</code>")


@router.message(Flow.city, F.text)
async def pick_city(message: Message, state: FSMContext) -> None:
    if message.text not in settings.cities:
        await message.answer(choose_city(), reply_markup=city_keyboard())
        return
    await state.update_data(city=message.text)
    await state.set_state(None)
    await message.answer(city_chosen(message.text))
    await message.answer(menu_intro(message.text), reply_markup=menu_keyboard())
