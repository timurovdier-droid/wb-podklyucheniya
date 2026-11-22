"""Установить webhook Telegram после деплоя на Vercel."""

import asyncio
import os
import sys
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


async def main() -> None:
    token = os.getenv("BOT_TOKEN", "").strip()
    base = os.getenv("WEBHOOK_BASE_URL", "").strip().rstrip("/")
    if not token or not base:
        print("Нужны BOT_TOKEN и WEBHOOK_BASE_URL (например https://xxx.vercel.app)", file=sys.stderr)
        sys.exit(1)
    url = f"{base}/api/webhook"
    api = f"https://api.telegram.org/bot{token}/setWebhook"
    async with aiohttp.ClientSession() as session:
        async with session.post(api, json={"url": url}) as resp:
            print(await resp.text())


if __name__ == "__main__":
    asyncio.run(main())