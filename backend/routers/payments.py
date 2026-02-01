from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.firestore import get_user, update_user_balance, update_user_plan

router = APIRouter(prefix="/api/payments", tags=["payments"])


# Пакеты генераций для покупки
GENERATION_PACKS = [
    {"id": "pack_10", "generations": 10, "price": 99, "currency": "RUB"},
    {"id": "pack_30", "generations": 30, "price": 249, "currency": "RUB"},
    {"id": "pack_100", "generations": 100, "price": 699, "currency": "RUB"},
]

# Тарифные планы
PLANS = {
    "free": {"name": "Free", "generations": 3, "price": 0},
    "basic": {"name": "Basic", "generations": 30, "price": 299},
    "pro": {"name": "Pro", "generations": 100, "price": 799},
}


class PurchaseRequest(BaseModel):
    telegram_id: int
    pack_id: str


class PlanUpgradeRequest(BaseModel):
    telegram_id: int
    plan: str


@router.get("/packs")
async def get_packs():
    """Получить список пакетов генераций"""
    return {"packs": GENERATION_PACKS}


@router.get("/plans")
async def get_plans():
    """Получить список тарифных планов"""
    return {"plans": PLANS}


@router.post("/purchase")
async def purchase_generations(request: PurchaseRequest):
    """
    Покупка пакета генераций
    В реальном приложении здесь будет интеграция с платёжной системой
    """
    # Находим пакет
    pack = next((p for p in GENERATION_PACKS if p["id"] == request.pack_id), None)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    
    # Проверяем пользователя
    user = await get_user(request.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # TODO: Здесь должна быть интеграция с платёжной системой
    # Для демо просто добавляем генерации
    
    updated_user = await update_user_balance(request.telegram_id, pack["generations"])
    
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to update balance")
    
    return {
        "success": True,
        "message": f"Добавлено {pack['generations']} генераций",
        "new_balance": updated_user["balance"]
    }


@router.post("/upgrade")
async def upgrade_plan(request: PlanUpgradeRequest):
    """
    Смена тарифного плана
    В реальном приложении здесь будет интеграция с платёжной системой
    """
    if request.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    user = await get_user(request.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # TODO: Здесь должна быть интеграция с платёжной системой
    
    plan_info = PLANS[request.plan]
    updated_user = await update_user_plan(
        request.telegram_id, 
        request.plan,
        bonus_generations=plan_info["generations"]
    )
    
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to update plan")
    
    return {
        "success": True,
        "message": f"Тариф изменён на {plan_info['name']}",
        "new_plan": updated_user["plan"],
        "new_balance": updated_user["balance"]
    }
