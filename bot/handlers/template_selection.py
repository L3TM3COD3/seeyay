from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import json
import logging

from bot.keyboards import (
    kb_config_onboarding, 
    kb_config_normal, 
    kb_config_pro,
    kb_template_grid
)
from bot.messages import (
    m3_config_onboarding,
    m4_1_config_normal,
    m4_2_config_pro
)
from bot.states import UserState
from bot.styles_data import get_style_by_id
from bot.firestore import get_user, set_user_timestamp
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("tpl:"))
async def handle_template_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора шаблона по кнопке"""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    style_id = callback.data.split(":", 1)[1]
    
    # Проверка на placeholder
    if style_id == "placeholder":
        await callback.message.answer("Этот шаблон скоро появится! 🎨")
        return
    
    # Получаем стиль
    style = get_style_by_id(style_id)
    if not style:
        await callback.message.answer("❌ Шаблон не найден")
        logger.error(f"Style not found: {style_id}")
        return
    
    style_name = style["name"]
    
    # Получаем пользователя
    user = await get_user(telegram_id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден. Используйте /start")
        return
    
    successful_generations = user.get("successful_generations", 0)
    
    # Сохраняем данные в FSM
    await state.update_data(
        style_id=style_id,
        style_name=style_name,
        mode="normal"
    )
    await state.set_state(UserState.awaiting_photo)
    
    # Записываем timestamp выбора шаблона (Plan 2)
    await set_user_timestamp(telegram_id, "template_selected_at", datetime.utcnow())
    
    # Определяем какое сообщение отправить
    if successful_generations == 0:
        # m3: onboarding конфигурация
        text = m3_config_onboarding(style_name, 1)
        keyboard = kb_config_onboarding(style_id)
    else:
        # m4.1: обычная конфигурация
        text = m4_1_config_normal(style_name, 1)
        keyboard = kb_config_normal(style_id)
    
    # Plan 2: Если у стиля есть cover_image, отправляем фото, иначе текст
    cover_image = style.get("cover_image")
    if cover_image:
        await callback.message.answer_photo(
            photo=cover_image,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    logger.info(f"User {telegram_id} selected template {style_id} (gens: {successful_generations})")


@router.callback_query(F.data.startswith("toggle_pro:"))
async def handle_toggle_pro(callback: CallbackQuery, state: FSMContext):
    """Переключение на PRO режим"""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    style_id = callback.data.split(":", 1)[1]
    
    # Получаем стиль
    style = get_style_by_id(style_id)
    if not style:
        await callback.message.answer("❌ Шаблон не найден")
        return
    
    style_name = style["name"]
    
    # Обновляем FSM - переключаем на PRO
    await state.update_data(
        style_id=style_id,
        style_name=style_name,
        mode="pro"
    )
    await state.set_state(UserState.awaiting_photo)
    
    # Отправляем m4.2
    text = m4_2_config_pro(style_name, 6)
    keyboard = kb_config_pro(style_id)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    logger.info(f"User {telegram_id} toggled to PRO mode for {style_id}")


@router.callback_query(F.data.startswith("toggle_normal:"))
async def handle_toggle_normal(callback: CallbackQuery, state: FSMContext):
    """Переключение на обычный режим"""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    style_id = callback.data.split(":", 1)[1]
    
    # Получаем стиль
    style = get_style_by_id(style_id)
    if not style:
        await callback.message.answer("❌ Шаблон не найден")
        return
    
    style_name = style["name"]
    
    # Обновляем FSM - переключаем на normal
    await state.update_data(
        style_id=style_id,
        style_name=style_name,
        mode="normal"
    )
    await state.set_state(UserState.awaiting_photo)
    
    # Отправляем m4.1
    text = m4_1_config_normal(style_name, 1)
    keyboard = kb_config_normal(style_id)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    logger.info(f"User {telegram_id} toggled to normal mode for {style_id}")


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext):
    """Обработчик данных из Mini App"""
    try:
        data = json.loads(message.web_app_data.data)
        
        telegram_id = message.from_user.id
        style_id = data.get("style_id")
        style_name = data.get("style_name")
        mode = data.get("mode", "normal")
        
        logger.info(f"Received webapp data: user={telegram_id}, style={style_id}, mode={mode}")
        
        # Получаем пользователя
        user = await get_user(telegram_id)
        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return
        
        successful_generations = user.get("successful_generations", 0)
        
        # Сохраняем данные в состояние
        await state.update_data(
            style_id=style_id,
            style_name=style_name,
            mode=mode
        )
        await state.set_state(UserState.awaiting_photo)
        
        # Записываем timestamp выбора шаблона (Plan 2)
        await set_user_timestamp(telegram_id, "template_selected_at", datetime.utcnow())
        
        # Определяем стоимость
        cost = 6 if mode == "pro" else 1
        
        # Определяем какое сообщение отправить
        if successful_generations == 0:
            # m3: onboarding
            text = m3_config_onboarding(style_name, cost)
            keyboard = kb_config_onboarding(style_id)
        elif mode == "pro":
            # m4.2: PRO конфигурация
            text = m4_2_config_pro(style_name, cost)
            keyboard = kb_config_pro(style_id)
        else:
            # m4.1: обычная конфигурация
            text = m4_1_config_normal(style_name, cost)
            keyboard = kb_config_normal(style_id)
        
        # Plan 2: Получаем стиль для проверки cover_image
        from bot.styles_data import get_style_by_id
        style = get_style_by_id(style_id)
        cover_image = style.get("cover_image") if style else None
        
        if cover_image:
            await message.answer_photo(
                photo=cover_image,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
    except json.JSONDecodeError:
        logger.error("Failed to decode webapp data")
        await message.answer("❌ Ошибка обработки данных. Попробуйте ещё раз.")
    except Exception as e:
        logger.error(f"Error in webapp handler: {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
