from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.firestore import get_user, create_user, update_user_balance

router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None


class UserResponse(BaseModel):
    telegram_id: int
    username: Optional[str]
    plan: str
    balance: int


class BalanceUpdate(BaseModel):
    amount: int  # положительное для пополнения, отрицательное для списания


@router.get("/{telegram_id}", response_model=UserResponse)
async def get_user_endpoint(telegram_id: int):
    """Получить профиль пользователя"""
    user = await get_user(telegram_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        telegram_id=user["telegram_id"],
        username=user.get("username"),
        plan=user.get("plan", "free"),
        balance=user.get("balance", 0)
    )


@router.post("", response_model=UserResponse)
async def create_user_endpoint(user_data: UserCreate):
    """Создать нового пользователя"""
    user = await create_user(
        telegram_id=user_data.telegram_id,
        username=user_data.username
    )
    
    return UserResponse(
        telegram_id=user["telegram_id"],
        username=user.get("username"),
        plan=user.get("plan", "free"),
        balance=user.get("balance", 0)
    )


@router.patch("/{telegram_id}/balance", response_model=UserResponse)
async def update_balance_endpoint(telegram_id: int, balance_update: BalanceUpdate):
    """Обновить баланс пользователя"""
    user = await update_user_balance(telegram_id, balance_update.amount)
    
    if not user:
        raise HTTPException(
            status_code=400, 
            detail="User not found or insufficient balance"
        )
    
    return UserResponse(
        telegram_id=user["telegram_id"],
        username=user.get("username"),
        plan=user.get("plan", "free"),
        balance=user.get("balance", 0)
    )
