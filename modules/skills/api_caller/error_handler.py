"""
Обработчик ошибок API - управление исключениями и повторами
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import aiohttp

@dataclass
class RetryConfig:
    """Конфигурация повторов запросов"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0

class APIErrorHandler:
    """Обработка ошибок при работе с API"""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()
        self.logger = logging.getLogger('api_error_handler')
        self.error_stats = {}
    
    async def handle_error(self, error: Exception, request: Any) -> Dict[str, Any]:
        """Обработка ошибки и решение о повторе"""
        error_type = type(error).__name__
        
        # Обновляем статистику ошибок
        self._update_error_stats(error_type, request.service)
        
        # Логируем ошибку
        self.logger.error(
            f"Ошибка при запросе к {request.service}: {error_type} - {str(error)}"
        )
        
        # Определяем, нужно ли повторять запрос
        if self._should_retry(error):
            return await self._retry_request(request, error)
        else:
            return self._format_error_response(error, request)
    
    def _should_retry(self, error: Exception) -> bool:
        """Определение необходимости повтора запроса"""
        retryable_errors = (
            aiohttp.ServerTimeoutError,
            aiohttp.ClientConnectionError,
            aiohttp.ServerDisconnectedError,
            asyncio.TimeoutError
        )
        
        if isinstance(error, retryable_errors):
            return True
        
        # Для HTTP ошибок повторяем только 5xx
        if isinstance(error, aiohttp.ClientResponseError):
            return 500 <= error.status < 600
            
        return False
    
    async def _retry_request(self, request: Any, original_error: Exception) -> Dict[str, Any]:
        """Повтор запроса с экспоненциальной задержкой"""
        for attempt in range(self.retry_config.max_retries):
            try:
                # Вычисляем задержку
                delay = min(
                    self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt),
                    self.retry_config.max_delay
                )
                
                self.logger.info(
                    f"Повтор запроса к {request.service} "
                    f"(попытка {attempt + 1}/{self.retry_config.max_retries}) "
                    f"через {delay:.2f} сек"
                )
                
                await asyncio.sleep(delay)
                
                # Здесь должен быть повторный вызов API
                # Для простоты возвращаем ошибку
                return self._format_error_response(original_error, request)
                
            except Exception as retry_error:
                self.logger.error(f"Ошибка при повторе запроса: {retry_error}")
                if attempt == self.retry_config.max_retries - 1:
                    return self._format_error_response(retry_error, request)
    
    def _format_error_response(self, error: Exception, request: Any) -> Dict[str, Any]:
        """Форматирование ответа с ошибкой"""
        return {
            'success': False,
            'error': {
                'type': type(error).__name__,
                'message': str(error),
                'service': request.service,
                'endpoint': request.endpoint
            },
            'data': None,
            'status_code': getattr(error, 'status', 500)
        }
    
    def _update_error_stats(self, error_type: str, service: str):
        """Обновление статистики ошибок"""
        service_stats = self.error_stats.setdefault(service, {})
        service_stats[error_type] = service_stats.get(error_type, 0) + 1
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Получение статистики ошибок"""
        return self.error_stats.copy()
    
    def reset_statistics(self):
        """Сброс статистики ошибок"""
        self.error_stats.clear()