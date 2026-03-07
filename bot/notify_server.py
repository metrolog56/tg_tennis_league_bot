"""
Минимальный HTTP-сервер для мгновенной отправки уведомления о матче на подтверждение.
POST /notify-pending-match с JSON {"match_id": "..."} и заголовком X-Notify-Secret.
Запускается в том же процессе, что и бот (фоновой задачей).
"""
import logging
import os
from typing import Optional

import aiohttp.web

from services import scheduler

logger = logging.getLogger(__name__)


def _get_secret() -> str:
    return (os.getenv("NOTIFY_SECRET") or "").strip()


async def handle_notify_pending(request: aiohttp.web.Request) -> aiohttp.web.Response:
    secret = _get_secret()
    if secret and request.headers.get("X-Notify-Secret") != secret:
        return aiohttp.web.json_response({"error": "unauthorized"}, status=401)
    try:
        body = await request.json()
    except Exception as e:
        logger.warning("notify-pending: invalid JSON: %s", e)
        return aiohttp.web.json_response({"error": "invalid json"}, status=400)
    match_id = body.get("match_id") if isinstance(body, dict) else None
    if not match_id:
        return aiohttp.web.json_response({"error": "match_id required"}, status=400)
    bot = scheduler._bot
    if not bot:
        logger.warning("notify-pending: bot not ready")
        return aiohttp.web.json_response({"error": "bot not ready"}, status=503)
    ok = await scheduler.send_pending_confirm_for_match(str(match_id), bot)
    return aiohttp.web.json_response({"ok": ok})


def create_app() -> aiohttp.web.Application:
    app = aiohttp.web.Application()
    app.router.add_post("/notify-pending-match", handle_notify_pending)
    return app


def _get_port() -> int:
    return int(os.getenv("NOTIFY_LISTEN_PORT", "8765"))


async def start_notify_server(host: str = "127.0.0.1", port: Optional[int] = None) -> aiohttp.web.AppRunner:
    """Запустить сервер. По умолчанию host=127.0.0.1, port из NOTIFY_LISTEN_PORT (8765)."""
    port = port if port is not None else _get_port()
    app = create_app()
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, host, port)
    await site.start()
    logger.info("Notify server listening on %s:%s", host, port)
    return runner
