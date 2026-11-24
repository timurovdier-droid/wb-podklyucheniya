"""Доступ к SQL: Turso (HTTP API) если задан TURSO_DATABASE_URL, иначе локальный SQLite."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any

import aiohttp
import aiosqlite

from bot.config import settings

Statement = tuple[str, tuple[Any, ...]]


class SqlError(RuntimeError):
    pass


@dataclass
class Result:
    rows: list[dict[str, Any]] = field(default_factory=list)
    lastrowid: int | None = None


def using_turso() -> bool:
    return bool(settings.turso_url)


def target() -> str:
    return settings.turso_url if using_turso() else str(settings.database_path)


async def execute(sql: str, params: tuple[Any, ...] = ()) -> Result:
    return (await batch([(sql, params)]))[0]


async def batch(statements: list[Statement]) -> list[Result]:
    """Выполняет запросы по порядку в одном соединении."""
    if using_turso():
        return await _turso_batch(statements)
    return await _local_batch(statements)


async def _local_batch(statements: list[Statement]) -> list[Result]:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[Result] = []
    async with aiosqlite.connect(settings.database_path) as db:
        db.row_factory = aiosqlite.Row
        for sql, params in statements:
            cursor = await db.execute(sql, params)
            rows = [dict(row) for row in await cursor.fetchall()]
            results.append(Result(rows=rows, lastrowid=cursor.lastrowid))
        await db.commit()
    return results


def _http_url() -> str:
    url = settings.turso_url.rstrip("/")
    if url.startswith("libsql://"):
        url = "https://" + url[len("libsql://") :]
    return url + "/v2/pipeline"


def _encode(value: Any) -> dict[str, Any]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "integer", "value": str(int(value))}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    if isinstance(value, (bytes, bytearray)):
        return {"type": "blob", "base64": base64.b64encode(bytes(value)).decode()}
    return {"type": "text", "value": str(value)}


def _decode(cell: dict[str, Any]) -> Any:
    kind = cell.get("type")
    if kind == "null":
        return None
    if kind == "integer":
        return int(cell["value"])
    if kind == "float":
        return float(cell["value"])
    if kind == "blob":
        return base64.b64decode(cell.get("base64") or "")
    return cell.get("value")


async def _turso_batch(statements: list[Statement]) -> list[Result]:
    requests: list[dict[str, Any]] = [
        {"type": "execute", "stmt": {"sql": sql, "args": [_encode(v) for v in params]}}
        for sql, params in statements
    ]
    requests.append({"type": "close"})
    headers = {"Authorization": f"Bearer {settings.turso_token}"}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(_http_url(), json={"requests": requests}, headers=headers) as resp:
            if resp.status != 200:
                raise SqlError(f"turso http {resp.status}: {(await resp.text())[:300]}")
            payload = await resp.json()

    results: list[Result] = []
    for item in payload.get("results", [])[: len(statements)]:
        if item.get("type") != "ok":
            message = (item.get("error") or {}).get("message", "unknown error")
            raise SqlError(f"turso: {message}")
        result = item["response"]["result"]
        names = [col.get("name") for col in result.get("cols", [])]
        rows = [{name: _decode(cell) for name, cell in zip(names, row)} for row in result.get("rows", [])]
        rowid = result.get("last_insert_rowid")
        results.append(Result(rows=rows, lastrowid=int(rowid) if rowid is not None else None))
    return results
