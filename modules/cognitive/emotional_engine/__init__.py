"""
Модуль эмоционального интеллекта
Обеспечивает детекцию эмоций, симуляцию эмоциональных реакций и эмпатию
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum

class EmotionalState(Enum):
    """Эмоциональные состояния системы"""
    NEUTRAL = "нейтральное"
    HAPPY = "радость"
    SAD = "грусть"
    ANGRY = "гнев"
    EXCITED = "возбуждение"
    CALM = "спокойствие"
    CURIOUS = "любопытство"
    CONFUSED = "замешательство"

class EmotionalEngine:
    """Основной класс модуля эмоционального интеллекта"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("EmotionalEngine")
        self.communication_bus = None
        self.is_initialized = False
        
        # Инициализация подмодулей
        self.emotion_detector = EmotionDetector(config.get('detection', {}))
        self.emotion_simulator = EmotionSimulator(config.get('simulation', {}))
        self.empathy_engine = EmpathyEngine(config.get('empathy', {}))
        self.mood_tracker = MoodTracker(config.get('mood', {}))
        
        # Текущее состояние
        self.current_mood = EmotionalState.NEUTRAL
        self.emotional_state = {}
        self.emotion_history = []
        
        self.logger.info("Модуль эмоционального интеллекта создан")

    async def initialize(self, communication_bus) -> bool:
        """Асинхронная инициализация модуля - ОБЯЗАТЕЛЬНЫЙ метод"""
        try:
            self.communication_bus = communication_bus
            self.is_initialized = True
            
            # Настройка коммуникации с шиной сообщений
            await self._setup_communication()
            
            # Инициализация подмодулей если требуется
            if hasattr(self.emotion_detector, 'initialize'):
                await self.emotion_detector.initialize()
            if hasattr(self.emotion_simulator, 'initialize'):
                await self.emotion_simulator.initialize()
            if hasattr(self.empathy_engine, 'initialize'):
                await self.empathy_engine.initialize()
            if hasattr(self.mood_tracker, 'initialize'):
                await self.mood_tracker.initialize()
            
            self.logger.info("✅ Модуль эмоционального интеллекта инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации модуля эмоционального интеллекта: {e}")
            return False

    async def _setup_communication(self):
        """Настройка коммуникации с шиной сообщений"""
        self.communication_bus.subscribe("emotion_analysis_request", self._handle_emotion_analysis)
        self.communication_bus.subscribe("emotional_state_request", self._handle_state_request)
        self.communication_bus.subscribe("module_health_check", self._handle_health_check)
        
        self.logger.debug("Коммуникация с шиной сообщений настроена")

    async def _handle_emotion_analysis(self, message):
        """Обработка запроса анализа эмоций"""
        try:
            data = message.data
            text = data.get('text', '')
            user_id = data.get('user_id')
            context = data.get('context', {})
            
            result = await self.process_input(text, user_id, context)
            
            await self.communication_bus.send_message({
                'source': 'emotional_engine',
                'destination': message.source,
                'message_type': 'emotion_analysis_response',
                'data': {
                    'request_id': data.get('request_id'),
                    'result': result,
                    'status': 'success'
                }
            })
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа эмоций: {e}")
            await self._send_error_response(message, str(e))

    async def _handle_state_request(self, message):
        """Обработка запроса текущего эмоционального состояния"""
        try:
            state = await self.get_current_state()
            
            await self.communication_bus.send_message({
                'source': 'emotional_engine',
                'destination': message.source,
                'message_type': 'emotional_state_response',
                'data': {
                    'request_id': message.data.get('request_id'),
                    'state': state,
                    'status': 'success'
                }
            })
            
        except Exception as e:
            self.logger.error(f"Ошибка получения состояния: {e}")
            await self._send_error_response(message, str(e))

    async def _handle_health_check(self, message):
        """Обработка проверки здоровья модуля"""
        health_status = await self.get_status()
        
        await self.communication_bus.send_message({
            'source': 'emotional_engine',
            'destination': message.source,
            'message_type': 'health_check_response',
            'data': health_status
        })

    async def _send_error_response(self, original_message, error_text):
        """Отправка сообщения об ошибке"""
        await self.communication_bus.send_message({
            'source': 'emotional_engine',
            'destination': original_message.source,
            'message_type': 'emotion_error_response',
            'data': {
                'request_id': original_message.data.get('request_id'),
                'error': error_text,
                'status': 'error'
            }
        })

    async def shutdown(self):
        """Корректное завершение работы модуля - ОБЯЗАТЕЛЬНЫЙ метод"""
        try:
            # Отписка от шины сообщений
            if self.communication_bus:
                self.communication_bus.unsubscribe("emotion_analysis_request")
                self.communication_bus.unsubscribe("emotional_state_request")
                self.communication_bus.unsubscribe("module_health_check")
            
            # Завершение работы подмодулей если требуется
            if hasattr(self.emotion_detector, 'shutdown'):
                await self.emotion_detector.shutdown()
            if hasattr(self.emotion_simulator, 'shutdown'):
                await self.emotion_simulator.shutdown()
            if hasattr(self.empathy_engine, 'shutdown'):
                await self.empathy_engine.shutdown()
            if hasattr(self.mood_tracker, 'shutdown'):
                await self.mood_tracker.shutdown()
            
            self.is_initialized = False
            self.logger.info("Модуль эмоционального интеллекта завершил работу")
            
        except Exception as e:
            self.logger.error(f"Ошибка завершения работы модуля: {e}")

    async def is_healthy(self) -> bool:
        """Проверка здоровья модуля - ОБЯЗАТЕЛЬНЫЙ метод"""
        return self.is_initialized and len(self.emotion_history) < 10000  # Простая проверка

    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса модуля - ОБЯЗАТЕЛЬНЫЙ метод"""
        return {
            'status': 'initialized' if self.is_initialized else 'error',
            'is_initialized': self.is_initialized,
            'current_mood': self.current_mood.value,
            'emotion_history_count': len(self.emotion_history),
            'submodules': {
                'emotion_detector': hasattr(self.emotion_detector, 'is_healthy') and await self.emotion_detector.is_healthy(),
                'emotion_simulator': hasattr(self.emotion_simulator, 'is_healthy') and await self.emotion_simulator.is_healthy(),
                'empathy_engine': hasattr(self.empathy_engine, 'is_healthy') and await self.empathy_engine.is_healthy(),
                'mood_tracker': hasattr(self.mood_tracker, 'is_healthy') and await self.mood_tracker.is_healthy()
            },
            'health': 'healthy' if self.is_initialized else 'unhealthy'
        }

    async def get_current_state(self) -> Dict[str, Any]:
        """Получение текущего эмоционального состояния"""
        return {
            'current_mood': self.current_mood.value,
            'emotional_state': self.emotional_state,
            'recent_emotions': self.emotion_history[-10:] if self.emotion_history else []
        }

    async def process_input(self, text: str, user_id: Optional[str] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Основной метод обработки входящих данных"""
        try:
            # Детекция эмоций в тексте
            detected_emotions = await self.emotion_detector.detect_emotions(text, context)
            
            # Обновление настроения системы
            self.current_mood = await self.emotion_simulator.simulate_response(
                detected_emotions, text, self.current_mood, context
            )
            
            # Генерация эмпатического ответа
            empathic_response = await self.empathy_engine.generate_response(
                detected_emotions, self.current_mood, text, context
            )
            
            # Логирование эмоционального состояния
            await self.mood_tracker.track_mood(
                user_id, detected_emotions, self.current_mood, text, context
            )
            
            # Сохранение в историю
            emotion_record = {
                'timestamp': asyncio.get_event_loop().time(),
                'text': text,
                'detected_emotions': detected_emotions,
                'system_mood': self.current_mood.value,
                'user_id': user_id
            }
            self.emotion_history.append(emotion_record)
            
            # Обновление общего эмоционального состояния
            self.emotional_state = {
                'current_mood': self.current_mood.value,
                'detected_emotions': detected_emotions,
                'empathy_level': await self.empathy_engine.get_empathy_level(),
                'mood_stability': await self.mood_tracker.get_mood_stability()
            }
            
            return {
                "detected_emotions": detected_emotions,
                "system_mood": self.current_mood.value,
                "empathic_response": empathic_response,
                "emotional_state": self.emotional_state
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка в Emotional Engine: {e}")
            return {
                "detected_emotions": {"neutral": 1.0},
                "system_mood": EmotionalState.NEUTRAL.value,
                "empathic_response": "Понимаю. Продолжайте, пожалуйста.",
                "emotional_state": self.emotional_state,
                "error": str(e)
            }

    async def adjust_emotional_response(self, feedback: Dict[str, Any]):
        """Корректировка эмоциональных реакций на основе обратной связи"""
        try:
            if hasattr(self.empathy_engine, 'adjust_empathy'):
                await self.empathy_engine.adjust_empathy(feedback)
            if hasattr(self.emotion_simulator, 'adjust_simulation'):
                await self.emotion_simulator.adjust_simulation(feedback)
            
            self.logger.info("Эмоциональные реакции скорректированы на основе фидбека")
            
        except Exception as e:
            self.logger.error(f"Ошибка корректировки эмоциональных реакций: {e}")

# Экспорт классов
__all__ = [
    'EmotionalEngine', 
    'EmotionDetector', 
    'EmotionSimulator', 
    'EmpathyEngine', 
    'MoodTracker',
    'EmotionalState'
]