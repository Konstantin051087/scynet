from .nlp_engine import NlpEngine
from .intent_classifier import IntentClassifier
from .entity_extractor import EntityExtractor
from .sentiment_analyzer import SentimentAnalyzer
from .context_integrator import ContextIntegrator

class TextUnderstander:
    def __init__(self, config_path: str = "config/modules/text_understander.yaml"):
        self.nlp_engine = NlpEngine(config_path)
        self.intent_classifier = IntentClassifier(config_path)
        self.entity_extractor = EntityExtractor(config_path)
        self.sentiment_analyzer = SentimentAnalyzer(config_path)
        self.context_integrator = ContextIntegrator(config_path)
        
    def process_text(self, text: str, user_id: str = "default", context: dict = None) -> dict:
        """Основной метод обработки текста"""
        # NLP обработка
        nlp_result = self.nlp_engine.process(text)
        
        # Анализ контекста
        context_data = self.context_integrator.get_context(user_id, context)
        
        # Классификация намерения
        intent = self.intent_classifier.classify(text, context_data)
        
        # Извлечение сущностей
        entities = self.entity_extractor.extract(text, nlp_result)
        
        # Анализ тональности
        sentiment = self.sentiment_analyzer.analyze(text)
        
        # Обновление контекста
        self.context_integrator.update_context(user_id, text, intent, entities)
        
        return {
            "text": text,
            "intent": intent,
            "entities": entities,
            "sentiment": sentiment,
            "nlp_result": nlp_result,
            "context": context_data
        }