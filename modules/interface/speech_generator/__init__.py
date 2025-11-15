"""
МОДУЛЬ ГЕНЕРАЦИИ РЕЧИ
Речевой аппарат системы Синтетический Разум
"""

import os
import logging
from typing import Dict, Any, Optional

from .tts_engine import TTSEngine
from .emotion_modulator import EmotionModulator
from .voice_synthesizer import VoiceSynthesizer
from .prosody_controller import ProsodyController
from .audio_postprocessor import AudioPostprocessor

class SpeechGenerator:
    """Основной класс модуля генерации речи"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.tts_engine = TTSEngine(config.get('tts', {}))
        self.emotion_modulator = EmotionModulator(config.get('emotion', {}))
        self.voice_synthesizer = VoiceSynthesizer(config.get('voice', {}))
        self.prosody_controller = ProsodyController(config.get('prosody', {}))
        self.audio_postprocessor = AudioPostprocessor(config.get('audio', {}))
        
        self.logger.info("Модуль генерации речи инициализирован")
    
    def generate_speech(self, text: str, emotion: str = "neutral", 
                       voice_profile: str = "neutral/male_neutral") -> str:
        """
        Генерация речи из текста с учетом эмоций и голосового профиля
        
        Args:
            text: Текст для синтеза
            emotion: Эмоциональная окраска
            voice_profile: Путь к голосовому профилю
            
        Returns:
            Путь к сгенерированному аудиофайлу
        """
        try:
            # Модуляция эмоций
            modulated_text = self.emotion_modulator.modulate(text, emotion)
            
            # Контроль просодии
            prosody_text = self.prosody_controller.apply_prosody(modulated_text, emotion)
            
            # Синтез голоса
            raw_audio = self.voice_synthesizer.synthesize(prosody_text, voice_profile)
            
            # Постобработка аудио
            final_audio = self.audio_postprocessor.process(raw_audio, emotion)
            
            self.logger.info(f"Речь успешно сгенерирована для текста: {text[:50]}...")
            return final_audio
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации речи: {str(e)}")
            raise
    
    def get_available_voices(self) -> list:
        """Получить список доступных голосовых профилей"""
        return self.voice_synthesizer.get_available_profiles()
    
    def set_voice_parameters(self, parameters: Dict[str, Any]):
        """Установка параметров голоса"""
        self.voice_synthesizer.update_parameters(parameters)

# Создание глобального экземпляра
_speech_generator = None

def init_module(config: Dict[str, Any]) -> SpeechGenerator:
    """Инициализация модуля"""
    global _speech_generator
    _speech_generator = SpeechGenerator(config)
    return _speech_generator

def get_instance() -> SpeechGenerator:
    """Получить экземпляр модуля"""
    if _speech_generator is None:
        raise RuntimeError("Модуль генерации речи не инициализирован")
    return _speech_generator