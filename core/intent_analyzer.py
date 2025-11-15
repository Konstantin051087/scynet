"""
Анализатор намерений пользователя
Определяет цель и сущности в запросе пользователя
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
import json
import yaml

class IntentAnalyzer:
    """Анализатор намерений пользователя"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('core.intent_analyzer')
        
        # Паттерны намерений
        self.intent_patterns = {}
        self.entity_patterns = {}
        
        # Модель для классификации (может быть заменена на ML модель)
        self.intent_model = None
        
        self.is_initialized = False

    async def initialize(self):
        """Инициализация анализатора намерений"""
        try:
            # Загрузка паттернов из конфигурации
            await self._load_patterns()
            
            # Здесь может быть загрузка ML модели
            # self.intent_model = await self._load_ml_model()
            
            self.is_initialized = True
            self.logger.info("Анализатор намерений инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации анализатора намерений: {e}")
            raise

    async def analyze(self, context) -> Dict[str, Any]:
        """
        Анализ намерения пользователя
        
        Args:
            context: Контекст обработки
            
        Returns:
            Dict с определенным намерением и сущностями
        """
        if not self.is_initialized:
            raise RuntimeError("Анализатор намерений не инициализирован")
        
        user_input = context.user_input
        input_type = context.input_type
        
        self.logger.debug(f"Анализ намерения для: {user_input}")
        
        try:
            # Предобработка в зависимости от типа ввода
            if input_type == 'text':
                processed_text = self._preprocess_text(user_input)
            elif input_type == 'audio':
                # Для аудио предполагаем, что уже есть текст от speech_recognizer
                processed_text = self._preprocess_text(user_input)
            else:
                processed_text = ""
            
            # Определение намерения
            intent, confidence = await self._detect_intent(processed_text)
            
            # Извлечение сущностей
            entities = await self._extract_entities(processed_text, intent)
            
            result = {
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'processed_text': processed_text
            }
            
            self.logger.info(f"Определено намерение: {intent} (уверенность: {confidence:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа намерения: {e}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'entities': {},
                'error': str(e)
            }

    async def _detect_intent(self, text: str) -> Tuple[str, float]:
        """Определение намерения на основе текста"""
        text_lower = text.lower()
        
        # Проверка паттернов для каждого намерения
        intents_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                intents_scores[intent] = score
        
        if intents_scores:
            # Выбираем намерение с наибольшим счетом
            best_intent = max(intents_scores, key=intents_scores.get)
            confidence = min(intents_scores[best_intent] / 5.0, 1.0)  # Нормализуем до 0-1
            return best_intent, confidence
        
        # Если не нашли - возвращаем unknown
        return 'unknown', 0.1

    async def _extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """Извлечение сущностей из текста"""
        entities = {}
        text_lower = text.lower()
        
        # Извлечение общих сущностей
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].append(match.group())
        
        # Извлечение специфичных для намерения сущностей
        intent_specific_entities = await self._extract_intent_specific_entities(text, intent)
        entities.update(intent_specific_entities)
        
        return entities

    async def _extract_intent_specific_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """Извлечение сущностей специфичных для намерения"""
        entities = {}
        
        if intent == 'weather':
            # Извлечение локации и времени для погоды
            location_patterns = [
                r'\b(в|на|у)\s+([А-Яа-яЁё\w\s-]+)',
                r'\b(москв[аеуы]|санкт-петербург[ае]|питер[ае]?)',
            ]
            
            for pattern in location_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if 'location' not in entities:
                        entities['location'] = []
                    entities['location'].append(match.group())
        
        elif intent == 'calculation':
            # Извлечение математических выражений
            math_patterns = [
                r'\d+\s*[\+\-\*\/]\s*\d+',
                r'посчитай\s+([\d\s\+\-\*\/\(\)]+)'
            ]
            
            for pattern in math_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if 'expression' not in entities:
                        entities['expression'] = []
                    entities['expression'].append(match.group())
        
        return entities

    def _preprocess_text(self, text: str) -> str:
        """Предобработка текста"""
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Приведение к нижнему регистру для анализа
        # (но сохраняем оригинал для сущностей)
        return text

    async def _load_patterns(self):
        """Загрузка паттернов намерений и сущностей"""
        # Базовые паттерны намерений
        self.intent_patterns = {
            'greeting': [
                r'привет|здравствуй|добрый|hello|hi',
                r'как\s+дела|как\s+ты'
            ],
            'weather': [
                r'погод[аеуы]|weather',
                r'температур[аеуы]|temperature',
                r'сколько\s+градус|холодно|тепло'
            ],
            'calculation': [
                r'посчитай|вычисли|calculate',
                r'сколько\s+будет|\d+\s*[\+\-\*\/]',
                r'математик|calculation'
            ],
            'time': [
                r'врем[яени]|time|который\s+час',
                r'сколько\s+времени|текущее\s+время'
            ],
            'search': [
                r'найди|поиск|search|find',
                r'информаци[яю]|сведения'
            ],
            'creative': [
                r'придумай|создай|напиши',
                r'истори[юя]|шутк[ау]|стих',
                r'креатив|creative'
            ],
            'planning': [
                r'план|расписание|schedule',
                r'задач[аи]|todo|сделать'
            ],
            'goodbye': [
                r'пока|до\s+свидания|спасибо',
                r'bye|goodbye|see you'
            ]
        }
        
        # Паттерны сущностей
        self.entity_patterns = {
            'date': [
                r'\b(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})\b',
                r'\b(сегодня|завтра|вчера)\b',
                r'\b(понедельник|вторник|сред[ае]|четверг|пятниц[ае]|суббот[ае]|воскресенье)\b'
            ],
            'time': [
                r'\b(\d{1,2}:\d{2})\b',
                r'\b(утр[оа]|день|вечер|ночь)\b'
            ],
            'number': [
                r'\b(\d+)\b'
            ],
            'location': [
                r'\b(в|на)\s+([А-Яа-яЁё\w\s-]+)'
            ]
        }
        
        self.logger.debug("Паттерны намерений и сущностей загружены")

    async def update_patterns(self, new_patterns: Dict[str, Any]):
        """Обновление паттернов анализатора"""
        if 'intents' in new_patterns:
            self.intent_patterns.update(new_patterns['intents'])
        if 'entities' in new_patterns:
            self.entity_patterns.update(new_patterns['entities'])
        
        self.logger.info("Паттерны анализатора обновлены")

    async def get_analysis_stats(self) -> Dict[str, Any]:
        """Получение статистики анализатора"""
        return {
            'intents_count': len(self.intent_patterns),
            'entities_types_count': len(self.entity_patterns),
            'is_initialized': self.is_initialized
        }