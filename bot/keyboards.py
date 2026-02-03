from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import get_settings


def _create_webapp_button(text: str, url: str) -> InlineKeyboardButton:
    """
    Создаёт кнопку для Mini App.
    Если URL начинается с https:// — используется WebAppInfo.
    Если HTTP (localhost) — используется callback кнопка с инструкцией.
    """
    if url.startswith("https://"):
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))
    else:
        # Для локальной разработки — callback кнопка (Telegram не разрешает HTTP URL)
        return InlineKeyboardButton(text=f"{text} (dev)", callback_data="open_miniapp_dev")


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для стартового сообщения"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [_create_webapp_button("✨ Выбрать стиль", settings.mini_app_url)]
    ])
    return keyboard


def get_photo_request_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после выбора стиля"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [_create_webapp_button("🔄 Выбрать другой стиль", settings.mini_app_url)],
        [
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel"
            )
        ]
    ])
    return keyboard


def get_generation_complete_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после завершения генерации"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [_create_webapp_button("✨ Ещё одна генерация", settings.mini_app_url)]
    ])
    return keyboard
