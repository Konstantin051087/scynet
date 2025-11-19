# tests/test_visual_processor.py
"""
Тесты для модуля visual_processor
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
import cv2
import numpy as np

from modules.interface.visual_processor import VisualProcessor
from modules.interface.visual_processor.api_interface import VisualProcessorAPI


class TestVisualProcessor:
    """Тесты основного класса visual_processor"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.visual_processor = VisualProcessor()
        self.test_image = self._create_test_image()
        
    def _create_test_image(self, width=640, height=480):
        """Создание тестового изображения"""
        # Создаем изображение с простыми геометрическими фигурами
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Красный прямоугольник
        cv2.rectangle(image, (50, 50), (200, 200), (0, 0, 255), -1)
        
        # Зеленая окружность
        cv2.circle(image, (400, 150), 80, (0, 255, 0), -1)
        
        # Синий треугольник
        pts = np.array([[300, 300], [250, 400], [350, 400]], np.int32)
        cv2.fillPoly(image, [pts], (255, 0, 0))
        
        return image
    
    def test_initialization(self):
        """Тест инициализации модуля"""
        success = self.visual_processor.initialize()
        assert success == True
        assert self.visual_processor.is_initialized == True
        
    def test_image_recognizer_initialization(self):
        """Тест инициализации распознавателя изображений"""
        self.visual_processor.initialize()
        assert self.visual_processor.image_recognizer is not None
        assert hasattr(self.visual_processor.image_recognizer, 'detect_objects')
        
    def test_face_detector_initialization(self):
        """Тест инициализации детектора лиц"""
        self.visual_processor.initialize()
        assert self.visual_processor.face_detector is not None
        assert hasattr(self.visual_processor.face_detector, 'detect_faces')
        
    def test_scene_analyzer_initialization(self):
        """Тест инициализации анализатора сцен"""
        self.visual_processor.initialize()
        assert self.visual_processor.scene_analyzer is not None
        assert hasattr(self.visual_processor.scene_analyzer, 'analyze_scene')
        
    def test_response_generator_initialization(self):
        """Тест инициализации генератора ответов"""
        self.visual_processor.initialize()
        assert self.visual_processor.response_generator is not None
        assert hasattr(self.visual_processor.response_generator, 'generate_summary')


class TestVisualProcessorAPI:
    """Тесты API интерфейса"""
    
    @pytest.fixture
    async def api(self):
        """Фикстура для создания API"""
        api = VisualProcessorAPI()
        await api.initialize()
        return api
    
    @pytest.fixture
    def test_image_path(self):
        """Создание временного тестового изображения"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            # Создаем простое тестовое изображение
            image = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.rectangle(image, (10, 10), (90, 90), (0, 255, 0), -1)
            cv2.imwrite(f.name, image)
            temp_path = f.name
        
        yield temp_path
        
        # Удаляем временный файл
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_api_initialization(self, api):
        """Тест инициализации API"""
        assert api.is_initialized == True
        assert api.visual_processor is not None
        
    @pytest.mark.asyncio
    async def test_process_image_success(self, api, test_image_path):
        """Тест успешной обработки изображения"""
        result = await api.process_image({
            'image_path': test_image_path,
            'tasks': ['object_detection']
        })
        
        assert result['status'] == 'success'
        assert 'results' in result
        assert 'processing_time' in result
        
    @pytest.mark.asyncio
    async def test_process_image_file_not_found(self, api):
        """Тест обработки отсутствующего файла"""
        result = await api.process_image({
            'image_path': '/nonexistent/image.jpg'
        })
        
        assert result['status'] == 'error'
        assert 'error' in result
        
    @pytest.mark.asyncio
    async def test_analyze_scene(self, api, test_image_path):
        """Тест анализа сцены"""
        result = await api.analyze_scene({
            'image_path': test_image_path
        })
        
        assert result['status'] == 'success'
        assert 'results' in result
        
    @pytest.mark.asyncio
    async def test_detect_objects(self, api, test_image_path):
        """Тест детекции объектов"""
        result = await api.detect_objects({
            'image_path': test_image_path
        })
        
        assert result['status'] == 'success'
        assert 'results' in result
        
    @pytest.mark.asyncio
    async def test_detect_faces(self, api, test_image_path):
        """Тест детекции лиц"""
        result = await api.detect_faces({
            'image_path': test_image_path
        })
        
        assert result['status'] == 'success'
        assert 'results' in result
        
    @pytest.mark.asyncio
    async def test_get_status(self, api):
        """Тест получения статуса"""
        status = await api.get_status()
        
        assert status['initialized'] == True
        assert 'supported_formats' in status
        assert 'max_image_size' in status


class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_processing_pipeline(self):
        """Тест полного пайплайна обработки"""
        from modules.interface.visual_processor.api_interface import visual_processor_api
        
        # Создаем тестовое изображение
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            image = np.zeros((200, 200, 3), dtype=np.uint8)
            cv2.rectangle(image, (50, 50), (150, 150), (255, 0, 0), -1)
            cv2.imwrite(f.name, image)
            test_path = f.name
        
        try:
            # Инициализация API
            await visual_processor_api.initialize()
            
            # Обработка изображения
            result = await visual_processor_api.process_image({
                'image_path': test_path,
                'tasks': ['object_detection', 'scene_analysis'],
                'generate_visual_output': True
            })
            
            assert result['status'] == 'success'
            assert 'results' in result
            
            # Проверяем структуру результатов
            results = result['results']
            assert 'processing_time' in results
            assert 'tasks_performed' in results
            
        finally:
            # Очистка
            if os.path.exists(test_path):
                os.unlink(test_path)
            await visual_processor_api.shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])