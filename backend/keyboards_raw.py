"""
Raw inline keyboards in dict format for backend Telegram API calls
Used by NotificationService and cron endpoints
"""
from typing import Dict, Any, List


def kb_template_grid_raw(mini_app_url: str) -> Dict[str, Any]:
    """
    Клавиатура с сеткой шаблонов (m2, m10.1, m10.2)
    2 реальных стиля + 2 плейсхолдера + кнопка "Смотреть все шаблоны"
    """
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Ледяной куб", "callback_data": "tpl:ice_cube"},
                {"text": "Зимний триптих", "callback_data": "tpl:winter_triptych"}
            ],
            [
                {"text": "Скоро...", "callback_data": "tpl:placeholder"},
                {"text": "Скоро...", "callback_data": "tpl:placeholder"}
            ],
            [
                {"text": "🎭 Смотреть все шаблоны", "web_app": {"url": mini_app_url}}
            ]
        ]
    }
    return keyboard


def kb_downsell_raw() -> Dict[str, Any]:
    """Клавиатура даунселл-пака (m12)"""
    keyboard = {
        "inline_keyboard": [
            [{"text": "Купить 8⚡ за 169₽", "callback_data": "buy_downsell"}],
            [{"text": "Другие пакеты", "callback_data": "show_balance:downsell"}]
        ]
    }
    return keyboard
