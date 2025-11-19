"""
Модуль работы с внешними API
Инициализация и экспорт основных компонентов
"""

import logging
from typing import Dict, Any, Optional, List

from .api_manager import APIManager
from .request_scheduler import RequestScheduler
from .response_parser import ResponseParser
from .error_handler import APIErrorHandler
from .service_integrations.weather import WeatherServiceIntegration, WeatherIntegration

class APICallerModule:
    """Основной класс модуля работы с внешними API"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.api_manager = APIManager()
        self.request_scheduler = RequestScheduler()
        self.response_parser = ResponseParser()
        self.error_handler = APIErrorHandler()
        
        # Инициализация сервисных интеграций
        self.service_integrations = {
            'weather': WeatherServiceIntegration()
        }
        
        self.initialized = False
    
    async def initialize(self):
        """Инициализация модуля"""
        try:
            # Инициализация компонентов
            await self.api_manager.initialize()
            await self.request_scheduler.initialize()
            await self.response_parser.initialize()
            await self.error_handler.initialize()
            
            # Инициализация сервисных интеграций
            for service_name, integration in self.service_integrations.items():
                if hasattr(integration, 'initialize'):
                    await integration.initialize()
            
            self.initialized = True
            self.logger.info("APICallerModule успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации APICallerModule: {e}")
            self.initialized = False
    
    async def call_api(self, service: str, endpoint: str, 
                      method: str = 'GET', data: Dict[str, Any] = None,
                      headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Вызов внешнего API
        
        Args:
            service: Название сервиса (weather, translate, etc.)
            endpoint: Конечная точка API
            method: HTTP метод
            data: Данные для отправки
            headers: HTTP заголовки
            
        Returns:
            Dict: Результат вызова API
        """
        if not self.initialized:
            self.logger.warning("APICallerModule не инициализирован, но используется")
        
        try:
            # Планируем запрос
            scheduled_request = await self.request_scheduler.schedule_request(
                service=service,
                endpoint=endpoint,
                method=method,
                data=data,
                headers=headers
            )
            
            # Выполняем запрос через API менеджер
            response = await self.api_manager.make_request(scheduled_request)
            
            # Обрабатываем возможные ошибки
            if response.get('status') == 'error':
                handled_error = await self.error_handler.handle_error(response)
                return handled_error
            
            # Парсим ответ
            parsed_response = await self.response_parser.parse_response(response)
            
            return {
                "status": "success",
                "service": service,
                "endpoint": endpoint,
                "data": parsed_response
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка вызова API {service}/{endpoint}: {e}")
            return await self.error_handler.handle_exception(e)
    
    async def call_service_integration(self, service: str, action: str, 
                                     parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Вызов через сервисную интеграцию
        
        Args:
            service: Название сервиса
            action: Действие
            parameters: Параметры
            
        Returns:
            Dict: Результат вызова
        """
        if service not in self.service_integrations:
            return {
                "status": "error",
                "error": f"Сервис {service} не поддерживается"
            }
        
        integration = self.service_integrations[service]
        
        try:
            if hasattr(integration, action):
                method = getattr(integration, action)
                result = await method(**(parameters or {}))
                return {
                    "status": "success",
                    "service": service,
                    "action": action,
                    "data": result
                }
            else:
                return {
                    "status": "error",
                    "error": f"Действие {action} не поддерживается для сервиса {service}"
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка вызова {service}.{action}: {e}")
            return await self.error_handler.handle_exception(e)
    
    def get_supported_services(self) -> List[str]:
        """Получение списка поддерживаемых сервисов"""
        return list(self.service_integrations.keys())
    
    async def get_service_capabilities(self, service: str) -> Dict[str, Any]:
        """
        Получение возможностей сервиса
        
        Args:
            service: Название сервиса
            
        Returns:
            Dict: Возможности сервиса
        """
        if service not in self.service_integrations:
            return {"status": "error", "error": f"Сервис {service} не поддерживается"}
        
        integration = self.service_integrations[service]
        
        if hasattr(integration, 'get_capabilities'):
            return await integration.get_capabilities()
        else:
            return {
                "status": "success",
                "service": service,
                "capabilities": ["basic_api_calls"]
            }
    
    async def get_request_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики запросов
        
        Returns:
            Dict: Статистика запросов
        """
        return {
            "total_requests": self.request_scheduler.get_total_requests(),
            "successful_requests": self.request_scheduler.get_successful_requests(),
            "failed_requests": self.request_scheduler.get_failed_requests(),
            "average_response_time": self.request_scheduler.get_average_response_time()
        }
    
    def get_module_info(self) -> Dict[str, Any]:
        """Получение информации о модуле"""
        return {
            "name": "api_caller",
            "version": "1.0",
            "description": "Модуль работы с внешними API и сервисами",
            "initialized": self.initialized,
            "supported_services": self.get_supported_services(),
            "components": {
                "api_manager": True,
                "request_scheduler": True,
                "response_parser": True,
                "error_handler": True
            }
        }

# Экспортируем основной класс и все остальные
__all__ = [
    'APICallerModule',
    'APIManager',
    'RequestScheduler', 
    'ResponseParser',
    'APIErrorHandler',
    'WeatherServiceIntegration'
]