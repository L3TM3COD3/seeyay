"""
Inline keyboards for the bot message chain
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import get_settings
import logging

logger = logging.getLogger(__name__)


def _create_webapp_button(text: str, url: str) -> InlineKeyboardButton:
    """
    Создаёт кнопку для Mini App.
    Если URL начинается с https:// — используется WebAppInfo.
    Если HTTP (localhost) — используется callback кнопка с инструкцией.
    """
    # region agent log
    logger.info(f"[DEBUG_MINIAPP_A_B] Creating webapp button: text={text}, url={url}, url_starts_with_https={url.startswith('https://') if url else False}, url_empty={not bool(url)}")
    # endregion
    
    if url.startswith("https://"):
        # region agent log
        logger.info(f"[DEBUG_MINIAPP_C] Creating HTTPS WebApp button with URL: {url}")
        # endregion
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))
    else:
        # region agent log
        logger.info(f"[DEBUG_MINIAPP_B] Creating callback button (not HTTPS), url: {url}")
        # endregion
        # Для локальной разработки — callback кнопка (Telegram не разрешает HTTP URL)
        return InlineKeyboardButton(text=f"{text} (dev)", callback_data="open_miniapp_dev")


def kb_template_grid() -> InlineKeyboardMarkup:
    """
    Клавиатура с сеткой шаблонов (m1, m2, m10.x)
    2 реальных стиля + 2 плейсхолдера + кнопка "Смотреть все шаблоны"
    """
    settings = get_settings()
    
    # region agent log
    logger.info(f"[DEBUG_MINIAPP_A_E] Settings loaded in kb_template_grid: mini_app_url={settings.mini_app_url}, bot_token_present={bool(settings.bot_token)}, backend_url={settings.backend_url}")
    # endregion
    
    webapp_button = _create_webapp_button("🎭 Смотреть все шаблоны", settings.mini_app_url)
    
    # region agent log
    logger.info(f"[DEBUG_MINIAPP_STRUCTURE] Webapp button created: has_web_app={hasattr(webapp_button, 'web_app')}, has_callback={hasattr(webapp_button, 'callback_data')}, web_app_value={webapp_button.web_app if hasattr(webapp_button, 'web_app') else None}")
    # endregion
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ледяной куб", callback_data="tpl:ice_cube"),
            InlineKeyboardButton(text="Зимний триптих", callback_data="tpl:winter_triptych")
        ],
        [
            InlineKeyboardButton(text="Скоро...", callback_data="tpl:placeholder"),
            InlineKeyboardButton(text="Скоро...", callback_data="tpl:placeholder")
        ],
        [
            webapp_button
        ]
    ])
    
    # region agent log
    logger.info(f"[DEBUG_MINIAPP_FULL_KB] Full keyboard structure: rows={len(keyboard.inline_keyboard)}, row_0_buttons={len(keyboard.inline_keyboard[0])}, row_2_button_0_text={keyboard.inline_keyboard[2][0].text}, row_2_button_0_has_webapp={hasattr(keyboard.inline_keyboard[2][0], 'web_app')}")
    # endregion
    
    return keyboard


def kb_config_onboarding(style_id: str) -> InlineKeyboardMarkup:
    """Клавиатура конфигурации для новичков (m3)"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [_create_webapp_button("🎭 Сменить шаблон", settings.mini_app_url)]
    ])
    return keyboard


def kb_config_normal(style_id: str) -> InlineKeyboardMarkup:
    """Клавиатура конфигурации в обычном режиме (m4.1)"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Использовать PRO-режим", callback_data=f"toggle_pro:{style_id}")],
        [_create_webapp_button("🎭 Сменить шаблон", settings.mini_app_url)]
    ])
    return keyboard


def kb_config_pro(style_id: str) -> InlineKeyboardMarkup:
    """Клавиатура конфигурации в PRO режиме (m4.2)"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Использовать обычный режим", callback_data=f"toggle_normal:{style_id}")],
        [_create_webapp_button("🎭 Сменить шаблон", settings.mini_app_url)]
    ])
    return keyboard


def kb_result_m71(style_id: str, file_id: str) -> InlineKeyboardMarkup:
    """Клавиатура результата после 1-ой генерации (m7.1)"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔁 Повторить 1⚡", callback_data=f"repeat:{style_id}")
        ],
        [_create_webapp_button("🎭 Сменить шаблон", settings.mini_app_url)]
    ])
    return keyboard


def kb_result_m72(style_id: str, file_id: str) -> InlineKeyboardMarkup:
    """Клавиатура результата после 2-ой генерации (m7.2)"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔁 Повторить 1⚡", callback_data=f"repeat:{style_id}")
        ],
        [
            _create_webapp_button("🎭 Сменить шаблон", settings.mini_app_url),
            InlineKeyboardButton(text="⚡ Пополнить баланс", callback_data="show_balance:result")
        ]
    ])
    return keyboard


def kb_result_m73(style_id: str, file_id: str) -> InlineKeyboardMarkup:
    """Клавиатура результата после 3-ей генерации (m7.3) - аналогична m7.2"""
    return kb_result_m72(style_id, file_id)


def kb_result_m8(style_id: str, file_id: str) -> InlineKeyboardMarkup:
    """Клавиатура обычного результата (m8) - аналогична m7.2"""
    return kb_result_m72(style_id, file_id)


def kb_starter_pack() -> InlineKeyboardMarkup:
    """Клавиатура стартер-пака (m9)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Забрать 100⚡ за 990₽", callback_data="buy_starter")],
        [InlineKeyboardButton(text="Другие пакеты", callback_data="show_balance:starter")]
    ])
    return keyboard


def kb_insufficient() -> InlineKeyboardMarkup:
    """Клавиатура недостаточной энергии (m11)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="10⚡ за 249₽", callback_data="buy_pack:pack_10"),
            InlineKeyboardButton(text="50⚡ за 790₽", callback_data="buy_pack:pack_50")
        ],
        [
            InlineKeyboardButton(text="120⚡ за 1290₽", callback_data="buy_pack:pack_120"),
            InlineKeyboardButton(text="300⚡ за 2490₽", callback_data="buy_pack:pack_300")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="show_menu")]
    ])
    return keyboard


def kb_menu() -> InlineKeyboardMarkup:
    """Клавиатура главного меню (m13)"""
    settings = get_settings()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            _create_webapp_button("🎭 Выбрать шаблон", settings.mini_app_url),
            InlineKeyboardButton(text="⚡️ Пополнить баланс", callback_data="show_balance:menu")
        ]
    ])
    return keyboard


def kb_balance(back_target: str = "menu") -> InlineKeyboardMarkup:
    """
    Клавиатура баланса (m14)
    back_target - откуда пришли (menu, result, starter и т.д.)
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back:{back_target}")],
        [
            InlineKeyboardButton(text="10⚡ за 249₽", callback_data="buy_pack:pack_10"),
            InlineKeyboardButton(text="50⚡ за 790₽", callback_data="buy_pack:pack_50")
        ],
        [
            InlineKeyboardButton(text="120⚡ за 1290₽", callback_data="buy_pack:pack_120"),
            InlineKeyboardButton(text="300⚡ за 2490₽", callback_data="buy_pack:pack_300")
        ],
        [InlineKeyboardButton(text="💬 Связаться с менеджером", callback_data="contact_manager")]
    ])
    return keyboard


def kb_downsell() -> InlineKeyboardMarkup:
    """Клавиатура даунселл-пака (m12)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить 8⚡ за 169₽", callback_data="buy_downsell")],
        [InlineKeyboardButton(text="Другие пакеты", callback_data="show_balance:downsell")]
    ])
    return keyboard
