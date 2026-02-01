from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, BufferedInputFile
from aiogram.fsm.context import FSMContext
import aiohttp
import logging

from bot.states import UserState
from bot.keyboards import get_start_keyboard, get_generation_complete_keyboard
from bot.services.vertex_ai import get_vertex_service
from bot.config import get_settings
from bot.firestore import get_pending_style_selection, clear_pending_style_selection

router = Router()
logger = logging.getLogger(__name__)


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
    # Получаем данные из состояния
    data = await state.get_data()
    style_id = data.get("style_id")
    style_name = data.get("style_name")
    photo_count = data.get("photo_count", 1)
    mode = data.get("mode", "normal")
    
    if not style_id:
        await message.answer(
            "❌ Не выбран стиль. Пожалуйста, сначала выберите стиль.",
            reply_markup=get_start_keyboard()
        )
        await state.set_state(UserState.idle)
        return
    
    # Переводим в состояние генерации
    await state.set_state(UserState.generating)
    
    # Формируем сообщение о генерации
    mode_text = "PRO" if mode == "pro" else "обычном"
    status_text = (
        f"⏳ Генерирую {photo_count} фото в стиле «{style_name}»...\n"
        f"Режим: {mode_text}\n\n"
        f"⏱ Это может занять до минуты."
    )
    status_message = await message.answer(status_text)
    
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
        
        # Обновляем статус
        await status_message.edit_text(
            f"🎨 Генерирую {photo_count} фото в стиле «{style_name}»...\n"
            f"Режим: {mode_text}\n\n"
            f"⏱ Обработка изображения..."
        )
        
        # Генерируем изображения через Vertex AI
        vertex_service = get_ai_service()
        results = await vertex_service.generate_batch(
            photo_bytes=photo_bytes,
            style_id=style_id,
            count=photo_count,
            mode=mode
        )
        
        # Удаляем статусное сообщение
        try:
            await status_message.delete()
        except Exception:
            pass
        
        # Отправляем результаты
        if results:
            logger.info(f"Generated {len(results)} images successfully")
            
            if len(results) == 1:
                # Одно фото - отправляем обычным способом
                input_file = BufferedInputFile(
                    results[0], 
                    filename="result.jpg"
                )
                await message.answer_photo(
                    photo=input_file,
                    caption=f"✨ Готово! Фото в стиле «{style_name}»",
                    reply_markup=get_generation_complete_keyboard()
                )
            else:
                # Несколько фото - отправляем как MediaGroup
                media_group = []
                for i, result_bytes in enumerate(results):
                    input_file = BufferedInputFile(
                        result_bytes, 
                        filename=f"result_{i+1}.jpg"
                    )
                    
                    # Подпись только к первому фото
                    caption = f"✨ {len(results)} фото в стиле «{style_name}»" if i == 0 else None
                    
                    media_group.append(InputMediaPhoto(
                        media=input_file,
                        caption=caption
                    ))
                
                # Отправляем MediaGroup
                await message.answer_media_group(media=media_group)
                
                # Отправляем клавиатуру отдельным сообщением
                await message.answer(
                    f"✅ Сгенерировано {len(results)} из {photo_count} фото",
                    reply_markup=get_generation_complete_keyboard()
                )
        else:
            logger.warning("No results from generation")
            await message.answer(
                "❌ К сожалению, не удалось сгенерировать изображения.\n"
                "Попробуйте ещё раз или выберите другой стиль.",
                reply_markup=get_start_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Error in photo handler: {e}", exc_info=True)
        
        try:
            await status_message.delete()
        except Exception:
            pass
        
        await message.answer(
            f"❌ Произошла ошибка при генерации.\n"
            "Попробуйте ещё раз позже.",
            reply_markup=get_start_keyboard()
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
            "📷 Чтобы создать фото в стиле, сначала выберите стиль!",
            reply_markup=get_start_keyboard()
        )
        return
    
    # Есть pending selection - используем данные из Firestore
    style_id = pending.get("style_id")
    style_name = pending.get("style_name")
    photo_count = pending.get("photo_count", 1)
    mode = pending.get("mode", "normal")
    
    logger.info(f"Processing photo with pending selection: style={style_id}, count={photo_count}, mode={mode}")
    
    # Очищаем pending selection
    await clear_pending_style_selection(telegram_id)
    
    # Переводим в состояние генерации
    await state.set_state(UserState.generating)
    
    # Формируем сообщение о генерации
    mode_text = "PRO" if mode == "pro" else "обычном"
    status_text = (
        f"⏳ Генерирую {photo_count} фото в стиле «{style_name}»...\n"
        f"Режим: {mode_text}\n\n"
        f"⏱ Это может занять до минуты."
    )
    status_message = await message.answer(status_text)
    
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
        
        # Обновляем статус
        await status_message.edit_text(
            f"🎨 Генерирую {photo_count} фото в стиле «{style_name}»...\n"
            f"Режим: {mode_text}\n\n"
            f"⏱ Обработка изображения..."
        )
        
        # Генерируем изображения через Vertex AI
        vertex_service = get_ai_service()
        results = await vertex_service.generate_batch(
            photo_bytes=photo_bytes,
            style_id=style_id,
            count=photo_count,
            mode=mode
        )
        
        logger.info(f"Generation completed: {len(results) if results else 0} images")
        
        # Удаляем статусное сообщение
        try:
            await status_message.delete()
        except Exception:
            pass
        
        # Отправляем результаты
        if results:
            logger.info(f"Generated {len(results)} images successfully")
            
            if len(results) == 1:
                # Одно фото - отправляем обычным способом
                input_file = BufferedInputFile(
                    results[0], 
                    filename="result.jpg"
                )
                await message.answer_photo(
                    photo=input_file,
                    caption=f"✨ Готово! Фото в стиле «{style_name}»",
                    reply_markup=get_generation_complete_keyboard()
                )
            else:
                # Несколько фото - отправляем как MediaGroup
                media_group = []
                for i, result_bytes in enumerate(results):
                    input_file = BufferedInputFile(
                        result_bytes, 
                        filename=f"result_{i+1}.jpg"
                    )
                    caption = f"✨ {len(results)} фото в стиле «{style_name}»" if i == 0 else None
                    media_group.append(InputMediaPhoto(
                        media=input_file,
                        caption=caption
                    ))
                
                await message.answer_media_group(media=media_group)
                await message.answer(
                    f"✅ Сгенерировано {len(results)} из {photo_count} фото",
                    reply_markup=get_generation_complete_keyboard()
                )
        else:
            logger.warning("No results from generation")
            await message.answer(
                "❌ К сожалению, не удалось сгенерировать изображения.\n"
                "Попробуйте ещё раз или выберите другой стиль.",
                reply_markup=get_start_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Error in photo handler (pending): {e}", exc_info=True)
        
        try:
            await status_message.delete()
        except Exception:
            pass
        
        await message.answer(
            f"❌ Произошла ошибка при генерации.\n"
            "Попробуйте ещё раз позже.",
            reply_markup=get_start_keyboard()
        )
    
    # Возвращаем в idle состояние
    await state.set_state(UserState.idle)


@router.callback_query(F.data == "cancel")
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки отмены"""
    await state.clear()
    await state.set_state(UserState.idle)
    
    await callback.message.edit_text(
        "❌ Генерация отменена.\n\n"
        "Чтобы начать заново, нажмите кнопку ниже.",
    )
    await callback.message.answer(
        "Выберите стиль для новой генерации:",
        reply_markup=get_start_keyboard()
    )
    await callback.answer()
