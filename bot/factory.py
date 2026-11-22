import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery

from bot.handlers import admin, apply, brand, fallback, menu, start

log = logging.getLogger(__name__)


class AckCallbackMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        try:
            await event.answer()
        except Exception:
            log.debug("callback ack skipped", exc_info=True)
        return await handler(event, data)


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.callback_query.outer_middleware(AckCallbackMiddleware())
    dispatcher.include_router(start.router)
    dispatcher.include_router(admin.router)
    dispatcher.include_router(menu.router)
    dispatcher.include_router(apply.router)
    dispatcher.include_router(brand.router)
    dispatcher.include_router(fallback.router)
    return dispatcher