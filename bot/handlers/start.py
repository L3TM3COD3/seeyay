from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_start_keyboard
from bot.states import UserState
from bot.config import get_settings

router = Router()

WELCOME_MESSAGE = """👋 Привет! Я бот СИЯЙ AI для создания нейрофотосессий.

✨ Что я умею:
• Превращать твои фото в стильные фотосессии
• Создавать образы в разных стилях: luxury, деловой, с шариками и др.
• Генерировать несколько вариантов за раз

🚀 Начни прямо сейчас — выбери стиль!"""


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    # Сбрасываем состояние
    await state.clear()
    await state.set_state(UserState.idle)
    
    # Отправляем приветственное сообщение
    await message.answer(
        text=WELCOME_MESSAGE,
        reply_markup=get_start_keyboard()
    )


@router.callback_query(F.data == "open_miniapp_dev")
async def callback_open_miniapp_dev(callback: CallbackQuery):
    """Обработчик для dev кнопки Mini App (когда нет HTTPS)"""
    settings = get_settings()
    await callback.answer()
    await callback.message.answer(
        f"🔧 Dev Mode: Mini App доступен по адресу:\n{settings.mini_app_url}\n\n"
        "Откройте этот URL в браузере для тестирования."
    )
