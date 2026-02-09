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
    set_pending_style_selection
)
from backend.styles_data import get_style_by_id
from backend.secrets import get_bot_token

router = APIRouter(prefix="/api/generate", tags=["generate"])
logger = logging.getLogger(__name__)


class StyleSelectionRequest(BaseModel):
    telegram_id: int
    style_id: str
    style_name: str
    mode: str = "normal"  # normal or pro


class StyleSelectionResponse(BaseModel):
    success: bool
    message: str


@router.post("/select-style", response_model=StyleSelectionResponse)
async def select_style_endpoint(request: StyleSelectionRequest):
    """
    Обработка выбора стиля из Mini App - сохраняет выбор и отправляет конфигурационное сообщение.
    """
    logger.info(f"Style selection received: user={request.telegram_id}, style={request.style_id}")
    
    try:
        # Получаем токен бота
        bot_token = get_bot_token()
        if not bot_token:
            logger.error("Bot token not available")
            raise HTTPException(status_code=500, detail="Bot token not configured")
        
        # Получаем пользователя для определения типа сообщения
        user = await get_user(request.telegram_id)
        if not user:
            logger.error(f"User not found: {request.telegram_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        successful_generations = user.get("successful_generations", 0)
        cost = 1 if request.mode == "normal" else 6
        
        # Определяем текст сообщения
        if successful_generations == 0:
            # m3: Конфигурация для новичка
            message_text = (
                f"<b>Выбран шаблон: {request.style_name}</b>\n\n"
                f"Стоимость: {cost}<b>⚡️</b>\n\n"
                f"<i>Для лучшей генерации:</i> сделай селфи с ровным светом, без фильтров\n\n"
                f"📸 Пришли фото хорошего качества"
            )
        elif request.mode == "pro":
            # m4.2: PRO конфигурация
            message_text = (
                f"<b>Выбран шаблон: {request.style_name}</b>\n\n"
                f"Режим: 💎 PRO\n"
                f"Стоимость: {cost}<b>⚡️</b>\n\n"
                f"<i>Для лучшей генерации:</i> сделай селфи с ровным светом, без фильтров\n\n"
                f"📸 Пришли фото хорошего качества"
            )
        else:
            # m4.1: Обычная конфигурация
            message_text = (
                f"<b>Выбран шаблон: {request.style_name}</b>\n\n"
                f"Режим: обычный\n"
                f"Стоимость: {cost}<b>⚡️</b>\n\n"
                f"<i>Для лучшей генерации:</i> используй PRO-режим (больше деталей и качества), сделай селфи с ровным светом, без фильтров\n\n"
                f"📸 Пришли фото хорошего качества"
            )
        
        # Получаем Mini App URL из переменных окружения
        mini_app_url = os.environ.get("MINI_APP_URL", "https://seeyay-miniapp-445810320877.europe-west4.run.app")
        
        # Формируем клавиатуру (зависит от режима и опыта пользователя)
        if successful_generations == 0:
            # Для новичков - только кнопка смены шаблона
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🎭 Сменить шаблон", "web_app": {"url": mini_app_url}}]
                ]
            }
        elif request.mode == "pro":
            # PRO режим - кнопка переключения на обычный + смена шаблона
            keyboard = {
                "inline_keyboard": [
                    [{"text": "Использовать обычный режим", "callback_data": f"toggle_normal:{request.style_id}"}],
                    [{"text": "🎭 Сменить шаблон", "web_app": {"url": mini_app_url}}]
                ]
            }
        else:
            # Обычный режим - кнопка переключения на PRO + смена шаблона
            keyboard = {
                "inline_keyboard": [
                    [{"text": "💎 Использовать PRO-режим", "callback_data": f"toggle_pro:{request.style_id}"}],
                    [{"text": "🎭 Сменить шаблон", "web_app": {"url": mini_app_url}}]
                ]
            }
        
        # Сохраняем выбор стиля в Firestore (для fallback при получении фото)
        await set_pending_style_selection(
            telegram_id=request.telegram_id,
            style_id=request.style_id,
            style_name=request.style_name,
            mode=request.mode
        )
        
        logger.info(f"Style selection saved to Firestore: {request.telegram_id} -> {request.style_id}")
        
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
        
        logger.info(f"Configuration message sent to user {request.telegram_id}")
        
        return StyleSelectionResponse(success=True, message="Style selected successfully")
        
    except Exception as e:
        logger.error(f"Error in select_style_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class GenerationRequest(BaseModel):
    telegram_id: int
    style_id: str
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
    
    # Рассчитываем стоимость (1 фото: normal = 1⚡, pro = 2⚡)
    cost = 1 if request.mode == "normal" else 2
    
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
        mode=request.mode
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
