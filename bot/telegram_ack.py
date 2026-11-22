import logging

import aiohttp

from bot.config import settings

log = logging.getLogger(__name__)


async def ack_callback_query(query_id: str) -> None:
    if not query_id or not settings.bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.bot_token}/answerCallbackQuery"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"callback_query_id": query_id}, timeout=aiohttp.ClientTimeout(total=5)):
                pass
    except Exception:
        log.exception("failed to ack callback %s", query_id)