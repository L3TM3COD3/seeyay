"""
Payments Router - платежи и подписки через CloudPayments
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from backend.firestore import (
    get_user,
    update_user_balance,
    update_user_plan,
    create_payment,
    update_subscription,
)
from backend.services.cloudpayments import (
    get_cloudpayments_client,
    create_receipt,
    create_receipt_item,
)
from backend.services.subscription import get_subscription_service, PLANS

router = APIRouter(prefix="/api/payments", tags=["payments"])
logger = logging.getLogger(__name__)


# Пакеты генераций для покупки
GENERATION_PACKS = [
    {"id": "pack_10", "energy": 10, "price": 249, "currency": "RUB"},
    {"id": "pack_50", "energy": 50, "price": 790, "currency": "RUB", "badge": "популярно"},
    {"id": "pack_120", "energy": 120, "price": 1290, "currency": "RUB", "badge": "выгодно"},
    {"id": "pack_300", "energy": 300, "price": 2490, "currency": "RUB"},
]


# ==================== Models ====================

class PackPurchaseRequest(BaseModel):
    telegram_id: int
    pack_id: str


class SubscriptionRequest(BaseModel):
    telegram_id: int
    plan: str


class CancelSubscriptionRequest(BaseModel):
    telegram_id: int


class SBPPaymentRequest(BaseModel):
    telegram_id: int
    product_type: str  # "pack" or "subscription"
    product_id: str


# ==================== Endpoints ====================

@router.get("/packs")
async def get_packs():
    """Получить список пакетов энергии"""
    return {"packs": GENERATION_PACKS}


@router.get("/plans")
async def get_plans():
    """Получить список тарифных планов"""
    return {"plans": PLANS}


@router.post("/create-pack-payment")
async def create_pack_payment(request: PackPurchaseRequest):
    """
    Инициация оплаты пакета энергии
    Возвращает параметры для CloudPayments виджета
    """
    # Находим пакет
    pack = next((p for p in GENERATION_PACKS if p["id"] == request.pack_id), None)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    
    # Проверяем пользователя
    user = await get_user(request.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Создаем запись платежа
    payment = await create_payment(
        user_id=str(request.telegram_id),
        payment_type="one_time",
        product=request.pack_id,
        amount=pack["price"],
        currency=pack["currency"],
        payment_method="card"
    )
    
    # Создаем чек для онлайн-кассы
    receipt_items = [
        create_receipt_item(
            label=f"Энергия {pack['energy']}⚡",
            price=pack["price"],
            quantity=1.0,
            vat=0,
            object_type=4  # услуга
        )
    ]
    receipt = create_receipt(
        items=receipt_items,
        email=user.get("username", f"{request.telegram_id}@telegram.user"),
        taxation_system=1
    )
    
    # Генерируем параметры для виджета
    cp_client = get_cloudpayments_client()
    widget_params = cp_client.generate_widget_params(
        amount=pack["price"],
        currency=pack["currency"],
        description=f"Покупка энергии {pack['energy']}⚡",
        invoice_id=payment["id"],
        account_id=str(request.telegram_id),
        email=user.get("username", f"{request.telegram_id}@telegram.user"),
        require_confirmation=False,
        receipt=receipt
    )
    
    logger.info(f"Pack payment created: {payment['id']}, user: {request.telegram_id}, pack: {request.pack_id}")
    
    return {
        "payment_id": payment["id"],
        "widget_params": widget_params
    }


@router.post("/create-subscription")
async def create_subscription(request: SubscriptionRequest):
    """
    Инициация подписки
    Возвращает параметры для CloudPayments виджета с рекуррентным токеном
    """
    if request.plan not in PLANS or request.plan == "free":
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    # Проверяем пользователя
    user = await get_user(request.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    plan_info = PLANS[request.plan]
    
    # Проверяем, есть ли у пользователя активная подписка с скидкой
    subscription = user.get("subscription", {})
    discount_percent = 0
    if subscription.get("status") in ["suspended", "expired", "canceled"]:
        discount_percent = subscription.get("discount_percent", 0)
    
    amount = plan_info["price"] * (1 - discount_percent / 100)
    
    # Создаем запись платежа
    payment = await create_payment(
        user_id=str(request.telegram_id),
        payment_type="subscription",
        product=request.plan,
        amount=amount,
        currency="RUB",
        payment_method="card"
    )
    
    # Создаем чек для онлайн-кассы
    discount_label = f" (скидка {discount_percent}%)" if discount_percent > 0 else ""
    receipt_items = [
        create_receipt_item(
            label=f"Подписка {plan_info['name']}{discount_label}",
            price=amount,
            quantity=1.0,
            vat=0,
            object_type=4  # услуга
        )
    ]
    receipt = create_receipt(
        items=receipt_items,
        email=user.get("username", f"{request.telegram_id}@telegram.user"),
        taxation_system=1
    )
    
    # Генерируем параметры для виджета с рекуррентным платежом
    cp_client = get_cloudpayments_client()
    widget_params = cp_client.generate_widget_params(
        amount=amount,
        currency="RUB",
        description=f"Подписка {plan_info['name']}",
        invoice_id=payment["id"],
        account_id=str(request.telegram_id),
        email=user.get("username", f"{request.telegram_id}@telegram.user"),
        require_confirmation=False,
        receipt=receipt
    )
    
    # Добавляем флаг рекуррентного платежа
    widget_params["data"] = widget_params.get("data", {})
    widget_params["data"]["cloudPayments"] = {
        "recurrent": {"interval": "Month", "period": 1}
    }
    
    logger.info(f"Subscription payment created: {payment['id']}, user: {request.telegram_id}, plan: {request.plan}")
    
    return {
        "payment_id": payment["id"],
        "widget_params": widget_params,
        "discount_applied": discount_percent
    }


@router.post("/sbp/create")
async def create_sbp_payment(request: SBPPaymentRequest):
    """
    Получение СБП ссылки/QR для оплаты
    """
    user = await get_user(request.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Определяем продукт и сумму
    if request.product_type == "pack":
        pack = next((p for p in GENERATION_PACKS if p["id"] == request.product_id), None)
        if not pack:
            raise HTTPException(status_code=404, detail="Pack not found")
        
        amount = pack["price"]
        description = f"Покупка энергии {pack['energy']}⚡"
        label = f"Энергия {pack['energy']}⚡"
        
    elif request.product_type == "subscription":
        if request.product_id not in PLANS or request.product_id == "free":
            raise HTTPException(status_code=400, detail="Invalid plan")
        
        plan_info = PLANS[request.product_id]
        
        # Проверяем скидку
        subscription = user.get("subscription", {})
        discount_percent = 0
        if subscription.get("status") in ["suspended", "expired", "canceled"]:
            discount_percent = subscription.get("discount_percent", 0)
        
        amount = plan_info["price"] * (1 - discount_percent / 100)
        discount_label = f" (скидка {discount_percent}%)" if discount_percent > 0 else ""
        description = f"Подписка {plan_info['name']}{discount_label}"
        label = f"Подписка {plan_info['name']}{discount_label}"
    else:
        raise HTTPException(status_code=400, detail="Invalid product type")
    
    # Создаем запись платежа
    payment = await create_payment(
        user_id=str(request.telegram_id),
        payment_type=request.product_type,
        product=request.product_id,
        amount=amount,
        currency="RUB",
        payment_method="sbp"
    )
    
    # Создаем чек для онлайн-кассы
    receipt_items = [
        create_receipt_item(
            label=label,
            price=amount,
            quantity=1.0,
            vat=0,
            object_type=4  # услуга
        )
    ]
    receipt = create_receipt(
        items=receipt_items,
        email=user.get("username", f"{request.telegram_id}@telegram.user"),
        taxation_system=1
    )
    
    # Получаем QR-код от CloudPayments
    cp_client = get_cloudpayments_client()
    try:
        result = await cp_client.create_sbp_qr(
            amount=amount,
            account_id=str(request.telegram_id),
            description=description,
            invoice_id=payment["id"],
            email=user.get("username", f"{request.telegram_id}@telegram.user"),
            receipt=receipt
        )
        
        qr_url = result.get("qrCodeUrl")
        deeplink = result.get("url")
        
        logger.info(f"SBP payment created: {payment['id']}, user: {request.telegram_id}, product: {request.product_id}")
        
        return {
            "payment_id": payment["id"],
            "qr_url": qr_url,
            "deeplink": deeplink
        }
        
    except Exception as e:
        logger.error(f"Error creating SBP payment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create SBP payment: {str(e)}")


@router.post("/cancel-subscription")
async def cancel_subscription(request: CancelSubscriptionRequest):
    """
    Отмена подписки пользователем
    """
    user = await get_user(request.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = user.get("subscription")
    if not subscription or subscription.get("status") not in ["active", "grace"]:
        raise HTTPException(status_code=400, detail="No active subscription to cancel")
    
    # Отменяем подписку через сервис
    subscription_service = get_subscription_service()
    try:
        await subscription_service.cancel_subscription(request.telegram_id)
        logger.info(f"Subscription canceled: user {request.telegram_id}")
        
        return {
            "success": True,
            "message": "Подписка отменена. Неизрасходованная энергия сохранена."
        }
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


@router.post("/resume-subscription")
async def resume_subscription(request: SubscriptionRequest):
    """
    Возобновление подписки (обычно с скидкой)
    Работает аналогично create-subscription
    """
    return await create_subscription(request)
