from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
import aiohttp
import asyncio
import logging

from bot.states import UserState
from bot.keyboards import (
    kb_result_m71,
    kb_result_m72,
    kb_result_m73,
    kb_result_m8,
    kb_starter_pack,
    kb_insufficient,
    kb_config_normal,
    kb_config_pro
)
from bot.messages import (
    m6_generating,
    m7_1_result_first,
    m7_2_result_second,
    m7_3_result_third,
    m8_result_regular,
    m9_starter_pack,
    m11_insufficient_energy,
    m4_1_config_normal,
    m4_2_config_pro
)
from bot.services.vertex_ai import get_vertex_service
from bot.config import get_settings
from bot.firestore import (
    get_pending_style_selection,
    clear_pending_style_selection,
    deduct_energy,
    update_user_balance,
    get_user,
    increment_successful_generations,
    set_user_flag,
    set_user_timestamp
)
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)

# Moon phase emoji for m6 animation (Plan 2)
MOON_PHASES = "🌑🌘🌗🌖🌕🌔🌓🌒"


async def animate_moon_emoji(message: Message, stop_event: asyncio.Event):
    """
    Анимация смены фаз луны в сообщении m6 (Plan 2)
    Цикл выполняется пока stop_event не установлен
    """
    i = 0
    base_text = "Генерируем ваше фото…\n\n⏱️ Будет готово через 10–30 секунд"
    
    while not stop_event.is_set():
        phase = MOON_PHASES[i % len(MOON_PHASES)]
        try:
            await message.edit_text(f"{phase} {base_text}", parse_mode="HTML")
        except Exception as e:
            # Игнорируем ошибки редактирования (например, если сообщение уже удалено)
            logger.debug(f"Moon animation edit error: {e}")
            break
        i += 1
        await asyncio.sleep(1)


def get_settings_instance():
    """Lazy initialization of settings to avoid startup issues"""
    return get_settings()


def get_ai_service():
    """Get Vertex AI service instance"""
    settings = get_settings_instance()
    return get_vertex_service(
        project_id=settings.gcp_project_id
    )


