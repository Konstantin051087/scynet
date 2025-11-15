"""
Синтезатор финального ответа
Объединяет результаты от модулей в единый согласованный ответ
"""

import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

class ResponseSynthesizer:
    """Синтезатор финального ответа системы"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('core.response_synthesizer')
        
        # Шаблоны ответов
        self.response_templates = {}
        
        # Стиль ответа
        self.response_style = config.get('style', 'neutral')
        
        self.is_initialized = False

    async def initialize(self):
        """Инициализация синтезатора ответов"""
        try:
            await self._load_templates()
            self.is_initialized = True
            self.logger.info("Синтезатор ответов инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации синтезатора ответов: {e}")
            raise

    async def synthesize(self, context) -> Dict[str, Any]:
        """
        Синтез финального ответа на основе результатов модулей
        
        Args:
            context: Контекст обработки запроса
            
        Returns:
            Синтезированный ответ
        """
        if not self.is_initialized:
            raise RuntimeError("Синтезатор ответов не инициализирован")
        
        self.logger.debug(f"Синтез ответа для намерения: {context.intent}")
        
        try:
            # Определяем тип ответа на основе намерения
            response_type = await self._determine_response_type(context)
            
            # Собираем данные от модулей
            response_data = await self._collect_module_data(context)
            
            # Создаем базовую структуру ответа
            base_response = {
                'timestamp': datetime.now().isoformat(),
                'request_id': context.request_id,
                'type': response_type,
                'intent': context.intent
            }
            
            # Генерируем контент ответа
            if response_type == 'text':
                content = await self._generate_text_response(context, response_data)
                base_response['text'] = content
                
            elif response_type == 'multimodal':
                content = await self._generate_multimodal_response(context, response_data)
                base_response.update(content)
                
            elif response_type == 'action':
                content = await self._generate_action_response(context, response_data)
                base_response.update(content)
                
            elif response_type == 'error':
                content = await self._generate_error_response(context)
                base_response.update(content)
            
            # Добавляем контекст если нужно
            if self.config.get('include_context', False):
                base_response['context'] = await self._prepare_context_data(context)
            
            self.logger.info(f"Синтезирован ответ типа: {response_type}")
            return base_response
            
        except Exception as e:
            self.logger.error(f"Ошибка синтеза ответа: {e}")
            return await self._generate_error_response(context, str(e))

    async def _determine_response_type(self, context) -> str:
        """Определение типа ответа на основе намерения и данных модулей"""
        intent = context.intent
        
        # Проверяем есть ли визуальные данные
        has_visual = any('image' in str(key).lower() or 'visual' in str(key).lower() 
                        for key in context.modules_responses.keys())
        
        # Проверяем есть ли действия
        has_actions = any('action' in str(key).lower() or 'executor' in str(key).lower()
                         for key in context.modules_responses.keys())
        
        if has_visual:
            return 'multimodal'
        elif has_actions:
            return 'action'
        elif intent in ['creative', 'story']:
            return 'text'  # Для креативных ответов - расширенный текст
        else:
            return 'text'

    async def _generate_text_response(self, context, module_data: Dict[str, Any]) -> str:
        """Генерация текстового ответа"""
        intent = context.intent
        
        # Используем шаблоны для стандартных намерений
        if intent in self.response_templates:
            template = self.response_templates[intent]
            return await self._fill_template(template, context, module_data)
        
        # Для неизвестных намерений пытаемся извлечь текст из модулей
        for module_name, data in module_data.items():
            if isinstance(data, dict) and 'text' in data:
                return data['text']
            elif isinstance(data, str):
                return data
        
        # Фолбэк ответ
        return "Я обработал ваш запрос, но не нашел подходящего ответа."

    async def _generate_multimodal_response(self, context, module_data: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация мультимодального ответа"""
        response = {'text': '', 'visual': None, 'audio': None}
        
        # Собираем текстовую часть
        response['text'] = await self._generate_text_response(context, module_data)
        
        # Ищем визуальные данные
        for module_name, data in module_data.items():
            if module_name == 'visual_processor' and isinstance(data, dict):
                if 'image' in data or 'visual' in data:
                    response['visual'] = data.get('image') or data.get('visual')
        
        return response

    async def _generate_action_response(self, context, module_data: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация ответа с действиями"""
        response = {
            'text': await self._generate_text_response(context, module_data),
            'actions': []
        }
        
        # Собираем действия от модулей
        for module_name, data in module_data.items():
            if isinstance(data, dict) and 'actions' in data:
                response['actions'].extend(data['actions'])
        
        return response

    async def _generate_error_response(self, context, error_msg: str = None) -> Dict[str, Any]:
        """Генерация ответа об ошибке"""
        error_msg = error_msg or "Произошла неизвестная ошибка"
        
        return {
            'text': f"Извините, возникла проблема: {error_msg}",
            'type': 'error',
            'error': error_msg
        }

    async def _collect_module_data(self, context) -> Dict[str, Any]:
        """Сбор и объединение данных от модулей"""
        combined_data = {}
        
        for module_name, response in context.modules_responses.items():
            if isinstance(response, dict):
                # Обрабатываем ответы с ошибками
                if 'error' in response:
                    self.logger.warning(f"Модуль {module_name} вернул ошибку: {response['error']}")
                    combined_data[f"{module_name}_error"] = response['error']
                else:
                    combined_data.update(response)
            else:
                combined_data[module_name] = response
        
        return combined_data

    async def _fill_template(self, template: str, context, module_data: Dict[str, Any]) -> str:
        """Заполнение шаблона ответа данными"""
        try:
            # Простая замена плейсхолдеров
            filled_template = template
            
            # Замена сущностей
            if context.entities:
                for entity_type, entities in context.entities.items():
                    if entities:
                        placeholder = f'{{{entity_type}}}'
                        if placeholder in filled_template:
                            filled_template = filled_template.replace(placeholder, entities[0])
            
            # Замена данных модулей
            for key, value in module_data.items():
                if isinstance(value, str):
                    placeholder = f'{{{key}}}'
                    if placeholder in filled_template:
                        filled_template = filled_template.replace(placeholder, value)
            
            return filled_template
            
        except Exception as e:
            self.logger.error(f"Ошибка заполнения шаблона: {e}")
            return template  # Возвращаем оригинальный шаблон при ошибке

    async def _prepare_context_data(self, context) -> Dict[str, Any]:
        """Подготовка контекстных данных для ответа"""
        return {
            'intent': context.intent,
            'entities': context.entities,
            'processing_time': getattr(context, 'processing_time', None),
            'modules_used': list(context.modules_responses.keys())
        }

    async def _load_templates(self):
        """Загрузка шаблонов ответов"""
        self.response_templates = {
            'greeting': [
                "Привет! Рад вас видеть. Чем могу помочь?",
                "Здравствуйте! Я к вашим услугам.",
                "Приветствую! Как ваши дела?"
            ],
            'weather': "Погода в {location}: {weather_description}. Температура: {temperature}°C.",
            'calculation': "Результат вычисления {expression}: {result}",
            'time': "Сейчас {current_time}",
            'search': "Вот что я нашел по вашему запросу: {search_results}",
            'creative': "{creative_content}",
            'goodbye': [
                "До свидания! Буду рад помочь снова.",
                "Пока! Хорошего дня!",
                "Всего наилучшего! Возвращайтесь с новыми вопросами."
            ],
            'unknown': "Извините, я не совсем понял ваш вопрос. Можете переформулировать?"
        }
        
        self.logger.debug("Шаблоны ответов загружены")

    async def update_templates(self, new_templates: Dict[str, Any]):
        """Обновление шаблонов ответов"""
        self.response_templates.update(new_templates)
        self.logger.info("Шаблоны ответов обновлены")

    async def set_response_style(self, style: str):
        """Установка стиля ответов"""
        allowed_styles = ['neutral', 'formal', 'friendly', 'professional']
        if style in allowed_styles:
            self.response_style = style
            self.logger.info(f"Стиль ответов изменен на: {style}")
        else:
            self.logger.warning(f"Недопустимый стиль: {style}")

    async def get_synthesis_stats(self) -> Dict[str, Any]:
        """Получение статистики синтезатора"""
        return {
            'templates_count': len(self.response_templates),
            'response_style': self.response_style,
            'is_initialized': self.is_initialized
        }