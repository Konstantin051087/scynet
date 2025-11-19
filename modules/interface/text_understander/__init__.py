# modules/interface/text_understander/__init__.py

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path

# Добавляем путь для импортов
sys.path.append(os.path.dirname(__file__))

# Настройка логирования
logger = logging.getLogger(__name__)

# Импорт компонентов с обработкой ошибок
try:
    from .intent_classifier import IntentClassifier
    from .entity_extractor import EntityExtractor
    from .sentiment_analyzer import SentimentAnalyzer
except ImportError as e:
    logger.error(f"❌ Ошибка импорта компонентов TextUnderstander: {e}")
    
    # Создаем заглушки для отсутствующих компонентов
    class IntentClassifier:
        def __init__(self, config_path: Optional[str] = None):
            self.config_path = config_path or "config/modules/text_understander.yaml"
            self.is_initialized = False
        
        async def initialize(self):
            self.is_initialized = True
            
        async def classify(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
            return {"intent": "unknown", "confidence": 0.5}
        
        async def get_model_info(self) -> Dict[str, Any]:
            return {"status": "stub", "version": "1.0"}
        
        async def shutdown(self):
            self.is_initialized = False

    class EntityExtractor:
        def __init__(self, config_path: Optional[str] = None):
            self.config_path = config_path or "config/modules/text_understander.yaml"
            self.is_initialized = False
            
            # Создаем дефолтный конфиг если файла нет
            if not os.path.exists(self.config_path):
                self._create_default_config()
        
        def _create_default_config(self):
            """Создает дефолтный конфиг если файл не существует"""
            default_config = {
                "entity_types": ["PERSON", "LOCATION", "ORGANIZATION", "DATE"],
                "min_confidence": 0.7,
                "language": "ru"
            }
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            import yaml
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f)
        
        async def initialize(self):
            self.is_initialized = True
            
        async def extract(self, text: str, nlp_result: Optional[Dict] = None) -> List[Dict]:
            return []
        
        async def shutdown(self):
            self.is_initialized = False

    class SentimentAnalyzer:
        def __init__(self, config_path: Optional[str] = None):
            self.config_path = config_path or "config/modules/text_understander.yaml"
            self.is_initialized = False
        
        async def initialize(self):
            self.is_initialized = True
            
        async def analyze(self, text: str) -> Dict[str, Any]:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.5}
        
        async def shutdown(self):
            self.is_initialized = False

# Дополнительные компоненты из второго файла
try:
    from .nlp_engine import NlpEngine
    from .context_integrator import ContextIntegrator
except ImportError:
    logger.warning("NlpEngine или ContextIntegrator не найдены, используются заглушки")
    
    class NlpEngine:
        def __init__(self, config_path: Optional[str] = None):
            self.config_path = config_path
            self.is_initialized = False
        
        async def initialize(self):
            self.is_initialized = True
            
        async def process(self, text: str) -> Dict[str, Any]:
            return {"tokens": text.split(), "language": "ru", "pos_tags": []}
        
        async def shutdown(self):
            self.is_initialized = False

    class ContextIntegrator:
        def __init__(self, config_path: Optional[str] = None):
            self.config_path = config_path
            self.is_initialized = False
            self.user_contexts = {}
        
        async def initialize(self):
            self.is_initialized = True
            
        async def get_context(self, user_id: str, external_context: Optional[Dict] = None) -> Dict[str, Any]:
            context = self.user_contexts.get(user_id, {})
            if external_context:
                context.update(external_context)
            return context
        
        async def update_context(self, user_id: str, text: str, intent: Dict, entities: List[Dict]):
            if user_id not in self.user_contexts:
                self.user_contexts[user_id] = {}
            
            self.user_contexts[user_id].update({
                "last_text": text,
                "last_intent": intent,
                "last_entities": entities,
                "timestamp": asyncio.get_event_loop().time()
            })
        
        async def shutdown(self):
            self.is_initialized = False

