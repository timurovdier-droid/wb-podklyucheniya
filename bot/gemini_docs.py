"""Распознавание документов заявки через Gemini API."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from io import BytesIO
from typing import Any

from aiogram import Bot

from bot.config import gemini_fallback_models, settings
from bot.texts import PHOTO_STEPS

log = logging.getLogger(__name__)

_DOC_COUNT = len(PHOTO_STEPS)

_PROMPT = """Смотри на {n} фото документов водителя (такси). Порядок снимков:
1. паспорт (лицевая)
2. водительское удостоверение (лицевая)
3. водительское удостоверение (оборот)
4. техпаспорт (лицевая)
5. техпаспорт (оборот)
6. селфи с документом
7. лицензия такси

Извлеки только то, что реально читается на фото. Не выдумывай. Нечитаемое — null.

Верни один JSON-объект (латиница/кириллица как на документе):
- familiya, ism, otasining_ismi, full_name (строкой, как на правах)
- tugilgan_sana (как на паспорте, например 12.02.1999)
- pinfl (14 цифр JSHSHIR из паспорта/ID-карты)
- tugilgan_joy (место рождения)
- prava_raqam (номер водительского удостоверения)
- prava_amal_muddati (срок действия прав, как на документе)
- texpasport_seriya_raqam (texpasport: 3 латинские буквы + 7 цифр, часто вертикально на полях, напр. AAF0030551)
- avtomobil_raqam (госномер с техпаспорта, поле 18, формат 01A161YA)
- mashina_marka_model, mashina_yili, mashina_rangi
- litsenziya_raqam (лицензия такси, если видно)
- eslatma (кратко: плохое фото или расхождения; иначе "")

Для texpasport_seriya_raqam читай КАЖДУЮ латинскую букву отдельно. Не путай F с C и E, B с 8, O с 0.
"""

_TEX_PROMPT = """Это техпаспорт (texpasport) автомобиля Узбекистана — лицевая и/или оборот.
Найди:
1) Серию и номер документа: ровно 3 LATIN буквы + 7 цифр (пример: AAF0030551). Часто напечатано вертикально сбоку.
2) Госномер (поле 18): как на бланке, без пробелов (01A161YA).
3) Марка/модель (поле 1-2), год выпуска (поле 9), цвет (поле 15).

