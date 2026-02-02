from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_start_keyboard
from bot.states import UserState

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
    # region agent log
    import json;open(r'c:\PetProjects\Seeyay.ai\.cursor\debug.log','a',encoding='utf-8').write(json.dumps({'location':'bot/handlers/start.py:23','message':'cmd_start called','data':{'user_id':message.from_user.id if message.from_user else None,'chat_id':message.chat.id if message.chat else None},'timestamp':__import__('time').time()*1000,'sessionId':'debug-session','runId':'run1','hypothesisId':'C'})+'\n')
    # endregion
    # Сбрасываем состояние
    await state.clear()
    await state.set_state(UserState.idle)
    
    # Отправляем приветственное сообщение
    await message.answer(
        text=WELCOME_MESSAGE,
        reply_markup=get_start_keyboard()
    )
    # region agent log
    import json;open(r'c:\PetProjects\Seeyay.ai\.cursor\debug.log','a',encoding='utf-8').write(json.dumps({'location':'bot/handlers/start.py:33','message':'cmd_start completed','data':{},'timestamp':__import__('time').time()*1000,'sessionId':'debug-session','runId':'run1','hypothesisId':'C'})+'\n')
    # endregion