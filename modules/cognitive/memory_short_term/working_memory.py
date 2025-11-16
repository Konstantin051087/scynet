"""
Рабочая память - хранение текущих вычислений и временных данных
"""

import threading
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

@dataclass
class WorkingMemoryItem:
    """Элемент рабочей памяти"""
    key: str
    value: Any
    timestamp: datetime
    ttl: Optional[timedelta] = None
    priority: int = 1  # Приоритет от 1 (низкий) до 5 (высокий)

class WorkingMemory:
    def __init__(self, max_size: int = 100, cleanup_interval: int = 60):
        """
        Инициализация рабочей памяти
        
        Args:
            max_size: Максимальное количество элементов
            cleanup_interval: Интервал очистки в секундах
        """
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.memory: Dict[str, WorkingMemoryItem] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Запуск фоновой очистки
        self._start_cleanup_thread()
        
    def store(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
              priority: int = 1) -> None:
        """
        Сохранение значения в рабочей памяти
        
        Args:
            key: Ключ для доступа
            value: Значение для хранения
            ttl_seconds: Время жизни в секундах
            priority: Приоритет элемента
        """
        with self.lock:
            # Если память заполнена, удаляем наименее приоритетные элементы
            if len(self.memory) >= self.max_size:
                self._evict_low_priority()
                
            ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else None
            item = WorkingMemoryItem(
                key=key,
                value=value,
                timestamp=datetime.now(),
                ttl=ttl,
                priority=priority
            )
            
            self.memory[key] = item
            self.logger.debug(f"Сохранен элемент в рабочей памяти: {key}")
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Получение значения из рабочей памяти
        
        Args:
            key: Ключ элемента
            
        Returns:
            Значение элемента или None если не найден
        """
        with self.lock:
            if key not in self.memory:
                return None
                
            item = self.memory[key]
            
            # Проверка TTL
            if item.ttl and datetime.now() - item.timestamp > item.ttl:
                del self.memory[key]
                self.logger.debug(f"Элемент {key} удален по TTL")
                return None
                
            return item.value
    
    def delete(self, key: str) -> bool:
        """
        Удаление элемента из рабочей памяти
        
        Args:
            key: Ключ элемента
            
        Returns:
            True если элемент удален, False если не найден
        """
        with self.lock:
            if key in self.memory:
                del self.memory[key]
                self.logger.debug(f"Элемент {key} удален из рабочей памяти")
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Проверка существования элемента"""
        with self.lock:
            return key in self.memory and not self._is_expired(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики рабочей памяти"""
        with self.lock:
            current_time = datetime.now()
            expired_count = 0
            priority_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            for item in self.memory.values():
                if item.ttl and current_time - item.timestamp > item.ttl:
                    expired_count += 1
                priority_distribution[item.priority] += 1
                
            return {
                "total_items": len(self.memory),
                "expired_items": expired_count,
                "max_size": self.max_size,
                "priority_distribution": priority_distribution,
                "memory_usage_percent": (len(self.memory) / self.max_size) * 100
            }
    
    def clear(self) -> None:
        """Полная очистка рабочей памяти"""
        with self.lock:
            self.memory.clear()
            self.logger.info("Рабочая память полностью очищена")
    
    def search_by_pattern(self, pattern: str) -> List[Any]:
        """
        Поиск элементов по шаблону в ключах
        
        Args:
            pattern: Шаблон для поиска
            
        Returns:
            Список найденных значений
        """
        with self.lock:
            results = []
            for key, item in self.memory.items():
                if pattern in key and not self._is_expired(key):
                    results.append(item.value)
            return results
    
    def _is_expired(self, key: str) -> bool:
        """Проверка истекшего TTL"""
        if key not in self.memory:
            return True
            
        item = self.memory[key]
        if item.ttl and datetime.now() - item.timestamp > item.ttl:
            del self.memory[key]
            return True
            
        return False
    
    def _evict_low_priority(self) -> None:
        """Удаление наименее приоритетных элементов при переполнении"""
        # Сортируем элементы по приоритету и времени
        items = sorted(
            self.memory.values(),
            key=lambda x: (x.priority, x.timestamp)
        )
        
        # Удаляем 10% наименее приоритетных элементов
        evict_count = max(1, len(items) // 10)
        for item in items[:evict_count]:
            del self.memory[item.key]
            self.logger.debug(f"Элемент {item.key} удален из-за нехватки памяти")
    
    def _start_cleanup_thread(self) -> None:
        """Запуск фонового потока для очистки"""
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired()
                
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired(self) -> None:
        """Очистка просроченных элементов"""
        with self.lock:
            expired_keys = []
            current_time = datetime.now()
            
            for key, item in self.memory.items():
                if item.ttl and current_time - item.timestamp > item.ttl:
                    expired_keys.append(key)
                    
            for key in expired_keys:
                del self.memory[key]
                
            if expired_keys:
                self.logger.debug(f"Очищено {len(expired_keys)} просроченных элементов")