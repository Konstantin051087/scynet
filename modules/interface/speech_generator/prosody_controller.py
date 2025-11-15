"""
КОНТРОЛЛЕР ИНТОНАЦИИ И РИТМА
Управление просодическими характеристиками речи
"""

import re
import logging
from typing import Dict, Any, List, Tuple
import random

class ProsodyController:
    """Контроллер просодических характеристик речи"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Паттерны интонации для разных типов предложений
        self.intonation_patterns = {
            'statement': {
                'pattern': 'falling',
                'final_pitch': 0.8,
                'range': 0.3
            },
            'question': {
                'pattern': 'rising',
                'final_pitch': 1.3,
                'range': 0.5
            },
            'exclamation': {
                'pattern': 'peak',
                'final_pitch': 1.5,
                'range': 0.7
            },
            'command': {
                'pattern': 'falling',
                'final_pitch': 0.7,
                'range': 0.4
            }
        }
        
        # Настройки ритма
        self.rhythm_settings = {
            'base_speed': config.get('base_speed', 1.0),
            'pause_duration': config.get('pause_duration', 0.3),
            'emphasis_strength': config.get('emphasis_strength', 1.2)
        }
        
        # Эмоциональные модификаторы просодии
        self.emotional_modifiers = {
            'happy': {
                'speed_multiplier': 1.2,
                'pitch_variation': 1.3,
                'pause_reduction': 0.7
            },
            'sad': {
                'speed_multiplier': 0.7,
                'pitch_variation': 0.6,
                'pause_increase': 1.5
            },
            'angry': {
                'speed_multiplier': 1.3,
                'pitch_variation': 1.5,
                'pause_reduction': 0.5
            },
            'neutral': {
                'speed_multiplier': 1.0,
                'pitch_variation': 1.0,
                'pause_multiplier': 1.0
            }
        }
        
        self.logger.info("Контроллер просодии инициализирован")
    
    def apply_prosody(self, text: str, emotion: str = 'neutral') -> str:
        """
        Применение просодических характеристик к тексту
        
        Args:
            text: Исходный текст
            emotion: Эмоция для модификации просодии
            
        Returns:
            Текст с примененными просодическими метками
        """
        # Определение типа предложения
        sentence_type = self._detect_sentence_type(text)
        
        # Получение паттерна интонации
        intonation_pattern = self.intonation_patterns.get(
            sentence_type, 
            self.intonation_patterns['statement']
        )
        
        # Получение эмоциональных модификаторов
        emotion_modifiers = self.emotional_modifiers.get(
            emotion,
            self.emotional_modifiers['neutral']
        )
        
        # Применение просодических меток
        prosodic_text = self._add_prosodic_marks(
            text, 
            intonation_pattern, 
            emotion_modifiers
        )
        
        self.logger.debug(f"Применена просодия: {sentence_type} с эмоцией {emotion}")
        return prosodic_text
    
    def _detect_sentence_type(self, text: str) -> str:
        """Определение типа предложения"""
        text_clean = text.strip()
        
        if text_clean.endswith('?'):
            return 'question'
        elif text_clean.endswith('!'):
            return 'exclamation'
        elif any(text_clean.lower().startswith(keyword) for keyword in 
                ['пожалуйста', 'сделай', 'выполни', 'найди']):
            return 'command'
        else:
            return 'statement'
    
    def _add_prosodic_marks(self, text: str, intonation_pattern: Dict[str, Any], 
                          emotion_modifiers: Dict[str, float]) -> str:
        """Добавление просодических меток к тексту"""
        words = text.split()
        marked_words = []
        
        for i, word in enumerate(words):
            marked_word = word
            
            # Определение ударения (примерная эвристика для русского языка)
            if self._should_emphasize(word, i, len(words)):
                marked_word = f"<emphasis>{word}</emphasis>"
            
            # Добавление пауз после знаков препинания
            if word.endswith(('.', ',', ';', ':')):
                pause_duration = self.rhythm_settings['pause_duration']
                adjusted_pause = pause_duration * emotion_modifiers.get('pause_multiplier', 1.0)
                marked_word = f"{word}<pause={adjusted_pause:.2f}>"
            
            marked_words.append(marked_word)
        
        # Сборка текста с метками
        prosodic_text = ' '.join(marked_words)
        
        # Добавление интонационной метки
        prosodic_text = f"<intonation={intonation_pattern['pattern']}>{prosodic_text}</intonation>"
        
        return prosodic_text
    
    def _should_emphasize(self, word: str, position: int, total_words: int) -> bool:
        """Определить, нужно ли выделять слово ударением"""
        # Эвристики для русского языка
        if len(word) <= 2:
            return False
        
        # Ключевые слова для выделения
        important_keywords = [
            'важно', 'срочно', 'внимание', 'опасно', 'прекрасно', 
            'ужасно', 'никогда', 'всегда', 'очень'
        ]
        
        if word.lower() in important_keywords:
            return True
        
        # Выделение первого и последнего значимых слов
        if position == 0 or position == total_words - 1:
            return True
        
        # Случайное выделение для разнообразия (20% chance)
        return random.random() < 0.2
    
    def generate_rhythm_pattern(self, text: str, emotion: str) -> List[float]:
        """
        Генерация ритмического паттерна для текста
        
        Args:
            text: Текст для анализа
            emotion: Эмоциональный контекст
            
        Returns:
            Список длительностей для каждого слова
        """
        words = text.split()
        durations = []
        
        emotion_modifier = self.emotional_modifiers.get(
            emotion, 
            self.emotional_modifiers['neutral']
        )
        speed_multiplier = emotion_modifier.get('speed_multiplier', 1.0)
        
        base_duration = 0.3 / speed_multiplier
        
        for word in words:
            # Базовая длительность зависит от длины слова
            word_duration = base_duration * (0.5 + 0.1 * len(word))
            
            # Случайные вариации для естественности
            variation = random.uniform(0.9, 1.1)
            word_duration *= variation
            
            durations.append(word_duration)
        
        return durations
    
    def get_intonation_curve(self, sentence_type: str, word_count: int) -> List[float]:
        """
        Генерация кривой интонации для предложения
        
        Args:
            sentence_type: Тип предложения
            word_count: Количество слов
            
        Returns:
            Список значений высоты тона для каждого слова
        """
        pattern = self.intonation_patterns.get(
            sentence_type, 
            self.intonation_patterns['statement']
        )
        
        pitch_curve = []
        
        if pattern['pattern'] == 'falling':
            # Нисходящая интонация
            for i in range(word_count):
                progress = i / max(1, word_count - 1)
                pitch = 1.0 - 0.4 * progress
                pitch_curve.append(pitch)
                
        elif pattern['pattern'] == 'rising':
            # Восходящая интонация
            for i in range(word_count):
                progress = i / max(1, word_count - 1)
                pitch = 0.8 + 0.6 * progress
                pitch_curve.append(pitch)
                
        elif pattern['pattern'] == 'peak':
            # Пиковая интонация (подъем и спад)
            for i in range(word_count):
                progress = i / max(1, word_count - 1)
                if progress < 0.5:
                    pitch = 0.8 + 1.2 * progress
                else:
                    pitch = 1.4 - 1.2 * (progress - 0.5)
                pitch_curve.append(pitch)
        
        # Нормализация
        if pitch_curve:
            max_pitch = max(pitch_curve)
            pitch_curve = [p * pattern['final_pitch'] / max_pitch for p in pitch_curve]
        
        return pitch_curve