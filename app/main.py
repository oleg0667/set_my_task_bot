import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import TelegramObject
from app.config import settings
from app.database.session import async_session_factory, init_db
from app.handlers import start, tasks, inline_callbacks, group_handlers, task_commands

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


class DbSessionMiddleware:
    """Middleware to inject SQLAlchemy async session into handler data."""

    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(self, handler, event: TelegramObject, data: dict):
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)


def create_aiohttp_session() -> AiohttpSession:
    """Create an aiogram aiohttp session with optional SOCKS5 proxy."""
    if settings.proxy_url:
        logger.info(f"Using proxy: {settings.PROXY_PROTOCOL}://{settings.PROXY_HOST}:{settings.PROXY_PORT}")
        session = AiohttpSession(
            proxy=settings.proxy_url,
        )
    else:
        session = AiohttpSession()
    return session


async def main():
    logger.info("Initializing database...")
    await init_db()

    logger.info("Creating bot and dispatcher...")
    aiohttp_session = create_aiohttp_session()
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
        session=aiohttp_session,
    )
    dp = Dispatcher()

    # Register middlewares
    dp.update.middleware(DbSessionMiddleware(async_session_factory))

    # Register routers
    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(inline_callbacks.router)
    dp.include_router(group_handlers.router)
    dp.include_router(task_commands.router)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())