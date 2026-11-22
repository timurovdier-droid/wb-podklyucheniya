import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot import db
from bot.config import settings
from bot.factory import create_dispatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")


async def main() -> None:
    if not settings.bot_token:
        log.error("BOT_TOKEN is empty. Copy .env.example to .env and fill it in.")
        sys.exit(1)
    await db.init()
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = create_dispatcher()
    if not settings.support_phone and not settings.operator_username:
        log.warning("SUPPORT_PHONE and OPERATOR_USERNAME are empty — contacts menu will be blank")
    log.info("bot started")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
