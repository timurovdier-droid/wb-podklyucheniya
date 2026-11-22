import asyncio
import logging
from pathlib import Path

from bot.config import settings
from bot.texts import STATUS_LABELS

log = logging.getLogger(__name__)

ULANISH_HEADERS = [
    "Дата",
    "Код",
    "Город",
    "Телефон",
    "Имя",
    "Username",
    "Госномер",
    "Статус",
    "Telegram ID",
]
BREND_HEADERS = [
    "Дата",
    "Код",
    "Город",
    "ФИО",
    "Телефон",
    "Модель",
    "Год",
    "Цвет",
    "Госномер",
    "Статус",
    "Username",
    "Telegram ID",
]

_ALIASES = {
    "дата": "created_at",
    "date": "created_at",
    "код": "code",
    "code": "code",
    "ariza": "code",
    "город": "city",
    "city": "city",
    "hudud": "city",
    "телефон": "phone",
    "phone": "phone",
    "имя": "full_name",
    "фио": "full_name",
    "ism": "full_name",
    "username": "username",
    "госномер": "plate",
    "номер": "plate",
    "plate": "plate",
    "статус": "status",
    "status": "status",
    "holat": "status",
    "chala rasm": "status",
    "hujjatlar to'liq emas": "status",
    "telegram id": "user_id",
    "id": "user_id",
    "модель": "car_model",
    "model": "car_model",
    "год": "car_year",
    "year": "car_year",
    "цвет": "car_color",
    "color": "car_color",
    "pinfl": "pinfl",
    "жшшир": "pinfl",
    "jshshir": "pinfl",
    "familiya": "familiya",
    "фамилия": "familiya",
    "tugilgan sana": "tugilgan_sana",
    "дата рождения": "tugilgan_sana",
    "tugilgan joy": "tugilgan_joy",
    "prava": "prava_raqam",
    "права": "prava_raqam",
    "texpasport": "texpasport_seriya_raqam",
    "техпаспорт": "texpasport_seriya_raqam",
}


def enabled() -> bool:
    if not settings.google_sheet_id:
        return False
    path = Path(settings.google_credentials_file)
    if not path.is_absolute():
        path = settings.assets_dir.parent / path
    return path.exists()


def _credentials_path() -> Path:
    path = Path(settings.google_credentials_file)
    if not path.is_absolute():
        path = settings.assets_dir.parent / path
    return path


def _field_map(app: dict) -> dict:
    ocr = app.get("extracted") if isinstance(app.get("extracted"), dict) else {}
    familiya = str(ocr.get("familiya") or "").strip()
    ism = str(ocr.get("ism") or "").strip()
    full_name = app.get("full_name") or ""
    if not full_name and (familiya or ism):
        full_name = " ".join(part for part in (familiya, ism, str(ocr.get("otasining_ismi") or "").strip()) if part)
    return {
        "created_at": app["created_at"],
        "code": app["code"],
        "city": app.get("city") or "",
        "phone": app.get("phone") or "",
        "full_name": full_name,
        "familiya": familiya,
        "ism": ism,
        "pinfl": str(ocr.get("pinfl") or ""),
        "tugilgan_sana": str(ocr.get("tugilgan_sana") or ""),
        "tugilgan_joy": str(ocr.get("tugilgan_joy") or ""),
        "prava_raqam": str(ocr.get("prava_raqam") or ""),
        "texpasport_seriya_raqam": str(ocr.get("texpasport_seriya_raqam") or ""),
        "username": f"@{app['username']}" if app.get("username") else "",
        "plate": app.get("plate") or "",
        "status": STATUS_LABELS.get(app["status"], app["status"]),
        "user_id": app["user_id"],
        "car_model": app.get("car_model") or str(ocr.get("mashina_marka_model") or ""),
        "car_year": app.get("car_year") or str(ocr.get("mashina_yili") or ""),
        "car_color": app.get("car_color") or str(ocr.get("mashina_rangi") or ""),
    }


def _worksheet(sheet, kind: str):
    title = "Ulanish" if kind == "ulanish" else "Brend"
    default = ULANISH_HEADERS if kind == "ulanish" else BREND_HEADERS
    try:
        worksheet = sheet.worksheet(title)
    except Exception:
        worksheet = sheet.add_worksheet(title=title, rows=1000, cols=len(default))
    headers = worksheet.row_values(1)
    if not headers:
        worksheet.update(values=[default], range_name="A1")
        headers = default
    return worksheet, headers


def build_row(headers: list[str], app: dict) -> list:
    fields = _field_map(app)
    row = []
    for header in headers:
        key = _ALIASES.get(header.strip().lower())
        row.append(fields.get(key, "") if key else "")
    return row


def _append_sync(app: dict) -> None:
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(
        str(_credentials_path()),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    sheet = gspread.authorize(creds).open_by_key(settings.google_sheet_id)
    worksheet, headers = _worksheet(sheet, app["kind"])
    worksheet.append_row(build_row(headers, app), value_input_option="USER_ENTERED")


def _update_status_sync(kind: str, code: str, status: str) -> None:
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(
        str(_credentials_path()),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    sheet = gspread.authorize(creds).open_by_key(settings.google_sheet_id)
    worksheet, headers = _worksheet(sheet, kind)
    code_col = None
    status_col = None
    for index, header in enumerate(headers, start=1):
        key = _ALIASES.get(header.strip().lower())
        if key == "code":
            code_col = index
        elif key == "status":
            status_col = index
    if not code_col or not status_col:
        log.warning("sheet %s has no code/status headers", kind)
        return
    label = STATUS_LABELS.get(status, status)
    for row_index, value in enumerate(worksheet.col_values(code_col), start=1):
        if value == code:
            worksheet.update_cell(row_index, status_col, label)
            return
    log.warning("application %s was not found on sheet %s", code, kind)


async def append_application(app: dict) -> None:
    if not enabled():
        return
    try:
        await asyncio.to_thread(_append_sync, app)
    except Exception:
        log.exception("failed to append application %s to google sheet", app.get("code"))


async def update_status(kind: str, code: str, status: str) -> None:
    if not enabled():
        return
    try:
        await asyncio.to_thread(_update_status_sync, kind, code, status)
    except Exception:
        log.exception("failed to update status for %s", code)
