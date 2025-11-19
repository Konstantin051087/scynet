"""
Основная модель распознавания речи
Использует Whisper для точного распознавания с поддержкой русского и английского
"""

import torch
import whisper
import numpy as np
from typing import Optional, Dict, Any, Tuple
import json
import os
from pathlib import Path
import logging
import asyncio
from typing import List

class SpeechRecognitionModel:
    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Инициализация модели распознавания речи
        
        Args:
            model_size: Размер модели Whisper (tiny, base, small, medium, large)
            device: Устройство для вычислений (auto, cuda, cpu)
        """
        self.logger = logging.getLogger(__name__)
        self.model_size = model_size
        self.device = self._setup_device(device)
        self.model = None
        self.vocabulary = {}
        self.accents = {}
        self.custom_words = set()
        
        self._load_vocabulary()
        self._load_accents()
        self._load_custom_words()
        
    def _setup_device(self, device: str) -> str:
        """Настройка вычислительного устройства"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def load_model(self):
        """Загрузка модели Whisper"""
        try:
            self.logger.info(f"Загрузка модели Whisper {self.model_size} на устройство {self.device}")
            self.model = whisper.load_model(self.model_size, device=self.device)
            self.logger.info("Модель успешно загружена")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            raise
    
    def _load_vocabulary(self):
        """Загрузка основного словаря произношений"""
        vocab_path = Path(__file__).parent / "vocabulary" / "main_vocab.dat"
        try:
            if vocab_path.exists():
                with open(vocab_path, 'r', encoding='utf-8') as f:
                    self.vocabulary = json.load(f)
                self.logger.info(f"Загружен словарь из {len(self.vocabulary)} слов")
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить словарь: {e}")
    
    def _load_accents(self):
        """Загрузка базы акцентов"""
        accents_dir = Path(__file__).parent / "vocabulary" / "accents"
        try:
            # Русские акценты
            russian_path = accents_dir / "russian_accents.db"
            if russian_path.exists():
                with open(russian_path, 'r', encoding='utf-8') as f:
                    self.accents['russian'] = json.load(f)
            
            # Английские акценты  
            english_path = accents_dir / "english_accents.db"
            if english_path.exists():
                with open(english_path, 'r', encoding='utf-8') as f:
                    self.accents['english'] = json.load(f)
                    
            self.logger.info(f"Загружены акценты для {list(self.accents.keys())}")
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить акценты: {e}")
    
    def _load_custom_words(self):
        """Загрузка пользовательских слов"""
        custom_path = Path(__file__).parent / "vocabulary" / "custom_words" / "user_added.txt"
        try:
            if custom_path.exists():
                with open(custom_path, 'r', encoding='utf-8') as f:
                    self.custom_words = set(line.strip() for line in f if line.strip())
                self.logger.info(f"Загружено {len(self.custom_words)} пользовательских слов")
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить пользовательские слова: {e}")
    
    def preprocess_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Предобработка аудио данных
        
        Args:
            audio_data: Входные аудио данные
            sample_rate: Частота дискретизации
            
        Returns:
            Обработанные аудио данные
        """
        # Нормализация аудио
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
        
        # Ресемплинг если необходимо
        if sample_rate != 16000:
            from scipy import signal
            audio_data = signal.resample(audio_data, 
                                       int(len(audio_data) * 16000 / sample_rate))
        
        return audio_data
    
    def transcribe(self, 
                  audio_data: np.ndarray, 
                  language: Optional[str] = None,
                  prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Транскрибация аудио в текст
        
        Args:
            audio_data: Аудио данные
            language: Язык распознавания (ru, en, None для автоопределения)
            prompt: Контекстная подсказка для улучшения распознавания
            
        Returns:
            Словарь с результатами распознавания
        """
        if self.model is None:
            self.load_model()
        
        try:
            # Подготовка параметров для Whisper
            whisper_kwargs = {
                "audio": audio_data,
                "fp16": torch.cuda.is_available() if self.device == "cuda" else False
            }
            
            if language:
                whisper_kwargs["language"] = language
            if prompt:
                whisper_kwargs["initial_prompt"] = prompt
            
            # Выполнение распознавания
            result = self.model.transcribe(**whisper_kwargs)
            
            # Постобработка результатов
            processed_result = self._postprocess_transcription(result)
            
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Ошибка транскрибации: {e}")
            return {
                "text": "",
                "segments": [],
                "language": language,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _postprocess_transcription(self, result: Dict) -> Dict[str, Any]:
        """Постобработка результатов транскрибации"""
        processed = {
            "text": result.get("text", "").strip(),
            "segments": result.get("segments", []),
            "language": result.get("language", "unknown"),
            "confidence": self._calculate_confidence(result),
            "timestamp": result.get("timestamp", (0, 0)),
            "words": self._extract_words_with_timestamps(result)
        }
        
        # Применение пользовательских слов
        if self.custom_words:
            processed["text"] = self._apply_custom_corrections(processed["text"])
        
        return processed
    
    def _calculate_confidence(self, result: Dict) -> float:
        """Вычисление уверенности распознавания"""
        segments = result.get("segments", [])
        if not segments:
            return 0.0
        
        confidences = [seg.get("confidence", 0.0) for seg in segments if "confidence" in seg]
        return float(np.mean(confidences)) if confidences else 0.0
    
    def _extract_words_with_timestamps(self, result: Dict) -> list:
        """Извлечение слов с временными метками"""
        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info.get("word", ""),
                    "start": word_info.get("start", 0),
                    "end": word_info.get("end", 0),
                    "confidence": word_info.get("confidence", 0.0)
                })
        return words
    
    def _apply_custom_corrections(self, text: str) -> str:
        """Применение коррекций на основе пользовательских слов"""
        # Здесь может быть сложная логика коррекции
        # В текущей реализации просто возвращаем исходный текст
        return text
    
    def detect_language(self, audio_data: np.ndarray) -> str:
        """
        Определение языка речи
        
        Args:
            audio_data: Аудио данные для анализа
            
        Returns:
            Код языка (ru, en, etc.)
        """
        if self.model is None:
            self.load_model()
        
        try:
            # Обрезка аудио для быстрого определения языка
            max_samples = 16000 * 30  # 30 секунд максимум
            if len(audio_data) > max_samples:
                audio_data = audio_data[:max_samples]
            
            # Определение языка с помощью Whisper
            mel = whisper.log_mel_spectrogram(audio_data).to(self.model.device)
            _, probs = self.model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            
            return detected_lang
            
        except Exception as e:
            self.logger.error(f"Ошибка определения языка: {e}")
            return "unknown"

    async def async_transcribe(self, 
                             audio_data: np.ndarray, 
                             language: Optional[str] = None,
                             prompt: Optional[str] = None) -> Dict[str, Any]:
        """Асинхронная версия транскрибации"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.transcribe, audio_data, language, prompt
        )