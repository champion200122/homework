import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import Config
from handlers import router as handlers_router, nemotron

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def webhook_handler(request: web.Request, bot: Bot, dp: Dispatcher) -> web.Response:
    """Обработчик webhook от Telegram"""
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_webhook_update(bot, update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return web.Response(text="Error", status=500)


async def ping_handler(request: web.Request) -> web.Response:
    """Health check endpoint для Render"""
    return web.Response(text="OK", status=200)


async def health_handler(request: web.Request) -> web.Response:
    """Подробная информация о статусе"""
    from storage import storage
    return web.json_response({
        "status": "running",
        "task_set": storage.has_task(),
        "photos_count": len(storage.student_photos)
    })


async def on_startup(bot: Bot, config: Config):
    """Действия при запуске"""
    # Устанавливаем webhook
    webhook_url = f"{config.webhook_url}/webhook"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    logger.info(f"✅ Webhook установлен: {webhook_url}")


async def on_shutdown(bot: Bot):
    """Действия при остановке"""
    await bot.delete_webhook()
    await bot.session.close()
    await nemotron.close()
    logger.info("🛑 Бот остановлен")


async def main():
    config = Config()
    
    # Проверяем необходимые переменные
    if not config.bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
    if not config.api_key:
        raise ValueError("API_TOKENROUTER_KEY не установлен!")
    
    # Инициализируем бота
    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем роутеры
    dp.include_router(handlers_router)
    
    # Создаем web приложение
    app = web.Application()
    
    # Маршруты
    app.router.add_post("/webhook", lambda r: webhook_handler(r, bot, dp))
    app.router.add_get("/ping", ping_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", ping_handler)  # Корень тоже отвечает 200
    
    # Хуки жизненного цикла
    app.on_startup.append(lambda _: on_startup(bot, config))
    app.on_shutdown.append(lambda _: on_shutdown(bot))
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host="0.0.0.0", port=config.port)
    await site.start()
    
    logger.info(f"🚀 Сервер запущен на порту {config.port}")
    
    # Держим процесс активным
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Получен сигнал остановки")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")
