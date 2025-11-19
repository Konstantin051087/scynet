"""
МОДУЛЬ ГЕНЕРАЦИИ РЕЧИ
Речевой аппарат системы Синтетический Разум
"""

import os
import logging
import asyncio
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
        self.communication_bus = None
        self.is_initialized = False
        
        # Инициализация компонентов
        self.tts_engine = TTSEngine(config.get('tts', {}))
        self.emotion_modulator = EmotionModulator(config.get('emotion', {}))
        self.voice_synthesizer = VoiceSynthesizer(config.get('voice', {}))
        self.prosody_controller = ProsodyController(config.get('prosody', {}))
        self.audio_postprocessor = AudioPostprocessor(config.get('audio', {}))
        
        self.logger.info("Модуль генерации речи создан")

    async def initialize(self, communication_bus) -> bool:
        """Асинхронная инициализация модуля"""
        try:
            self.communication_bus = communication_bus
            
            # Подписка на сообщения
            await self._setup_communication()
            
            # Инициализация компонентов
            await self._initialize_components()
            
            self.is_initialized = True
            self.logger.info("✅ Модуль генерации речи инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации модуля генерации речи: {e}")
            return False

    async def _setup_communication(self):
        """Настройка коммуникации с шиной сообщений"""
        # Подписка на запросы генерации речи
        self.communication_bus.subscribe("speech_generation_request", self._handle_speech_request)
        self.communication_bus.subscribe("module_health_check", self._handle_health_check)
        
        self.logger.debug("Коммуникация с шиной сообщений настроена")

    async def _initialize_components(self):
        """Инициализация всех компонентов модуля"""
        # Здесь можно добавить асинхронную инициализацию компонентов
        # если они будут требовать долгих операций
        pass

    async def _handle_speech_request(self, message):
        """Обработка запроса на генерацию речи"""
        try:
            text = message.data.get('text', '')
            emotion = message.data.get('emotion', 'neutral')
            voice_profile = message.data.get('voice_profile', 'neutral/male_neutral')
            
            # Генерация речи
            audio_path = await self.generate_speech(text, emotion, voice_profile)
            
            # Отправка ответа
            response_message = {
                'request_id': message.data.get('request_id'),
                'audio_path': audio_path,
                'status': 'success'
            }
            
            await self.communication_bus.send_message({
                'source': 'speech_generator',
                'destination': message.source,
                'message_type': 'speech_generation_response',
                'data': response_message
            })
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса речи: {e}")
            await self._send_error_response(message, str(e))

    async def _handle_health_check(self, message):
        """Обработка проверки здоровья модуля"""
        health_status = await self.get_status()
        
        await self.communication_bus.send_message({
            'source': 'speech_generator',
            'destination': message.source,
            'message_type': 'health_check_response',
            'data': health_status
        })

    async def _send_error_response(self, original_message, error_text):
        """Отправка сообщения об ошибке"""
        await self.communication_bus.send_message({
            'source': 'speech_generator',
            'destination': original_message.source,
            'message_type': 'speech_generation_error',
            'data': {
                'request_id': original_message.data.get('request_id'),
                'error': error_text,
                'status': 'error'
            }
        })

    async def generate_speech(self, text: str, emotion: str = "neutral", 
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

    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса модуля для ModuleManager"""
        return {
            'status': 'initialized' if self.is_initialized else 'error',
            'is_initialized': self.is_initialized,
            'components': {
                'tts_engine': True,
                'emotion_modulator': True,
                'voice_synthesizer': True,
                'prosody_controller': True,
                'audio_postprocessor': True
            },
            'health': 'healthy' if self.is_initialized else 'unhealthy'
        }

    async def shutdown(self):
        """Корректное завершение работы модуля"""
        try:
            # Отписка от шины сообщений
            if self.communication_bus:
                self.communication_bus.unsubscribe("speech_generation_request")
                self.communication_bus.unsubscribe("module_health_check")
            
            self.is_initialized = False
            self.logger.info("Модуль генерации речи завершил работу")
            
        except Exception as e:
            self.logger.error(f"Ошибка завершения работы модуля: {e}")

    def get_available_voices(self) -> list:
        """Получить список доступных голосовых профилей"""
        return self.voice_synthesizer.get_available_profiles()

    def set_voice_parameters(self, parameters: Dict[str, Any]):
        """Установка параметров голоса"""
        self.voice_synthesizer.update_parameters(parameters)

# Создание глобального экземпляра
_speech_generator = None

async def init_module(config: Dict[str, Any], communication_bus) -> SpeechGenerator:
    """Инициализация модуля"""
    global _speech_generator
    _speech_generator = SpeechGenerator(config)
    await _speech_generator.initialize(communication_bus)
    return _speech_generator

def get_instance() -> SpeechGenerator:
    """Получить экземпляр модуля"""
    if _speech_generator is None:
        raise RuntimeError("Модуль генерации речи не инициализирован")
    return _speech_generator