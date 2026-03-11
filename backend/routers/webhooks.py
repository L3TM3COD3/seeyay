"""
Webhooks Router - обработка уведомлений от CloudPayments
https://developers.cloudpayments.ru/#uvedomleniya
"""
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional
from urllib.parse import parse_qs
import logging
import json

from backend.firestore import (
    get_user,
    get_payment,
    update_payment_status,
    update_user_balance,
)
from backend.services.cloudpayments import get_cloudpayments_client
from backend.services.subscription import get_subscription_service
from backend.services.notifications import get_notification_service

router = APIRouter(prefix="/api/webhooks/cloudpayments", tags=["webhooks"])
logger = logging.getLogger(__name__)


def verify_signature(data: str, signature: Optional[str]) -> bool:
    """Проверка подписи webhook от CloudPayments"""
    if not signature:
        return False
    
    cp_client = get_cloudpayments_client()
    return cp_client.verify_notification(data, signature)


async def _parse_webhook_data(request: Request):
    """
    Парсит данные webhook от CloudPayments.
    Поддерживает JSON и application/x-www-form-urlencoded.
    Возвращает (raw_body_str, parsed_dict).
    """
    body = await request.body()
    data_str = body.decode("utf-8")

    content_type = request.headers.get("content-type", "")

    # Явный JSON
    if "application/json" in content_type:
        try:
            return data_str, json.loads(data_str)
        except json.JSONDecodeError:
            logger.error("Failed to parse webhook body as JSON", exc_info=True)
            return data_str, {}

    # form-urlencoded
    if "application/x-www-form-urlencoded" in content_type:
        parsed = parse_qs(data_str, keep_blank_values=True)
        parsed_simple = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        return data_str, parsed_simple

    # Fallback: пробуем JSON, затем form-urlencoded
    try:
        return data_str, json.loads(data_str)
    except json.JSONDecodeError:
        parsed = parse_qs(data_str, keep_blank_values=True)
        parsed_simple = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        return data_str, parsed_simple


@router.post("/check")
async def webhook_check(
    request: Request,
    content_hmac: Optional[str] = Header(None, alias="Content-HMAC")
):
    """
    Check notification - проверка возможности платежа
    Вызывается перед списанием средств
    https://developers.cloudpayments.ru/#check
    """
    data_str, data = await _parse_webhook_data(request)
    
    # Проверяем подпись
    if not verify_signature(data_str, content_hmac):
        logger.warning("Invalid signature in check webhook")
        return {"code": 13}  # Ошибка проверки подписи
    
    try:
        account_id = data.get("AccountId")
        invoice_id = data.get("InvoiceId")
        amount_raw = data.get("Amount")
        
        logger.info(f"Check webhook: account={account_id}, invoice={invoice_id}, amount={amount_raw}")
        
        # Проверяем пользователя
        try:
            telegram_id = int(account_id)
            user = await get_user(telegram_id)
            
            if not user:
                logger.warning(f"User not found: {telegram_id}")
                return {"code": 10}  # Пользователь не найден
        except (ValueError, TypeError):
            logger.error(f"Invalid account_id: {account_id}")
            return {"code": 10}
        
        # Проверяем платеж
        payment = await get_payment(invoice_id)
        if not payment:
            logger.warning(f"Payment not found: {invoice_id}")
            return {"code": 11}  # Платеж не найден
        
        if payment.get("status") == "completed":
            logger.warning(f"Payment already completed: {invoice_id}")
            return {"code": 12}  # Платеж уже проведен
        
        # Проверяем сумму
        try:
            amount = float(amount_raw)
            expected_amount = float(payment.get("amount", 0))
        except (TypeError, ValueError):
            logger.warning(f"Invalid amount format in check webhook: expected={payment.get('amount')}, got={amount_raw}")
            return {"code": 11}

        if abs(expected_amount - amount) > 0.01:
            logger.warning(f"Amount mismatch: expected {expected_amount}, got {amount}")
            return {"code": 11}
        
        # Всё ок
        return {"code": 0}
        
    except Exception as e:
        logger.error(f"Error in check webhook: {e}", exc_info=True)
        return {"code": 13}


@router.post("/pay")
async def webhook_pay(
    request: Request,
    content_hmac: Optional[str] = Header(None, alias="Content-HMAC")
):
    """
    Pay notification - успешная оплата
    Вызывается после успешного платежа
    https://developers.cloudpayments.ru/#pay
    """
    data_str, data = await _parse_webhook_data(request)
    
    # Проверяем подпись
    if not verify_signature(data_str, content_hmac):
        logger.warning("Invalid signature in pay webhook")
        return {"code": 13}
    
    try:
        account_id = data.get("AccountId")
        invoice_id = data.get("InvoiceId")
        transaction_id = data.get("TransactionId")
        amount = data.get("Amount")
        token = data.get("Token")  # Рекуррентный токен (если есть)
        
        logger.info(f"Pay webhook: account={account_id}, invoice={invoice_id}, transaction={transaction_id}, amount={amount}")
        
        telegram_id = int(account_id)
        
        # Обновляем статус платежа
        await update_payment_status(
            payment_id=invoice_id,
            status="completed",
            transaction_id=str(transaction_id)
        )
        
        # Получаем информацию о платеже
        payment = await get_payment(invoice_id)
        if not payment:
            logger.error(f"Payment not found after pay: {invoice_id}")
            return {"code": 0}  # Всё равно возвращаем успех, чтобы не было повторных попыток
        
        payment_type = payment.get("type")
        product = payment.get("product")
        
        # Обрабатываем платеж в зависимости от типа
        if payment_type == "one_time":
            # Единоразовая покупка пакета энергии
            from backend.routers.payments import GENERATION_PACKS
            pack = next((p for p in GENERATION_PACKS if p["id"] == product), None)
            
            if pack:
                # Начисляем энергию
                updated = await update_user_balance(telegram_id, pack["energy"])
                logger.info(f"Energy added: {pack['energy']} for user {telegram_id}")
                new_balance = updated.get("balance", 0) if updated else pack["energy"]
                notifications = get_notification_service()
                await notifications.notify_pack_purchase_success(
                    telegram_id=telegram_id,
                    energy_amount=pack["energy"],
                    new_balance=new_balance
                )

        elif payment_type == "subscription":
            # Первый платеж по подписке
            subscription_service = get_subscription_service()
            
            if token:
                # Сохраняем токен и активируем подписку
                await subscription_service.create_subscription(
                    telegram_id=telegram_id,
                    plan=product,
                    token=token,
                    discount_percent=0
                )
                logger.info(f"Subscription created: {product} for user {telegram_id}")
                
                # TODO: Отправить уведомление в Telegram
            else:
                logger.warning(f"No token received for subscription payment: {invoice_id}")
        
        return {"code": 0}
        
    except Exception as e:
        logger.error(f"Error in pay webhook: {e}", exc_info=True)
        return {"code": 0}  # Возвращаем успех, чтобы избежать повторных попыток


