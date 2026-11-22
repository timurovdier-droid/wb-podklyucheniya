import logging
import os

from aiogram import Bot
from aiogram.types import InputMediaPhoto

from bot import db, gemini_docs, sheets
from bot.config import settings
from bot.keyboards import status_keyboard
from bot.texts import admin_card

log = logging.getLogger(__name__)


async def deliver(bot: Bot, app: dict) -> bool:
    if not settings.admin_chat_id:
        log.warning("ADMIN_CHAT_ID is empty, application %s was saved but not sent", app["code"])
        app = await _enrich_ocr(bot, app)
        await sheets.append_application(app)
        return False
    album_ids: list[int] = []
    try:
        if app["kind"] == "ulanish":
            photos = app["photos"]
            album_ids.extend(
                await _album(bot, settings.admin_chat_id, photos[:7], f"Ulanish {app['code']} — hujjatlar")
            )
            album_ids.extend(
                await _album(bot, settings.admin_chat_id, photos[7:], f"Ulanish {app['code']} — mashina")
            )
        app = await _enrich_ocr(bot, app)
        message = await bot.send_message(
            settings.admin_chat_id,
            admin_card(app),
            reply_markup=status_keyboard(app["id"], app.get("status") or "new"),
        )
    except Exception:
        log.exception("failed to deliver application %s", app["code"])
        return False
    await db.set_admin_message(app["id"], message.chat.id, message.message_id, album_ids)
    await sheets.append_application(app)
    return True


async def _enrich_ocr(bot: Bot, app: dict) -> dict:
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return app
    if not gemini_docs.enabled():
        return app
    extracted = await gemini_docs.extract_from_application(bot, app) or {}
    app = {**app, "extracted": extracted}
    await db.save_extracted(app["id"], extracted)
    full_name = str(extracted.get("full_name") or "").strip()
    if full_name and app.get("kind") == "ulanish":
        await db.update_full_name(app["id"], full_name)
        app["full_name"] = full_name
    return app


async def forward_to_work(bot: Bot, app: dict) -> bool:
    if not settings.work_chat_id:
        log.info("WORK_CHAT_ID not set, skip forward for %s", app.get("code"))
        return True
    try:
        if app.get("kind") == "ulanish":
            photos = list(app.get("photos") or [])
            if photos:
                await _album(
                    bot,
                    settings.work_chat_id,
                    photos[:7],
                    f"✅ Tayyor · {app['code']} — hujjatlar",
                )
                await _album(
                    bot,
                    settings.work_chat_id,
                    photos[7:],
                    f"✅ Tayyor · {app['code']} — mashina",
                )
        await bot.send_message(settings.work_chat_id, admin_card(app))
        return True
    except Exception:
        log.exception("failed to forward application %s to work chat", app.get("code"))
        return False


async def remove_from_admin(bot: Bot, app: dict, card_message_id: int | None = None) -> None:
    chat_id = app.get("admin_chat_id") or settings.admin_chat_id
    if not chat_id:
        return
    for message_id in app.get("admin_album_message_ids") or []:
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            log.debug("could not delete album message %s in chat %s", message_id, chat_id)
    mid = card_message_id or app.get("admin_message_id")
    if mid:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            log.debug("could not delete card message %s in chat %s", mid, chat_id)


async def _album(bot: Bot, chat_id: int, file_ids: list[str], caption: str) -> list[int]:
    if not file_ids:
        return []
    media = []
    for index, file_id in enumerate(file_ids):
        media.append(InputMediaPhoto(media=file_id, caption=caption if index == 0 else None))
    messages = await bot.send_media_group(chat_id, media=media)
    return [item.message_id for item in messages]
