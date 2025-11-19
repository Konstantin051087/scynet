"""
Менеджер API - управление вызовами внешних сервисов
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import aiohttp
from .request_scheduler import RequestScheduler
from .response_parser import ResponseParser
from .error_handler import APIErrorHandler

@dataclass
class APIRequest:
    """Структура запроса к API"""
    service: str
    endpoint: str
    method: str = "GET"
    params: Dict[str, Any] = None
    headers: Dict[str, str] = None
    data: Any = None
    timeout: int = 30

class APIManager:
    """Основной менеджер для работы с API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scheduler = RequestScheduler(config.get('rate_limits', {}))
        self.parser = ResponseParser()
        self.error_handler = APIErrorHandler()
        self.active_sessions: Dict[str, aiohttp.ClientSession] = {}
        self.logger = logging.getLogger('api_manager')
        
        # Загрузка интеграций сервисов
        self.service_integrations = self._load_service_integrations()
        
    def _load_service_integrations(self) -> Dict[str, Any]:
        """Загрузка интеграций с сервисами"""
        integrations = {}
    
        # Загрузка погодных сервисов
        try:
            from .service_integrations.weather import WeatherIntegration
            integrations['weather'] = WeatherIntegration(self.config)
        except ImportError as e:
            self.logger.warning(f"Не удалось загрузить модуль погоды: {e}")
            # Фолбэк на базовую реализацию
            try:
                from .service_integrations.weather import WeatherServiceIntegration
                integrations['weather'] = WeatherServiceIntegration(self.config)
            except ImportError:
                self.logger.error("Не удалось загрузить ни одну реализацию погодного сервиса")
            
        return integrations
    
    async def make_request(self, request: APIRequest) -> Dict[str, Any]:
        """Выполнение запроса к API"""
        try:
            # Проверка лимитов запросов
            await self.scheduler.wait_if_needed(request.service)
            
            # Получение сессии
            session = await self._get_session(request.service)
            
            # Выполнение запроса
            async with session.request(
                method=request.method,
                url=self._build_url(request),
                params=request.params,
                headers=request.headers,
                json=request.data,
                timeout=request.timeout
            ) as response:
                
                # Обработка ответа
                parsed_response = await self.parser.parse_response(response, request.service)
                
                # Логирование успешного запроса
                self.logger.info(f"Успешный запрос к {request.service}: {request.endpoint}")
                
                return parsed_response
                
        except Exception as e:
            # Обработка ошибок
            return await self.error_handler.handle_error(e, request)
    
    async def _get_session(self, service: str) -> aiohttp.ClientSession:
        """Получение или создание клиентской сессии"""
        if service not in self.active_sessions:
            timeout = aiohttp.ClientTimeout(total=self.config.get('timeout', 30))
            connector = aiohttp.TCPConnector(limit=100)
            self.active_sessions[service] = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
        return self.active_sessions[service]
    
    def _build_url(self, request: APIRequest) -> str:
        """Построение полного URL для запроса"""
        base_url = self.config.get('services', {}).get(request.service, {}).get('base_url', '')
        return f"{base_url}{request.endpoint}"
    
    async def call_service(self, service_name: str, action: str, **kwargs) -> Any:
        """Упрощенный вызов сервиса через интеграции"""
        if service_name in self.service_integrations:
            integration = self.service_integrations[service_name]
            return await integration.execute(action, **kwargs)
        else:
            raise ValueError(f"Сервис {service_name} не найден")
    
    async def close(self):
        """Закрытие всех активных сессий"""
        for session in self.active_sessions.values():
            await session.close()
        self.active_sessions.clear()