import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import yaml
from typing import Dict, List
import os
import re

class SentimentAnalyzer:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Пути к локальным моделям
        self.model_ru_path = "/home/konstanin/GitHub/scynet/data/models/rubert-tiny2-ru-go-emotions"
        self.model_en_path = "/home/konstanin/GitHub/scynet/data/models/distilbert-base-uncased-finetuned-sst-2-english"
        
        # Инициализация моделей для разных языков
        self.sentiment_pipeline_ru = None
        self.sentiment_pipeline_en = None
        
        # Загрузка русской модели
        if os.path.exists(self.model_ru_path):
            try:
                print(f"✅ Загрузка русской модели: {self.model_ru_path}")
                self.sentiment_pipeline_ru = pipeline(
                    "sentiment-analysis",
                    model=self.model_ru_path,
                    tokenizer=self.model_ru_path,
                    local_files_only=True
                )
            except Exception as e:
                print(f"❌ Ошибка загрузки русской модели: {e}")
        else:
            print(f"❌ Русская модель не найдена: {self.model_ru_path}")
        
        # Загрузка английской модели
        if os.path.exists(self.model_en_path):
            try:
                print(f"✅ Загрузка английской модели: {self.model_en_path}")
                self.sentiment_pipeline_en = pipeline(
                    "sentiment-analysis",
                    model=self.model_en_path,
                    tokenizer=self.model_en_path,
                    local_files_only=True
                )
            except Exception as e:
                print(f"❌ Ошибка загрузки английской модели: {e}")
        else:
            print(f"❌ Английская модель не найдена: {self.model_en_path}")
        
        # Эмоциональные словари для разных языков
        self.emotion_lexicon_ru = self._load_emotion_lexicon_ru()
        self.emotion_lexicon_en = self._load_emotion_lexicon_en()
    
    def _detect_language(self, text: str) -> str:
        """Определение языка текста"""
        # Простая эвристика: если есть кириллические символы - русский, иначе английский
        if re.search('[а-яА-Я]', text):
            return 'ru'
        else:
            return 'en'
    
    def _load_emotion_lexicon_ru(self) -> Dict:
        """Загрузка эмоционального лексикона для русского языка"""
        return {
            'радость': ['хорошо', 'отлично', 'прекрасно', 'замечательно', 'счастье', 'рад', 'доволен', 'восторг'],
            'грусть': ['плохо', 'ужасно', 'грустно', 'печально', 'тоска', 'несчастный', 'депрессия'],
            'гнев': ['злой', 'сердит', 'разозлён', 'бесит', 'раздражает', 'ярость', 'возмущение'],
            'страх': ['боюсь', 'страшно', 'испуг', 'опасно', 'пугает', 'тревога', 'паника'],
            'удивление': ['неожиданно', 'удивительно', 'внезапно', 'ого', 'вау', 'невероятно'],
            'нейтральный': ['нормально', 'обычно', 'стандартно', 'типично']
        }
    
    def _load_emotion_lexicon_en(self) -> Dict:
        """Загрузка эмоционального лексикона для английского языка"""
        return {
            'joy': ['good', 'great', 'excellent', 'awesome', 'happy', 'glad', 'pleased', 'delighted'],
            'sadness': ['bad', 'terrible', 'awful', 'sad', 'unhappy', 'depressed', 'miserable'],
            'anger': ['angry', 'mad', 'furious', 'annoyed', 'irritated', 'outraged'],
            'fear': ['afraid', 'scared', 'frightened', 'terrified', 'anxious', 'worried'],
            'surprise': ['unexpected', 'surprising', 'amazing', 'wow', 'incredible', 'astonishing'],
            'neutral': ['okay', 'normal', 'usual', 'typical', 'standard']
        }
    
    def analyze(self, text: str) -> Dict:
        """Анализ тональности и эмоций текста с учетом языка"""
        language = self._detect_language(text)
        
        if language == 'ru' and self.sentiment_pipeline_ru is not None:
            return self._analyze_with_model(text, language, self.sentiment_pipeline_ru)
        elif language == 'en' and self.sentiment_pipeline_en is not None:
            return self._analyze_with_model(text, language, self.sentiment_pipeline_en)
        else:
            return self._fallback_sentiment_analysis(text, language)
    
    def _analyze_with_model(self, text: str, language: str, pipeline) -> Dict:
        """Анализ с использованием модели"""
        try:
            result = pipeline(text)[0]
            emotions = self._analyze_emotions(text, language)
            
            return {
                "sentiment": result['label'],
                "confidence": result['score'],
                "emotions": emotions,
                "language": language,
                "source": f"model_{language}"
            }
        except Exception as e:
            print(f"❌ Ошибка анализа тональности ({language}): {e}")
            return self._fallback_sentiment_analysis(text, language)
    
    def _analyze_emotions(self, text: str, language: str) -> Dict[str, float]:
        """Анализ эмоциональной окраски текста с учетом языка"""
        emotions_score = {}
        text_lower = text.lower()
        
        emotion_lexicon = self.emotion_lexicon_ru if language == 'ru' else self.emotion_lexicon_en
        
        for emotion, words in emotion_lexicon.items():
            count = sum(1 for word in words if word in text_lower)
            emotions_score[emotion] = count / len(words) if words else 0
        
        return emotions_score
    
    def _fallback_sentiment_analysis(self, text: str, language: str) -> Dict:
        """Резервный анализ тональности на основе ключевых слов"""
        if language == 'ru':
            positive_words = ['хорош', 'отличн', 'прекрасн', 'замечательн', 'рад', 'счастлив', 'восторг']
            negative_words = ['плох', 'ужасн', 'грустн', 'печальн', 'зл', 'сердит', 'раздража']
        else:
            positive_words = ['good', 'great', 'excellent', 'awesome', 'happy', 'glad', 'pleased', 'wonderful']
            negative_words = ['bad', 'terrible', 'awful', 'sad', 'angry', 'mad', 'horrible']
        
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
        
        emotions = self._analyze_emotions(text, language)
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "emotions": emotions,
            "language": language,
            "source": "fallback"
        }
    
    def get_model_status(self) -> Dict:
        """Получение статуса загруженных моделей"""
        return {
            "russian_model": {
                "loaded": self.sentiment_pipeline_ru is not None,
                "path": self.model_ru_path,
                "exists": os.path.exists(self.model_ru_path)
            },
            "english_model": {
                "loaded": self.sentiment_pipeline_en is not None,
                "path": self.model_en_path,
                "exists": os.path.exists(self.model_en_path)
            }
        }
    
    def add_emotion_word(self, emotion: str, words: List[str], language: str = 'ru'):
        """Добавление слов в эмоциональный лексикон"""
        emotion_lexicon = self.emotion_lexicon_ru if language == 'ru' else self.emotion_lexicon_en
        
        if emotion not in emotion_lexicon:
            emotion_lexicon[emotion] = []
        
        emotion_lexicon[emotion].extend(words)