from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import logging

from backend.firestore import (
    get_user, 
    update_user_balance, 
    create_generation,
    update_generation_status,
    set_pending_style_selection,
    get_pending_style_selection,
    clear_pending_style_selection
)
from backend.styles_data import get_style_by_id
from backend.secrets import get_bot_token

router = APIRouter(prefix="/api/generate", tags=["generate"])
logger = logging.getLogger(__name__)


class StyleSelectionRequest(BaseModel):
    telegram_id: int
    style_id: str
    style_name: str
    photo_count: int = 1
    mode: str = "normal"  # normal or pro


class StyleSelectionResponse(BaseModel):
    success: bool
    message: str


@router.post("/select-style", response_model=StyleSelectionResponse)
async def select_style_endpoint(request: StyleSelectionRequest):
    """Обработка выбора стиля из Mini App - сохраняет выбор и отправляет сообщение пользователю"""
    logger.info(f"Style selection received: user={request.telegram_id}, style={request.style_id}")
    
    try:
        # Получаем токен бота
        bot_token = get_bot_token()
        if not bot_token:
            logger.error("Bot token not available")
            raise HTTPException(status_code=500, detail="Bot token not configured")
        
        # Сохраняем выбор стиля в Firestore (для использования при получении фото)
        await set_pending_style_selection(
            telegram_id=request.telegram_id,
            style_id=request.style_id,
            style_name=request.style_name,
            photo_count=request.photo_count,
            mode=request.mode
        )
        
        # Формируем сообщение
        cost = request.photo_count if request.mode == "normal" else request.photo_count * 2
        mode_text = "PRO" if request.mode == "pro" else "Обычный"
        
        message_text = (
            f"✨ Отлично! Ты выбрал стиль: <b>{request.style_name}</b>\n\n"
            f"📊 Настройки:\n"
            f"• Количество фото: {request.photo_count}\n"
            f"• Режим: {mode_text}\n"
            f"• Стоимость: {cost} генераций\n\n"
            f"📷 Теперь отправь мне свою фотографию, и я создам для тебя потрясающий результат!"
        )
        
        # Кнопки
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔄 Выбрать другой стиль", "web_app": {"url": os.environ.get("MINI_APP_URL", "https://seeyay-miniapp-445810320877.europe-west4.run.app")}}],
                [{"text": "❌ Отменить", "callback_data": "cancel"}]
            ]
        }
        
        # Отправляем сообщение через Telegram API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": request.telegram_id,
                    "text": message_text,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail=f"Failed to send message: {response.text}")
        
        return StyleSelectionResponse(success=True, message="Style selected successfully")
        
    except Exception as e:
        logger.error(f"Error in select_style_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class GenerationRequest(BaseModel):
    telegram_id: int
    style_id: str
    photo_count: int = 1
    mode: str = "normal"  # normal or pro


class GenerationResponse(BaseModel):
    success: bool
    generation_id: Optional[str] = None
    message: str
    remaining_balance: Optional[int] = None


@router.post("", response_model=GenerationResponse)
async def create_generation_endpoint(request: GenerationRequest):
    """Создать запрос на генерацию"""
    
    # Проверяем стиль
    style = get_style_by_id(request.style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    
    # Получаем пользователя
    user = await get_user(request.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Рассчитываем стоимость
    cost = request.photo_count if request.mode == "normal" else request.photo_count * 2
    
    # Проверяем баланс
    if user.get("balance", 0) < cost:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. Required: {cost}, available: {user.get('balance', 0)}"
        )
    
    # Списываем с баланса
    updated_user = await update_user_balance(request.telegram_id, -cost)
    if not updated_user:
        raise HTTPException(status_code=400, detail="Failed to deduct balance")
    
    # Создаём запись о генерации
    generation = await create_generation(
        telegram_id=request.telegram_id,
        style_id=request.style_id,
        mode=request.mode,
        photo_count=request.photo_count
    )
    
    return GenerationResponse(
        success=True,
        generation_id=generation["id"],
        message=f"Generation started. {cost} credits deducted.",
        remaining_balance=updated_user["balance"]
    )


@router.patch("/{generation_id}/status")
async def update_generation_status_endpoint(generation_id: str, status: str):
    """Обновить статус генерации"""
    success = await update_generation_status(generation_id, status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    return {"success": True, "status": status}
