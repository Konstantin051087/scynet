"""
Менеджер контекста диалога - управление контекстом разговора
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

class ContextManager:
    def __init__(self, max_context_length: int = 10, context_timeout: int = 3600):
        """
        Инициализация менеджера контекста
        
        Args:
            max_context_length: Максимальная длина контекста
            context_timeout: Таймаут контекста в секундах
        """
        self.max_context_length = max_context_length
        self.context_timeout = context_timeout
        self.conversation_context: Dict[str, List[Dict]] = {}
        self.user_profiles: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        
    def add_message(self, user_id: str, message: str, role: str = "user", 
                   metadata: Optional[Dict] = None) -> None:
        """
        Добавление сообщения в контекст
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            role: Роль (user/assistant)
            metadata: Дополнительные метаданные
        """
        if user_id not in self.conversation_context:
            self.conversation_context[user_id] = []
            
        message_data = {
            "role": role,
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversation_context[user_id].append(message_data)
        
        # Ограничение длины контекста
        if len(self.conversation_context[user_id]) > self.max_context_length:
            self.conversation_context[user_id] = self.conversation_context[user_id][-self.max_context_length:]
            
        self._cleanup_old_contexts()
        self.logger.debug(f"Добавлено сообщение в контекст пользователя {user_id}")
        
    def get_context(self, user_id: str, max_messages: Optional[int] = None) -> List[Dict]:
        """
        Получение контекста пользователя
        
        Args:
            user_id: ID пользователя
            max_messages: Максимальное количество сообщений
            
        Returns:
            Список сообщений контекста
        """
        context = self.conversation_context.get(user_id, [])
        
        # Очистка старых контекстов
        self._cleanup_old_contexts()
        
        if max_messages and len(context) > max_messages:
            return context[-max_messages:]
            
        return context
    
    def clear_context(self, user_id: str) -> None:
        """Очистка контекста пользователя"""
        if user_id in self.conversation_context:
            del self.conversation_context[user_id]
            self.logger.info(f"Контекст пользователя {user_id} очищен")
    
    def update_user_profile(self, user_id: str, profile_data: Dict) -> None:
        """Обновление профиля пользователя"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
            
        self.user_profiles[user_id].update(profile_data)
        self.logger.debug(f"Обновлен профиль пользователя {user_id}")
        
    def get_user_profile(self, user_id: str) -> Dict:
        """Получение профиля пользователя"""
        return self.user_profiles.get(user_id, {})
    
    def get_conversation_summary(self, user_id: str) -> Dict:
        """Получение сводки разговора"""
        context = self.get_context(user_id)
        if not context:
            return {}
            
        return {
            "user_id": user_id,
            "message_count": len(context),
            "last_message_time": context[-1]["timestamp"] if context else None,
            "topics": self._extract_topics(context),
            "sentiment": self._analyze_sentiment(context)
        }
    
    def _cleanup_old_contexts(self) -> None:
        """Очистка устаревших контекстов"""
        current_time = time.time()
        users_to_remove = []
        
        for user_id, context in self.conversation_context.items():
            if context:
                last_message_time = datetime.fromisoformat(context[-1]["timestamp"]).timestamp()
                if current_time - last_message_time > self.context_timeout:
                    users_to_remove.append(user_id)
                    
        for user_id in users_to_remove:
            del self.conversation_context[user_id]
            self.logger.info(f"Удален устаревший контекст пользователя {user_id}")
    
    def _extract_topics(self, context: List[Dict]) -> List[str]:
        """Извлечение основных тем из контекста (упрощенная версия)"""
        # В реальной реализации здесь будет NLP-анализ
        topics = set()
        for message in context:
            content = message["content"].lower()
            if "погод" in content:
                topics.add("погода")
            if "новост" in content:
                topics.add("новости")
            if "помощ" in content:
                topics.add("помощь")
            if "вопрос" in content:
                topics.add("вопросы")
                
        return list(topics)
    
    def _analyze_sentiment(self, context: List[Dict]) -> str:
        """Анализ тональности разговора (упрощенная версия)"""
        # В реальной реализации здесь будет анализ sentiment
        positive_words = {"спасибо", "хорошо", "отлично", "прекрасно", "супер"}
        negative_words = {"плохо", "ужасно", "неправильно", "ошибка", "проблема"}
        
        sentiment_score = 0
        for message in context:
            content = message["content"].lower()
            for word in positive_words:
                if word in content:
                    sentiment_score += 1
            for word in negative_words:
                if word in content:
                    sentiment_score -= 1
                    
        if sentiment_score > 2:
            return "positive"
        elif sentiment_score < -2:
            return "negative"
        else:
            return "neutral"