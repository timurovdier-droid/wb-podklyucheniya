import re

_LETTER = re.compile(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ]")


def is_full_name(text: str) -> bool:
    parts = [part for part in text.strip().split() if part]
    if len(parts) < 2:
        return False
    for part in parts:
        letters = _LETTER.findall(part)
        if len(letters) < 2:
            return False
    return True


def phone_digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def is_phone(text: str) -> bool:
    return len(phone_digits(text)) >= 9


def normalize_phone(text: str) -> str:
    digits = phone_digits(text)
    if len(digits) == 9:
        return f"998{digits}"
    if digits.startswith("998") and len(digits) >= 12:
        return digits[:12]
    if digits.startswith("8") and len(digits) == 10:
        return f"998{digits[1:]}"
    return digits


def is_forbidden_model(model: str) -> bool:
    compact = re.sub(r"[\s_\-]+", "", model.lower().replace("ё", "е"))
    if "spark" in compact:
        return True
    if "nexia3" in compact or "нексия3" in compact:
        return True
    return False


def parse_year(text: str) -> int | None:
    value = text.strip()
    if not re.fullmatch(r"\d{4}", value):
        return None
    return int(value)


def brand_block_reason(model: str, year: int) -> str | None:
    if is_forbidden_model(model):
        return "model"
    if year <= 2015:
        return "year"
    return None


def normalize_plate(text: str) -> str:
    return re.sub(r"\s+", "", text).upper()


def is_plate(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9]{4,10}", normalize_plate(text)))
