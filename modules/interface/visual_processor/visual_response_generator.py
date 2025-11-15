"""
МОДУЛЬ ГЕНЕРАЦИИ ВИЗУАЛЬНЫХ ОТВЕТОВ
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import json
from typing import Dict, Any, List, Optional
import os

class VisualResponseGenerator:
    """Класс для генерации визуальных ответов на основе анализа"""
    
    def __init__(self):
        self.is_initialized = False
        self.colors = {
            'object': (0, 255, 0),      # Зеленый для объектов
            'face': (255, 0, 0),        # Синий для лиц
            'emotion': (0, 0, 255),     # Красный для эмоций
            'text': (255, 255, 255),    # Белый для текста
            'background': (0, 0, 0)     # Черный для фона
        }
        
    def initialize(self):
        """Инициализация генератора визуальных ответов"""
        try:
            # Проверка доступности шрифтов
            self._load_fonts()
            self.is_initialized = True
            print("Генератор визуальных ответов инициализирован")
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации генератора: {e}")
            return False
    
    def _load_fonts(self):
        """Загрузка шрифтов для аннотаций"""
        self.fonts = {}
        try:
            # Попытка загрузки разных шрифтов
            font_sizes = {'small': 12, 'medium': 16, 'large': 20}
            
            for size_name, size in font_sizes.items():
                try:
                    self.fonts[size_name] = ImageFont.truetype("arial.ttf", size)
                except:
                    # Fallback на базовый шрифт
                    self.fonts[size_name] = ImageFont.load_default()
                    
        except Exception as e:
            print(f"Ошибка загрузки шрифтов: {e}")
            # Использование шрифтов по умолчанию
            self.fonts = {
                'small': ImageFont.load_default(),
                'medium': ImageFont.load_default(),
                'large': ImageFont.load_default()
            }
    
    def generate_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерация сводки по результатам анализа
        
        Args:
            analysis_results (dict): Результаты анализа изображения
            
        Returns:
            dict: Сводная информация
        """
        summary = {
            'image_info': {
                'path': analysis_results.get('image_path', 'unknown'),
                'processing_time': analysis_results.get('processing_time', 0)
            },
            'detection_summary': {},
            'scene_summary': {},
            'recommendations': []
        }
        
        # Сводка по объектам
        if 'objects' in analysis_results:
            objects = analysis_results['objects']
            summary['detection_summary']['total_objects'] = len(objects)
            summary['detection_summary']['object_types'] = list(set(
                obj['class'] for obj in objects
            ))
        
        # Сводка по лицам
        if 'faces' in analysis_results:
            faces = analysis_results['faces']
            summary['detection_summary']['total_faces'] = len(faces)
        
        # Сводка по эмоциям
        if 'emotions' in analysis_results:
            emotions = analysis_results['emotions']
            if emotions:
                dominant_emotions = [e['dominant_emotion'] for e in emotions]
                summary['detection_summary']['dominant_emotions'] = list(set(dominant_emotions))
        
        # Сводка по сцене
        if 'scene' in analysis_results:
            scene = analysis_results['scene']
            summary['scene_summary'] = {
                'scene_type': scene.get('scene_type', {}),
                'lighting_conditions': scene.get('lighting_conditions', {}),
                'key_elements': scene.get('key_elements', [])
            }
        
        # Генерация рекомендаций
        summary['recommendations'] = self._generate_recommendations(analysis_results)
        
        return summary
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций на основе анализа"""
        recommendations = []
        
        # Анализ объектов
        if 'objects' in analysis_results:
            objects = analysis_results['objects']
            if len(objects) > 20:
                recommendations.append("Изображение содержит много объектов, рассмотрите упрощение композиции")
            elif len(objects) < 3:
                recommendations.append("Изображение содержит мало объектов, возможно стоит добавить деталей")
        
        # Анализ лиц
        if 'faces' in analysis_results:
            faces = analysis_results['faces']
            if len(faces) == 0:
                recommendations.append("На изображении не обнаружено лиц")
            else:
                for face in faces:
                    if face.get('area', 0) < 1000:
                        recommendations.append("Обнаружены маленькие лица, рассмотрите съемку с более близкого расстояния")
        
        # Анализ сцены
        if 'scene' in analysis_results:
            scene = analysis_results['scene']
            lighting = scene.get('lighting_conditions', {})
            
            if lighting.get('brightness', 0.5) < 0.3:
                recommendations.append("Изображение слишком темное, увеличьте освещение")
            elif lighting.get('brightness', 0.5) > 0.8:
                recommendations.append("Изображение переэкспонировано, уменьшите освещение")
            
            composition = scene.get('composition', {})
            if composition.get('rule_of_thirds_score', 0) < 0.3:
                recommendations.append("Рассмотрите использование правила третей для улучшения композиции")
        
        return recommendations[:5]  # Ограничиваем 5 рекомендациями
    
    def create_visual_output(self, 
                           analysis_results: Dict[str, Any], 
                           output_path: Optional[str] = None) -> np.ndarray:
        """
        Создание визуального представления результатов анализа
        
        Args:
            analysis_results (dict): Результаты анализа
            output_path (str, optional): Путь для сохранения
            
        Returns:
            numpy.ndarray: Изображение с визуализацией
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            image_path = analysis_results.get('image_path')
            if not image_path or not os.path.exists(image_path):
                raise ValueError("Неверный путь к изображению")
            
            # Загрузка исходного изображения
            original_image = cv2.imread(image_path)
            if original_image is None:
                raise ValueError("Не удалось загрузить изображение")
            
            # Создание визуализации
            visualized_image = self._create_annotation_overlay(
                original_image, 
                analysis_results
            )
            
            # Создание информационной панели
            final_image = self._create_info_panel(
                visualized_image, 
                analysis_results
            )
            
            if output_path:
                cv2.imwrite(output_path, final_image)
                print(f"Визуальный ответ сохранен: {output_path}")
            
            return final_image
            
        except Exception as e:
            print(f"Ошибка создания визуального ответа: {e}")
            # Возврат черного изображения с сообщением об ошибке
            return self._create_error_image(str(e))
    
    def _create_annotation_overlay(self, 
                                 image: np.ndarray, 
                                 analysis_results: Dict[str, Any]) -> np.ndarray:
        """Создание аннотаций поверх изображения"""
        annotated_image = image.copy()
        
        # Аннотации объектов
        if 'objects' in analysis_results:
            for obj in analysis_results['objects']:
                if obj['confidence'] > 0.5:  # Только уверенные детекции
                    self._draw_object_annotation(annotated_image, obj)
        
        # Аннотации лиц
        if 'faces' in analysis_results:
            for face in analysis_results['faces']:
                self._draw_face_annotation(annotated_image, face)
        
        # Аннотации эмоций
        if 'emotions' in analysis_results:
            for emotion in analysis_results['emotions']:
                self._draw_emotion_annotation(annotated_image, emotion)
        
        return annotated_image
    
    def _draw_object_annotation(self, image: np.ndarray, obj: Dict[str, Any]):
        """Отрисовка аннотации объекта"""
        bbox = obj['bbox']
        class_name = obj['class']
        confidence = obj['confidence']
        
        x1, y1, x2, y2 = bbox
        
        # Рисование bounding box
        cv2.rectangle(image, (x1, y1), (x2, y2), self.colors['object'], 2)
        
        # Текст с классом и уверенностью
        label = f"{class_name}: {confidence:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        
        # Фон для текста
        cv2.rectangle(image, (x1, y1 - label_size[1] - 10), 
                     (x1 + label_size[0], y1), self.colors['object'], -1)
        
        # Текст
        cv2.putText(image, label, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 2)
    
    def _draw_face_annotation(self, image: np.ndarray, face: Dict[str, Any]):
        """Отрисовка аннотации лица"""
        bbox = face['bbox']
        x, y, w, h = bbox
        
        # Рисование bounding box лица
        cv2.rectangle(image, (x, y), (x + w, y + h), self.colors['face'], 2)
        
        # ID лица
        face_id = face.get('face_id', 0)
        label = f"Face {face_id}"
        
        cv2.putText(image, label, (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['face'], 2)
    
    def _draw_emotion_annotation(self, image: np.ndarray, emotion: Dict[str, Any]):
        """Отрисовка аннотации эмоции"""
        bbox = emotion['bbox']
        dominant_emotion = emotion['dominant_emotion']
        confidence = emotion['emotion_confidence']
        
        x, y, w, h = bbox
        
        # Текст эмоции
        label = f"{dominant_emotion}: {confidence:.2f}"
        
        # Размещение текста под bounding box лица
        text_y = y + h + 20
        
        cv2.putText(image, label, (x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['emotion'], 2)
    
    def _create_info_panel(self, 
                          image: np.ndarray, 
                          analysis_results: Dict[str, Any]) -> np.ndarray:
        """Создание информационной панели с результатами"""
        height, width = image.shape[:2]
        
        # Создание панели с текстовой информацией
        panel_height = 200
        panel_width = width
        
        # Создание панели
        info_panel = np.zeros((panel_height, panel_width, 3), dtype=np.uint8)
        info_panel[:] = (50, 50, 50)  # Темно-серый фон
        
        # Конвертация для использования PIL для текста
        info_panel_pil = Image.fromarray(info_panel)
        draw = ImageDraw.Draw(info_panel_pil)
        
        # Генерация текстовой информации
        summary = self.generate_summary(analysis_results)
        
        text_lines = [
            "РЕЗУЛЬТАТЫ АНАЛИЗА ИЗОБРАЖЕНИЯ",
            f"Время обработки: {summary['image_info']['processing_time']} сек",
            f"Обнаружено объектов: {summary['detection_summary'].get('total_objects', 0)}",
            f"Обнаружено лиц: {summary['detection_summary'].get('total_faces', 0)}",
            ""
        ]
        
        # Добавление рекомендаций
        if summary['recommendations']:
            text_lines.append("РЕКОМЕНДАЦИИ:")
            for rec in summary['recommendations'][:3]:  # Первые 3 рекомендации
                text_lines.append(f"• {rec}")
        
        # Отрисовка текста
        y_offset = 10
        for line in text_lines:
            draw.text((10, y_offset), line, fill=(255, 255, 255), 
                     font=self.fonts['small'])
            y_offset += 20
        
        # Конвертация обратно в OpenCV format
        info_panel = np.array(info_panel_pil)
        
        # Объединение с основным изображением
        final_image = np.vstack([image, info_panel])
        
        return final_image
    
    def _create_error_image(self, error_message: str) -> np.ndarray:
        """Создание изображения с сообщением об ошибке"""
        height, width = 400, 600
        error_image = np.zeros((height, width, 3), dtype=np.uint8)
        error_image[:] = (0, 0, 0)  # Черный фон
        
        # Конвертация для текста
        error_image_pil = Image.fromarray(error_image)
        draw = ImageDraw.Draw(error_image_pil)
        
        # Текст ошибки
        lines = [
            "ОШИБКА ВИЗУАЛИЗАЦИИ",
            "",
            error_message[:100]  # Ограничение длины
        ]
        
        y_offset = 50
        for line in lines:
            draw.text((50, y_offset), line, fill=(255, 255, 255), 
                     font=self.fonts['medium'])
            y_offset += 30
        
        return np.array(error_image_pil)
    
    def generate_comparison_view(self, 
                               image_paths: List[str], 
                               analysis_results: List[Dict],
                               output_path: Optional[str] = None) -> np.ndarray:
        """
        Генерация сравнительного представления нескольких изображений
        
        Args:
            image_paths (list): Список путей к изображениям
            analysis_results (list): Результаты анализа для каждого изображения
            output_path (str, optional): Путь для сохранения
            
        Returns:
            numpy.ndarray: Сравнительное изображение
        """
        if len(image_paths) != len(analysis_results):
            raise ValueError("Количество изображений и результатов анализа должно совпадать")
        
        visualized_images = []
        for img_path, results in zip(image_paths, analysis_results):
            try:
                vis_image = self.create_visual_output(results)
                visualized_images.append(vis_image)
            except Exception as e:
                print(f"Ошибка обработки {img_path}: {e}")
                error_image = self._create_error_image(str(e))
                visualized_images.append(error_image)
        
        # Создание сетки изображений
        if len(visualized_images) == 1:
            comparison_image = visualized_images[0]
        else:
            # Простая вертикальная компоновка
            comparison_image = np.vstack(visualized_images)
        
        if output_path:
            cv2.imwrite(output_path, comparison_image)
        
        return comparison_image
    
    def create_analysis_report(self, 
                             analysis_results: Dict[str, Any], 
                             output_path: str):
        """
        Создание полного отчета анализа в формате JSON
        
        Args:
            analysis_results (dict): Результаты анализа
            output_path (str): Путь для сохранения отчета
        """
        try:
            report = {
                'metadata': {
                    'timestamp': self._get_timestamp(),
                    'version': '1.0',
                    'module': 'visual_processor'
                },
                'analysis_summary': self.generate_summary(analysis_results),
                'detailed_results': analysis_results
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"Отчет сохранен: {output_path}")
            return report
            
        except Exception as e:
            print(f"Ошибка создания отчета: {e}")
            return {'error': str(e)}
    
    def _get_timestamp(self) -> str:
        """Получение текущей временной метки"""
        from datetime import datetime
        return datetime.now().isoformat()