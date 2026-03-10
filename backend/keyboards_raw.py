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


def kb_payment_confirm_raw(payment_url: str, payment_id: str) -> Dict[str, Any]:
    """
    Клавиатура подтверждения оплаты (m15) для backend:
    - Перейти к оплате (URL)
    - Отмена (callback cancel_payment:{payment_id})
    """
    keyboard: Dict[str, Any] = {
        "inline_keyboard": [
            [{"text": "💳 Перейти к оплате", "url": payment_url}],
            [{"text": "Отмена", "callback_data": f"cancel_payment:{payment_id}"}],
        ]
    }
    return keyboard


def kb_payment_retry_raw() -> Dict[str, Any]:
    """
    Клавиатура повторной попытки оплаты (используется с m16):
    Кнопки пакетов как в m11/m14.
    """
    keyboard: Dict[str, Any] = {
        "inline_keyboard": [
            [
                {"text": "10⚡ за 249₽", "callback_data": "buy_pack:pack_10"},
                {"text": "50⚡ за 790₽", "callback_data": "buy_pack:pack_50"},
            ],
            [
                {"text": "120⚡ за 1290₽", "callback_data": "buy_pack:pack_120"},
                {"text": "300⚡ за 2490₽", "callback_data": "buy_pack:pack_300"},
            ],
            [
                {"text": "🏠 Главное меню", "callback_data": "show_menu"},
            ],
        ]
    }
    return keyboard


def kb_payment_success_raw(mini_app_url: str) -> Dict[str, Any]:
    """
    Клавиатура после успешной оплаты (m17) для backend:
    - Открыть мини-приложение (web_app кнопка)
    """
    keyboard: Dict[str, Any] = {
        "inline_keyboard": [
            [
                {
                    "text": "🚀 Открыть Сияй AI",
                    "web_app": {"url": mini_app_url},
                }
            ]
        ]
    }
    return keyboard
