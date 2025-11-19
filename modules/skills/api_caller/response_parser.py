"""
Парсер ответов API - преобразование ответов в стандартный формат
"""

import json
import logging
from typing import Dict, Any, Optional
import aiohttp

class ResponseParser:
    """Парсинг и нормализация ответов от различных API"""
    
    def __init__(self):
        self.logger = logging.getLogger('response_parser')
        self.parsers = {
            'json': self._parse_json,
            'xml': self._parse_xml,
            'text': self._parse_text
        }
    
    async def parse_response(self, response: aiohttp.ClientResponse, service: str) -> Dict[str, Any]:
        """Основной метод парсинга ответа"""
        try:
            # Определяем тип контента
            content_type = response.headers.get('content-type', '').lower()
            
            # Выбираем парсер в зависимости от типа контента
            if 'application/json' in content_type:
                parser = self.parsers['json']
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                parser = self.parsers['xml']
            else:
                parser = self.parsers['text']
            
            # Парсим ответ
            parsed_data = await parser(response)
            
            # Добавляем метаданные
            result = {
                'data': parsed_data,
                'status_code': response.status,
                'headers': dict(response.headers),
                'service': service,
                'success': 200 <= response.status < 300
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга ответа от {service}: {e}")
            return {
                'data': None,
                'status_code': response.status,
                'error': str(e),
                'service': service,
                'success': False
            }
    
    async def _parse_json(self, response: aiohttp.ClientResponse) -> Any:
        """Парсинг JSON ответа"""
        try:
            return await response.json()
        except json.JSONDecodeError as e:
            text = await response.text()
            self.logger.warning(f"Невалидный JSON, возвращаем текст: {e}")
            return {'raw_text': text}
    
    async def _parse_xml(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Парсинг XML ответа (упрощенный)"""
        try:
            text = await response.text()
            # Здесь можно добавить полноценный XML парсер like xml.etree.ElementTree
            return {'raw_xml': text}
        except Exception as e:
            self.logger.error(f"Ошибка парсинга XML: {e}")
            return {'error': str(e)}
    
    async def _parse_text(self, response: aiohttp.ClientResponse) -> str:
        """Парсинг текстового ответа"""
        return await response.text()
    
    def normalize_weather_data(self, raw_data: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Нормализация данных о погоде от разных провайдеров"""
        normalizers = {
            'openweather': self._normalize_openweather,
            'accuweather': self._normalize_accuweather
        }
        
        if provider in normalizers:
            return normalizers[provider](raw_data)
        else:
            self.logger.warning(f"Нормализатор для {provider} не найден")
            return raw_data
    
    def _normalize_openweather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализация данных OpenWeather"""
        return {
            'temperature': data.get('main', {}).get('temp'),
            'feels_like': data.get('main', {}).get('feels_like'),
            'humidity': data.get('main', {}).get('humidity'),
            'pressure': data.get('main', {}).get('pressure'),
            'wind_speed': data.get('wind', {}).get('speed'),
            'description': data.get('weather', [{}])[0].get('description'),
            'city': data.get('name'),
            'provider': 'openweather'
        }
    
    def _normalize_accuweather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализация данных AccuWeather"""
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        
        return {
            'temperature': data.get('Temperature', {}).get('Metric', {}).get('Value'),
            'weather_text': data.get('WeatherText'),
            'humidity': data.get('RelativeHumidity'),
            'pressure': data.get('Pressure', {}).get('Metric', {}).get('Value'),
            'wind_speed': data.get('Wind', {}).get('Speed', {}).get('Metric', {}).get('Value'),
            'provider': 'accuweather'
        }