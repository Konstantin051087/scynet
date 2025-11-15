"""
МОДУЛЬ АНАЛИЗА СЦЕН И КОНТЕКСТА
"""

import cv2
import numpy as np
import torch
from transformers import ViTFeatureExtractor, ViTForImageClassification
from PIL import Image
import torchvision.transforms as transforms
from typing import Dict, Any, List

class SceneAnalyzer:
    """Класс для анализа сцен и контекста изображений"""
    
    def __init__(self):
        self.feature_extractor = None
        self.scene_model = None
        self.is_initialized = False
        self.scene_categories = []
        
    def initialize(self):
        """Инициализация моделей анализа сцен"""
        try:
            # Использование Vision Transformer для классификации сцен
            model_name = "google/vit-base-patch16-224"
            self.feature_extractor = ViTFeatureExtractor.from_pretrained(model_name)
            self.scene_model = ViTForImageClassification.from_pretrained(model_name)
            
            # Загрузка категорий сцен
            self._load_scene_categories()
            
            self.is_initialized = True
            print("Модель анализа сцен инициализирована")
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации анализатора сцен: {e}")
            return self._initialize_fallback()
    
    def _initialize_fallback(self):
        """Fallback инициализация с OpenCV и традиционным CV"""
        try:
            # Простой анализатор цветов и текстур
            self.is_initialized = True
            print("Используется базовый анализатор сцен")
            return True
            
        except Exception as e:
            print(f"Ошибка fallback инициализации: {e}")
            return False
    
    def _load_scene_categories(self):
        """Загрузка категорий сцен"""
        # Базовые категории сцен
        self.scene_categories = [
            'indoors', 'outdoors', 'urban', 'nature', 'water', 
            'mountain', 'forest', 'beach', 'street', 'building',
            'room', 'vehicle', 'animal', 'person', 'food',
            'sports', 'art', 'document', 'other'
        ]
    
    def analyze_scene(self, image_path: str) -> Dict[str, Any]:
        """
        Комплексный анализ сцены
        
        Args:
            image_path (str): Путь к изображению
            
        Returns:
            dict: Результаты анализа сцены
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            image = Image.open(image_path)
            
            analysis_results = {
                'scene_type': self._classify_scene_type(image),
                'color_analysis': self._analyze_colors(image_path),
                'texture_analysis': self._analyze_texture(image_path),
                'composition': self._analyze_composition(image_path),
                'lighting_conditions': self._analyze_lighting(image_path),
                'key_elements': self._extract_key_elements(image_path)
            }
            
            # Генерация текстового описания сцены
            analysis_results['description'] = self._generate_scene_description(
                analysis_results
            )
            
            return analysis_results
            
        except Exception as e:
            print(f"Ошибка анализа сцены: {e}")
            return {'error': str(e)}
    
    def _classify_scene_type(self, image: Image.Image) -> Dict[str, float]:
        """Классификация типа сцены"""
        try:
            if self.scene_model:
                # Использование ViT для классификации
                inputs = self.feature_extractor(images=image, return_tensors="pt")
                outputs = self.scene_model(**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                top_probs, top_indices = torch.topk(probabilities, 5)
                
                scene_types = {}
                for i in range(5):
                    label = self.scene_model.config.id2label[top_indices[0][i].item()]
                    confidence = top_probs[0][i].item()
                    scene_types[label] = round(confidence, 3)
                
                return scene_types
            else:
                # Базовая классификация по цветовым характеристикам
                return self._basic_scene_classification(image)
                
        except Exception as e:
            print(f"Ошибка классификации сцены: {e}")
            return {'unknown': 1.0}
    
    def _basic_scene_classification(self, image: Image.Image) -> Dict[str, float]:
        """Базовая классификация сцены"""
        # Упрощенная логика классификации на основе цветов
        np_image = np.array(image)
        
        # Анализ доминирующих цветов
        hsv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2HSV)
        
        # Определение типа сцены по цветовому распределению
        scene_scores = {}
        
        # Анализ зеленого (природа)
        green_mask = cv2.inRange(hsv_image, (36, 25, 25), (86, 255, 255))
        green_ratio = np.sum(green_mask > 0) / (image.size[0] * image.size[1])
        scene_scores['nature'] = min(green_ratio * 3, 1.0)
        
        # Анализ синего (вода/небо)
        blue_mask = cv2.inRange(hsv_image, (100, 50, 50), (130, 255, 255))
        blue_ratio = np.sum(blue_mask > 0) / (image.size[0] * image.size[1])
        scene_scores['water_sky'] = min(blue_ratio * 2, 1.0)
        
        # Анализ серого (городские структуры)
        gray_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
        edge_density = cv2.Canny(gray_image, 50, 150)
        edge_ratio = np.sum(edge_density > 0) / (image.size[0] * image.size[1])
        scene_scores['urban'] = min(edge_ratio * 5, 1.0)
        
        # Нормализация scores
        total = sum(scene_scores.values())
        if total > 0:
            for key in scene_scores:
                scene_scores[key] = round(scene_scores[key] / total, 3)
        
        return scene_scores
    
    def _analyze_colors(self, image_path: str) -> Dict[str, Any]:
        """Анализ цветовой палитры изображения"""
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Преобразование в HSV для анализа
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        color_analysis = {
            'dominant_colors': self._extract_dominant_colors(image_rgb),
            'color_variance': float(np.var(image_rgb) / 255),
            'brightness': float(np.mean(hsv_image[:,:,2]) / 255),
            'saturation': float(np.mean(hsv_image[:,:,1]) / 255),
            'color_temperature': self._estimate_color_temperature(hsv_image)
        }
        
        return color_analysis
    
    def _extract_dominant_colors(self, image: np.ndarray, k: int = 5) -> List[Dict]:
        """Извлечение доминирующих цветов с использованием k-means"""
        from sklearn.cluster import KMeans
        
        pixels = image.reshape(-1, 3)
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(pixels)
        
        colors = []
        for center in kmeans.cluster_centers_:
            colors.append({
                'rgb': [int(c) for c in center],
                'percentage': round(np.sum(kmeans.labels_ == np.argmax(kmeans.cluster_centers_, axis=0)[0]) / len(kmeans.labels_), 3)
            })
        
        return colors
    
    def _estimate_color_temperature(self, hsv_image: np.ndarray) -> str:
        """Оценка цветовой температуры"""
        hue_mean = np.mean(hsv_image[:,:,0])
        
        if hue_mean < 30:
            return 'warm'
        elif hue_mean < 90:
            return 'neutral'
        else:
            return 'cool'
    
    def _analyze_texture(self, image_path: str) -> Dict[str, float]:
        """Анализ текстурных характеристик"""
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        texture_analysis = {
            'smoothness': float(1 / (1 + np.var(cv2.Laplacian(image, cv2.CV_64F)))),
            'contrast': float(np.std(image)),
            'homogeneity': self._calculate_homogeneity(image),
            'entropy': self._calculate_entropy(image)
        }
        
        return texture_analysis
    
    def _calculate_homogeneity(self, image: np.ndarray) -> float:
        """Вычисление однородности текстуры"""
        from skimage.feature import greycomatrix, greycoprops
        
        glcm = greycomatrix(image, [1], [0], symmetric=True, normed=True)
        homogeneity = greycoprops(glcm, 'homogeneity')[0, 0]
        return float(homogeneity)
    
    def _calculate_entropy(self, image: np.ndarray) -> float:
        """Вычисление энтропии изображения"""
        histogram = cv2.calcHist([image], [0], None, [256], [0, 256])
        histogram /= histogram.sum()
        entropy = -np.sum(histogram * np.log2(histogram + 1e-10))
        return float(entropy)
    
    def _analyze_composition(self, image_path: str) -> Dict[str, Any]:
        """Анализ композиции изображения"""
        image = cv2.imread(image_path)
        height, width = image.shape[:2]
        
        composition = {
            'aspect_ratio': round(width / height, 2),
            'rule_of_thirds_score': self._calculate_rule_of_thirds(image),
            'symmetry_score': self._calculate_symmetry(image),
            'balance_score': self._calculate_balance(image)
        }
        
        return composition
    
    def _calculate_rule_of_thirds(self, image: np.ndarray) -> float:
        """Оценка правила третей"""
        # Упрощенная реализация - можно улучшить
        edges = cv2.Canny(image, 50, 150)
        third_x = image.shape[1] // 3
        third_y = image.shape[0] // 3
        
        # Подсчет edges в областях правила третей
        interest_zones = [
            (third_x, third_y, third_x * 2, third_y * 2)
        ]
        
        total_edges = np.sum(edges > 0)
        if total_edges == 0:
            return 0.0
        
        zone_edges = 0
        for zone in interest_zones:
            x1, y1, x2, y2 = zone
            zone_edges += np.sum(edges[y1:y2, x1:x2] > 0)
        
        return round(zone_edges / total_edges, 3)
    
    def _calculate_symmetry(self, image: np.ndarray) -> float:
        """Оценка симметрии"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        flipped = cv2.flip(gray, 1)
        diff = cv2.absdiff(gray, flipped)
        symmetry_score = 1 - (np.mean(diff) / 255)
        return round(symmetry_score, 3)
    
    def _calculate_balance(self, image: np.ndarray) -> float:
        """Оценка баланса композиции"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        left_half = gray[:, :gray.shape[1]//2]
        right_half = gray[:, gray.shape[1]//2:]
        
        left_brightness = np.mean(left_half)
        right_brightness = np.mean(right_half)
        
        balance = 1 - abs(left_brightness - right_brightness) / 255
        return round(balance, 3)
    
    def _analyze_lighting(self, image_path: str) -> Dict[str, float]:
        """Анализ условий освещения"""
        image = cv2.imread(image_path)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        lighting = {
            'brightness': float(np.mean(hsv[:,:,2]) / 255),
            'contrast': float(np.std(image) / 255),
            'shadow_intensity': self._estimate_shadow_intensity(hsv),
            'highlight_ratio': self._calculate_highlight_ratio(hsv)
        }
        
        return lighting
    
    def _estimate_shadow_intensity(self, hsv_image: np.ndarray) -> float:
        """Оценка интенсивности теней"""
        low_value_mask = hsv_image[:,:,2] < 50
        shadow_ratio = np.sum(low_value_mask) / (hsv_image.shape[0] * hsv_image.shape[1])
        return round(shadow_ratio, 3)
    
    def _calculate_highlight_ratio(self, hsv_image: np.ndarray) -> float:
        """Вычисление соотношения светлых областей"""
        high_value_mask = hsv_image[:,:,2] > 200
        highlight_ratio = np.sum(high_value_mask) / (hsv_image.shape[0] * hsv_image.shape[1])
        return round(highlight_ratio, 3)
    
    def _extract_key_elements(self, image_path: str) -> List[str]:
        """Извлечение ключевых элементов сцены"""
        # Используем простые эвристики для определения ключевых элементов
        elements = []
        
        # Можно интегрировать с image_recognizer для более точного определения
        try:
            from .image_recognizer import ImageRecognizer
            recognizer = ImageRecognizer()
            objects = recognizer.detect_objects(image_path)
            
            for obj in objects:
                if obj['confidence'] > 0.7:
                    elements.append(obj['class'])
        
        except Exception as e:
            print(f"Ошибка извлечения ключевых элементов: {e}")
        
        return list(set(elements))  # Уникальные элементы
    
    def _generate_scene_description(self, analysis_results: Dict) -> str:
        """Генерация текстового описания сцены"""
        scene_type = max(analysis_results['scene_type'].items(), key=lambda x: x[1])[0]
        lighting = analysis_results['lighting_conditions']
        
        description_parts = []
        
        # Тип сцены
        description_parts.append(f"Сцена классифицирована как: {scene_type}")
        
        # Освещение
        if lighting['brightness'] > 0.7:
            description_parts.append("Хорошо освещенная сцена")
        elif lighting['brightness'] < 0.3:
            description_parts.append("Темная сцена")
        
        # Ключевые элементы
        if analysis_results['key_elements']:
            elements = ", ".join(analysis_results['key_elements'][:5])
            description_parts.append(f"Ключевые элементы: {elements}")
        
        # Композиция
        if analysis_results['composition']['rule_of_thirds_score'] > 0.6:
            description_parts.append("Хорошая композиция по правилу третей")
        
        return ". ".join(description_parts)