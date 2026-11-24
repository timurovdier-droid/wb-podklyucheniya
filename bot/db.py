import json
from datetime import datetime, timedelta, timezone

from bot import cache, sql
from bot.config import settings

TZ = timezone(timedelta(hours=5))

_initialized: set[str] = set()


def now_text() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


async def init() -> None:
    target = sql.target()
    if target in _initialized:
        return
    await sql.batch(
        [
            (
                """
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    kind TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    city TEXT,
                    plate TEXT,
                    car_model TEXT,
                    car_year TEXT,
                    car_color TEXT,
                    photos_json TEXT,
                    status TEXT NOT NULL,
                    admin_chat_id INTEGER,
                    admin_message_id INTEGER,
                    created_at TEXT NOT NULL
                )
                """,
                (),
            ),
            (
                """
                CREATE TABLE IF NOT EXISTS fsm_state (
                    k TEXT PRIMARY KEY,
                    state TEXT,
                    data TEXT
                )
                """,
                (),
            ),
            ("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)", ()),
        ]
    )
    await _ensure_extra_columns()
    _initialized.add(target)


async def _ensure_extra_columns() -> None:
    info = await sql.execute("PRAGMA table_info(applications)")
    names = {row["name"] for row in info.rows}
    missing = [
        (f"ALTER TABLE applications ADD COLUMN {column} TEXT", ())
        for column in ("extracted_json", "admin_album_msg_ids")
        if column not in names
    ]
    if missing:
        await sql.batch(missing)


async def create_application(payload: dict) -> dict:
    inserted, _ = await sql.batch(
        [
            (
                """
                INSERT INTO applications (
                    kind, user_id, username, full_name, phone, city, plate,
                    car_model, car_year, car_color, photos_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
                """,
                (
                    payload["kind"],
                    payload["user_id"],
                    payload.get("username"),
                    payload.get("full_name"),
                    payload.get("phone"),
                    payload.get("city"),
                    payload.get("plate"),
                    payload.get("car_model"),
                    payload.get("car_year"),
                    payload.get("car_color"),
                    json.dumps(payload.get("photos") or [], ensure_ascii=False),
                    now_text(),
                ),
            ),
            (
                "UPDATE applications SET code = ? || '-' || printf('%06d', id) WHERE id = last_insert_rowid()",
                (settings.code_prefix,),
            ),
        ]
    )
    app_id = inserted.lastrowid
    if app_id is None:
        raise RuntimeError("application was not saved")
    app = await get_application(app_id)
    if app is None:
        raise RuntimeError("application was not saved")
    cache.remember(app)
    return app


async def get_application(app_id: int) -> dict | None:
    result = await sql.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
    if not result.rows:
        return cache.recall(app_id)
    app = _row_to_dict(result.rows[0])
    cache.remember(app)
    return app


async def save_extracted(app_id: int, extracted: dict) -> None:
    await sql.execute(
        "UPDATE applications SET extracted_json = ? WHERE id = ?",
        (json.dumps(extracted, ensure_ascii=False), app_id),
    )


async def update_full_name(app_id: int, full_name: str) -> None:
    await sql.execute(
        "UPDATE applications SET full_name = ? WHERE id = ?",
        (full_name, app_id),
    )


async def set_admin_message(
    app_id: int,
    chat_id: int,
    message_id: int,
    album_message_ids: list[int] | None = None,
) -> None:
    await sql.execute(
        """
        UPDATE applications
        SET admin_chat_id = ?, admin_message_id = ?, admin_album_msg_ids = ?
        WHERE id = ?
        """,
        (
            chat_id,
            message_id,
            json.dumps(album_message_ids or [], ensure_ascii=False),
            app_id,
        ),
    )


async def set_status(app_id: int, status: str) -> dict | None:
    await sql.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
    app = await get_application(app_id)
    if app is not None:
        return app
    cached = cache.recall(app_id)
    if cached is None:
        return None
    cached = {**cached, "status": status}
    cache.remember(cached)
    return cached


def _row_to_dict(row: dict) -> dict:
    data = dict(row)
    data["photos"] = json.loads(data.pop("photos_json") or "[]")
    raw = data.pop("extracted_json", None)
    if raw:
        try:
            data["extracted"] = json.loads(raw)
        except json.JSONDecodeError:
            data["extracted"] = None
    else:
        data["extracted"] = None
    album_raw = data.pop("admin_album_msg_ids", None)
    if album_raw:
        try:
            data["admin_album_message_ids"] = json.loads(album_raw)
        except json.JSONDecodeError:
            data["admin_album_message_ids"] = []
    else:
        data["admin_album_message_ids"] = []
    return data
