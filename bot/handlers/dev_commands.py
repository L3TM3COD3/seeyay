"""
DEV ONLY - REMOVE BEFORE PRODUCTION
Development commands for testing bot functionality
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import logging

from bot.firestore import ensure_user_exists, update_user_balance, get_user, get_db

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("_reset"))
async def cmd_reset_user(message: Message):
    """DEV ONLY: Reset user to fresh state"""
    telegram_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    try:
        # Delete existing user document
        db = get_db()
        await db.collection("users").document(str(telegram_id)).delete()
        logger.info(f"DEV: Deleted user {telegram_id}")
        
        # Recreate with fresh defaults
        await ensure_user_exists(telegram_id, username)
        logger.info(f"DEV: Recreated user {telegram_id} with fresh data")
        
        await message.answer(
            "✅ Твои данные сброшены!\n\n"
            "💫 Ты снова новый пользователь\n"
            "⚡️ Баланс: 3 энергии\n"
            "🎯 Все достижения сброшены"
        )
    except Exception as e:
        logger.error(f"DEV: Error resetting user {telegram_id}: {e}")
        await message.answer(f"❌ Ошибка сброса: {e}")


@router.message(Command("_addbalance"))
async def cmd_add_balance(message: Message):
    """DEV ONLY: Add +24 energy to balance"""
    telegram_id = message.from_user.id
    
    try:
        result = await update_user_balance(telegram_id, 24)
        if result:
            new_balance = result.get("balance", 0)
            await message.answer(
                f"✅ Добавлено +24⚡\n\n"
                f"💰 Текущий баланс: {new_balance}⚡"
            )
            logger.info(f"DEV: Added +24 energy to user {telegram_id}, new balance: {new_balance}")
        else:
            await message.answer("❌ Пользователь не найден. Используй /start сначала")
    except Exception as e:
        logger.error(f"DEV: Error adding balance to {telegram_id}: {e}")
        await message.answer(f"❌ Ошибка добавления энергии: {e}")
