"""
Механизм внимания - фокусировка на важной информации
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import re

class AttentionMechanism:
    def __init__(self, attention_threshold: float = 0.7, decay_rate: float = 0.1):
        """
        Инициализация механизма внимания
        
        Args:
            attention_threshold: Порог внимания (0-1)
            decay_rate: Скорость затухания внимания
        """
        self.attention_threshold = attention_threshold
        self.decay_rate = decay_rate
        self.attention_scores: Dict[str, float] = {}
        self.attention_history: List[Dict] = []
        self.important_keywords = {
            "urgent": {"срочно", "важно", "немедленно", "критический", "авария"},
            "emotional": {"помогите", "пожалуйста", "спасибо", "извините", "problem"},
            "personal": {"имя", "профиль", "настройки", "персональный", "private"},
            "system": {"ошибка", "баг", "глюк", "не работает", "system error"}
        }
        self.logger = logging.getLogger(__name__)
    
    def calculate_attention_score(self, text: str, metadata: Optional[Dict] = None) -> float:
        """
        Расчет уровня внимания для текста
        
        Args:
            text: Анализируемый текст
            metadata: Дополнительные метаданные
            
        Returns:
            Уровень внимания (0-1)
        """
        base_score = 0.5  # Базовый уровень
        
        # Анализ ключевых слов
        keyword_score = self._analyze_keywords(text)
        
        # Анализ длины текста (длинные сообщения могут быть важнее)
        length_score = min(len(text) / 500, 1.0) * 0.2
        
        # Анализ эмоциональной окраски
        emotion_score = self._analyze_emotion(text)
        
        # Учет метаданных
        metadata_score = self._analyze_metadata(metadata) if metadata else 0
        
        total_score = base_score + keyword_score + length_score + emotion_score + metadata_score
        
        # Ограничение диапазона 0-1
        return max(0.0, min(1.0, total_score))
    
    def update_attention(self, entity_id: str, score: float, context: str = "") -> None:
        """
        Обновление уровня внимания для сущности
        
        Args:
            entity_id: ID сущности (пользователь, тема и т.д.)
            score: Уровень внимания
            context: Контекст обновления
        """
        current_time = datetime.now()
        
        # Применяем затухание к существующему счету
        if entity_id in self.attention_scores:
            time_passed = 1  # Упрощенная логика временного затухания
            decay = self.attention_scores[entity_id] * self.decay_rate * time_passed
            self.attention_scores[entity_id] -= decay
        
        # Обновляем счет
        self.attention_scores[entity_id] = max(0.0, min(1.0, score))
        
        # Сохраняем в историю
        self.attention_history.append({
            'entity_id': entity_id,
            'score': score,
            'timestamp': current_time,
            'context': context
        })
        
        # Ограничиваем размер истории
        if len(self.attention_history) > 1000:
            self.attention_history = self.attention_history[-500:]
            
        self.logger.debug(f"Обновлен уровень внимания для {entity_id}: {score:.3f}")
    
    def get_focus_areas(self, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Получение наиболее важных областей внимания
        
        Args:
            top_n: Количество возвращаемых элементов
            
        Returns:
            Список кортежей (entity_id, score)
        """
        # Фильтруем элементы выше порога
        focused_items = [
            (entity_id, score) 
            for entity_id, score in self.attention_scores.items() 
            if score >= self.attention_threshold
        ]
        
        # Сортируем по убыванию важности
        focused_items.sort(key=lambda x: x[1], reverse=True)
        
        return focused_items[:top_n]
    
    def should_focus_on(self, entity_id: str) -> bool:
        """
        Проверка, должна ли система фокусироваться на сущности
        
        Args:
            entity_id: ID сущности
            
        Returns:
            True если внимание выше порога
        """
        return self.attention_scores.get(entity_id, 0) >= self.attention_threshold
    
    def analyze_conversation_focus(self, conversation: List[Dict]) -> Dict[str, float]:
        """
        Анализ фокуса внимания в разговоре
        
        Args:
            conversation: Список сообщений разговора
            
        Returns:
            Словарь с оценками внимания по темам
        """
        focus_scores = {}
        
        for message in conversation:
            text = message.get('content', '')
            topics = self._extract_topics(text)
            
            for topic in topics:
                if topic not in focus_scores:
                    focus_scores[topic] = 0
                focus_scores[topic] += 1
        
        # Нормализация scores
        total_messages = len(conversation)
        if total_messages > 0:
            for topic in focus_scores:
                focus_scores[topic] = focus_scores[topic] / total_messages
                
        return focus_scores
    
    def get_attention_stats(self) -> Dict[str, Any]:
        """Получение статистики механизма внимания"""
        focused_count = len([s for s in self.attention_scores.values() if s >= self.attention_threshold])
        
        return {
            "total_tracked_entities": len(self.attention_scores),
            "currently_focused": focused_count,
            "attention_threshold": self.attention_threshold,
            "average_attention": np.mean(list(self.attention_scores.values())) if self.attention_scores else 0,
            "history_size": len(self.attention_history)
        }
    
    def _analyze_keywords(self, text: str) -> float:
        """Анализ ключевых слов в тексте"""
        text_lower = text.lower()
        score = 0.0
        
        for category, keywords in self.important_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if category == "urgent":
                        score += 0.3
                    elif category == "emotional":
                        score += 0.2
                    elif category == "personal":
                        score += 0.15
                    elif category == "system":
                        score += 0.25
                        
        return min(score, 0.5)  # Ограничиваем максимальный вклад ключевых слов
    
    def _analyze_emotion(self, text: str) -> float:
        """Анализ эмоциональной окраски текста"""
        # Упрощенный анализ эмоций по ключевым словам
        positive_words = {"отлично", "прекрасно", "спасибо", "хорошо", "рад", "успех"}
        negative_words = {"плохо", "ужасно", "проблема", "ошибка", "неправильно", "злой"}
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Эмоционально окрашенные сообщения получают больше внимания
        if positive_count > 0 or negative_count > 0:
            return 0.1
            
        return 0.0
    
    def _analyze_metadata(self, metadata: Dict) -> float:
        """Анализ метаданных для определения важности"""
        score = 0.0
        
        # Учет приоритета
        priority = metadata.get('priority', 1)
        if priority == 'high':
            score += 0.2
        elif priority == 'critical':
            score += 0.4
            
        # Учет источника
        source = metadata.get('source', '')
        if source in ['user_input', 'system_alert']:
            score += 0.1
            
        return score
    
    def _extract_topics(self, text: str) -> List[str]:
        """Извлечение тем из текста"""
        topics = []
        text_lower = text.lower()
        
        # Простая логика извлечения тем по ключевым словам
        topic_keywords = {
            "погода": ["погод", "дождь", "солнце", "температур"],
            "новости": ["новост", "событи", "происшеств"],
            "техника": ["компьютер", "телефон", "интернет", "wifi"],
            "помощь": ["помощ", "вопрос", "объясн", "как сделать"],
            "настройки": ["настройк", "конфиг", "параметр", "установк"]
        }
        
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    topics.append(topic)
                    break
                    
        return topics