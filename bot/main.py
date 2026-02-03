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
    # region agent log
    import json;open(r'c:\PetProjects\Seeyay.ai\.cursor\debug.log','a',encoding='utf-8').write(json.dumps({'location':'bot/main.py:27','message':'webhook_handler called','data':{'bot_initialized':bot_initialized},'timestamp':__import__('time').time()*1000,'sessionId':'debug-session','runId':'run1','hypothesisId':'E'})+'\n')
    # endregion
    
    if not bot_initialized:
        # region agent log
        import json;open(r'c:\PetProjects\Seeyay.ai\.cursor\debug.log','a',encoding='utf-8').write(json.dumps({'location':'bot/main.py:31','message':'bot NOT initialized - returning 503','data':{},'timestamp':__import__('time').time()*1000,'sessionId':'debug-session','runId':'run1','hypothesisId':'E'})+'\n')
        # endregion
        return web.Response(text="Bot not initialized", status=503)
    
    try:
        from aiogram.types import Update
        data = await request.json()
        # region agent log
        import json;open(r'c:\PetProjects\Seeyay.ai\.cursor\debug.log','a',encoding='utf-8').write(json.dumps({'location':'bot/main.py:37','message':'received update data','data':{'has_message':('message' in data),'has_callback':('callback_query' in data)},'timestamp':__import__('time').time()*1000,'sessionId':'debug-session','runId':'run1','hypothesisId':'E'})+'\n')
        # endregion
        update = Update(**data)
        await dp.feed_update(bot=bot, update=update)
        # region agent log
        import json;open(r'c:\PetProjects\Seeyay.ai\.cursor\debug.log','a',encoding='utf-8').write(json.dumps({'location':'bot/main.py:40','message':'update processed successfully','data':{},'timestamp':__import__('time').time()*1000,'sessionId':'debug-session','runId':'run1','hypothesisId':'E'})+'\n')
        # endregion
        return web.Response(text="OK", status=200)
    except Exception as e:
        # region agent log
        import json;open(r'c:\PetProjects\Seeyay.ai\.cursor\debug.log','a',encoding='utf-8').write(json.dumps({'location':'bot/main.py:43','message':'EXCEPTION in webhook_handler','data':{'error':str(e),'error_type':type(e).__name__},'timestamp':__import__('time').time()*1000,'sessionId':'debug-session','runId':'run1','hypothesisId':'E'})+'\n')
        # endregion
        logger.error(f"Error processing update: {e}")
        return web.Response(text="Error", status=500)


async def start_polling():
    """Запуск polling для локальной разработки"""
    global bot, dp
    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Polling error: {e}")


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
        
        # Устанавливаем webhook или запускаем polling
        webhook_url = os.environ.get("WEBHOOK_URL")
        use_polling = os.environ.get("USE_POLLING", "").lower() in ("true", "1", "yes")
        
        if webhook_url and not use_polling:
            await bot.set_webhook(f"{webhook_url}/webhook")
            logger.info(f"Webhook set to {webhook_url}/webhook")
        else:
            # Удаляем webhook для использования polling
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted, will use polling mode")
            
            # Запускаем polling в фоне
            asyncio.create_task(start_polling())
        
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
