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
        
        # Инициализация компонентов
        self.metaphor_generator = MetaphorGenerator(config.get('metaphor', {}))
        self.joke_engine = JokeEngine(config.get('joke', {}))
        self.poetry_composer = PoetryComposer(config.get('poetry', {}))
        self.story_teller = StoryTeller(config.get('story', {}))
        self.idea_generator = IdeaGenerator(config.get('idea', {}))
        self.feedback_analyzer = FeedbackAnalyzer(config.get('feedback', {}))
        
        self.logger.info("Модуль творчества инициализирован")
    
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