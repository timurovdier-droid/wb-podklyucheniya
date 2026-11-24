"""Отправка файлов из assets с кэшем Telegram file_id (в памяти и в таблице meta)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, InputMediaPhoto, Message

from bot import db, sql

log = logging.getLogger(__name__)

_memory: dict[str, str] = {}


def _key(path: Path) -> str:
    return f"file_id:{path.name}:{path.stat().st_size}"


async def _cached(keys: list[str]) -> dict[str, str]:
    found = {key: _memory[key] for key in keys if key in _memory}
    missing = [key for key in keys if key not in found]
    if not missing:
        return found
    try:
        await db.init()
        marks = ",".join("?" for _ in missing)
        result = await sql.execute(f"SELECT k, v FROM meta WHERE k IN ({marks})", tuple(missing))
        for row in result.rows:
            _memory[row["k"]] = row["v"]
            found[row["k"]] = row["v"]
    except Exception:
        log.exception("file_id cache read failed")
    return found


async def _remember(pairs: dict[str, str]) -> None:
    if not pairs:
        return
    _memory.update(pairs)
    try:
        await sql.batch(
            [
                ("INSERT INTO meta (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v", (k, v))
                for k, v in pairs.items()
            ]
        )
    except Exception:
        log.exception("file_id cache write failed")


def _forget(keys: list[str]) -> None:
    for key in keys:
        _memory.pop(key, None)


async def answer_photo(message: Message, path: Path, **kwargs: Any) -> Message:
    key = _key(path)
    file_id = (await _cached([key])).get(key)
    if file_id:
        try:
            return await message.answer_photo(file_id, **kwargs)
        except TelegramBadRequest:
            _forget([key])
    sent = await message.answer_photo(FSInputFile(path), **kwargs)
    if sent.photo:
        await _remember({key: sent.photo[-1].file_id})
    return sent


async def answer_voice(message: Message, path: Path, **kwargs: Any) -> Message:
    key = _key(path)
    file_id = (await _cached([key])).get(key)
    if file_id:
        try:
            return await message.answer_voice(file_id, **kwargs)
        except TelegramBadRequest:
            _forget([key])
    sent = await message.answer_voice(FSInputFile(path), **kwargs)
    if sent.voice:
        await _remember({key: sent.voice.file_id})
    return sent


async def answer_photo_album(message: Message, items: list[tuple[Path, str | None]]) -> list[Message]:
    keys = [_key(path) for path, _ in items]
    cached = await _cached(keys)
    if len(cached) == len(keys):
        try:
            return await message.answer_media_group(
                [InputMediaPhoto(media=cached[key], caption=caption) for key, (_, caption) in zip(keys, items)]
            )
        except TelegramBadRequest:
            _forget(keys)
    sent = await message.answer_media_group(
        [InputMediaPhoto(media=FSInputFile(path), caption=caption) for path, caption in items]
    )
    await _remember({key: msg.photo[-1].file_id for key, msg in zip(keys, sent) if msg.photo})
    return sent
