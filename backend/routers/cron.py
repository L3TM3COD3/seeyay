"""
Cron Router - endpoints для периодических задач (вызываются Cloud Scheduler)
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import logging

from backend.firestore import get_free_plan_users_for_daily_energy, give_daily_energy
from backend.services.subscription import get_subscription_service

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
