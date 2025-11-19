# modules/interface/visual_processor/api_interface.py
"""
API Interface для модуля visual_processor
Интеграция с шиной сообщений и координатором
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..visual_processor import VisualProcessor

class VisualProcessorAPI:
    """API Interface для интеграции visual_processor с системой"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger('visual_processor.api')
        self.visual_processor = None
        self.is_initialized = False
        
        # Настройки по умолчанию
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        self.max_image_size = (1920, 1080)
        
    async def initialize(self):
        """Инициализация API и visual_processor"""
        try:
            self.logger.info("Инициализация VisualProcessor API")
            
            # Создаем экземпляр visual_processor
            self.visual_processor = VisualProcessor()
            
            # Инициализация модуля
            success = self.visual_processor.initialize()
            if not success:
                raise Exception("Не удалось инициализировать visual_processor")
            
            self.is_initialized = True
            self.logger.info("VisualProcessor API успешно инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации VisualProcessor API: {e}")
            return False
    
    async def process_image(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основной метод обработки изображения
        
        Args:
            image_data: Данные изображения
                - image_path: путь к файлу
                - image_bytes: байты изображения (опционально)
                - tasks: список задач ['object_detection', 'face_detection', 'scene_analysis']
                
        Returns:
            Результаты обработки
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            image_path = image_data.get('image_path')
            tasks = image_data.get('tasks', ['object_detection', 'face_detection', 'scene_analysis'])
            
            # Валидация входных данных
            if not image_path:
                return await self._create_error_response("Не указан image_path")
            
            if not Path(image_path).exists():
                return await self._create_error_response(f"Файл не существует: {image_path}")
            
            # Проверка формата файла
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in self.supported_formats:
                return await self._create_error_response(f"Неподдерживаемый формат: {file_ext}")
            
            self.logger.info(f"Обработка изображения: {image_path}, задачи: {tasks}")
            
            # Обработка изображения
            results = self.visual_processor.process_image(image_path, tasks)
            
            # Генерация визуального ответа если требуется
            if image_data.get('generate_visual_output', False):
                output_path = image_data.get('output_path')
                visual_output = self.visual_processor.generate_visual_response(results, output_path)
                results['visual_output_generated'] = True
                if output_path:
                    results['visual_output_path'] = output_path
            
            return {
                'status': 'success',
                'results': results,
                'processing_time': results.get('processing_time', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки изображения: {e}")
            return await self._create_error_response(str(e))
    
    async def analyze_scene(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Специализированный метод для анализа сцены"""
        image_data['tasks'] = ['scene_analysis']
        return await self.process_image(image_data)
    
    async def detect_objects(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Специализированный метод для детекции объектов"""
        image_data['tasks'] = ['object_detection']
        return await self.process_image(image_data)
    
    async def detect_faces(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Специализированный метод для детекции лиц и эмоций"""
        image_data['tasks'] = ['face_detection']
        return await self.process_image(image_data)
    
    async def compare_images(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сравнение нескольких изображений
        
        Args:
            comparison_data: 
                - image_paths: список путей к изображениям
                - output_path: путь для сохранения сравнения
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            image_paths = comparison_data.get('image_paths', [])
            output_path = comparison_data.get('output_path')
            
            if len(image_paths) < 1:
                return await self._create_error_response("Не указаны image_paths для сравнения")
            
            # Анализ каждого изображения
            analysis_results = []
            for img_path in image_paths:
                if not Path(img_path).exists():
                    continue
                
                result = self.visual_processor.process_image(img_path)
                analysis_results.append(result)
            
            # Создание сравнительного представления
            if len(analysis_results) > 1 and hasattr(self.visual_processor.response_generator, 'generate_comparison_view'):
                comparison_image = self.visual_processor.response_generator.generate_comparison_view(
                    image_paths, analysis_results, output_path
                )
                
                return {
                    'status': 'success',
                    'comparison_generated': True,
                    'images_processed': len(analysis_results),
                    'output_path': output_path,
                    'results': analysis_results
                }
            else:
                return {
                    'status': 'success',
                    'comparison_generated': False,
                    'images_processed': len(analysis_results),
                    'results': analysis_results
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка сравнения изображений: {e}")
            return await self._create_error_response(str(e))
    
    async def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Создание ответа об ошибке"""
        return {
            'status': 'error',
            'error': error_msg,
            'results': None
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса модуля"""
        return {
            'initialized': self.is_initialized,
            'visual_processor_ready': self.visual_processor is not None and self.visual_processor.is_initialized,
            'supported_formats': self.supported_formats,
            'max_image_size': self.max_image_size
        }
    
    async def shutdown(self):
        """Корректное завершение работы"""
        self.logger.info("Завершение работы VisualProcessor API")
        self.is_initialized = False
        self.visual_processor = None

# Создаем глобальный экземпляр для использования в системе
visual_processor_api = VisualProcessorAPI()

async def initialize_visual_processor(config: Dict[str, Any] = None) -> bool:
    """Функция инициализации для module_manager"""
    global visual_processor_api
    visual_processor_api = VisualProcessorAPI(config)
    return await visual_processor_api.initialize()

async def process_image_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Обработчик сообщений для communication_bus"""
    return await visual_processor_api.process_image(message_data)

async def get_visual_processor_status() -> Dict[str, Any]:
    """Получение статуса для мониторинга"""
    return await visual_processor_api.get_status()