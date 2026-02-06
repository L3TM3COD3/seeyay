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
        logger.info("=== Initializing bot ===")
        sys.stdout.flush()
        
        logger.info("Importing aiogram...")
        sys.stdout.flush()
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        logger.info("Importing bot.config...")
        sys.stdout.flush()
        from bot.config import get_settings
        
        logger.info("Importing bot.handlers...")
        sys.stdout.flush()
        from bot.handlers import (
            start_router,
            template_selection_router,
            energy_router,
            photo_router
        )
        logger.info("All imports successful!")
        sys.stdout.flush()
        
        settings = get_settings()
        logger.info(f"Got settings, token present: {bool(settings.bot_token)}")
        sys.stdout.flush()
        
        # Создаём бота
        logger.info("Creating bot instance...")
        sys.stdout.flush()
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Создаём диспетчер с хранилищем состояний
        logger.info("Creating dispatcher...")
        sys.stdout.flush()
        dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрируем роутеры (порядок важен!)
        logger.info("Registering routers...")
        sys.stdout.flush()
        dp.include_router(start_router)
        dp.include_router(template_selection_router)
        dp.include_router(energy_router)
        dp.include_router(photo_router)
        logger.info("All routers registered!")
        sys.stdout.flush()
        
        # Устанавливаем webhook
        webhook_url = os.environ.get("WEBHOOK_URL")
        if webhook_url:
            logger.info(f"Setting webhook to {webhook_url}/webhook...")
            sys.stdout.flush()
            await bot.set_webhook(f"{webhook_url}/webhook")
            logger.info(f"Webhook set successfully!")
            sys.stdout.flush()
        else:
            logger.warning("WEBHOOK_URL not set!")
            sys.stdout.flush()
        
        bot_initialized = True
        logger.info("=== Bot initialized successfully! ===")
        sys.stdout.flush()
        
    except Exception as e:
        logger.error(f"=== FAILED to initialize bot: {e} ===", exc_info=True)
        sys.stdout.flush()


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
    logger.info("=== Starting application ===")
    sys.stdout.flush()
    
    # Создаём aiohttp приложение
    logger.info("Creating aiohttp application...")
    sys.stdout.flush()
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
    
    logger.info(f"=== Starting server on port {port} ===")
    sys.stdout.flush()
    
    # Запускаем веб-сервер
    web.run_app(app, host="0.0.0.0", port=port, print=logger.info)


if __name__ == "__main__":
    main()
