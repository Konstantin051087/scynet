"""
МОДУЛЯТОР ЭМОЦИЙ В РЕЧИ
Добавление эмоциональной окраски в синтезированную речь
"""

import logging
import re
from typing import Dict, Any, Tuple
import json

class EmotionModulator:
    """Модулятор эмоциональной окраски речи"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # База эмоциональных паттернов
        self.emotion_patterns = self._load_emotion_patterns()
        
        # Параметры модуляции для разных эмоций
        self.modulation_params = {
            'happy': {
                'pitch_variation': 1.2,
                'speech_rate': 1.1,
                'energy': 1.3,
                'pause_frequency': 0.8
            },
            'sad': {
                'pitch_variation': 0.8,
                'speech_rate': 0.7,
                'energy': 0.6,
                'pause_frequency': 1.2
            },
            'angry': {
                'pitch_variation': 1.4,
                'speech_rate': 1.3,
                'energy': 1.5,
                'pause_frequency': 0.6
            },
            'neutral': {
                'pitch_variation': 1.0,
                'speech_rate': 1.0,
                'energy': 1.0,
                'pause_frequency': 1.0
            },
            'excited': {
                'pitch_variation': 1.3,
                'speech_rate': 1.4,
                'energy': 1.4,
                'pause_frequency': 0.5
            },
            'calm': {
                'pitch_variation': 0.9,
                'speech_rate': 0.9,
                'energy': 0.8,
                'pause_frequency': 1.1
            }
        }
        
        self.logger.info("Модулятор эмоций инициализирован")
    
    def _load_emotion_patterns(self) -> Dict[str, Any]:
        """Загрузка эмоциональных паттернов"""
        base_patterns = {
            'happy': {
                'keywords': ['отлично', 'прекрасно', 'замечательно', 'рад', 'счастлив', 'ура'],
                'exclamations': ['!', '!!', ':)'],
                'intensifiers': ['очень', 'невероятно', 'потрясающе']
            },
            'sad': {
                'keywords': ['грустно', 'печально', 'жаль', 'расстроен', 'плохо'],
                'exclamations': ['...', ':(', ';('],
                'intensifiers': ['очень', 'сильно', 'крайне']
            },
            'angry': {
                'keywords': ['злой', 'сердит', 'разозлился', 'бесит', 'раздражен'],
                'exclamations': ['!', '!!', '!!!'],
                'intensifiers': ['очень', 'чрезвычайно', 'невероятно']
            }
        }
        return base_patterns
    
    def modulate(self, text: str, emotion: str) -> str:
        """
        Модуляция текста с учетом эмоции
        
        Args:
            text: Исходный текст
            emotion: Целевая эмоция
            
        Returns:
            Модулированный текст
        """
        if emotion not in self.modulation_params:
            self.logger.warning(f"Неизвестная эмоция: {emotion}, используется нейтральная")
            emotion = 'neutral'
        
        # Анализ исходного текста
        detected_emotion = self._detect_emotion(text)
        self.logger.debug(f"Обнаружена эмоция в тексте: {detected_emotion}")
        
        # Применение модуляции
        modulated_text = self._apply_emotional_modulation(text, emotion)
        
        return modulated_text
    
    def _detect_emotion(self, text: str) -> str:
        """Автоматическое определение эмоции в тексте"""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            
            # Проверка ключевых слов
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    score += 2
            
            # Проверка восклицаний
            for exclamation in patterns['exclamations']:
                if exclamation in text:
                    score += 1
            
            # Проверка усилителей
            for intensifier in patterns['intensifiers']:
                if intensifier in text_lower:
                    score += 1
            
            emotion_scores[emotion] = score
        
        # Определение эмоции с максимальным счетом
        if emotion_scores:
            max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            if max_emotion[1] > 0:
                return max_emotion[0]
        
        return 'neutral'
    
    def _apply_emotional_modulation(self, text: str, target_emotion: str) -> str:
        """Применение эмоциональной модуляции к тексту"""
        params = self.modulation_params[target_emotion]
        
        # Модификация текста в зависимости от эмоции
        if target_emotion == 'happy':
            text = self._make_text_happier(text)
        elif target_emotion == 'sad':
            text = self._make_text_sadder(text)
        elif target_emotion == 'angry':
            text = self._make_text_angrier(text)
        elif target_emotion == 'excited':
            text = self._make_text_excited(text)
        
        return text
    
    def _make_text_happier(self, text: str) -> str:
        """Сделать текст более радостным"""
        # Добавление позитивных междометий
        happy_words = ['здорово', 'отлично', 'прекрасно']
        if not any(word in text.lower() for word in happy_words):
            if text.endswith('.'):
                text = text[:-1] + '!'
        
        return text
    
    def _make_text_sadder(self, text: str) -> str:
        """Сделать текст более грустным"""
        # Удаление восклицательных знаков
        text = text.replace('!', '.')
        return text
    
    def _make_text_angrier(self, text: str) -> str:
        """Сделать текст более сердитым"""
        # Добавление восклицательных знаков
        if not text.endswith('!'):
            text += '!'
        return text
    
    def _make_text_excited(self, text: str) -> str:
        """Сделать текст более возбужденным"""
        if text.endswith('.'):
            text = text[:-1] + '!'
        return text
    
    def get_modulation_parameters(self, emotion: str) -> Dict[str, float]:
        """Получить параметры модуляции для конкретной эмоции"""
        return self.modulation_params.get(emotion, self.modulation_params['neutral'])
    
    def add_custom_emotion(self, emotion_name: str, parameters: Dict[str, float]):
        """Добавить пользовательскую эмоцию"""
        self.modulation_params[emotion_name] = parameters
        self.logger.info(f"Добавлена пользовательская эмоция: {emotion_name}")