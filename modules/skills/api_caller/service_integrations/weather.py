"""
Интеграция с погодными сервисами - базовый класс
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..api_manager import APIRequest

class BaseWeatherService(ABC):
    """Абстрактный базовый класс для погодных сервисов"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = self._get_api_key()
        self.base_url = self._get_base_url()
        self.logger = logging.getLogger(f'weather_{self.get_provider_name()}')
    
    @abstractmethod
    def _get_api_key(self) -> str:
        """Получение API ключа"""
        pass
    
    @abstractmethod
    def _get_base_url(self) -> str:
        """Получение базового URL"""
        pass
    
    @abstractmethod
    async def get_current_weather(self, city: str) -> Dict[str, Any]:
        """Получение текущей погоды"""
        pass
    
    @abstractmethod
    async def get_forecast(self, city: str, days: int = 5) -> Dict[str, Any]:
        """Получение прогноза погоды"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Получение имени провайдера"""
        pass

class WeatherServiceIntegration:
    """Универсальная интеграция с погодными сервисами"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = self._initialize_providers()
        self.logger = logging.getLogger('weather_integration')
    
    def _initialize_providers(self) -> Dict[str, BaseWeatherService]:
        """Инициализация провайдеров погоды"""
        providers = {}
        
        try:
            from .openweather import OpenWeatherService
            providers['openweather'] = OpenWeatherService(self.config)
        except ImportError as e:
            self.logger.warning(f"Не удалось загрузить OpenWeather: {e}")
        
        try:
            from .accuweather import AccuWeatherService
            providers['accuweather'] = AccuWeatherService(self.config)
        except ImportError as e:
            self.logger.warning(f"Не удалось загрузить AccuWeather: {e}")
            
        return providers
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Выполнение действия с погодными сервисами"""
        provider_name = kwargs.get('provider', 'openweather')
        
        if provider_name not in self.providers:
            return {
                'success': False,
                'error': f'Провайдер {provider_name} не доступен'
            }
        
        provider = self.providers[provider_name]
        
        try:
            if action == 'current_weather':
                return await provider.get_current_weather(kwargs['city'])
            elif action == 'forecast':
                return await provider.get_forecast(
                    kwargs['city'], 
                    kwargs.get('days', 5)
                )
            else:
                return {
                    'success': False,
                    'error': f'Неизвестное действие: {action}'
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка в {provider_name}.{action}: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': provider_name
            }
    
    def get_available_providers(self) -> list:
        """Получение списка доступных провайдеров"""
        return list(self.providers.keys())

class WeatherIntegration:
    """Класс-обертка для совместимости с существующим кодом"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.service = WeatherServiceIntegration(self.config)
    
    async def initialize(self):
        """Инициализация для совместимости с ModuleManager"""
        return True
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Выполнение действия через WeatherServiceIntegration"""
        return await self.service.execute(action, **kwargs)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Получение возможностей сервиса"""
        return {
            "provider": "weather_integration",
            "available_providers": self.service.get_available_providers(),
            "actions": ["current_weather", "forecast"]
        }