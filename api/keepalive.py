import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler

from bot import db, sql

logging.basicConfig(level=logging.INFO)


async def _ping() -> dict:
    if not sql.using_turso():
        return {"status": "skipped", "reason": "turso is not configured"}
    await db.init()
    stamp = db.now_text()
    await sql.batch(
        [
            ("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)", ()),
            (
                "INSERT INTO meta (k, v) VALUES ('keepalive', ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v",
                (stamp,),
            ),
        ]
    )
    return {"status": "ok", "at": stamp}


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        code = 200
        try:
            payload = asyncio.run(_ping())
        except Exception as exc:
            logging.exception("keepalive failed")
            code = 500
            payload = {"status": "error", "error": str(exc)[:200]}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
