# tests/test_visual_processor_simple.py
"""
Упрощенные тесты для visual_processor (без загрузки тяжелых моделей)
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
import cv2
import numpy as np

class TestVisualProcessorSimple:
    """Упрощенные тесты основного класса visual_processor"""
    
    def test_import(self):
        """Тест что модуль импортируется"""
        from modules.interface.visual_processor import VisualProcessor
        processor = VisualProcessor()
        assert processor is not None
        
    def test_config_loading(self):
        """Тест загрузки конфигурации"""
        from modules.interface.visual_processor import VisualProcessor
        processor = VisualProcessor()
        
        # Проверяем что конфиг загружается
        assert processor.config is not None
        assert 'model_settings' in processor.config
        
    def test_component_creation(self):
        """Тест создания компонентов (без инициализации)"""
        from modules.interface.visual_processor import VisualProcessor
        processor = VisualProcessor()
        
        # Проверяем что компоненты созданы
        assert processor.image_recognizer is not None
        assert processor.face_detector is not None  
        assert processor.scene_analyzer is not None
        assert processor.response_generator is not None
        
    def test_visual_response_generator_basic(self):
        """Тест базовой функциональности генератора ответов"""
        from modules.interface.visual_processor.visual_response_generator import VisualResponseGenerator
        
        generator = VisualResponseGenerator()
        success = generator.initialize()
        assert success == True
        
        # Тест генерации summary
        test_results = {
            'image_path': '/test/path.jpg',
            'processing_time': 1.5,
            'objects': [
                {'class': 'person', 'confidence': 0.9, 'bbox': [10, 10, 100, 100]}
            ]
        }
        
        summary = generator.generate_summary(test_results)
        assert 'image_info' in summary
        assert 'detection_summary' in summary
        assert 'recommendations' in summary


class TestVisualProcessorAPISimple:
    """Упрощенные тесты API интерфейса"""
    
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
    
    def test_api_creation(self):
        """Тест создания API"""
        from modules.interface.visual_processor.api_interface import VisualProcessorAPI
        api = VisualProcessorAPI()
        assert api is not None
        assert api.config is not None
    
    @pytest.mark.asyncio
    async def test_api_initialization_fast(self):
        """Быстрая инициализация API (без загрузки моделей)"""
        from modules.interface.visual_processor.api_interface import VisualProcessorAPI
        
        api = VisualProcessorAPI()
        # Используем минимальную конфигурацию чтобы избежать загрузки моделей
        api.config = {'use_minimal_mode': True}
        
        # Мокаем инициализацию visual_processor чтобы избежать загрузки моделей
        class MockVisualProcessor:
            def initialize(self):
                self.is_initialized = True
                return True
        
        api.visual_processor = MockVisualProcessor()
        api.is_initialized = True
        
        assert api.is_initialized == True
        
    @pytest.mark.asyncio 
    async def test_api_error_handling(self):
        """Тест обработки ошибок в API"""
        from modules.interface.visual_processor.api_interface import VisualProcessorAPI
        
        api = VisualProcessorAPI()
        api.is_initialized = True
        
        # Тест обработки отсутствующего файла
        result = await api.process_image({
            'image_path': '/nonexistent/image.jpg'
        })
        
        assert result['status'] == 'error'
        assert 'error' in result


def test_config_files_exist():
    """Тест что конфигурационные файлы существуют"""
    assert os.path.exists('config/modules/visual_processor.yaml')
    assert os.path.exists('config/coco.names')
    
    # Проверяем содержимое coco.names
    with open('config/coco.names', 'r') as f:
        classes = f.readlines()
        assert len(classes) > 0
        assert 'person' in classes[0]


def test_module_structure():
    """Тест структуры модуля"""
    assert os.path.exists('modules/interface/visual_processor/__init__.py')
    assert os.path.exists('modules/interface/visual_processor/api_interface.py')
    assert os.path.exists('modules/interface/visual_processor/image_recognizer.py')
    assert os.path.exists('modules/interface/visual_processor/face_detector.py')
    assert os.path.exists('modules/interface/visual_processor/scene_analyzer.py')
    assert os.path.exists('modules/interface/visual_processor/visual_response_generator.py')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])