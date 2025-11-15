"""
МОДУЛЬ ОБРАБОТКИ ИЗОБРАЖЕНИЙ (ЗРЕНИЕ)
Инициализация пакета visual_processor
"""

from .image_recognizer import ImageRecognizer
from .face_detector import FaceDetector
from .scene_analyzer import SceneAnalyzer
from .visual_response_generator import VisualResponseGenerator

__all__ = [
    'ImageRecognizer',
    'FaceDetector', 
    'SceneAnalyzer',
    'VisualResponseGenerator'
]

# Версия модуля
__version__ = "1.0.0"
__author__ = "Synthetic Mind Team"

class VisualProcessor:
    """Основной класс модуля обработки изображений"""
    
    def __init__(self, config_path=None):
        """
        Инициализация модуля обработки изображений
        
        Args:
            config_path (str): Путь к конфигурационному файлу
        """
        self.image_recognizer = ImageRecognizer()
        self.face_detector = FaceDetector()
        self.scene_analyzer = SceneAnalyzer()
        self.response_generator = VisualResponseGenerator()
        
        self.is_initialized = False
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path):
        """Загрузка конфигурации"""
        import yaml
        import os
        
        default_config = {
            'model_settings': {
                'confidence_threshold': 0.7,
                'max_faces': 10,
                'image_size': (640, 640)
            },
            'performance': {
                'use_gpu': True,
                'batch_size': 4
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    # Объединяем с конфигом по умолчанию
                    default_config.update(user_config)
            except Exception as e:
                print(f"Ошибка загрузки конфига: {e}")
        
        return default_config
    
    def initialize(self):
        """Инициализация всех компонентов модуля"""
        try:
            self.image_recognizer.initialize()
            self.face_detector.initialize()
            self.scene_analyzer.initialize()
            self.response_generator.initialize()
            
            self.is_initialized = True
            print("Модуль обработки изображений успешно инициализирован")
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации модуля обработки изображений: {e}")
            return False
    
    def process_image(self, image_path, tasks=None):
        """
        Основной метод обработки изображения
        
        Args:
            image_path (str): Путь к изображению
            tasks (list): Список задач для выполнения
            
        Returns:
            dict: Результаты обработки
        """
        if not self.is_initialized:
            self.initialize()
        
        if tasks is None:
            tasks = ['object_detection', 'face_detection', 'scene_analysis']
        
        results = {
            'image_path': image_path,
            'processing_time': None,
            'tasks_performed': tasks
        }
        
        import time
        start_time = time.time()
        
        try:
            # Выполнение запрошенных задач
            if 'object_detection' in tasks:
                results['objects'] = self.image_recognizer.detect_objects(image_path)
            
            if 'face_detection' in tasks:
                results['faces'] = self.face_detector.detect_faces(image_path)
                results['emotions'] = self.face_detector.analyze_emotions(image_path)
            
            if 'scene_analysis' in tasks:
                results['scene'] = self.scene_analyzer.analyze_scene(image_path)
            
            # Генерация сводного ответа
            results['summary'] = self.response_generator.generate_summary(results)
            
            processing_time = time.time() - start_time
            results['processing_time'] = round(processing_time, 2)
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            return results
    
    def generate_visual_response(self, analysis_results, output_path=None):
        """Генерация визуального ответа"""
        return self.response_generator.create_visual_output(
            analysis_results, 
            output_path
        )