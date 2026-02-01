from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import json
import logging

from bot.keyboards import get_photo_request_keyboard
from bot.states import UserState

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext):
    """Обработчик данных из Mini App"""
    try:
        data = json.loads(message.web_app_data.data)
        
        style_id = data.get("style_id")
        style_name = data.get("style_name")
        photo_count = data.get("photo_count", 1)
        mode = data.get("mode", "normal")  # normal или pro
        
        logger.info(f"Received webapp data: style={style_id}, count={photo_count}, mode={mode}")
        
        # Сохраняем данные в состояние
        await state.update_data(
            style_id=style_id,
            style_name=style_name,
            photo_count=photo_count,
            mode=mode
        )
        
        # Переводим в состояние ожидания фото
        await state.set_state(UserState.awaiting_photo)
        
        # Формируем сообщение о стоимости
        cost = photo_count if mode == "normal" else photo_count * 2
        mode_text = "PRO" if mode == "pro" else "Обычный"
        
        await message.answer(
            f"✨ Отлично! Ты выбрал стиль: <b>{style_name}</b>\n\n"
            f"📊 Настройки:\n"
            f"• Количество фото: {photo_count}\n"
            f"• Режим: {mode_text}\n"
            f"• Стоимость: {cost} генераций\n\n"
            f"📷 Теперь отправь мне свою фотографию, и я создам для тебя потрясающий результат!",
            reply_markup=get_photo_request_keyboard(),
            parse_mode="HTML"
        )
        
    except json.JSONDecodeError:
        logger.error("Failed to decode webapp data")
        await message.answer("❌ Ошибка обработки данных. Попробуйте ещё раз.")
    except Exception as e:
        logger.error(f"Error in webapp handler: {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
