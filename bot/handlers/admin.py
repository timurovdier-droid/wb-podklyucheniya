import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import cache, db, notify, sheets
from bot.config import settings
from bot.keyboards import menu_keyboard, status_keyboard
from bot.message_utils import application_code_from_message
from bot.texts import admin_card, incomplete_docs_notice, status_notice

log = logging.getLogger(__name__)
router = Router()

_ALLOWED = {"contacted", "connected", "incomplete", "rejected"}


async def _reply(callback: CallbackQuery, text: str) -> None:
    if callback.message:
        await callback.message.reply(text)


async def _ack(callback: CallbackQuery, text: str = "") -> None:
    try:
        await callback.answer(text)
    except Exception:
        log.debug("callback answer skipped", exc_info=True)


@router.callback_query(F.data.startswith("st:"))
async def set_status(callback: CallbackQuery) -> None:
    await _ack(callback)
    try:
        if not callback.message:
            return
        admin_chat = settings.admin_chat_id
        if admin_chat and callback.message.chat.id != admin_chat:
            await _reply(callback, "Bu tugma faqat operatorlar guruhida ishlaydi.")
            return
        parts = (callback.data or "").split(":")
        if len(parts) != 3 or parts[2] not in _ALLOWED:
            return
        app_id = int(parts[1])
        status = parts[2]
        current = await db.get_application(app_id)
        if current is None:
            code = application_code_from_message(callback.message)
            if code:
                current = cache.recall_by_code(code)
        if current is None and status != "connected":
            await _reply(
                callback,
                "Ariza serverda topilmadi (qayta yuklash). "
                "Yangi ariza yuboring yoki botni kompyuterdan ishga tushiring.",
            )
            return
        if current and not current.get("photos"):
            cached = cache.recall(app_id) or cache.recall_by_code(str(current.get("code") or ""))
            if cached and cached.get("photos"):
                current = cached

        target_status = status
        if current:
            if status == "contacted" and current["status"] == "contacted":
                target_status = "new"
            elif current["status"] == status:
                await _reply(callback, "Bu holat allaqachon qo'yilgan.")
                return

        if target_status == "connected":
            ok, result_text = await notify.complete_tayyor(callback.bot, callback.message, current)
            if not ok:
                await _reply(callback, result_text)
                return
            updated = await db.set_status(app_id, target_status)
            if updated is None and current:
                updated = {**current, "status": target_status}
                cache.remember(updated)
            elif updated is None:
                updated = current
            if updated and updated.get("user_id"):
                try:
                    await callback.bot.send_message(
                        updated["user_id"],
                        status_notice(updated["kind"], target_status, updated.get("code") or ""),
                    )
                except Exception:
                    log.exception("failed to notify driver %s", updated.get("user_id"))
            if updated:
                await sheets.update_status(updated["kind"], updated["code"], target_status)
            await _reply(callback, result_text)
            return

        updated = await db.set_status(app_id, target_status)
        if updated is None:
            await _reply(callback, "Holat saqlanmadi.")
            return

        try:
            await callback.message.edit_text(
                admin_card(updated),
                reply_markup=status_keyboard(app_id, updated["status"]),
            )
        except Exception:
            log.exception("failed to edit admin card %s", updated["code"])

        if target_status == "incomplete" and updated["kind"] == "ulanish":
            try:
                await callback.bot.send_message(
                    updated["user_id"],
                    incomplete_docs_notice(updated["code"]),
                    reply_markup=menu_keyboard(),
                )
            except Exception:
                log.exception("failed to notify driver %s", updated["user_id"])
        elif target_status not in ("contacted", "new"):
            try:
                await callback.bot.send_message(
                    updated["user_id"],
                    status_notice(updated["kind"], target_status, updated["code"]),
                )
            except Exception:
                log.exception("failed to notify driver %s", updated["user_id"])

        await sheets.update_status(updated["kind"], updated["code"], target_status)
    except Exception:
        log.exception("admin set_status failed")
        await _reply(callback, "Vaqtinchalik xatolik. Qayta urinib ko'ring.")