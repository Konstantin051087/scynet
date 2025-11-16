"""
Система кэширования - кэширование текущих данных для ускорения доступа
"""

import pickle
import hashlib
import threading
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

class CacheSystem:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Инициализация системы кэширования
        
        Args:
            max_size: Максимальный размер кэша
            default_ttl: Время жизни по умолчанию в секундах
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict] = {}
        self.lock = threading.RLock()
        self.access_stats: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получение значения из кэша
        
        Args:
            key: Ключ кэша
            
        Returns:
            Значение или None если не найдено или истекло
        """
        with self.lock:
            cache_key = self._generate_key(key)
            
            if cache_key not in self.cache:
                return None
                
            cache_item = self.cache[cache_key]
            
            # Проверка TTL
            if datetime.now() > cache_item['expires_at']:
                del self.cache[cache_key]
                self.logger.debug(f"Кэш истек для ключа: {key}")
                return None
                
            # Обновление статистики доступа
            self.access_stats[cache_key] = self.access_stats.get(cache_key, 0) + 1
            
            # Обновление времени последнего доступа
            cache_item['last_accessed'] = datetime.now()
            
            self.logger.debug(f"Кэш попадание для ключа: {key}")
            return cache_item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Сохранение значения в кэш
        
        Args:
            key: Ключ кэша
            value: Значение для кэширования
            ttl: Время жизни в секундах
        """
        with self.lock:
            cache_key = self._generate_key(key)
            
            # Проверка размера кэша
            if len(self.cache) >= self.max_size:
                self._evict_least_used()
                
            ttl_seconds = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
            self.cache[cache_key] = {
                'value': value,
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'expires_at': expires_at,
                'access_count': 0
            }
            
            self.logger.debug(f"Значение закэшировано для ключа: {key}")
    
    def delete(self, key: str) -> bool:
        """
        Удаление значения из кэша
        
        Args:
            key: Ключ кэша
            
        Returns:
            True если удалено, False если не найдено
        """
        with self.lock:
            cache_key = self._generate_key(key)
            
            if cache_key in self.cache:
                del self.cache[cache_key]
                if cache_key in self.access_stats:
                    del self.access_stats[cache_key]
                self.logger.debug(f"Кэш удален для ключа: {key}")
                return True
                
            return False
    
    def clear(self) -> None:
        """Полная очистка кэша"""
        with self.lock:
            self.cache.clear()
            self.access_stats.clear()
            self.logger.info("Кэш полностью очищен")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        with self.lock:
            current_time = datetime.now()
            total_items = len(self.cache)
            expired_items = 0
            total_size = 0
            
            for item in self.cache.values():
                try:
                    item_size = len(pickle.dumps(item['value']))
                    total_size += item_size
                except:
                    item_size = 0
                    
                if current_time > item['expires_at']:
                    expired_items += 1
            
            hit_count = sum(self.access_stats.values())
            miss_count = total_items  # Упрощенная логика
            
            hit_ratio = hit_count / (hit_count + miss_count) if (hit_count + miss_count) > 0 else 0
            
            return {
                "total_items": total_items,
                "expired_items": expired_items,
                "total_size_bytes": total_size,
                "hit_count": hit_count,
                "miss_count": miss_count,
                "hit_ratio": hit_ratio,
                "max_size": self.max_size
            }
    
    def cleanup_expired(self) -> int:
        """
        Очистка просроченных записей
        
        Returns:
            Количество удаленных записей
        """
        with self.lock:
            current_time = datetime.now()
            expired_keys = []
            
            for key, item in self.cache.items():
                if current_time > item['expires_at']:
                    expired_keys.append(key)
                    
            for key in expired_keys:
                del self.cache[key]
                if key in self.access_stats:
                    del self.access_stats[key]
                    
            if expired_keys:
                self.logger.info(f"Очищено {len(expired_keys)} просроченных записей кэша")
                
            return len(expired_keys)
    
    def _generate_key(self, key: str) -> str:
        """
        Генерация хэш-ключа
        
        Args:
            key: Исходный ключ
            
        Returns:
            Хэшированный ключ
        """
        return hashlib.md5(key.encode()).hexdigest()
    
    def _evict_least_used(self) -> None:
        """Удаление наименее используемых записей"""
        if not self.cache:
            return
            
        # Находим запись с наименьшим количеством обращений
        least_used_key = None
        min_access_count = float('inf')
        
        for key, item in self.cache.items():
            access_count = self.access_stats.get(key, 0)
            if access_count < min_access_count:
                min_access_count = access_count
                least_used_key = key
                
        if least_used_key:
            del self.cache[least_used_key]
            if least_used_key in self.access_stats:
                del self.access_stats[least_used_key]
            self.logger.debug(f"Удален наименее используемый ключ кэша: {least_used_key}")