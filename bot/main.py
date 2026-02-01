import asyncio
import logging
import os
import sys
from aiohttp import web

# Настройка логирования - ДО всех импортов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Глобальные переменные для бота
bot = None
dp = None
bot_initialized = False


async def health_check(request):
    """Health check endpoint для Cloud Run"""
    return web.Response(text="OK", status=200)


async def webhook_handler(request):
    """Обработчик webhook запросов от Telegram"""
    global bot, dp, bot_initialized
    
    if not bot_initialized:
        return web.Response(text="Bot not initialized", status=503)
    
    try:
        from aiogram.types import Update
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return web.Response(text="Error", status=500)


async def init_bot(app):
    """Инициализация бота при запуске приложения"""
    global bot, dp, bot_initialized
    
    try:
        logger.info("Initializing bot...")
        
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from bot.config import get_settings
        from bot.handlers import start_router, photo_router, webapp_router
        
        settings = get_settings()
        logger.info(f"Got settings, token present: {bool(settings.bot_token)}")
        
        # Создаём бота
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Создаём диспетчер с хранилищем состояний
        dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрируем роутеры
        dp.include_router(start_router)
        dp.include_router(webapp_router)
        dp.include_router(photo_router)
        
        # Устанавливаем webhook
        webhook_url = os.environ.get("WEBHOOK_URL")
        if webhook_url:
            await bot.set_webhook(f"{webhook_url}/webhook")
            logger.info(f"Webhook set to {webhook_url}/webhook")
        else:
            logger.warning("WEBHOOK_URL not set, webhook not configured")
        
        bot_initialized = True
        logger.info("Bot initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}", exc_info=True)


async def cleanup_bot(app):
    """Очистка при остановке"""
    global bot
    if bot:
        try:
            await bot.session.close()
        except Exception:
            pass


def main():
    """Главная функция запуска"""
    logger.info("Starting application...")
    
    # Создаём aiohttp приложение
    app = web.Application()
    
    # Health check endpoints (всегда работают)
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    # Webhook endpoint
    app.router.add_post("/webhook", webhook_handler)
    
    # Регистрируем инициализацию бота при старте
    app.on_startup.append(init_bot)
    app.on_cleanup.append(cleanup_bot)
    
    # Получаем порт из переменной окружения
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting server on port {port}...")
    
    # Запускаем веб-сервер
    web.run_app(app, host="0.0.0.0", port=port, print=logger.info)


if __name__ == "__main__":
    main()
