"""
Детектор эмоций в тексте и речи
Использует NLP модели для определения эмоциональной окраски
"""

import re
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import yaml
import os

class EmotionDetector:
    def __init__(self, model_path: Optional[str] = None):
        try:
            self.logger = logging.getLogger("EmotionDetector")
            self.emotion_categories = [
                'joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 
                'neutral', 'excitement', 'frustration', 'contentment'
            ]
            
            # Загрузка эмоциональных паттернов
            self.load_emotional_patterns()
            
            # Инициализация модели (заглушка - в реальности использовать transformers)
            self.model_loaded = False
            self.load_model(model_path)
            self.logger.info("✅ Emotion Detector инициализирован")
        except Exception as e:
            self.logger = logging.getLogger("EmotionDetector")
            self.logger.error(f"❌ Ошибка инициализации Emotion Detector: {e}")
            self.emotion_categories = ['neutral']
            self.emotional_patterns = {}
    
    def load_emotional_patterns(self):
        """Загрузка паттернов эмоций из конфигурации"""
        try:
            config_path = os.path.join('config', 'emotional_rules.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.emotional_patterns = config.get('emotion_patterns', {})
        except FileNotFoundError:
            self.logger.warning("⚠️ Файл emotional_rules.yaml не найден, используются значения по умолчанию")
            # Паттерны по умолчанию
            self.emotional_patterns = {
                'joy': ['рад', 'счастлив', 'ура', 'отлично', 'прекрасно', 'замечательно'],
                'sadness': ['грустно', 'печально', 'плохо', 'тоска', 'несчастен'],
                'anger': ['злой', 'сердит', 'разозлился', 'бесит', 'раздражен'],
                'fear': ['боюсь', 'страшно', 'испуг', 'тревожно', 'опасно'],
                'surprise': ['удивлен', 'неожиданно', 'ого', 'вау', 'невероятно'],
                'excitement': ['волнуюсь', 'взволнован', 'ожидание', 'интересно']
            }
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки паттернов эмоций: {e}")
            self.emotional_patterns = {
                'neutral': ['нейтрально', 'нормально', 'обычно']
            }
    
    def load_model(self, model_path: Optional[str]):
        """Загрузка ML модели для детекции эмоций"""
        try:
            # В реальной реализации здесь будет загрузка модели из Hugging Face
            # Например: from transformers import pipeline
            # self.classifier = pipeline("text-classification", model=model_path)
            self.model_loaded = True
            self.logger.info("✅ Emotion detection model loaded (simulated)")
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модели: {e}")
            self.model_loaded = False
    
    def detect_emotions(self, text: str) -> Dict[str, float]:
        """Определение эмоций в тексте"""
        try:
            if not text or not isinstance(text, str):
                return {'neutral': 1.0}
            
            text_lower = text.lower()
            emotion_scores = {emotion: 0.0 for emotion in self.emotion_categories}
            
            # Анализ по ключевым словам
            for emotion, patterns in self.emotional_patterns.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        emotion_scores[emotion] += 0.3
            
            # Анализ эмоциональных маркеров
            emotion_scores = self._analyze_emotional_markers(text_lower, emotion_scores)
            
            # Анализ знаков препинания и регистра
            emotion_scores = self._analyze_text_features(text, emotion_scores)
            
            # Нормализация scores
            total = sum(emotion_scores.values())
            if total > 0:
                emotion_scores = {k: v/total for k, v in emotion_scores.items()}
            else:
                emotion_scores['neutral'] = 1.0
            
            return emotion_scores
        except Exception as e:
            self.logger.error(f"❌ Ошибка детекции эмоций: {e}")
            return {'neutral': 1.0}
    
    def _analyze_emotional_markers(self, text: str, scores: Dict[str, float]) -> Dict[str, float]:
        """Анализ эмоциональных маркеров в тексте"""
        try:
            # Восклицательные знаки - радость/гнев
            if '!' in text:
                scores['joy'] += 0.2
                scores['anger'] += 0.1
                scores['excitement'] += 0.1
            
            # Вопросительные знаки - удивление/страх
            if '?' in text:
                scores['surprise'] += 0.2
                scores['fear'] += 0.1
            
            # Многоточие - грусть/неуверенность
            if '...' in text or '…' in text:
                scores['sadness'] += 0.2
                scores['fear'] += 0.1
            
            # Капс - гнев/возбуждение
            if text.upper() == text and len(text) > 3:
                scores['anger'] += 0.3
                scores['excitement'] += 0.2
            
            return scores
        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа эмоциональных маркеров: {e}")
            return scores
    
    def _analyze_text_features(self, text: str, scores: Dict[str, float]) -> Dict[str, float]:
        """Анализ особенностей текста"""
        try:
            words = text.split()
            
            # Длина текста
            if len(words) < 3:
                scores['neutral'] += 0.2
            
            # Повторы букв (например: "нооорм")
            for word in words:
                if len(word) > 3:
                    for i in range(len(word) - 2):
                        if word[i] == word[i+1] == word[i+2]:
                            scores['excitement'] += 0.1
                            break
            
            return scores
        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа особенностей текста: {e}")
            return scores
    
    def detect_emotion_intensity(self, emotion_scores: Dict[str, float]) -> float:
        """Определение интенсивности доминирующей эмоции"""
        try:
            if not emotion_scores:
                return 0.0
            
            max_score = max(emotion_scores.values())
            return max_score
        except Exception as e:
            self.logger.error(f"❌ Ошибка определения интенсивности эмоции: {e}")
            return 0.0