Читай серию ПОСИМВОЛЬНО. Критично различай F и C, F и E, G и C, O и 0, I и 1.
Только факты с фото. JSON:
{"texpasport_seriya_raqam":"","avtomobil_raqam":"","mashina_marka_model":"","mashina_yili":"","mashina_rangi":""}
"""

_RETRYABLE = {429, 500, 503, 504}


def enabled() -> bool:
    return bool(settings.gemini_api_key)


def _on_vercel() -> bool:
    return bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))


def _models_to_try() -> list[str]:
    chain = [settings.gemini_model, *gemini_fallback_models()]
    seen: set[str] = set()
    out: list[str] = []
    for name in chain:
        if name not in seen:
            seen.add(name)
            out.append(name)
    if _on_vercel():
        return out[:2]
    return out


async def extract_from_application(bot: Bot, app: dict) -> dict[str, Any] | None:
    if not enabled() or app.get("kind") != "ulanish":
        return None
    photos = list(app.get("photos") or [])
    if len(photos) < _DOC_COUNT:
        return None
    try:
        images = await _download_doc_photos(bot, photos[:_DOC_COUNT])
        if len(images) < _DOC_COUNT:
            log.warning(
                "only %s/%s document photos downloaded for %s",
                len(images),
                _DOC_COUNT,
                app.get("code"),
            )
            return {"eslatma": "Ba'zi hujjat rasmlari yuklab olinmadi — tekshiring."}
        return await asyncio.to_thread(_call_gemini, images)
    except Exception:
        log.exception("gemini extraction failed for %s", app.get("code"))
        return {
            "eslatma": (
                "OCR xizmati vaqtincha javob bermadi (Gemini). "
                "Bir daqiqa kutib, arizani qayta yuboring yoki hujjatlarni qo'lda kiriting."
            )
        }


async def _download_one(bot: Bot, file_id: str) -> tuple[bytes, str] | None:
    try:
        tg_file = await bot.get_file(file_id)
        if not tg_file.file_path:
            return None
        raw = await bot.download_file(tg_file.file_path)
        if isinstance(raw, BytesIO):
            data = raw.getvalue()
        elif isinstance(raw, (bytes, bytearray)):
            data = bytes(raw)
        else:
            data = raw.read()
        if not data:
            return None
        return data, _guess_mime(tg_file.file_path)
    except Exception:
        log.exception("failed to download telegram photo %s", file_id)
        return None


async def _download_doc_photos(bot: Bot, file_ids: list[str]) -> list[tuple[bytes, str]]:
    downloaded = await asyncio.gather(*(_download_one(bot, file_id) for file_id in file_ids))
    return [item for item in downloaded if item]


def _guess_mime(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def _is_retryable(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code in _RETRYABLE:
        return True
    status = getattr(exc, "status", None)
    if isinstance(status, str) and status.upper() == "UNAVAILABLE":
        return True
    return False


def _call_gemini(images: list[tuple[bytes, str]]) -> dict[str, Any] | None:
    client = _genai_client()
    deadline = time.monotonic() + (40.0 if _on_vercel() else 120.0)
    parts: list[Any] = _image_parts(images)
    parts.append(_text_part(_PROMPT.format(n=len(images))))

    parsed = _request_json(
        client,
        parts,
        thinking_level="LOW",
        label=f"all-docs ({len(images)} img)",
        deadline=deadline,
    )
    if parsed is None:
        return {"eslatma": "OCR ishlamadi — javob yo'q. Qayta urinib ko'ring."}

    if len(images) >= 5 and time.monotonic() < deadline - 8:
        tex_parts = _image_parts(images[3:5])
        tex_parts.append(_text_part(_TEX_PROMPT))
        tex = _request_json(
            client,
            tex_parts,
            thinking_level="LOW" if _on_vercel() else "MEDIUM",
            label="texpasport",
            deadline=deadline,
        )
        if tex:
            _merge_tech_fields(parsed, tex)

    return parsed


def _genai_client():
    from google import genai
    from google.genai import types

    timeout_ms = 20_000 if _on_vercel() else 60_000
    try:
        return genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )
    except TypeError:
        return genai.Client(api_key=settings.gemini_api_key)


def _image_parts(images: list[tuple[bytes, str]]) -> list[Any]:
    from google.genai import types

    return [types.Part.from_bytes(data=data, mime_type=mime) for data, mime in images]


def _text_part(text: str):
    from google.genai import types

    return types.Part.from_text(text=text)


def _request_json(
    client: Any,
    parts: list[Any],
    *,
    thinking_level: str,
    label: str,
    deadline: float | None = None,
) -> dict[str, Any] | None:
    from google.genai import types
    from google.genai.errors import APIError

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
        response_mime_type="application/json",
    )
    attempts = 2 if _on_vercel() else 4
    last_error: str | None = None
    for model_name in _models_to_try():
        for attempt in range(attempts):
            if deadline is not None and time.monotonic() >= deadline:
                log.warning("gemini %s stopped: time budget", label)
                return None
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=parts,
                    config=config,
                )
                parsed = _parse_response(response)
                if parsed is not None:
                    log.info("gemini ocr ok [%s] model=%s", label, model_name)
                    return parsed
                last_error = "empty response"
                break
            except APIError as exc:
                last_error = f"{model_name}: {getattr(exc, 'message', exc)!s}"[:200]
                if _is_retryable(exc) and attempt < attempts - 1:
                    delay = 1 if _on_vercel() else 3 * (attempt + 1)
                    if deadline is not None:
                        delay = min(delay, max(0.0, deadline - time.monotonic() - 1))
                    if delay > 0:
                        time.sleep(delay)
                    continue
                log.warning("gemini %s failed: %s", label, last_error)
                break
    return None


def _merge_tech_fields(main: dict[str, Any], tex: dict[str, Any]) -> None:
    for key in (
        "texpasport_seriya_raqam",
        "avtomobil_raqam",
        "mashina_marka_model",
        "mashina_yili",
        "mashina_rangi",
    ):
        value = str(tex.get(key) or "").strip()
        if value:
            main[key] = value


def _parse_response(response: Any) -> dict[str, Any] | None:
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        log.warning("gemini returned non-json: %s", text[:200])
        return None
    if not isinstance(data, dict):
        return None
    return _normalize(data)


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            out[key] = ""
            continue
        if isinstance(value, str):
            out[key] = value.strip()
        else:
            out[key] = value
    full_name = str(out.get("full_name") or "").strip()
    if not full_name:
        chunks = [
            str(out.get("familiya") or "").strip(),
            str(out.get("ism") or "").strip(),
            str(out.get("otasining_ismi") or "").strip(),
        ]
        joined = " ".join(part for part in chunks if part)
        if joined:
            out["full_name"] = joined
    serial = str(out.get("texpasport_seriya_raqam") or "")
    out["texpasport_seriya_raqam"] = _normalize_tex_serial(serial)
    plate = str(out.get("avtomobil_raqam") or "")
    out["avtomobil_raqam"] = re.sub(r"\s+", "", plate.upper())
    return out


def _normalize_tex_serial(value: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9]", "", value.upper())
    match = re.fullmatch(r"([A-Z]{3})(\d{7,10})", raw)
    if match:
        return match.group(1) + match.group(2)[:7]
    return raw