@router.post("/fail")
async def webhook_fail(
    request: Request,
    content_hmac: Optional[str] = Header(None, alias="Content-HMAC")
):
    """
    Fail notification - неудачная оплата
    https://developers.cloudpayments.ru/#fail
    """
    data_str, data = await _parse_webhook_data(request)
    
    # Проверяем подпись
    if not verify_signature(data_str, content_hmac):
        logger.warning("Invalid signature in fail webhook")
        return {"code": 0}
    
    try:
        account_id = data.get("AccountId")
        invoice_id = data.get("InvoiceId")
        reason = data.get("Reason", "Unknown error")
        
        logger.info(f"Fail webhook: account={account_id}, invoice={invoice_id}, reason={reason}")
        
        # Обновляем статус платежа
        await update_payment_status(
            payment_id=invoice_id,
            status="failed",
            error_message=reason
        )
        notifications = get_notification_service()
        await notifications.notify_payment_failed(telegram_id=int(account_id), reason=reason)

        return {"code": 0}
        
    except Exception as e:
        logger.error(f"Error in fail webhook: {e}", exc_info=True)
        return {"code": 0}


@router.post("/recurrent")
async def webhook_recurrent(
    request: Request,
    content_hmac: Optional[str] = Header(None, alias="Content-HMAC")
):
    """
    Recurrent notification - рекуррентный платёж
    Вызывается при автоматическом списании по подписке
    https://developers.cloudpayments.ru/#recurrent
    """
    data_str, data = await _parse_webhook_data(request)
    
    # Проверяем подпись
    if not verify_signature(data_str, content_hmac):
        logger.warning("Invalid signature in recurrent webhook")
        return {"code": 0}
    
    try:
        account_id = data.get("AccountId")
        transaction_id = data.get("TransactionId")
        amount = data.get("Amount")
        success = data.get("Success", False)
        reason = data.get("Reason")
        
        logger.info(f"Recurrent webhook: account={account_id}, transaction={transaction_id}, success={success}")
        
        telegram_id = int(account_id)
        subscription_service = get_subscription_service()
        
        if success:
            # Успешное продление
            await subscription_service.renew_subscription(
                telegram_id=telegram_id,
                transaction_id=transaction_id
            )
            logger.info(f"Subscription renewed for user {telegram_id}")
            
            # TODO: Отправить уведомление в Telegram
        else:
            # Неудачное списание - переводим в grace
            await subscription_service.handle_payment_failure(
                telegram_id=telegram_id,
                error_message=reason or "Payment failed"
            )
            logger.warning(f"Subscription payment failed for user {telegram_id}: {reason}")
            
            # TODO: Отправить уведомление в Telegram
        
        return {"code": 0}
        
    except Exception as e:
        logger.error(f"Error in recurrent webhook: {e}", exc_info=True)
        return {"code": 0}


@router.post("/refund")
async def webhook_refund(
    request: Request,
    content_hmac: Optional[str] = Header(None, alias="Content-HMAC")
):
    """
    Refund notification - возврат
    https://developers.cloudpayments.ru/#refund
    """
    data_str, data = await _parse_webhook_data(request)
    
    # Проверяем подпись
    if not verify_signature(data_str, content_hmac):
        logger.warning("Invalid signature in refund webhook")
        return {"code": 0}
    
    try:
        account_id = data.get("AccountId")
        invoice_id = data.get("InvoiceId")
        amount = data.get("Amount")
        
        logger.info(f"Refund webhook: account={account_id}, invoice={invoice_id}, amount={amount}")
        
        # Обновляем статус платежа
        await update_payment_status(
            payment_id=invoice_id,
            status="refunded"
        )
        
        # Получаем информацию о платеже
        payment = await get_payment(invoice_id)
        if payment:
            telegram_id = int(payment.get("user_id"))
            payment_type = payment.get("type")
            product = payment.get("product")
            
            # Списываем энергию обратно
            if payment_type == "one_time":
                from backend.routers.payments import GENERATION_PACKS
                pack = next((p for p in GENERATION_PACKS if p["id"] == product), None)
                
                if pack:
                    # Списываем энергию (отрицательное значение)
                    await update_user_balance(telegram_id, -pack["energy"])
                    logger.info(f"Energy deducted after refund: {pack['energy']} for user {telegram_id}")
            notifications = get_notification_service()
            await notifications.notify_refund(telegram_id=telegram_id, amount=amount)

        return {"code": 0}

    except Exception as e:
        logger.error(f"Error in refund webhook: {e}", exc_info=True)
        return {"code": 0}
