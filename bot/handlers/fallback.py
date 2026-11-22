from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import city_keyboard, menu_keyboard
from bot.states import Flow
from bot.texts import choose_city

router = Router()


@router.message(F.chat.type == "private")
async def fallback(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("city") and await state.get_state() is None:
        await message.answer("Menyudan bo'limni tanlang.", reply_markup=menu_keyboard())
        return
    if await state.get_state() is None:
        await state.set_state(Flow.city)
        await message.answer(choose_city(), reply_markup=city_keyboard())
