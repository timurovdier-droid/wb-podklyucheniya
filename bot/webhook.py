"""Обработка Telegram webhook (Vercel / serverless)."""

from __future__ import annotations

import json
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update

from bot import db
from bot.config import settings
from bot.factory import create_dispatcher

log = logging.getLogger("bot.webhook")

_dispatcher = None


def _get_dispatcher():
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = create_dispatcher()
    return _dispatcher


async def process_webhook(body: bytes) -> None:
    if not settings.bot_token:
        log.error("BOT_TOKEN is empty on the server")
        return
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await db.init()
        raw = json.loads(body.decode("utf-8"))
        update = Update.model_validate(raw)
        await _get_dispatcher().feed_update(bot, update)
    except Exception:
        log.exception("webhook processing failed")
    finally:
        await bot.session.close()
