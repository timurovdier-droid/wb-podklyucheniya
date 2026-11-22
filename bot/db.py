import json
from datetime import datetime, timedelta, timezone

import aiosqlite

from bot import cache
from bot.config import settings

TZ = timezone(timedelta(hours=5))


def now_text() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


def _connect() -> aiosqlite.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return aiosqlite.connect(settings.database_path)


async def init() -> None:
    async with _connect() as db:
        await db.execute(
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
            """
        )
        await db.commit()
        await _ensure_extracted_column(db)


async def _ensure_extracted_column(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("PRAGMA table_info(applications)")
    rows = await cursor.fetchall()
    names = {row[1] for row in rows}
    if "extracted_json" not in names:
        await db.execute("ALTER TABLE applications ADD COLUMN extracted_json TEXT")
    if "admin_album_msg_ids" not in names:
        await db.execute("ALTER TABLE applications ADD COLUMN admin_album_msg_ids TEXT")
    await db.commit()


async def create_application(payload: dict) -> dict:
    async with _connect() as db:
        cursor = await db.execute(
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
        )
        app_id = cursor.lastrowid
        code = f"{settings.code_prefix}-{app_id:06d}"
        await db.execute("UPDATE applications SET code = ? WHERE id = ?", (code, app_id))
        await db.commit()
    app = await get_application(app_id)
    if app is None:
        raise RuntimeError("application was not saved")
    cache.remember(app)
    return app


async def get_application(app_id: int) -> dict | None:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = await cursor.fetchone()
    if row is None:
        return cache.recall(app_id)
    app = _row_to_dict(row)
    cache.remember(app)
    return app


async def save_extracted(app_id: int, extracted: dict) -> None:
    async with _connect() as db:
        await db.execute(
            "UPDATE applications SET extracted_json = ? WHERE id = ?",
            (json.dumps(extracted, ensure_ascii=False), app_id),
        )
        await db.commit()


async def update_full_name(app_id: int, full_name: str) -> None:
    async with _connect() as db:
        await db.execute(
            "UPDATE applications SET full_name = ? WHERE id = ?",
            (full_name, app_id),
        )
        await db.commit()


async def set_admin_message(
    app_id: int,
    chat_id: int,
    message_id: int,
    album_message_ids: list[int] | None = None,
) -> None:
    async with _connect() as db:
        await db.execute(
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
        await db.commit()


async def set_status(app_id: int, status: str) -> dict | None:
    async with _connect() as db:
        await db.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
        await db.commit()
    app = await get_application(app_id)
    if app is not None:
        return app
    cached = cache.recall(app_id)
    if cached is None:
        return None
    cached = {**cached, "status": status}
    cache.remember(cached)
    return cached


def _row_to_dict(row: aiosqlite.Row) -> dict:
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
