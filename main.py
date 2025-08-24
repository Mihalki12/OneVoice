import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.config import load_config, settings
from app.db import init_db, set_db_path
from app.routers.common import router as common_router
from app.routers.passenger import router as passenger_router
from app.routers.driver import router as driver_router
from app.routers.admin import router as admin_router


async def on_startup() -> None:
    # Initialize database schema
    await init_db()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Load configuration from environment
    load_config()

    # Configure DB path for DB module
    set_db_path(settings.db_path)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Routers
    dp.include_router(common_router)
    dp.include_router(passenger_router)
    dp.include_router(driver_router)
    dp.include_router(admin_router)

    # Register startup task
    dp.startup.register(on_startup)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
