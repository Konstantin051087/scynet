"""
Планировщик запросов - ограничение частоты обращений к API
"""

import asyncio
import time
import logging
from typing import Dict, Any
from collections import defaultdict

class RequestScheduler:
    """Управление частотой запросов к различным API"""
    
    def __init__(self, rate_limits: Dict[str, Any]):
        self.rate_limits = rate_limits
        self.request_timestamps = defaultdict(list)
        self.locks = defaultdict(asyncio.Lock)
        self.logger = logging.getLogger('request_scheduler')
        
    async def wait_if_needed(self, service: str):
        """Ожидание если превышен лимит запросов"""
        if service not in self.rate_limits:
            return
            
        limits = self.rate_limits[service]
        max_requests = limits.get('max_requests', 60)
        time_window = limits.get('time_window', 60)
        
        async with self.locks[service]:
            current_time = time.time()
            
            # Удаляем старые запросы вне временного окна
            self.request_timestamps[service] = [
                ts for ts in self.request_timestamps[service] 
                if current_time - ts < time_window
            ]
            
            # Проверяем количество запросов
            if len(self.request_timestamps[service]) >= max_requests:
                # Вычисляем время ожидания
                oldest_request = self.request_timestamps[service][0]
                wait_time = time_window - (current_time - oldest_request)
                
                if wait_time > 0:
                    self.logger.warning(
                        f"Достигнут лимит запросов для {service}. "
                        f"Ожидание {wait_time:.2f} секунд"
                    )
                    await asyncio.sleep(wait_time)
                    
                    # Обновляем временные метки после ожидания
                    self.request_timestamps[service] = []
            
            # Добавляем текущий запрос
            self.request_timestamps[service].append(time.time())
    
    def update_rate_limits(self, service: str, new_limits: Dict[str, Any]):
        """Обновление лимитов для сервиса"""
        self.rate_limits[service] = new_limits
        self.logger.info(f"Обновлены лимиты для {service}: {new_limits}")