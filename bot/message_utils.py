import re

from aiogram.types import Message


def application_code_from_message(message: Message | None) -> str | None:
    if not message or not message.text:
        return None
    text = message.text
    for entity in message.entities or []:
        if entity.type == "code":
            return text[entity.offset : entity.offset + entity.length].strip()
    return None


def user_id_from_message(message: Message | None) -> int | None:
    if not message:
        return None
    for entity in message.entities or []:
        url = getattr(entity, "url", None) or ""
        match = re.search(r"tg://user\?id=(-?\d+)", url)
        if match:
            return int(match.group(1))
    text = message.text or message.caption or ""
    match = re.search(r"tg://user\?id=(-?\d+)", text)
    if match:
        return int(match.group(1))
    match = re.search(r"Telegram ID:\s*<code>(-?\d+)</code>", text)
    if match:
        return int(match.group(1))
    match = re.search(r"Telegram ID:\s*(-?\d+)", text)
    if match:
        return int(match.group(1))
    return None