class TextUnderstander:
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logger
        self.config_path = config_path or "config/modules/text_understander.yaml"
        self.is_initialized = False
        
        # Инициализация компонентов с гарантией корректного config_path
        self.nlp_engine = NlpEngine(self.config_path)
        self.intent_classifier = IntentClassifier(self.config_path)
        self.entity_extractor = EntityExtractor(self.config_path)  # Теперь config_path гарантированно не None
        self.sentiment_analyzer = SentimentAnalyzer(self.config_path)
        self.context_integrator = ContextIntegrator(self.config_path)
        
        self.logger.info("📝 TextUnderstander создан")
    
    async def initialize(self):
        """Асинхронная инициализация всех компонентов"""
        try:
            self.logger.info("🔄 Инициализация TextUnderstander...")
            
            # Параллельная инициализация компонентов
            await asyncio.gather(
                self.nlp_engine.initialize(),
                self.intent_classifier.initialize(),
                self.entity_extractor.initialize(),
                self.sentiment_analyzer.initialize(),
                self.context_integrator.initialize(),
                return_exceptions=True
            )
            
            self.is_initialized = True
            self.logger.info("✅ TextUnderstander инициализирован")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации TextUnderstander: {e}")
            self.is_initialized = False
    
    async def process_text(self, text: str, user_id: str = "default", context: Optional[Dict] = None) -> Dict[str, Any]:
        """Основной метод обработки текста"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Получение контекста
            context_data = await self.context_integrator.get_context(user_id, context)
            
            # Параллельная обработка разными компонентами
            nlp_result, intent_result, entities_result, sentiment_result = await asyncio.gather(
                self.nlp_engine.process(text),
                self.intent_classifier.classify(text, context_data),
                self.entity_extractor.extract(text),
                self.sentiment_analyzer.analyze(text),
                return_exceptions=True
            )
            
            # Обработка исключений
            if isinstance(nlp_result, Exception):
                self.logger.error(f"❌ Ошибка NLP обработки: {nlp_result}")
                nlp_result = {"tokens": text.split(), "language": "ru", "pos_tags": []}
            
            if isinstance(intent_result, Exception):
                self.logger.error(f"❌ Ошибка классификации намерения: {intent_result}")
                intent_result = {"intent": "error", "confidence": 0.0}
            
            if isinstance(entities_result, Exception):
                self.logger.error(f"❌ Ошибка извлечения сущностей: {entities_result}")
                entities_result = []
            
            if isinstance(sentiment_result, Exception):
                self.logger.error(f"❌ Ошибка анализа тональности: {sentiment_result}")
                sentiment_result = {"sentiment": "neutral", "score": 0.0, "confidence": 0.5}
            
            # Обновление контекста
            await self.context_integrator.update_context(user_id, text, intent_result, entities_result)
            
            return {
                "text": text,
                "user_id": user_id,
                "intent": intent_result,
                "entities": entities_result,
                "sentiment": sentiment_result,
                "nlp_result": nlp_result,
                "context": context_data,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки текста: {e}")
            return {
                "text": text,
                "user_id": user_id,
                "intent": {"intent": "error", "confidence": 0.0},
                "entities": [],
                "sentiment": {"sentiment": "neutral", "score": 0.0, "confidence": 0.5},
                "nlp_result": {"tokens": text.split(), "language": "ru", "pos_tags": []},
                "context": {},
                "success": False,
                "error": str(e)
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Возвращает статус модуля"""
        model_info = await self.intent_classifier.get_model_info()
        
        return {
            "initialized": self.is_initialized,
            "config_path": self.config_path,
            "model_info": model_info,
            "components": {
                "nlp_engine": self.nlp_engine.is_initialized,
                "intent_classifier": self.intent_classifier.is_initialized,
                "entity_extractor": self.entity_extractor.is_initialized,
                "sentiment_analyzer": self.sentiment_analyzer.is_initialized,
                "context_integrator": self.context_integrator.is_initialized
            }
        }
    
    async def shutdown(self):
        """Корректное завершение работы"""
        self.logger.info("🛑 Завершение работы TextUnderstander...")
        
        await asyncio.gather(
            self.nlp_engine.shutdown(),
            self.intent_classifier.shutdown(),
            self.entity_extractor.shutdown(),
            self.sentiment_analyzer.shutdown(),
            self.context_integrator.shutdown(),
            return_exceptions=True
        )
        
        self.is_initialized = False
        self.logger.info("✅ TextUnderstander завершил работу")

# Глобальный экземпляр для импорта
text_understander = TextUnderstander()