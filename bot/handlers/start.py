from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
import logging

from bot.keyboards import kb_template_grid, kb_menu
from bot.messages import m1_welcome, m13_main_menu
from bot.states import UserState
from bot.config import get_settings
from bot.firestore import ensure_user_exists, get_user, set_user_timestamp
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start - отправляет m1"""
    telegram_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "пользователь"
    
    # Проверяем, существует ли пользователь
    user = await get_user(telegram_id)
    is_new_user = user is None
    
    # Создаём пользователя если не существует
    await ensure_user_exists(telegram_id, username)
    
    # Для новых пользователей ИЛИ пользователей без started_at записываем started_at (Plan 2)
    # FIX: Также устанавливаем started_at для пользователей у которых он None (после reset)
    should_set_started_at = is_new_user or (user and user.get("started_at") is None)
    
    if should_set_started_at:
        await set_user_timestamp(telegram_id, "started_at", datetime.utcnow())
        logger.info(f"User {telegram_id}, set started_at timestamp (new or reset user)")
    
    # Сбрасываем состояние
    await state.clear()
    await state.set_state(UserState.idle)
    
    # Отправляем m1: приветственное сообщение
    await message.answer(
        text=m1_welcome(),
        reply_markup=kb_template_grid(),
        parse_mode="HTML"
    )
    
    logger.info(f"User {telegram_id} started the bot")


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Обработчик команды /menu - отправляет m13"""
    telegram_id = message.from_user.id
    
    # Получаем данные пользователя
    user = await get_user(telegram_id)
    if not user:
        # Если пользователь не найден, редирект на /start
        await message.answer("Пожалуйста, сначала используйте /start")
        return
    
    username = user.get("username") or "пользователь"
    balance = user.get("balance", 0)
    
    # Отправляем m13: главное меню
    await message.answer(
        text=m13_main_menu(username, balance),
        reply_markup=kb_menu(),
        parse_mode="HTML"
    )
    
    logger.info(f"User {telegram_id} opened main menu")


@router.callback_query(F.data == "open_miniapp_dev")
async def callback_open_miniapp_dev(callback: CallbackQuery):
    """Обработчик для dev кнопки Mini App (когда нет HTTPS)"""
    settings = get_settings()
    await callback.answer()
    await callback.message.answer(
        f"🔧 Dev Mode: Mini App доступен по адресу:\n{settings.mini_app_url}\n\n"
        "Откройте этот URL в браузере для тестирования."
    )
