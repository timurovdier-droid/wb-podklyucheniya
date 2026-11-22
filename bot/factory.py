from aiogram import Dispatcher

from bot.fsm_sqlite import SqliteStorage
from bot.handlers import admin, apply, brand, fallback, menu, start


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=SqliteStorage())
    dispatcher.include_router(start.router)
    dispatcher.include_router(admin.router)
    dispatcher.include_router(menu.router)
    dispatcher.include_router(apply.router)
    dispatcher.include_router(brand.router)
    dispatcher.include_router(fallback.router)
    return dispatcher
