# modules/interface/text_understander/intent_classifier.py

import logging
import asyncio
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class IntentClassifier:
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logger
        self.config_path = config_path
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        
        # Пути к локальной модели
        self.local_model_path = Path("data/models/bert-base-multilingual-uncased")
        self.use_local_model = self.local_model_path.exists()
        
        self.logger.info(f"🔍 Проверка локальной модели: {self.local_model_path}")
        self.logger.info(f"📁 Локальная модель доступна: {self.use_local_model}")
        
        if self.use_local_model:
            self._check_model_files()
    
    def _check_model_files(self):
        """Проверяет наличие всех необходимых файлов модели"""
        required_files = [
            "config.json",
            "vocab.txt",
            "tokenizer_config.json"
        ]
        
        # Проверяем файлы весов (может быть один из вариантов)
        weight_files = ["pytorch_model.bin", "model.safetensors", "tf_model.h5"]
        has_weights = any((self.local_model_path / file).exists() for file in weight_files)
        
        missing_files = []
        for file in required_files:
            if not (self.local_model_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            self.logger.warning(f"⚠️ Отсутствуют файлы модели: {missing_files}")
            self.use_local_model = False
        elif not has_weights:
            self.logger.warning("⚠️ Отсутствуют файлы весов модели")
            self.use_local_model = False
        else:
            self.logger.info("✅ Все файлы модели присутствуют")
    
    async def initialize(self):
        """Асинхронная инициализация модели"""
        try:
            if self.use_local_model:
                await self._initialize_from_local()
            else:
                await self._initialize_from_huggingface()
                
            self.is_initialized = True
            self.logger.info("✅ IntentClassifier инициализирован")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации IntentClassifier: {e}")
            self.is_initialized = False
    
    async def _initialize_from_local(self):
        """Загрузка модели из локальной директории"""
        self.logger.info(f"🔄 Загрузка модели из локальной директории: {self.local_model_path}")
        
        try:
            # Импортируем здесь, чтобы отложить зависимость до момента использования
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            self.model, self.tokenizer = await asyncio.get_event_loop().run_in_executor(
                None,
                self._load_local_model_sync
            )
            self.logger.info("✅ Локальная модель успешно загружена")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки локальной модели: {e}")
            self.logger.info("🔄 Пробуем загрузить из Hugging Face как fallback...")
            await self._initialize_from_huggingface()
    
    async def _initialize_from_huggingface(self):
        """Загрузка модели из Hugging Face Hub"""
        self.logger.info("🌐 Загрузка модели из Hugging Face Hub...")
        
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            self.model, self.tokenizer = await asyncio.get_event_loop().run_in_executor(
                None,
                self._load_huggingface_model_sync
            )
            self.logger.info("✅ Модель из Hugging Face успешно загружена")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модели из Hugging Face: {e}")
            raise
    
    def _load_local_model_sync(self):
        """Синхронная загрузка локальной модели"""
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        
        self.logger.info(f"📥 Загрузка модели из: {self.local_model_path}")
        
        model = AutoModelForSequenceClassification.from_pretrained(
            str(self.local_model_path),
            local_files_only=True,
            num_labels=5  # Базовое количество классов для начала
        )
        tokenizer = AutoTokenizer.from_pretrained(
            str(self.local_model_path), 
            local_files_only=True
        )
        
        return model, tokenizer
    
    def _load_huggingface_model_sync(self):
        """Синхронная загрузка модели из Hugging Face"""
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        
        # Создаем директорию для кэша если её нет
        cache_dir = Path("data/models/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        model = AutoModelForSequenceClassification.from_pretrained(
            "bert-base-multilingual-uncased",
            cache_dir=str(cache_dir),
            num_labels=5
        )
        tokenizer = AutoTokenizer.from_pretrained(
            "bert-base-multilingual-uncased",
            cache_dir=str(cache_dir)
        )
        
        return model, tokenizer
    
    async def classify(self, text: str) -> Dict[str, Any]:
        """Классификация намерения из текста"""
        if not self.is_initialized:
            raise RuntimeError("IntentClassifier не инициализирован")
        
        try:
            # Простейшая реализация классификации
            # В будущем можно добавить полноценную логику
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._classify_sync,
                text
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка классификации: {e}")
            return {
                "intent": "error",
                "confidence": 0.0,
                "text": text,
                "error": str(e)
            }
    
    def _classify_sync(self, text: str) -> Dict[str, Any]:
        """Синхронная классификация текста"""
        # Базовая логика классификации
        # Пока используем простые правила, позже заменим на модель
        
        text_lower = text.lower().strip()
        
        # Простые правила для демонстрации
        if any(word in text_lower for word in ['привет', 'здравствуй', 'hello', 'hi']):
            return {
                "intent": "greeting",
                "confidence": 0.9,
                "text": text,
                "entities": []
            }
        elif any(word in text_lower for word in ['пока', 'до свидания', 'bye', 'goodbye']):
            return {
                "intent": "farewell", 
                "confidence": 0.9,
                "text": text,
                "entities": []
            }
        elif any(word in text_lower for word in ['погод', 'weather']):
            return {
                "intent": "weather_query",
                "confidence": 0.8,
                "text": text,
                "entities": []
            }
        elif any(word in text_lower for word in ['врем', 'time']):
            return {
                "intent": "time_query",
                "confidence": 0.8,
                "text": text,
                "entities": []
            }
        else:
            return {
                "intent": "general_query",
                "confidence": 0.5,
                "text": text,
                "entities": []
            }
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Возвращает информацию о загруженной модели"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "model_type": "bert-base-multilingual-uncased",
            "local_model": self.use_local_model,
            "model_path": str(self.local_model_path) if self.use_local_model else "huggingface_hub"
        }
    
    async def shutdown(self):
        """Очистка ресурсов"""
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        self.logger.info("✅ IntentClassifier завершил работу")