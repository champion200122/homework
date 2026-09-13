import asyncio
import logging
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import Config
from handlers import router as handlers_router, gemini  # ← gemini, НЕ nemotron

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def webhook_handler(request: web.Request, bot: Bot, dp: Dispatcher) -> web.Response:
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_webhook_update(bot, update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Ошибка webhook: {e}")
        return web.Response(text="Error", status=500)


async def ping_handler(request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)


async def health_handler(request: web.Request) -> web.Response:
    from storage import storage
    return web.json_response({
        "status": "running",
        "task_photos": len(storage.task_photos),
        "student_photos": len(storage.student_photos)
    })


async def auto_ping(config: Config):
    while True:
        try:
            await asyncio.sleep(600)
            async with ClientSession() as session:
                async with session.get(f"{config.webhook_url}/ping", timeout=30) as resp:
                    logger.info(f"🔄 Автопинг: {resp.status}")
        except Exception as e:
            logger.warning(f"Ошибка автопинга: {e}")


async def on_startup(bot: Bot, config: Config):
    webhook_url = f"{config.webhook_url}/webhook"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    logger.info(f"✅ Webhook установлен: {webhook_url}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    await bot.session
