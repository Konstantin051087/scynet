"""
TTS ДВИЖОК (Text-to-Speech)
Основной движок преобразования текста в речь
"""

import os
import tempfile
import logging
from typing import Dict, Any, Optional
import pyttsx3
import torch
import numpy as np
from gtts import gTTS
import io

class TTSEngine:
    """Движок преобразования текста в речь"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Настройки движка
        self.engine_type = config.get('engine_type', 'pyttsx3')
        self.language = config.get('language', 'ru')
        self.rate = config.get('speech_rate', 200)
        self.volume = config.get('volume', 1.0)
        
        # Инициализация выбранного движка
        if self.engine_type == 'pyttsx3':
            self.engine = self._init_pyttsx3()
        elif self.engine_type == 'gtts':
            self.engine = self._init_gtts()
        else:
            self.engine = self._init_pyttsx3()
        
        self.logger.info(f"TTS движок инициализирован: {self.engine_type}")
    
    def _init_pyttsx3(self) -> pyttsx3.Engine:
        """Инициализация оффлайн TTS движка"""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            # Установка голоса по умолчанию
            voices = engine.getProperty('voices')
            if voices:
                # Предпочтение русскоязычных голосов
                for voice in voices:
                    if 'russian' in voice.name.lower() or 'ru' in voice.id.lower():
                        engine.setProperty('voice', voice.id)
                        break
                else:
                    engine.setProperty('voice', voices[0].id)
            
            return engine
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации pyttsx3: {str(e)}")
            raise
    
    def _init_gtts(self):
        """Инициализация Google TTS"""
        # gTTS не требует предварительной инициализации
        return None
    
    def synthesize(self, text: str, save_path: Optional[str] = None) -> str:
        """
        Синтез речи из текста
        
        Args:
            text: Текст для синтеза
            save_path: Путь для сохранения аудио
            
        Returns:
            Путь к аудиофайлу
        """
        if not save_path:
            # Создание временного файла
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            save_path = temp_file.name
            temp_file.close()
        
        try:
            if self.engine_type == 'pyttsx3':
                self._synthesize_pyttsx3(text, save_path)
            elif self.engine_type == 'gtts':
                self._synthesize_gtts(text, save_path)
            
            self.logger.debug(f"Аудио сохранено: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.error(f"Ошибка синтеза речи: {str(e)}")
            # Резервный метод
            return self._fallback_synthesis(text, save_path)
    
    def _synthesize_pyttsx3(self, text: str, save_path: str):
        """Синтез с помощью pyttsx3"""
        self.engine.save_to_file(text, save_path)
        self.engine.runAndWait()
    
    def _synthesize_gtts(self, text: str, save_path: str):
        """Синтез с помощью Google TTS"""
        tts = gTTS(text=text, lang=self.language, slow=False)
        tts.save(save_path)
    
    def _fallback_synthesis(self, text: str, save_path: str) -> str:
        """Резервный метод синтеза"""
        self.logger.warning("Использование резервного метода синтеза")
        
        # Простой синтез через системные утилиты
        try:
            if os.name == 'nt':  # Windows
                import winsound
                # Здесь можно добавить простой синтез для Windows
                pass
            else:  # Linux/Mac
                import subprocess
                # Использование espeak для базового синтеза
                subprocess.run(['espeak', '-v', 'ru', '-w', save_path, text], 
                             capture_output=True)
            
            return save_path
        except Exception as e:
            self.logger.error(f"Резервный синтез также не удался: {str(e)}")
            raise
    
    def set_voice_parameters(self, rate: Optional[int] = None, 
                           volume: Optional[float] = None):
        """Установка параметров голоса"""
        if rate is not None:
            self.rate = rate
            if hasattr(self, 'engine'):
                self.engine.setProperty('rate', rate)
        
        if volume is not None:
            self.volume = volume
            if hasattr(self, 'engine'):
                self.engine.setProperty('volume', volume)
    
    def get_available_voices(self) -> list:
        """Получить список доступных голосов"""
        if hasattr(self, 'engine') and self.engine_type == 'pyttsx3':
            voices = self.engine.getProperty('voices')
            return [{'id': voice.id, 'name': voice.name} for voice in voices]
        return []