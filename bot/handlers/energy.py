from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from bot.keyboards import kb_balance, kb_menu
from bot.messages import m13_main_menu, m14_balance
from bot.firestore import get_user

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("buy_pack:"))
async def handle_buy_pack(callback: CallbackQuery):
    """Обработчик покупки обычного пакета энергии"""
    await callback.answer("Открываю форму оплаты...")
    
    telegram_id = callback.from_user.id
    pack_id = callback.data.split(":", 1)[1]
    
    # TODO: Здесь будет интеграция с backend API для создания платежа
    # На данный момент просто информируем пользователя
    await callback.message.answer(
        f"💳 Покупка пакета {pack_id}\n\n"
        f"Интеграция платежей будет добавлена в следующей версии.\n"
        f"Пока что обратитесь к менеджеру для ручного пополнения."
    )
    
    logger.info(f"User {telegram_id} attempted to buy pack {pack_id}")


@router.callback_query(F.data == "buy_starter")
async def handle_buy_starter(callback: CallbackQuery):
    """Обработчик покупки стартер-пака (100⚡ за 990₽)"""
    await callback.answer("Открываю форму оплаты...")
    
    telegram_id = callback.from_user.id
    
    # TODO: Здесь будет интеграция с backend API
    # После успешной оплаты нужно установить starter_pack_purchased = True
    await callback.message.answer(
        f"💳 Покупка СТАРТЕР-ПАКА (100⚡ за 990₽)\n\n"
        f"Интеграция платежей будет добавлена в следующей версии.\n"
        f"Пока что обратитесь к менеджеру для ручного пополнения."
    )
    
    logger.info(f"User {telegram_id} attempted to buy starter pack")


@router.callback_query(F.data == "buy_downsell")
async def handle_buy_downsell(callback: CallbackQuery):
    """Обработчик покупки даунселл-пака (8⚡ за 169₽)"""
    await callback.answer("Открываю форму оплаты...")
    
    telegram_id = callback.from_user.id
    
    # TODO: Здесь будет интеграция с backend API
    await callback.message.answer(
        f"💳 Покупка пробного пакета (8⚡ за 169₽)\n\n"
        f"Интеграция платежей будет добавлена в следующей версии.\n"
        f"Пока что обратитесь к менеджеру для ручного пополнения."
    )
    
    logger.info(f"User {telegram_id} attempted to buy downsell pack")


@router.callback_query(F.data == "show_menu")
async def handle_show_menu(callback: CallbackQuery):
    """Обработчик кнопки "Главное меню" - показывает m13"""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    
    # Получаем данные пользователя
    user = await get_user(telegram_id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден. Используйте /start")
        return
    
    username = user.get("username") or "пользователь"
    balance = user.get("balance", 0)
    
    # Отправляем m13
    await callback.message.answer(
        text=m13_main_menu(username, balance),
        reply_markup=kb_menu(),
        parse_mode="HTML"
    )
    
    logger.info(f"User {telegram_id} opened main menu via callback")


@router.callback_query(F.data.startswith("show_balance:"))
async def handle_show_balance(callback: CallbackQuery):
    """Обработчик кнопки "Пополнить баланс" - показывает m14"""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    back_target = callback.data.split(":", 1)[1]
    
    # Получаем данные пользователя
    user = await get_user(telegram_id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден. Используйте /start")
        return
    
    username = user.get("username") or "пользователь"
    balance = user.get("balance", 0)
    
    # Отправляем m14
    await callback.message.answer(
        text=m14_balance(username, balance),
        reply_markup=kb_balance(back_target),
        parse_mode="HTML"
    )
    
    logger.info(f"User {telegram_id} opened balance page from {back_target}")


@router.callback_query(F.data.startswith("back:"))
async def handle_back(callback: CallbackQuery):
    """Обработчик кнопки "Назад" - возвращает к предыдущему экрану"""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    target = callback.data.split(":", 1)[1]
    
    user = await get_user(telegram_id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден. Используйте /start")
        return
    
    username = user.get("username") or "пользователь"
    balance = user.get("balance", 0)
    
    if target == "menu":
        # Возврат в главное меню (m13)
        await callback.message.edit_text(
            text=m13_main_menu(username, balance),
            reply_markup=kb_menu(),
            parse_mode="HTML"
        )
    elif target in ["result", "starter", "downsell"]:
        # Возврат к предыдущему сообщению - просто удаляем текущее
        try:
            await callback.message.delete()
        except Exception:
            await callback.message.answer("Возвращаемся назад...")
    else:
        # Неизвестный target - просто удаляем
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    logger.info(f"User {telegram_id} navigated back from balance to {target}")


@router.callback_query(F.data == "contact_manager")
async def handle_contact_manager(callback: CallbackQuery):
    """Обработчик кнопки "Связаться с менеджером"""
    await callback.answer()
    
    # TODO: Вставить реальный контакт менеджера
    await callback.message.answer(
        "💬 <b>Связаться с менеджером</b>\n\n"
        "По всем вопросам пишите:\n"
        "@support_username\n\n"
        "Мы ответим в течение 1-2 часов!",
        parse_mode="HTML"
    )
    
    logger.info(f"User {callback.from_user.id} requested manager contact")
