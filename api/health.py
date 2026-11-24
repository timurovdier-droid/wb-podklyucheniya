import json
from http.server import BaseHTTPRequestHandler

from bot.config import settings


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        payload = {
            "status": "ok",
            "service": "wb-podklyucheniya",
            "bot_token": bool(settings.bot_token),
            "admin_chat": bool(settings.admin_chat_id),
            "work_chat": bool(settings.work_chat_id),
            "gemini": bool(settings.gemini_api_key),
            "turso": bool(settings.turso_url and settings.turso_token),
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
