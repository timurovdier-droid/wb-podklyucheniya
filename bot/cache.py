"""Кеш заявок в памяти процесса (для тёплых serverless-инстансов)."""

from __future__ import annotations

from typing import Any

_store: dict[int, dict[str, Any]] = {}
_by_code: dict[str, int] = {}


def remember(app: dict[str, Any]) -> None:
    app_id = int(app["id"])
    snapshot = dict(app)
    _store[app_id] = snapshot
    _by_code[str(app.get("code") or "")] = app_id


def recall(app_id: int) -> dict[str, Any] | None:
    app = _store.get(app_id)
    return dict(app) if app else None


def recall_by_code(code: str) -> dict[str, Any] | None:
    raw = (code or "").strip()
    if not raw:
        return None
    app_id = _by_code.get(raw)
    if app_id is None:
        for item in _store.values():
            if item.get("code") == raw:
                return dict(item)
        return None
    return recall(app_id)