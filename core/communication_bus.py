"""
Шина сообщений между модулями (нервная система)
Обеспечивает асинхронное взаимодействие между компонентами
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
import redis.asyncio as redis
from dataclasses import dataclass
import json
import uuid

@dataclass
class Message:
    """Структура сообщения в шине"""
    message_id: str
    source: str
    destination: str
    message_type: str
    data: Dict[str, Any]
    timestamp: float
    priority: int = 1

class CommunicationBus:
    """Шина сообщений для межмодульного взаимодействия"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('core.communication_bus')
        
        # Подписчики на типы сообщений
        self.subscribers: Dict[str, List[Callable]] = {}
        
        # Redis клиент для продакшена
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = config.get('use_redis', False)
        
        # In-memory хранилище для разработки
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.processing_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Инициализация шины сообщений"""
        try:
            if self.use_redis:
                self.redis_client = redis.Redis(
                    host=self.config.get('redis_host', 'localhost'),
                    port=self.config.get('redis_port', 6379),
                    password=self.config.get('redis_password'),
                    decode_responses=True
                )
                # Проверяем подключение
                await self.redis_client.ping()
                self.logger.info("Redis подключен для шины сообщений")
            else:
                self.logger.info("Используется in-memory шина сообщений")
            
            # Запускаем обработчик сообщений
            self.is_running = True
            self.processing_task = asyncio.create_task(self._message_processor())
            
            self.logger.info("Шина сообщений инициализирована")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации шины сообщений: {e}")
            raise

    async def is_healthy(self) -> bool:
        """
        Проверка здоровья шины сообщений
        
        Returns:
            True если шина работает корректно
        """
        try:
            if self.use_redis and self.redis_client:
                # Проверяем подключение к Redis
                await self.redis_client.ping()
            # Для in-memory проверяем что обработчик запущен
            return self.is_running and (self.processing_task is not None and not self.processing_task.done())
        except Exception as e:
            self.logger.warning(f"Проверка здоровья шины сообщений не пройдена: {e}")
            return False

    async def send_message(self, message: Message) -> str:
        """
        Отправка сообщения в шину
        
        Args:
            message: Сообщение для отправки
            
        Returns:
            ID отправленного сообщения
        """
        try:
            if self.use_redis and self.redis_client:
                # Отправка через Redis
                channel = f"module:{message.destination}"
                message_data = {
                    'message_id': message.message_id,
                    'source': message.source,
                    'destination': message.destination,
                    'message_type': message.message_type,
                    'data': message.data,
                    'timestamp': message.timestamp
                }
                await self.redis_client.publish(channel, json.dumps(message_data))
            else:
                # In-memory отправка
                await self.message_queue.put(message)
            
            self.logger.debug(f"Сообщение {message.message_id} отправлено от {message.source} к {message.destination}")
            return message.message_id
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения: {e}")
            raise

    async def send_to_module(self, module_name: str, message_type: str, data: Dict[str, Any]) -> Any:
        """
        Упрощенная отправка сообщения модулю с ожиданием ответа
        
        Args:
            module_name: Имя модуля-получателя
            message_type: Тип сообщения
            data: Данные сообщения
            
        Returns:
            Ответ от модуля
        """
        message = Message(
            message_id=str(uuid.uuid4()),
            source='coordinator',
            destination=module_name,
            message_type=message_type,
            data=data,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # Создаем Future для ожидания ответа
        response_future = asyncio.Future()
        
        # Временная подписка на ответ
        response_type = f"response_{message.message_id}"
        self.subscribe(response_type, lambda msg: response_future.set_result(msg.data))
        
        # Отправляем сообщение
        await self.send_message(message)
        
        try:
            # Ждем ответ с таймаутом
            response = await asyncio.wait_for(response_future, timeout=30.0)
            return response
        except asyncio.TimeoutError:
            self.logger.error(f"Таймаут ожидания ответа от {module_name}")
            return {'error': 'timeout'}
        finally:
            # Убираем временную подписку
            self.unsubscribe(response_type)

    def subscribe(self, message_type: str, callback: Callable):
        """
        Подписка на тип сообщений
        
        Args:
            message_type: Тип сообщения для подписки
            callback: Функция-обработчик
        """
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        self.subscribers[message_type].append(callback)
        self.logger.debug(f"Добавлена подписка на {message_type}")

    def unsubscribe(self, message_type: str, callback: Callable = None):
        """
        Отписка от типа сообщений
        
        Args:
            message_type: Тип сообщения
            callback: Конкретный обработчик (если None - отписываем все)
        """
        if message_type in self.subscribers:
            if callback:
                self.subscribers[message_type] = [cb for cb in self.subscribers[message_type] if cb != callback]
            else:
                self.subscribers[message_type] = []
            self.logger.debug(f"Удалена подписка с {message_type}")

    async def _message_processor(self):
        """Обработчик входящих сообщений (для in-memory режима)"""
        while self.is_running:
            try:
                # Ждем сообщение
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Уведомляем подписчиков
                if message.message_type in self.subscribers:
                    for callback in self.subscribers[message.message_type]:
                        try:
                            await callback(message) if asyncio.iscoroutinefunction(callback) else callback(message)
                        except Exception as e:
                            self.logger.error(f"Ошибка в обработчике сообщения: {e}")
                
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Ошибка обработки сообщения: {e}")

    async def broadcast(self, message_type: str, data: Dict[str, Any]):
        """
        Широковещательная рассылка сообщения
        
        Args:
            message_type: Тип сообщения
            data: Данные для рассылки
        """
        message = Message(
            message_id=str(uuid.uuid4()),
            source='system',
            destination='broadcast',
            message_type=message_type,
            data=data,
            timestamp=asyncio.get_event_loop().time()
        )
        
        await self.send_message(message)

    async def get_bus_metrics(self) -> Dict[str, Any]:
        """Получение метрик шины сообщений"""
        return {
            'is_running': self.is_running,
            'use_redis': self.use_redis,
            'queue_size': self.message_queue.qsize() if not self.use_redis else 0,
            'subscribers_count': {msg_type: len(callbacks) for msg_type, callbacks in self.subscribers.items()}
        }

    async def shutdown(self):
        """Корректное завершение работы шины"""
        self.is_running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
            
        self.logger.info("Шина сообщений завершила работу")
