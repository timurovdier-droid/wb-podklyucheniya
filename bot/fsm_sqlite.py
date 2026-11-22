from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import aiosqlite
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey

from bot.config import settings


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
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.database_path

    async def _connect(self) -> aiosqlite.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = await aiosqlite.connect(self.path)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS fsm_state (
                k TEXT PRIMARY KEY,
                state TEXT,
                data TEXT
            )
            """
        )
        await db.commit()
        return db

    async def set_state(self, key: StorageKey, state: str | State | None = None) -> None:
        async with await self._connect() as db:
            await db.execute(
                """
                INSERT INTO fsm_state (k, state, data) VALUES (?, ?, '{}')
                ON CONFLICT(k) DO UPDATE SET state = excluded.state
                """,
                (_key(key), _state_value(state)),
            )
            await db.commit()

    async def get_state(self, key: StorageKey) -> str | None:
        async with await self._connect() as db:
            cursor = await db.execute("SELECT state FROM fsm_state WHERE k = ?", (_key(key),))
            row = await cursor.fetchone()
        return row[0] if row else None

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        payload = json.dumps(dict(data), ensure_ascii=False)
        async with await self._connect() as db:
            await db.execute(
                """
                INSERT INTO fsm_state (k, state, data) VALUES (?, NULL, ?)
                ON CONFLICT(k) DO UPDATE SET data = excluded.data
                """,
                (_key(key), payload),
            )
            await db.commit()

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        async with await self._connect() as db:
            cursor = await db.execute("SELECT data FROM fsm_state WHERE k = ?", (_key(key),))
            row = await cursor.fetchone()
        if not row or not row[0]:
            return {}
        try:
            parsed = json.loads(row[0])
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    async def close(self) -> None:
        return
