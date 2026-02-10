"""
Cron Router - endpoints для периодических задач (вызываются Cloud Scheduler)
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import logging

from backend.firestore import (
    get_free_plan_users_for_daily_energy, 
    give_daily_energy,
    get_users_for_delayed_messages
)
from backend.services.subscription import get_subscription_service
from backend.services.notifications import get_notification_service
from google.cloud import firestore
from backend.services.notifications import get_notification_service
from backend.secrets import get_secret
import os

router = APIRouter(prefix="/api/cron", tags=["cron"])
logger = logging.getLogger(__name__)


def verify_cron_auth(authorization: Optional[str]) -> bool:
    """
    Проверка, что запрос пришел от Cloud Scheduler
    В production нужно проверять токен или IP
    """
    # TODO: Добавить реальную проверку токена
    # Для начала просто проверяем наличие заголовка
    return authorization is not None


@router.post("/daily-energy")
async def daily_energy(authorization: Optional[str] = Header(None)):
    """
    Начисление ежедневной энергии пользователям на free плане
    Вызывается каждый день в 00:00 по МСК (21:00 UTC)
    """
    if not verify_cron_auth(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Получаем всех пользователей на free плане
        users = await get_free_plan_users_for_daily_energy()
        
        results = {
            "total": len(users),
            "processed": 0,
            "errors": 0
        }
        
        for user in users:
            try:
                telegram_id = user["telegram_id"]
                await give_daily_energy(telegram_id)
                results["processed"] += 1
                
            except Exception as e:
                logger.error(f"Error giving daily energy to user {user.get('telegram_id')}: {e}")
                results["errors"] += 1
        
        logger.info(f"Daily energy job completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in daily energy job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription-retry")
async def subscription_retry(authorization: Optional[str] = Header(None)):
    """
    Попытка повторной оплаты для подписок в grace статусе
    Вызывается каждые 30 минут
    """
    if not verify_cron_auth(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        subscription_service = get_subscription_service()
        results = await subscription_service.process_retry_queue()
        
        logger.info(f"Subscription retry job completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in subscription retry job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscription-status")
async def subscription_status(authorization: Optional[str] = Header(None)):
    """
    Обработка переходов статусов подписок:
    - GRACE -> SUSPENDED (после истечения 72 часов)
    - SUSPENDED -> EXPIRED (после 7 дней)
    Вызывается каждый час
    """
    if not verify_cron_auth(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        subscription_service = get_subscription_service()
        
        # Обрабатываем истечения grace периодов
        grace_results = await subscription_service.process_grace_expirations()
        
        # Обрабатываем истечения suspended периодов
        suspended_results = await subscription_service.process_suspended_expirations()
        
        results = {
            "grace_expirations": grace_results,
            "suspended_expirations": suspended_results
        }
        
        logger.info(f"Subscription status job completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in subscription status job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delayed-messages")
async def delayed_messages(authorization: Optional[str] = Header(None)):
    """
    Отправка отложенных (delayed) сообщений пользователям (Plan 2)
    - m2: через 1ч после /start (если нет генераций)
    - m5: через 7 мин после выбора шаблона (если не прислал фото)
    - m10.1: через 60 мин после 1-й генерации
    - m10.2: через 60 мин после 2-й генерации
    - m12: через 24ч после m9 (если не купил пакеты)
    Вызывается каждые 2 минуты
    """
    if not verify_cron_auth(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Получаем пользователей для всех типов сообщений
        users_by_type = await get_users_for_delayed_messages()
        
        notification_service = get_notification_service()
        db = firestore.AsyncClient()
        
        # Определяем Mini App URL из переменной окружения
        mini_app_url = os.getenv("MINI_APP_URL", "https://seeyay-miniapp-445810320877.europe-west4.run.app")
        
        results = {
            "m2": {"total": len(users_by_type["m2"]), "sent": 0, "errors": 0},
            "m5": {"total": len(users_by_type["m5"]), "sent": 0, "errors": 0},
            "m10_1": {"total": len(users_by_type["m10_1"]), "sent": 0, "errors": 0},
            "m10_2": {"total": len(users_by_type["m10_2"]), "sent": 0, "errors": 0},
            "m12": {"total": len(users_by_type["m12"]), "sent": 0, "errors": 0}
        }
        
        # Отправляем m2
        for user in users_by_type["m2"]:
            try:
                telegram_id = user["telegram_id"]
                success = await notification_service.send_m2_reminder(telegram_id, mini_app_url)
                if success:
                    await db.collection("users").document(str(telegram_id)).update({"m2_sent": True})
                    results["m2"]["sent"] += 1
                else:
                    results["m2"]["errors"] += 1
            except Exception as e:
                logger.error(f"Error sending m2 to user {user.get('telegram_id')}: {e}")
                results["m2"]["errors"] += 1
        
        # Отправляем m5
        for user in users_by_type["m5"]:
            try:
                telegram_id = user["telegram_id"]
                success = await notification_service.send_m5_photo_reminder(telegram_id)
                if success:
                    await db.collection("users").document(str(telegram_id)).update({"m5_sent": True})
                    results["m5"]["sent"] += 1
                else:
                    results["m5"]["errors"] += 1
            except Exception as e:
                logger.error(f"Error sending m5 to user {user.get('telegram_id')}: {e}")
                results["m5"]["errors"] += 1
        
        # Отправляем m10.1
        for user in users_by_type["m10_1"]:
            try:
                telegram_id = user["telegram_id"]
                success = await notification_service.send_m10_1_tips(telegram_id, mini_app_url)
                if success:
                    await db.collection("users").document(str(telegram_id)).update({"m10_1_sent": True})
                    results["m10_1"]["sent"] += 1
                else:
                    results["m10_1"]["errors"] += 1
            except Exception as e:
                logger.error(f"Error sending m10.1 to user {user.get('telegram_id')}: {e}")
                results["m10_1"]["errors"] += 1
        
        # Отправляем m10.2
        for user in users_by_type["m10_2"]:
            try:
                telegram_id = user["telegram_id"]
                success = await notification_service.send_m10_2_pro_suggestion(telegram_id, mini_app_url)
                if success:
                    await db.collection("users").document(str(telegram_id)).update({"m10_2_sent": True})
                    results["m10_2"]["sent"] += 1
                else:
                    results["m10_2"]["errors"] += 1
            except Exception as e:
                logger.error(f"Error sending m10.2 to user {user.get('telegram_id')}: {e}")
                results["m10_2"]["errors"] += 1
        
        # Отправляем m12
        for user in users_by_type["m12"]:
            try:
                telegram_id = user["telegram_id"]
                success = await notification_service.send_m12_downsell(telegram_id)
                if success:
                    await db.collection("users").document(str(telegram_id)).update({"m12_sent": True})
                    results["m12"]["sent"] += 1
                else:
                    results["m12"]["errors"] += 1
            except Exception as e:
                logger.error(f"Error sending m12 to user {user.get('telegram_id')}: {e}")
                results["m12"]["errors"] += 1
        
        logger.info(f"Delayed messages job completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in delayed messages job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
