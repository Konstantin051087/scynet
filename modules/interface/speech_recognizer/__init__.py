"""
Модуль распознавания речи (Speech Recognizer)
Орган слуха системы - преобразует аудио в текст
"""

from typing import Optional, Dict, Any
import numpy as np

try:
    from .model import SpeechRecognitionModel
    from .audio_preprocessor import AudioPreprocessor
except ImportError as e:
    print(f"Warning: Could not import some components: {e}")
    SpeechRecognitionModel = None
    AudioPreprocessor = None

# Создаем основной класс модуля
class SpeechRecognizer:
    """Основной класс модуля распознавания речи"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация модуля распознавания речи
        
        Args:
            config: Конфигурация модуля
        """
        self.config = config or {}
        self.model = None
        self.preprocessor = None
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Инициализация модуля"""
        try:
            if AudioPreprocessor:
                self.preprocessor = AudioPreprocessor(
                    target_sr=self.config.get('target_sr', 16000),
                    chunk_duration=self.config.get('chunk_duration', 30.0)
                )
            
            if SpeechRecognitionModel:
                self.model = SpeechRecognitionModel(
                    model_size=self.config.get('model_size', 'base'),
                    device=self.config.get('device', 'auto')
                )
                self.model.load_model()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing SpeechRecognizer: {e}")
            return False
    
    async def process_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        Основной метод обработки аудио
        
        Args:
            audio_data: Аудио данные
            sample_rate: Частота дискретизации
            
        Returns:
            Результаты распознавания
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Предобработка аудио
            if self.preprocessor:
                processed_audio = self.preprocessor.preprocess(audio_data, sample_rate)
            else:
                processed_audio = audio_data
            
            # Распознавание речи
            if self.model:
                result = self.model.transcribe(processed_audio)
                return result
            else:
                return {"text": "", "error": "Model not available"}
                
        except Exception as e:
            return {"text": "", "error": str(e)}
    
    async def shutdown(self):
        """Завершение работы модуля"""
        self.is_initialized = False
        self.model = None
        self.preprocessor = None

# Экспортируем основной класс
__all__ = ['SpeechRecognizer']

__version__ = "1.0.0"
__author__ = "Synthetic Mind Team"