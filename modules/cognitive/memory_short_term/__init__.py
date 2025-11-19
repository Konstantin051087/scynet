# modules/cognitive/memory_short_term/__init__.py
"""
Модуль кратковременной памяти - оперативная память системы
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .context_manager import ContextManager
from .working_memory import WorkingMemory
from .cache_system import CacheSystem
from .attention_mechanism import AttentionMechanism
from .memory_buffer import MemoryBuffer

@dataclass
class MemoryItem:
    """Элемент памяти"""
    content: Any
    timestamp: float
    importance: float
    context: Dict[str, Any]

class MemoryShortTerm:
    """Основной класс модуля кратковременной памяти"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('modules.cognitive.memory_short_term')
        
        # Инициализация подмодулей
        self.context_manager = ContextManager()
        self.working_memory = WorkingMemory()
        self.cache_system = CacheSystem()
        self.attention_mechanism = AttentionMechanism()
        self.memory_buffer = MemoryBuffer()
        
        # Основное хранилище
        self.context_buffer: Dict[str, MemoryItem] = {}
        self.attention_focus: Optional[str] = None
        
        # Настройки
        self.max_buffer_size = config.get('max_buffer_size', 100)
        self.retention_time = config.get('retention_time', 300)
        
        self.is_initialized = False

    async def initialize(self):
        """Инициализация модуля - ОБЯЗАТЕЛЬНЫЙ метод для диагностики"""
        try:
            self.logger.info("Инициализация модуля кратковременной памяти...")
            
            # Здесь может быть дополнительная инициализация подмодулей
            # если они требуют асинхронной инициализации
            
            self.is_initialized = True
            self.logger.info("✅ Модуль кратковременной памяти инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации модуля памяти: {e}")
            return False

    async def shutdown(self):
        """Завершение работы - ОБЯЗАТЕЛЬНЫЙ метод для диагностики"""
        self.is_initialized = False
        self.logger.info("Модуль кратковременной памяти завершил работу")

    async def is_healthy(self) -> bool:
        """Проверка здоровья - ОБЯЗАТЕЛЬНЫЙ метод для диагностики"""
        return self.is_initialized and len(self.context_buffer) < self.max_buffer_size

    # Основные методы работы с памятью
    async def store_context(self, key: str, content: Any, importance: float = 1.0, context: Optional[Dict] = None):
        """Сохранение контекста в память"""
        if not self.is_initialized:
            raise RuntimeError("Модуль памяти не инициализирован")
            
        memory_item = MemoryItem(
            content=content,
            timestamp=time.time(),
            importance=importance,
            context=context or {}
        )
        
        self.context_buffer[key] = memory_item
        await self._cleanup_old_memories()
        
        self.logger.debug(f"Контекст сохранен: {key}")

    async def retrieve_context(self, key: str) -> Optional[Any]:
        """Извлечение контекста из памяти"""
        if key in self.context_buffer:
            item = self.context_buffer[key]
            # Обновляем timestamp при доступе
            item.timestamp = time.time()
            return item.content
        return None

    async def get_current_context(self) -> Dict[str, Any]:
        """Получение текущего контекста"""
        return {k: v.content for k, v in self.context_buffer.items()}

    async def set_attention_focus(self, focus_key: str):
        """Установка фокуса внимания"""
        self.attention_focus = focus_key
        await self.attention_mechanism.set_focus(focus_key)
        self.logger.debug(f"Фокус внимания установлен на: {focus_key}")

    async def clear_memory(self):
        """Очистка памяти"""
        self.context_buffer.clear()
        await self.working_memory.clear_working_memory()
        await self.memory_buffer.clear()
        self.attention_focus = None
        self.logger.info("Кратковременная память очищена")

    # Внутренние методы
    async def _cleanup_old_memories(self):
        """Очистка устаревших воспоминаний"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, item in self.context_buffer.items():
            if current_time - item.timestamp > self.retention_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.context_buffer[key]
            
        if keys_to_remove:
            self.logger.debug(f"Очищено устаревших воспоминаний: {len(keys_to_remove)}")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Получение статистики памяти"""
        buffer_stats = await self.memory_buffer.get_buffer_stats()
        cache_stats = await self.cache_system.get_stats()
        attention_stats = await self.attention_mechanism.get_attention_stats()
        
        return {
            'total_items': len(self.context_buffer),
            'working_memory_size': len(self.working_memory.memory_slots),
            'attention_focus': self.attention_focus,
            'max_buffer_size': self.max_buffer_size,
            'is_initialized': self.is_initialized,
            'buffer_stats': buffer_stats,
            'cache_stats': cache_stats,
            'attention_stats': attention_stats
        }

    async def process_attention(self, items: List[Dict[str, Any]]) -> List[float]:
        """Обработка внимания для списка элементов"""
        return await self.attention_mechanism.calculate_attention(items)

    async def cache_data(self, key: str, data: Any, ttl: int = 300):
        """Кэширование данных"""
        return await self.cache_system.set(key, data, ttl)

    async def get_cached_data(self, key: str) -> Any:
        """Получение кэшированных данных"""
        return await self.cache_system.get(key)

# Экспорт основного класса для системы
__all__ = [
    'MemoryShortTerm',  # ⚠️ ДОБАВИТЬ этот основной класс!
    'ContextManager',
    'WorkingMemory', 
    'CacheSystem',
    'AttentionMechanism',
    'MemoryBuffer'
]