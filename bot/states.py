from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    """Состояния пользователя"""
    idle = State()  # Ожидание действия
    awaiting_photo = State()  # Ожидание фото после выбора стиля
    generating = State()  # Генерация в процессе