@router.message(UserState.awaiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    """Обработчик фото в состоянии ожидания"""
    telegram_id = message.from_user.id
    
    # Получаем данные из состояния
    data = await state.get_data()
    style_id = data.get("style_id")
    style_name = data.get("style_name")
    mode = data.get("mode", "normal")
    
    if not style_id:
        await message.answer("❌ Не выбран стиль. Пожалуйста, сначала выберите стиль.")
        await state.set_state(UserState.idle)
        return
    
    # Рассчитываем стоимость: PRO = 6 энергии, normal = 1
    cost = 6 if mode == "pro" else 1
    
    # Проверяем баланс пользователя
    user = await get_user(telegram_id)
    if not user:
        await message.answer("❌ Пользователь не найден. Используйте /start для регистрации.")
        await state.set_state(UserState.idle)
        return
    
    current_balance = user.get("balance", 0)
    successful_generations = user.get("successful_generations", 0)
    is_new_user = user.get("is_new_user", True)
    m9_shown = user.get("m9_shown", False)
    
    # Проверка недостаточного баланса
    if current_balance < cost:
        # m9 или m11
        if is_new_user and successful_generations >= 1 and not m9_shown:
            # Отправляем m9: стартер-пак
            await message.answer(
                text=m9_starter_pack(current_balance, cost),
                reply_markup=kb_starter_pack(),
                parse_mode="HTML"
            )
            await set_user_flag(telegram_id, "m9_shown", True)
            # Записываем timestamp показа m9 (Plan 2)
            await set_user_timestamp(telegram_id, "m9_sent_at", datetime.utcnow())
        else:
            # Отправляем m11: обычное сообщение о недостатке энергии
            await message.answer(
                text=m11_insufficient_energy(current_balance, cost),
                reply_markup=kb_insufficient(),
                parse_mode="HTML"
            )
        
        await state.set_state(UserState.idle)
        return
    
    # Списываем энергию ДО генерации (атомарная операция)
    deduct_result = await deduct_energy(telegram_id, cost)
    if not deduct_result:
        await message.answer(
            f"❌ Не удалось списать энергию. Возможно, баланс изменился.\n"
            f"Попробуйте еще раз."
        )
        await state.set_state(UserState.idle)
        return
    
    new_balance = deduct_result.get("balance", 0)
    logger.info(f"Energy deducted for user {telegram_id}: {cost} ⚡, new balance: {new_balance}")
    
    # Переводим в состояние генерации
    await state.set_state(UserState.generating)
    
    # Отправляем m6: "Генерируем..." с анимацией луны (Plan 2)
    status_message = await message.answer(
        text=m6_generating(),
        parse_mode="HTML"
    )
    
    # Запускаем фоновую анимацию луны
    stop_animation = asyncio.Event()
    animation_task = asyncio.create_task(animate_moon_emoji(status_message, stop_animation))
    
    try:
        settings = get_settings_instance()
        
        # Получаем файл фото (берём самое большое качество)
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_path = file.file_path
        
        # Скачиваем фото
        file_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file_path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download photo: {response.status}")
                photo_bytes = await response.read()
        
        logger.info(f"Downloaded photo: {len(photo_bytes)} bytes")
        
        # Генерируем изображение через Vertex AI
        vertex_service = get_ai_service()
        result_bytes = await vertex_service.generate_single(
            photo_bytes=photo_bytes,
            style_id=style_id,
            mode=mode
        )
        
        # Останавливаем анимацию и удаляем статусное сообщение
        stop_animation.set()
        try:
            await animation_task
        except Exception:
            pass
        
        try:
            await status_message.delete()
        except Exception:
            pass
        
        # Отправляем результат
        if result_bytes:
            logger.info(f"Generated image successfully for user {telegram_id}")
            
            # Увеличиваем счётчик успешных генераций
            new_count = await increment_successful_generations(telegram_id)
            if new_count is None:
                new_count = successful_generations + 1  # fallback
            
            # Записываем timestamp последней успешной генерации (Plan 2)
            await set_user_timestamp(telegram_id, "last_generation_at", datetime.utcnow())
            
            logger.info(f"User {telegram_id} now has {new_count} successful generations")
            
            # Отправляем фото с правильным сообщением
            input_file = BufferedInputFile(
                result_bytes,
                filename="result.jpg"
            )
            
            # Определяем какое сообщение и клавиатуру отправить
            if new_count == 1 and not user.get("m7_1_sent", False):
                # m7.1: первая генерация
                text = m7_1_result_first(style_name, new_balance)
                sent_msg = await message.answer_photo(
                    photo=input_file,
                    caption=text,
                    parse_mode="HTML"
                )
                keyboard = kb_result_m71(style_id, str(sent_msg.message_id))
                await sent_msg.edit_reply_markup(reply_markup=keyboard)
                await set_user_flag(telegram_id, "m7_1_sent", True)
                
            elif new_count == 2 and not user.get("m7_2_sent", False):
                # m7.2: вторая генерация
                text = m7_2_result_second(style_name, new_balance)
                sent_msg = await message.answer_photo(
                    photo=input_file,
                    caption=text,
                    parse_mode="HTML"
                )
                keyboard = kb_result_m72(style_id, str(sent_msg.message_id))
                await sent_msg.edit_reply_markup(reply_markup=keyboard)
                await set_user_flag(telegram_id, "m7_2_sent", True)
                
            elif new_count == 3 and not user.get("m7_3_sent", False):
                # m7.3: третья генерация
                text = m7_3_result_third(style_name, new_balance)
                sent_msg = await message.answer_photo(
                    photo=input_file,
                    caption=text,
                    parse_mode="HTML"
                )
                keyboard = kb_result_m73(style_id, str(sent_msg.message_id))
                await sent_msg.edit_reply_markup(reply_markup=keyboard)
                await set_user_flag(telegram_id, "m7_3_sent", True)
                
            else:
                # m8: обычный результат
                text = m8_result_regular(style_name, new_balance)
                sent_msg = await message.answer_photo(
                    photo=input_file,
                    caption=text,
                    parse_mode="HTML"
                )
                keyboard = kb_result_m8(style_id, str(sent_msg.message_id))
                await sent_msg.edit_reply_markup(reply_markup=keyboard)
        else:
            logger.warning(f"No results from generation for user {telegram_id}")
            
            # Возвращаем энергию при ошибке генерации
            await update_user_balance(telegram_id, cost)
            logger.info(f"Energy refunded for user {telegram_id}: {cost} ⚡")
            
            await message.answer(
                "❌ К сожалению, не удалось сгенерировать изображение.\n"
                f"Энергия возвращена: +{cost} ⚡\n\n"
                "Попробуйте ещё раз или выберите другой стиль."
            )
        
    except Exception as e:
        logger.error(f"Error in photo handler: {e}", exc_info=True)
        
        # Останавливаем анимацию при ошибке
        stop_animation.set()
        try:
            await animation_task
        except Exception:
            pass
        
        try:
            await status_message.delete()
        except Exception:
            pass
        
        # Возвращаем энергию при ошибке
        try:
            await update_user_balance(telegram_id, cost)
            logger.info(f"Energy refunded after error for user {telegram_id}: {cost} ⚡")
            
            await message.answer(
                f"❌ Произошла ошибка при генерации.\n"
                f"Энергия возвращена: +{cost} ⚡\n\n"
                "Попробуйте ещё раз позже."
            )
        except Exception as refund_error:
            logger.error(f"Error refunding energy: {refund_error}")
            await message.answer(
                f"❌ Произошла ошибка при генерации.\n"
                "Попробуйте ещё раз позже."
            )
    
    # Возвращаем в idle состояние
    await state.set_state(UserState.idle)


@router.message(UserState.awaiting_photo)
async def handle_not_photo(message: Message, state: FSMContext):
    """Обработчик любых сообщений кроме фото в состоянии ожидания"""
    await message.answer(
        "📷 Пожалуйста, отправьте фотографию для генерации.\n"
        "Если хотите выбрать другой стиль, нажмите кнопку ниже."
    )


@router.message(F.photo)
async def handle_photo_with_pending_selection(message: Message, state: FSMContext):
    """
    Fallback обработчик фото - проверяет pending selection в Firestore.
    Срабатывает когда FSM состояние не awaiting_photo, но есть pending selection.
    """
    telegram_id = message.from_user.id
    
    # Проверяем, есть ли pending selection в Firestore
    pending = await get_pending_style_selection(telegram_id)
    
    if not pending:
        # Нет pending selection - просим выбрать стиль
        await message.answer(
            "📷 Чтобы создать фото в стиле, сначала выберите стиль!\n"
            "Используйте /start или /menu"
        )
        return
    
    # Есть pending selection - используем данные из Firestore
    style_id = pending.get("style_id")
    style_name = pending.get("style_name")
    mode = pending.get("mode", "normal")
    
    logger.info(f"Processing photo with pending selection: style={style_id}, mode={mode}")
    
    # Очищаем pending selection
    await clear_pending_style_selection(telegram_id)
    
    # Устанавливаем данные в FSM и перенаправляем на основной обработчик
    await state.update_data(
        style_id=style_id,
        style_name=style_name,
        mode=mode
    )
    await state.set_state(UserState.awaiting_photo)
    
    # Вызываем основной обработчик фото
    await handle_photo(message, state)


@router.callback_query(F.data.startswith("repeat:"))
async def handle_repeat(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки "Повторить" - возвращает в режим выбора фото"""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    style_id = callback.data.split(":", 1)[1]
    
    # Получаем стиль из styles_data
    from bot.styles_data import get_style_by_id
    style = get_style_by_id(style_id)
    if not style:
        await callback.message.answer("❌ Шаблон не найден")
        return
    
    style_name = style["name"]
    
    # Получаем пользователя для проверки кол-ва генераций
    user = await get_user(telegram_id)
    if not user:
        await callback.message.answer("❌ Пользователь не найден. Используйте /start")
        return
    
    successful_generations = user.get("successful_generations", 0)
    
    # Сохраняем в FSM
    await state.update_data(
        style_id=style_id,
        style_name=style_name,
        mode="normal"
    )
    await state.set_state(UserState.awaiting_photo)
    
    # Отправляем конфигурацию (m4.1 для тех у кого >= 1 генерации)
    if successful_generations >= 1:
        text = m4_1_config_normal(style_name, 1)
        keyboard = kb_config_normal(style_id)
    else:
        # На всякий случай, хотя "Повторить" доступна только после генерации
        from bot.messages import m3_config_onboarding
        from bot.keyboards import kb_config_onboarding
        text = m3_config_onboarding(style_name, 1)
        keyboard = kb_config_onboarding(style_id)
    
    await callback.message.answer(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    logger.info(f"User {telegram_id} repeated generation for {style_id}")


@router.callback_query(F.data.startswith("download:"))
async def handle_download(callback: CallbackQuery):
    """Обработчик кнопки "Скачать файл" - скачивает фото из Telegram и отправляет как документ"""
    await callback.answer("Отправляю файл в полном качестве...")
    
    try:
        # Получаем file_id фото из сообщения с кнопкой
        if not callback.message.photo:
            await callback.message.answer("❌ Фото не найдено в сообщении")
            return
        
        file_id = callback.message.photo[-1].file_id
        
        # Скачиваем фото из Telegram
        file = await callback.bot.get_file(file_id)
        file_data = await callback.bot.download_file(file.file_path)
        
        # Отправляем как документ для полного качества
        input_file = BufferedInputFile(
            file_data.read(),
            filename="seeyay_result.jpg"
        )
        
        await callback.message.answer_document(
            document=input_file,
            caption="📥 Ваше фото в максимальном качестве"
        )
        logger.info(f"File downloaded and sent as document for user {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error downloading and sending file: {e}", exc_info=True)
        await callback.message.answer("❌ Не удалось отправить файл")
