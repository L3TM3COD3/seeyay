"""
Subscription Service - управление подписками и retry логикой
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

from backend.firestore import (
    get_user,
    update_subscription,
    update_user_balance,
    update_user_plan,
    get_users_for_retry,
    get_expired_grace_users,
    get_suspended_users_for_expiry,
)
from backend.services.cloudpayments import get_cloudpayments_client, create_receipt, create_receipt_item

logger = logging.getLogger(__name__)


# Тарифные планы
PLANS = {
    "free": {"name": "Free", "energy": 1, "price": 0, "period_days": 1},
    "basic": {"name": "Basic", "energy": 30, "price": 499, "period_days": 30},
    "pro": {"name": "PRO", "energy": 150, "price": 1299, "period_days": 30},
}


class SubscriptionService:
    """Service for managing subscriptions"""
    
    def __init__(self):
        self.cp_client = get_cloudpayments_client()
    
    async def create_subscription(
        self,
        telegram_id: int,
        plan: str,
        token: str,
        discount_percent: int = 0
    ) -> Dict[str, Any]:
        """
        Создание новой подписки после успешного первого платежа
        """
        if plan not in PLANS or plan == "free":
            raise ValueError(f"Invalid plan: {plan}")
        
        plan_info = PLANS[plan]
        energy = plan_info["energy"]
        
        # Начисляем энергию
        await update_user_balance(telegram_id, energy)
        
        # Создаем данные подписки
        subscription_data = {
            "status": "active",
            "plan": plan,
            "token": token,
            "started_at": datetime.utcnow(),
            "next_billing_at": datetime.utcnow() + timedelta(days=plan_info["period_days"]),
            "grace_ends_at": None,
            "retry_count": 0,
            "last_retry_at": None,
            "canceled_at": None,
            "discount_percent": discount_percent,
        }
        
        # Обновляем план пользователя
        await update_user_plan(telegram_id, plan)
        
        # Сохраняем подписку
        result = await update_subscription(telegram_id, subscription_data)
        
        logger.info(f"Subscription created for user {telegram_id}, plan: {plan}")
        return result
    
    async def renew_subscription(
        self,
        telegram_id: int,
        transaction_id: int
    ) -> Dict[str, Any]:
        """
        Продление подписки после успешного рекуррентного платежа
        """
        user = await get_user(telegram_id)
        if not user:
            raise ValueError(f"User {telegram_id} not found")
        
        subscription = user.get("subscription")
        if not subscription:
            raise ValueError(f"No subscription found for user {telegram_id}")
        
        plan = subscription["plan"]
        if plan not in PLANS or plan == "free":
            raise ValueError(f"Invalid plan: {plan}")
        
        plan_info = PLANS[plan]
        energy = plan_info["energy"]
        
        # Начисляем энергию
        await update_user_balance(telegram_id, energy)
        
        # Обновляем подписку
        subscription_data = {
            **subscription,
            "status": "active",
            "next_billing_at": datetime.utcnow() + timedelta(days=plan_info["period_days"]),
            "grace_ends_at": None,
            "retry_count": 0,
            "last_retry_at": None,
        }
        
        result = await update_subscription(telegram_id, subscription_data)
        
        logger.info(f"Subscription renewed for user {telegram_id}, plan: {plan}")
        return result
    
    async def handle_payment_failure(
        self,
        telegram_id: int,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Обработка неудачного рекуррентного платежа - переход в grace период
        """
        user = await get_user(telegram_id)
        if not user:
            raise ValueError(f"User {telegram_id} not found")
        
        subscription = user.get("subscription")
        if not subscription:
            raise ValueError(f"No subscription found for user {telegram_id}")
        
        # Переводим в grace на 72 часа
        subscription_data = {
            **subscription,
            "status": "grace",
            "grace_ends_at": datetime.utcnow() + timedelta(hours=72),
            "retry_count": 0,
            "last_retry_at": None,
        }
        
        result = await update_subscription(telegram_id, subscription_data)
        
        logger.warning(f"Subscription payment failed for user {telegram_id}: {error_message}")
        return result
    
    async def retry_payment(
        self,
        telegram_id: int,
    ) -> bool:
        """
        Попытка повторной оплаты для подписки в grace статусе
        """
        user = await get_user(telegram_id)
        if not user:
            logger.error(f"User {telegram_id} not found for retry")
            return False
        
        subscription = user.get("subscription")
        if not subscription or subscription["status"] != "grace":
            logger.warning(f"User {telegram_id} not in grace status")
            return False
        
        plan = subscription["plan"]
        token = subscription.get("token")
        
        if not token:
            logger.error(f"No token found for user {telegram_id}")
            return False
        
        plan_info = PLANS.get(plan)
        if not plan_info:
            logger.error(f"Invalid plan {plan} for user {telegram_id}")
            return False
        
        # Применяем скидку, если есть
        discount = subscription.get("discount_percent", 0)
        amount = plan_info["price"] * (1 - discount / 100)
        
        try:
            # Создаем чек
            receipt_items = [
                create_receipt_item(
                    label=f"Подписка {plan_info['name']}",
                    price=amount,
                    quantity=1.0,
                    vat=0,
                    object_type=4  # услуга
                )
            ]
            receipt = create_receipt(
                items=receipt_items,
                email=user.get("username", f"{telegram_id}@telegram.user"),
                taxation_system=1
            )
            
            # Попытка списания
            result = await self.cp_client.charge_token(
                amount=amount,
                currency="RUB",
                account_id=str(telegram_id),
                token=token,
                description=f"Продление подписки {plan_info['name']}",
                invoice_id=f"renewal_{telegram_id}_{int(datetime.utcnow().timestamp())}",
                receipt=receipt
            )
            
            if result.get("Success"):
                # Успешная оплата - продлеваем подписку
                transaction_id = result["Model"]["TransactionId"]
                await self.renew_subscription(telegram_id, transaction_id)
                logger.info(f"Retry payment successful for user {telegram_id}")
                return True
            else:
                # Неудачная попытка - увеличиваем счетчик
                retry_count = subscription.get("retry_count", 0) + 1
                subscription_data = {
                    **subscription,
                    "retry_count": retry_count,
                    "last_retry_at": datetime.utcnow(),
                }
                await update_subscription(telegram_id, subscription_data)
                
                logger.warning(f"Retry payment failed for user {telegram_id}, attempt {retry_count}")
                return False
                
        except Exception as e:
            logger.error(f"Error retrying payment for user {telegram_id}: {e}")
            
            # Увеличиваем счетчик попыток
            retry_count = subscription.get("retry_count", 0) + 1
            subscription_data = {
                **subscription,
                "retry_count": retry_count,
                "last_retry_at": datetime.utcnow(),
            }
            await update_subscription(telegram_id, subscription_data)
            
            return False
    
    async def suspend_subscription(
        self,
        telegram_id: int
    ) -> Dict[str, Any]:
        """
        Перевод подписки в suspended статус после истечения grace периода
        """
        user = await get_user(telegram_id)
        if not user:
            raise ValueError(f"User {telegram_id} not found")
        
        subscription = user.get("subscription")
        if not subscription:
            raise ValueError(f"No subscription found for user {telegram_id}")
        
        # Переводим на free план, но сохраняем данные подписки для возможного восстановления
        await update_user_plan(telegram_id, "free", bonus_generations=0)
        
        # Сбрасываем баланс до 1 (free план)
        current_balance = user.get("balance", 0)
        if current_balance > 1:
            await update_user_balance(telegram_id, 1 - current_balance)
        
        subscription_data = {
            **subscription,
            "status": "suspended",
            "discount_percent": 25,  # Скидка для возврата
        }
        
        result = await update_subscription(telegram_id, subscription_data)
        
        logger.info(f"Subscription suspended for user {telegram_id}")
        return result
    
    async def expire_subscription(
        self,
        telegram_id: int
    ) -> Dict[str, Any]:
        """
        Перевод подписки в expired статус через 7 дней после suspended
        """
        user = await get_user(telegram_id)
        if not user:
            raise ValueError(f"User {telegram_id} not found")
        
        subscription = user.get("subscription")
        if not subscription:
            raise ValueError(f"No subscription found for user {telegram_id}")
        
        subscription_data = {
            **subscription,
            "status": "expired",
            "discount_percent": 25,  # Скидка для возврата
        }
        
        result = await update_subscription(telegram_id, subscription_data)
        
        logger.info(f"Subscription expired for user {telegram_id}")
        return result
    
    async def cancel_subscription(
        self,
        telegram_id: int
    ) -> Dict[str, Any]:
        """
        Отмена подписки пользователем
        """
        user = await get_user(telegram_id)
        if not user:
            raise ValueError(f"User {telegram_id} not found")
        
        subscription = user.get("subscription")
        if not subscription:
            raise ValueError(f"No subscription found for user {telegram_id}")
        
        # Переводим на free план, но оставляем неизрасходованную энергию
        await update_user_plan(telegram_id, "free", bonus_generations=0)
        
        subscription_data = {
            **subscription,
            "status": "canceled",
            "canceled_at": datetime.utcnow(),
            "discount_percent": 25,  # Скидка для возврата
        }
        
        result = await update_subscription(telegram_id, subscription_data)
        
        logger.info(f"Subscription canceled for user {telegram_id}")
        return result
    
    async def process_retry_queue(self) -> Dict[str, Any]:
        """
        Обработка очереди retry платежей (вызывается cron job'ом)
        """
        users = await get_users_for_retry()
        
        results = {
            "total": len(users),
            "successful": 0,
            "failed": 0,
        }
        
        for user in users:
            telegram_id = user["telegram_id"]
            success = await self.retry_payment(telegram_id)
            
            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"Retry queue processed: {results}")
        return results
    
    async def process_grace_expirations(self) -> Dict[str, Any]:
        """
        Обработка истечения grace периодов (вызывается cron job'ом)
        """
        users = await get_expired_grace_users()
        
        results = {
            "total": len(users),
            "suspended": 0,
        }
        
        for user in users:
            telegram_id = user["telegram_id"]
            try:
                await self.suspend_subscription(telegram_id)
                results["suspended"] += 1
            except Exception as e:
                logger.error(f"Error suspending subscription for user {telegram_id}: {e}")
        
        logger.info(f"Grace expirations processed: {results}")
        return results
    
    async def process_suspended_expirations(self) -> Dict[str, Any]:
        """
        Обработка истечения suspended периодов (вызывается cron job'ом)
        """
        users = await get_suspended_users_for_expiry()
        
        results = {
            "total": len(users),
            "expired": 0,
        }
        
        for user in users:
            telegram_id = user["telegram_id"]
            try:
                await self.expire_subscription(telegram_id)
                results["expired"] += 1
            except Exception as e:
                logger.error(f"Error expiring subscription for user {telegram_id}: {e}")
        
        logger.info(f"Suspended expirations processed: {results}")
        return results


# Singleton instance
_service: Optional[SubscriptionService] = None


def get_subscription_service() -> SubscriptionService:
    """Get subscription service instance"""
    global _service
    if _service is None:
        _service = SubscriptionService()
    return _service
