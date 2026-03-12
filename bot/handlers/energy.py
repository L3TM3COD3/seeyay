from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiohttp
import logging

from bot.keyboards import kb_balance, kb_menu, kb_payment_confirm
from bot.messages import m13_main_menu, m14_balance, m15_payment_confirm, m16_payment_cancelled
from bot.firestore import get_user
from bot.config import get_settings

router = Router()
logger = logging.getLogger(__name__)

PACK_LABELS = {
    "pack_10": "10⚡ за 249₽",
    "pack_50": "50⚡ за 790₽",
    "pack_120": "120⚡ за 1290₽",
    "pack_300": "300⚡ за 2490₽",
    "pack_starter": "100⚡ за 990₽ (стартер)",
    "pack_downsell": "8⚡ за 169₽ (пробный)",
}


async def _create_payment(
    telegram_id: int,
    pack_id: str,
) -> tuple[str | None, str | None, int | None, int | None]:
    """
    Вызывает backend API и возвращает (payment_url, payment_id, energy, price) или (None, None, None, None) при ошибке.
    """
    settings = get_settings()
    url = f"{settings.backend_url.rstrip('/')}/api/payments/create-payment-url"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"telegram_id": telegram_id, "pack_id": pack_id}) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    logger.error(f"Backend create-payment-url failed: {resp.status} - {err}")
                    return None, None, None, None
                data = await resp.json()
                return (
                    data.get("payment_url"),
                    data.get("payment_id"),
                    data.get("energy"),
                    data.get("price"),
                )
    except Exception as e:
        logger.error(f"Failed to create payment: {e}")
        return None, None, None, None


async def _send_payment_message(callback: CallbackQuery, pack_id: str, label: str):
    """
    Создаёт платёж, отправляет m15 с описанием и клавиатурой:
    - Перейти к оплате (URL)
    - Отмена
    """
    await callback.answer("Открываю форму оплаты...")
    telegram_id = callback.from_user.id

    payment_url, payment_id, energy, price = await _create_payment(telegram_id, pack_id)
    if not payment_url or not payment_id:
        await callback.message.answer(
            "❌ Не удалось создать платёж. Убедитесь, что вы нажали /start, и попробуйте снова."
        )
        return

    # Если backend не вернул energy/price, используем PACK_LABELS только как fallback для текста
    energy_val = energy if energy is not None else None
    price_val = price if price is not None else None

    if energy_val is None or price_val is None:
        # Попробуем вытащить из label вида "10⚡ за 249₽"
        try:
            parts = label.split(" за ")
            energy_val = int(parts[0].split("⚡")[0])
            price_val = int(parts[1].split("₽")[0])
        except Exception:
            logger.warning(f"Failed to parse energy/price from label '{label}' for pack {pack_id}")
            energy_val = 0
            price_val = 0

    text = m15_payment_confirm(energy=energy_val, price=price_val)
    kb = kb_payment_confirm(payment_url=payment_url, payment_id=payment_id)

    await callback.message.answer(text=text, reply_markup=kb, parse_mode="HTML")
    logger.info(f"User {telegram_id} opened payment for {pack_id}, payment_id={payment_id}")


@router.callback_query(F.data.startswith("buy_pack:"))
async def handle_buy_pack(callback: CallbackQuery):
    """Обработчик покупки обычного пакета энергии"""
    pack_id = callback.data.split(":", 1)[1]
    label = PACK_LABELS.get(pack_id, pack_id)
    await _send_payment_message(callback, pack_id, label)


@router.callback_query(F.data == "buy_starter")
async def handle_buy_starter(callback: CallbackQuery):
    """Обработчик покупки стартер-пака (100⚡ за 990₽)"""
    await _send_payment_message(callback, "pack_starter", PACK_LABELS["pack_starter"])


@router.callback_query(F.data == "buy_downsell")
async def handle_buy_downsell(callback: CallbackQuery):
    """Обработчик покупки даунселл-пака (8⚡ за 169₽)"""
    await _send_payment_message(callback, "pack_downsell", PACK_LABELS["pack_downsell"])


@router.callback_query(F.data.startswith("cancel_payment:"))
async def handle_cancel_payment(callback: CallbackQuery):
    """
    Обработчик кнопки "Отмена" в m15.
    По ТЗ: сообщение должно превратиться в m16 (платёж отменён) с кнопками повторной покупки.
    """
    await callback.answer("Платёж отменён")  # краткий toast

    # Превращаем текущее сообщение в m16
    text = m16_payment_cancelled()
    # Повторные пакеты и \"Главное меню\" можно дать как в m11 (kb_insufficient),
    # но здесь просто оставляем кнопки из исходного сообщения или можно удалить клавиатуру.
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, parse_mode="HTML")


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
