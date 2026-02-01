from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import get_settings


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для стартового сообщения"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✨ Выбрать стиль",
                web_app=WebAppInfo(url=settings.mini_app_url)
            )
        ]
    ])
    return keyboard


def get_photo_request_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после выбора стиля"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔄 Выбрать другой стиль",
                web_app=WebAppInfo(url=settings.mini_app_url)
            )
        ],
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
        [
            InlineKeyboardButton(
                text="✨ Ещё одна генерация",
                web_app=WebAppInfo(url=settings.mini_app_url)
            )
        ]
    ])
    return keyboard
