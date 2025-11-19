"""
Модуль творчества (Creativity Module)
Креативное мышление и генерация контента
"""

import os
import logging
from typing import Dict, Any, List, Optional

from .metaphor_generator import MetaphorGenerator
from .joke_engine import JokeEngine
from .poetry_composer import PoetryComposer
from .story_teller import StoryTeller
from .idea_generator import IdeaGenerator
from .feedback_analyzer import FeedbackAnalyzer

class CreativityModule:
    """Главный класс модуля творчества"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.communication_bus = None
        self.is_initialized = False
        
        # Инициализация компонентов
        self.metaphor_generator = MetaphorGenerator(config.get('metaphor', {}))
        self.joke_engine = JokeEngine(config.get('joke', {}))
        self.poetry_composer = PoetryComposer(config.get('poetry', {}))
        self.story_teller = StoryTeller(config.get('story', {}))
        self.idea_generator = IdeaGenerator(config.get('idea', {}))
        self.feedback_analyzer = FeedbackAnalyzer(config.get('feedback', {}))
        
        self.logger.info("Модуль творчества создан")

    async def initialize(self, communication_bus) -> bool:
        """Асинхронная инициализация модуля - ОБЯЗАТЕЛЬНЫЙ метод"""
        try:
            self.communication_bus = communication_bus
            self.is_initialized = True
            
            # Настройка коммуникации с шиной сообщений
            await self._setup_communication()
            
            self.logger.info("✅ Модуль творчества инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации модуля творчества: {e}")
            return False

    async def _setup_communication(self):
        """Настройка коммуникации с шиной сообщений"""
        self.communication_bus.subscribe("creativity_request", self._handle_creativity_request)
        self.communication_bus.subscribe("module_health_check", self._handle_health_check)
        self.logger.debug("Коммуникация с шиной сообщений настроена")

    async def _handle_creativity_request(self, message):
        """Обработка запроса на творческий контент"""
        try:
            data = message.data
            content_type = data.get('content_type', 'idea')
            prompt = data.get('prompt', '')
            
            result = self.generate_creative_content(prompt, content_type, **data.get('params', {}))
            
            await self.communication_bus.send_message({
                'source': 'creativity',
                'destination': message.source,
                'message_type': 'creativity_response',
                'data': {
                    'request_id': data.get('request_id'),
                    'result': result,
                    'status': 'success'
                }
            })
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки творческого запроса: {e}")
            await self._send_error_response(message, str(e))

    async def _handle_health_check(self, message):
        """Обработка проверки здоровья модуля"""
        health_status = await self.get_status()
        await self.communication_bus.send_message({
            'source': 'creativity',
            'destination': message.source,
            'message_type': 'health_check_response',
            'data': health_status
        })

    async def _send_error_response(self, original_message, error_text):
        """Отправка сообщения об ошибке"""
        await self.communication_bus.send_message({
            'source': 'creativity',
            'destination': original_message.source,
            'message_type': 'creativity_error_response',
            'data': {
                'request_id': original_message.data.get('request_id'),
                'error': error_text,
                'status': 'error'
            }
        })

    async def shutdown(self):
        """Корректное завершение работы модуля - ОБЯЗАТЕЛЬНЫЙ метод"""
        try:
            # Отписка от шины сообщений
            if self.communication_bus:
                self.communication_bus.unsubscribe("creativity_request")
                self.communication_bus.unsubscribe("module_health_check")
            
            self.is_initialized = False
            self.logger.info("Модуль творчества завершил работу")
            
        except Exception as e:
            self.logger.error(f"Ошибка завершения работы модуля: {e}")

    async def is_healthy(self) -> bool:
        """Проверка здоровья модуля - ОБЯЗАТЕЛЬНЫЙ метод"""
        return self.is_initialized

    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса модуля - ОБЯЗАТЕЛЬНЫЙ метод"""
        return {
            'status': 'initialized' if self.is_initialized else 'error',
            'is_initialized': self.is_initialized,
            'submodules': {
                'metaphor_generator': True,
                'joke_engine': True,
                'poetry_composer': True,
                'story_teller': True,
                'idea_generator': True,
                'feedback_analyzer': True
            },
            'health': 'healthy' if self.is_initialized else 'unhealthy'
        }

    # Существующие методы остаются без изменений
    def generate_creative_content(self, prompt: str, content_type: str, **kwargs) -> Dict[str, Any]:
        """Генерация творческого контента по запросу"""
        
        content_type = content_type.lower()
        
        try:
            if content_type == 'metaphor':
                result = self.metaphor_generator.generate(prompt, **kwargs)
            elif content_type == 'joke':
                result = self.joke_engine.generate(prompt, **kwargs)
            elif content_type == 'poetry':
                result = self.poetry_composer.generate(prompt, **kwargs)
            elif content_type == 'story':
                result = self.story_teller.generate(prompt, **kwargs)
            elif content_type == 'idea':
                result = self.idea_generator.generate(prompt, **kwargs)
            else:
                raise ValueError(f"Неизвестный тип контента: {content_type}")
            
            # Анализ качества контента
            feedback = self.feedback_analyzer.analyze(result['content'], content_type)
            result['quality_score'] = feedback['score']
            result['improvement_suggestions'] = feedback['suggestions']
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации контента: {e}")
            return {
                'content': f"Извините, не удалось сгенерировать {content_type}. Ошибка: {str(e)}",
                'type': content_type,
                'quality_score': 0.0,
                'error': str(e)
            }
    
    def process_feedback(self, content: str, content_type: str, user_feedback: float) -> None:
        """Обработка пользовательской обратной связи"""
        self.feedback_analyzer.learn_from_feedback(content, content_type, user_feedback)

# Экспорт основных классов
__all__ = [
    'CreativityModule',
    'MetaphorGenerator', 
    'JokeEngine',
    'PoetryComposer',
    'StoryTeller',
    'IdeaGenerator',
    'FeedbackAnalyzer'
]