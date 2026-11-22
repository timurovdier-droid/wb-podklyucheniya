from aiogram.types import Message


def application_code_from_message(message: Message | None) -> str | None:
    if not message or not message.text:
        return None
    text = message.text
    for entity in message.entities or []:
        if entity.type == "code":
            return text[entity.offset : entity.offset + entity.length].strip()
    return None