import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import db, notify, sheets
from bot.config import settings
from bot.keyboards import menu_keyboard, status_keyboard
from bot.texts import STATUS_LABELS, admin_card, incomplete_docs_notice, status_notice

log = logging.getLogger(__name__)
router = Router()

_ALLOWED = {"contacted", "connected", "incomplete", "rejected"}


@router.callback_query(F.data.startswith("st:"))
async def set_status(callback: CallbackQuery) -> None:
    if not callback.message or callback.message.chat.id != settings.admin_chat_id:
        await callback.answer("Bu tugma faqat operatorlar guruhida ishlaydi.", show_alert=True)
        return
    parts = (callback.data or "").split(":")
    if len(parts) != 3 or parts[2] not in _ALLOWED:
        await callback.answer()
        return
    app_id = int(parts[1])
    status = parts[2]
    current = await db.get_application(app_id)
    if current is None:
        await callback.answer("Ariza topilmadi.", show_alert=True)
        return
    target_status = status
    if status == "contacted" and current["status"] == "contacted":
        target_status = "new"
    elif current["status"] == status:
        await callback.answer("Bu holat allaqachon qo'yilgan.")
        return
    if target_status == "connected":
        forwarded = await notify.forward_to_work(callback.bot, current)
        if not forwarded:
            await callback.answer(
                "Ariza ish guruhiga yuborilmadi. "
                f"Botni ish guruhiga qo'shing (WORK_CHAT_ID={settings.work_chat_id}) "
                "va unga yozish huquqini bering.",
                show_alert=True,
            )
            return
    updated = await db.set_status(app_id, target_status)
    if updated is None:
        await callback.answer()
        return
    if target_status == "connected":
        card_id = callback.message.message_id if callback.message else None
        await notify.remove_from_admin(callback.bot, updated, card_id)
    else:
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
    if target_status == "contacted":
        await callback.answer("🟡 Boshqa operator ulayapti — haydovchiga xabar yo'q")
    elif target_status == "new" and status == "contacted":
        await callback.answer("🟢 Jarayonda bekor qilindi")
    elif target_status == "incomplete":
        await callback.answer("Haydovchiga xabar yuborildi — qayta to'ldirish")
    else:
        await callback.answer(STATUS_LABELS.get(target_status, target_status))
