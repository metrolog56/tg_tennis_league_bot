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
    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
