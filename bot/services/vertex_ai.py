"""
Vertex AI Service for image generation using Gemini 2.5 Flash/Pro Image models
Supports batch generation and ADC authentication
"""
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
import asyncio
from typing import List, Optional
import logging
import base64

from bot.styles_data import get_style_by_id

logger = logging.getLogger(__name__)


class VertexAIService:
    """Сервис для работы с Vertex AI Gemini Image Generation"""
    
    # Модели и их регионы
    # Normal mode: regional endpoint (europe-west4)
    # PRO mode: global endpoint (required for gemini-3-pro-image-preview)
    MODELS = {
        "normal": {
            "name": "gemini-2.5-flash-image",
            "location": "europe-west4"  # Regional endpoint
        },
        "pro": {
            "name": "gemini-3-pro-image-preview",
            "location": "global"  # Global-only model
        }
    }
    
    # Максимальное количество retry при ошибках
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # секунды
    
    def __init__(self, project_id: str):
        """
        Инициализация Vertex AI с ADC (Application Default Credentials)
        
        Args:
            project_id: ID проекта в Google Cloud
        """
        self.project_id = project_id
        
        # Кэш моделей для переиспользования
        self._models = {}
        
        # Отслеживание инициализированных locations
        self._initialized_locations = set()
        
        logger.info(f"VertexAIService initialized for project {project_id}")
    
    def _ensure_location_initialized(self, location: str):
        """Убедиться что Vertex AI инициализирован для нужного location"""
        if location not in self._initialized_locations:
            vertexai.init(project=self.project_id, location=location)
            self._initialized_locations.add(location)
            logger.info(f"Initialized Vertex AI for location: {location}")
    
    def _get_model(self, mode: str) -> GenerativeModel:
        """Получить модель по режиму с правильным location"""
        if mode not in self._models:
            model_config = self.MODELS.get(mode, self.MODELS["normal"])
            model_name = model_config["name"]
            location = model_config["location"]
            
            # Инициализируем Vertex AI для нужного location
            self._ensure_location_initialized(location)
            
            # Создаём модель
            self._models[mode] = GenerativeModel(model_name)
            logger.info(f"Loaded model {model_name} for mode '{mode}' in location '{location}'")
        
        return self._models[mode]
    
    def _get_generation_config(self) -> GenerationConfig:
        """Конфигурация для генерации изображений"""
        return GenerationConfig(
            response_modalities=["IMAGE", "TEXT"],
            temperature=0.8,
            max_output_tokens=8192,
        )
    
    async def _generate_with_retry(
        self,
        model: GenerativeModel,
        contents: list,
        generation_config: GenerationConfig
    ) -> Optional[bytes]:
        """Генерация с retry-логикой"""
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Запускаем синхронный вызов в executor
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: model.generate_content(
                        contents,
                        generation_config=generation_config
                    )
                )
                
                # Извлекаем изображение из ответа
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        # Проверяем наличие inline_data (изображение)
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_data = part.inline_data.data
                            if isinstance(image_data, str):
                                # Если данные в base64
                                return base64.b64decode(image_data)
                            return image_data
                
                # Если изображение не найдено в ответе
                logger.warning(f"No image in response (attempt {attempt + 1})")
                
            except Exception as e:
                last_error = e
                logger.error(f"Generation error (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
        
        if last_error:
            logger.error(f"All retry attempts failed: {last_error}")
        return None
    
    async def generate_single(
        self, 
        photo_bytes: bytes, 
        style_id: str,
        mode: str = "normal"
    ) -> Optional[bytes]:
        """
        Генерация одного изображения
        
        Args:
            photo_bytes: Исходное фото в байтах
            style_id: ID стиля
            mode: Режим генерации (normal или pro)
            
        Returns:
            Сгенерированное изображение в байтах или None при ошибке
        """
        try:
            # Получаем информацию о стиле
            style = get_style_by_id(style_id)
            if not style:
                logger.error(f"Style not found: {style_id}")
                return None
            
            # Получаем модель
            model = self._get_model(mode)
            
            # Создаём Part из изображения пользователя
            image_part = Part.from_data(photo_bytes, mime_type="image/jpeg")
            
            # Формируем промпт для трансформации
            prompt = style["prompt"]
            
            # Добавляем системные инструкции если есть
            system_instruction = style.get("system_instruction", "")
            if system_instruction:
                prompt = f"{system_instruction}\n\n{prompt}"
            
            # Собираем контент для модели
            contents = [prompt, image_part]
            
            # Генерируем с retry
            result = await self._generate_with_retry(
                model=model,
                contents=contents,
                generation_config=self._get_generation_config()
            )
            
            if result:
                logger.info(f"Successfully generated image for style '{style_id}' in mode '{mode}'")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in generate_single: {e}", exc_info=True)
            return None
    
    async def generate_batch(
        self, 
        photo_bytes: bytes, 
        style_id: str,
        count: int = 1,
        mode: str = "normal"
    ) -> List[bytes]:
        """
        Batch-генерация нескольких изображений параллельно
        
        Args:
            photo_bytes: Исходное фото в байтах
            style_id: ID стиля
            count: Количество генераций (макс 5)
            mode: Режим генерации (normal или pro)
            
        Returns:
            Список сгенерированных изображений в байтах
        """
        # Ограничиваем количество параллельных генераций
        count = min(count, 5)
        
        logger.info(f"Starting batch generation: {count} images, style={style_id}, mode={mode}")
        
        # Создаём задачи для параллельной генерации
        tasks = [
            self.generate_single(photo_bytes, style_id, mode)
            for _ in range(count)
        ]
        
        # Выполняем параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch item {i + 1} failed: {result}")
            elif result is not None:
                successful_results.append(result)
            else:
                logger.warning(f"Batch item {i + 1} returned None")
        
        logger.info(f"Batch generation complete: {len(successful_results)}/{count} successful")
        
        return successful_results


# Синглтон для переиспользования
_vertex_service: Optional[VertexAIService] = None


def get_vertex_service(project_id: str) -> VertexAIService:
    """Получить инстанс Vertex AI сервиса (синглтон)"""
    global _vertex_service
    if _vertex_service is None:
        _vertex_service = VertexAIService(project_id)
    return _vertex_service


def reset_vertex_service():
    """Сбросить синглтон (для тестирования)"""
    global _vertex_service
    _vertex_service = None
