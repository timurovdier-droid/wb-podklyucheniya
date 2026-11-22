"""Обработка Telegram webhook (Vercel / serverless)."""

from __future__ import annotations

import json
import logging
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update

from bot import db
from bot.config import settings
from bot.factory import create_dispatcher

log = logging.getLogger("bot.webhook")

_runtime: dict[str, Any] | None = None


async def _runtime_bundle() -> dict[str, Any]:
    global _runtime
    if _runtime is None:
        await db.init()
        bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dispatcher = create_dispatcher()
        _runtime = {"bot": bot, "dispatcher": dispatcher}
    return _runtime


async def process_webhook(body: bytes) -> None:
    if not settings.bot_token:
        log.error("BOT_TOKEN is empty on the server")
        return
    try:
        raw = json.loads(body.decode("utf-8"))
        bundle = await _runtime_bundle()
        update = Update.model_validate(raw)
        await bundle["dispatcher"].feed_update(bundle["bot"], update)
    except Exception:
        log.exception("webhook processing failed")
