import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _text(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _cities() -> list[str]:
    raw = _text("CITIES", "Toshkent shahri")
    items = [part.strip() for part in raw.split(",") if part.strip()]
    return items or ["Toshkent shahri"]


def _sheet_id(raw: str) -> str:
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", raw)
    return match.group(1) if match else raw.strip()


def _chat_id(raw: str) -> int:
    raw = (raw or "").strip()
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        return 0


def _first_text(*names: str, default: str = "") -> str:
    for name in names:
        value = _text(name, default)
        if value:
            return value
    return default


def _database_path() -> Path:
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        return Path("/tmp") / "bot.sqlite"
    return ROOT / "data" / "bot.sqlite"


def _normalize_username(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    lowered = value.lower()
    if "t.me/" in lowered:
        value = value.split("t.me/", 1)[-1]
    value = value.split("?", 1)[0].strip("/").strip()
    return value.lstrip("@")


class Settings:
    bot_token = _text("BOT_TOKEN")
    admin_chat_id = _chat_id(os.getenv("ADMIN_CHAT_ID", ""))
    work_chat_id = _chat_id(os.getenv("WORK_CHAT_ID", ""))
    park_name = _text("PARK_NAME", "WB TAXI")
    support_phone = _first_text("SUPPORT_PHONE", "PHONE", "CONTACT_PHONE", "TELEFON")
    operator_username = _normalize_username(
        _first_text("OPERATOR_USERNAME", "TELEGRAM_USERNAME", "OPERATOR_TELEGRAM", "SUPPORT_USERNAME")
    )
    channel_url = _text("CHANNEL_URL")
    instagram = _text("INSTAGRAM")
    cities = _cities()
    code_prefix = _text("CODE_PREFIX", "WB") or "WB"
    office_address = _text(
        "OFFICE_ADDRESS",
        "Toshkent shahri, Mirzo Ulug'bek tumani, Yalang'och massivi, 100-uy (Eko bozor)",
    )
    office_landmark = _text("OFFICE_LANDMARK", "Eko bozor")
    office_map_url = _text(
        "OFFICE_MAP_URL",
        "https://yandex.ru/maps?whatshere%5Bzoom%5D=17&whatshere%5Bpoint%5D=69.350167,41.351756&si=b8hgm71vvwf7ejfepxra863z7c",
    )
    google_sheet_id = _sheet_id(os.getenv("GOOGLE_SHEET_ID", ""))
    google_credentials_file = _text("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    gemini_api_key = _text("GEMINI_API_KEY")
    gemini_model = _text("GEMINI_MODEL", "gemini-3.8-flash") or "gemini-3.8-flash"
    database_path = _database_path()
    assets_dir = ROOT / "assets"


settings = Settings()


def gemini_fallback_models() -> list[str]:
    raw = _text(
        "GEMINI_FALLBACK_MODELS",
        "gemini-3.6-flash,gemini-3.5-flash-lite",
    )
    primary = settings.gemini_model
    seen = {primary}
    result: list[str] = []
    for part in raw.split(","):
        name = part.strip()
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result
