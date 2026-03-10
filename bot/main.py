"""
Точка входа Telegram-бота «Лига настольного тенниса».
Регистрация хендлеров, FSM, polling, логирование.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import common, results, rating, admin
from services.scheduler import start_scheduler
from notify_server import start_notify_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    from pathlib import Path
    from dotenv import load_dotenv
    import os

    # Загружать .env из каталога bot, чтобы не зависеть от текущей рабочей директории
    bot_dir = Path(__file__).resolve().parent
    load_dotenv(bot_dir / ".env")
    token = (os.getenv("BOT_TOKEN") or "").strip()
    if not token:
        raise ValueError("BOT_TOKEN not set in .env")

    async def _start_health_server() -> None:
        """Запустить простой TCP-сервер для health-check Koyeb."""
        port = int(os.getenv("PORT", "8000"))

        async def handle_client(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            try:
                await reader.read(1024)
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
                await writer.drain()
            except Exception:
                pass
            finally:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

        server = await asyncio.start_server(handle_client, host="0.0.0.0", port=port)
        addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        logger.info("Health server listening on %s", addresses)

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(common.router)
    dp.include_router(results.router)
    dp.include_router(rating.router)
    dp.include_router(admin.router)

    start_scheduler(bot)
    if os.getenv("NOTIFY_LISTEN_PORT"):
        await start_notify_server()
    await _start_health_server()
    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
