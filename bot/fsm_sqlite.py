from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey

from bot import db, sql


def _key(key: StorageKey) -> str:
    return (
        f"{key.bot_id}:{key.chat_id}:{key.user_id}:"
        f"{key.thread_id}:{key.business_connection_id}:{key.destiny}"
    )


def _state_value(state: str | State | None) -> str | None:
    if state is None:
        return None
    if isinstance(state, State):
        return state.state
    return str(state)


class SqliteStorage(BaseStorage):
    """FSM в таблице fsm_state (Turso или локальный SQLite — см. bot.sql)."""

    async def set_state(self, key: StorageKey, state: str | State | None = None) -> None:
        await db.init()
        await sql.execute(
            """
            INSERT INTO fsm_state (k, state, data) VALUES (?, ?, '{}')
            ON CONFLICT(k) DO UPDATE SET state = excluded.state
            """,
            (_key(key), _state_value(state)),
        )

    async def get_state(self, key: StorageKey) -> str | None:
        await db.init()
        result = await sql.execute("SELECT state FROM fsm_state WHERE k = ?", (_key(key),))
        return result.rows[0]["state"] if result.rows else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        await db.init()
        await sql.execute(
            """
            INSERT INTO fsm_state (k, state, data) VALUES (?, NULL, ?)
            ON CONFLICT(k) DO UPDATE SET data = excluded.data
            """,
            (_key(key), json.dumps(dict(data), ensure_ascii=False)),
        )

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        await db.init()
        result = await sql.execute("SELECT data FROM fsm_state WHERE k = ?", (_key(key),))
        raw = result.rows[0]["data"] if result.rows else None
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    async def close(self) -> None:
        return
