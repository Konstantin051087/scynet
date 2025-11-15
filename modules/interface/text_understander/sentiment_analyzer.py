import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import yaml
from typing import Dict

class SentimentAnalyzer:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Инициализация пайплайна для анализа тональности
        model_name = self.config.get('sentiment_model', 'seara/rubert-tiny2-ru-go-emotions')
        
        try:
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name
            )
        except Exception as e:
            print(f"Ошибка загрузки модели анализа тональности: {e}")
            self.sentiment_pipeline = None
        
        # Эмоциональный словарь
        self.emotion_lexicon = self._load_emotion_lexicon()
    
    def _load_emotion_lexicon(self) -> Dict:
        """Загрузка эмоционального лексикона"""
        # Базовый эмоциональный словарь
        return {
            'радость': ['хорошо', 'отлично', 'прекрасно', 'замечательно', 'счастье', 'рад', 'доволен'],
            'грусть': ['плохо', 'ужасно', 'грустно', 'печально', 'тоска', 'несчастный'],
            'гнев': ['злой', 'сердит', 'разозлён', 'бесит', 'раздражает', 'ярость'],
            'страх': ['боюсь', 'страшно', 'испуг', 'опасно', 'пугает'],
            'удивление': ['неожиданно', 'удивительно', 'внезапно', 'ого', 'вау']
        }
    
    def analyze(self, text: str) -> Dict:
        """Анализ тональности и эмоций текста"""
        if self.sentiment_pipeline is None:
            return self._fallback_sentiment_analysis(text)
        
        try:
            # Анализ с помощью модели
            result = self.sentiment_pipeline(text)[0]
            
            # Дополнительный анализ эмоций
            emotions = self._analyze_emotions(text)
            
            return {
                "sentiment": result['label'],
                "confidence": result['score'],
                "emotions": emotions,
                "source": "model"
            }
        except Exception as e:
            print(f"Ошибка анализа тональности: {e}")
            return self._fallback_sentiment_analysis(text)
    
    def _analyze_emotions(self, text: str) -> Dict[str, float]:
        """Анализ эмоциональной окраски текста"""
        emotions_score = {}
        text_lower = text.lower()
        
        for emotion, words in self.emotion_lexicon.items():
            count = sum(1 for word in words if word in text_lower)
            emotions_score[emotion] = count / len(words) if words else 0
        
        return emotions_score
    
    def _fallback_sentiment_analysis(self, text: str) -> Dict:
        """Резервный анализ тональности на основе ключевых слов"""
        positive_words = ['хорош', 'отличн', 'прекрасн', 'замечательн', 'рад', 'счастлив']
        negative_words = ['плох', 'ужасн', 'грустн', 'печальн', 'зл', 'сердит']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "POSITIVE"
            confidence = positive_count / (positive_count + negative_count + 1)
        elif negative_count > positive_count:
            sentiment = "NEGATIVE"
            confidence = negative_count / (positive_count + negative_count + 1)
        else:
            sentiment = "NEUTRAL"
            confidence = 0.5
        
        emotions = self._analyze_emotions(text)
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "emotions": emotions,
            "source": "fallback"
        }
    
    def add_emotion_word(self, emotion: str, words: List[str]):
        """Добавление слов в эмоциональный лексикон"""
        if emotion not in self.emotion_lexicon:
            self.emotion_lexicon[emotion] = []
        
        self.emotion_lexicon[emotion].extend(words)