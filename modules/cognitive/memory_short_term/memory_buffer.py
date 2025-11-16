"""
Буфер памяти - временное хранение данных для быстрого доступа
"""

import threading
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from collections import deque
import logging

class MemoryBuffer:
    def __init__(self, buffer_size: int = 100, cleanup_interval: int = 30):
        """
        Инициализация буфера памяти
        
        Args:
            buffer_size: Максимальный размер буфера
            cleanup_interval: Интервал очистки в секундах
        """
        self.buffer_size = buffer_size
        self.cleanup_interval = cleanup_interval
        self.buffers: Dict[str, deque] = {}
        self.buffer_metadata: Dict[str, Dict] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Запуск фоновой очистки
        self._start_cleanup_thread()
    
    def create_buffer(self, buffer_name: str, max_items: Optional[int] = None) -> bool:
        """
        Создание нового буфера
        
        Args:
            buffer_name: Имя буфера
            max_items: Максимальное количество элементов
            
        Returns:
            True если создан успешно, False если уже существует
        """
        with self.lock:
            if buffer_name in self.buffers:
                return False
                
            max_items = max_items or self.buffer_size
            self.buffers[buffer_name] = deque(maxlen=max_items)
            self.buffer_metadata[buffer_name] = {
                'created_at': datetime.now(),
                'max_items': max_items,
                'item_count': 0,
                'last_accessed': datetime.now()
            }
            
            self.logger.debug(f"Создан буфер: {buffer_name}")
            return True
    
    def push(self, buffer_name: str, item: Any, item_type: str = "generic") -> bool:
        """
        Добавление элемента в буфер
        
        Args:
            buffer_name: Имя буфера
            item: Элемент для добавления
            item_type: Тип элемента
            
        Returns:
            True если успешно, False если буфер не существует
        """
        with self.lock:
            if buffer_name not in self.buffers:
                self.logger.warning(f"Буфер {buffer_name} не существует")
                return False
                
            buffer_item = {
                'data': item,
                'type': item_type,
                'timestamp': datetime.now(),
                'id': self._generate_item_id()
            }
            
            self.buffers[buffer_name].append(buffer_item)
            self.buffer_metadata[buffer_name]['item_count'] = len(self.buffers[buffer_name])
            self.buffer_metadata[buffer_name]['last_accessed'] = datetime.now()
            
            self.logger.debug(f"Добавлен элемент в буфер {buffer_name}")
            return True
    
    def pop(self, buffer_name: str) -> Optional[Any]:
        """
        Извлечение элемента из буфера (FIFO)
        
        Args:
            buffer_name: Имя буфера
            
        Returns:
            Элемент или None если буфер пуст
        """
        with self.lock:
            if buffer_name not in self.buffers or not self.buffers[buffer_name]:
                return None
                
            buffer_item = self.buffers[buffer_name].popleft()
            self.buffer_metadata[buffer_name]['item_count'] = len(self.buffers[buffer_name])
            self.buffer_metadata[buffer_name]['last_accessed'] = datetime.now()
            
            self.logger.debug(f"Извлечен элемент из буфера {buffer_name}")
            return buffer_item['data']
    
    def peek(self, buffer_name: str, index: int = 0) -> Optional[Any]:
        """
        Просмотр элемента без извлечения
        
        Args:
            buffer_name: Имя буфера
            index: Индекс элемента (0 - первый)
            
        Returns:
            Элемент или None если не найден
        """
        with self.lock:
            if (buffer_name not in self.buffers or 
                index >= len(self.buffers[buffer_name])):
                return None
                
            buffer_item = self.buffers[buffer_name][index]
            self.buffer_metadata[buffer_name]['last_accessed'] = datetime.now()
            
            return buffer_item['data']
    
    def get_all(self, buffer_name: str) -> List[Any]:
        """
        Получение всех элементов буфера
        
        Args:
            buffer_name: Имя буфера
            
        Returns:
            Список элементов
        """
        with self.lock:
            if buffer_name not in self.buffers:
                return []
                
            self.buffer_metadata[buffer_name]['last_accessed'] = datetime.now()
            return [item['data'] for item in self.buffers[buffer_name]]
    
    def clear_buffer(self, buffer_name: str) -> bool:
        """
        Очистка буфера
        
        Args:
            buffer_name: Имя буфера
            
        Returns:
            True если успешно, False если буфер не существует
        """
        with self.lock:
            if buffer_name not in self.buffers:
                return False
                
            self.buffers[buffer_name].clear()
            self.buffer_metadata[buffer_name]['item_count'] = 0
            self.buffer_metadata[buffer_name]['last_accessed'] = datetime.now()
            
            self.logger.info(f"Буфер {buffer_name} очищен")
            return True
    
    def delete_buffer(self, buffer_name: str) -> bool:
        """
        Удаление буфера
        
        Args:
            buffer_name: Имя буфера
            
        Returns:
            True если успешно, False если буфер не существует
        """
        with self.lock:
            if buffer_name not in self.buffers:
                return False
                
            del self.buffers[buffer_name]
            del self.buffer_metadata[buffer_name]
            
            self.logger.info(f"Буфер {buffer_name} удален")
            return True
    
    def get_buffer_stats(self, buffer_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение статистики буфера
        
        Args:
            buffer_name: Имя буфера
            
        Returns:
            Статистика буфера или None если не существует
        """
        with self.lock:
            if buffer_name not in self.buffers:
                return None
                
            metadata = self.buffer_metadata[buffer_name]
            buffer = self.buffers[buffer_name]
            
            # Анализ типов элементов
            type_distribution = {}
            for item in buffer:
                item_type = item['type']
                type_distribution[item_type] = type_distribution.get(item_type, 0) + 1
            
            return {
                'buffer_name': buffer_name,
                'item_count': len(buffer),
                'max_items': metadata['max_items'],
                'created_at': metadata['created_at'],
                'last_accessed': metadata['last_accessed'],
                'type_distribution': type_distribution,
                'usage_percent': (len(buffer) / metadata['max_items']) * 100
            }
    
    def get_all_buffers_stats(self) -> Dict[str, Dict[str, Any]]:
        """Получение статистики всех буферов"""
        with self.lock:
            stats = {}
            for buffer_name in self.buffers:
                stats[buffer_name] = self.get_buffer_stats(buffer_name)
            return stats
    
    def search_in_buffer(self, buffer_name: str, search_func: callable) -> List[Any]:
        """
        Поиск элементов в буфере по функции
        
        Args:
            buffer_name: Имя буфера
            search_func: Функция для поиска (принимает элемент, возвращает bool)
            
        Returns:
            Список найденных элементов
        """
        with self.lock:
            if buffer_name not in self.buffers:
                return []
                
            results = []
            for item in self.buffers[buffer_name]:
                if search_func(item['data']):
                    results.append(item['data'])
                    
            self.buffer_metadata[buffer_name]['last_accessed'] = datetime.now()
            return results
    
    def _generate_item_id(self) -> str:
        """Генерация ID для элемента буфера"""
        return f"item_{int(time.time() * 1000)}_{hash(str(time.time()))}"
    
    def _start_cleanup_thread(self) -> None:
        """Запуск фонового потока для очистки"""
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_old_buffers()
                
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_buffers(self) -> None:
        """Очистка старых неиспользуемых буферов"""
        with self.lock:
            current_time = datetime.now()
            buffers_to_remove = []
            
            for buffer_name, metadata in self.buffer_metadata.items():
                time_since_last_access = current_time - metadata['last_accessed']
                
                # Удаляем буферы, к которым не обращались более 1 часа и которые пусты
                if (time_since_last_access > timedelta(hours=1) and 
                    len(self.buffers[buffer_name]) == 0):
                    buffers_to_remove.append(buffer_name)
                    
            for buffer_name in buffers_to_remove:
                self.delete_buffer(buffer_name)
                
            if buffers_to_remove:
                self.logger.info(f"Удалено {len(buffers_to_remove)} неиспользуемых буферов")