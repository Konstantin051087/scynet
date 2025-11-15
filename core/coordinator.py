"""
Главный класс-координатор (мозг системы)
Управляет всем процессом обработки запросов
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time
import uuid

@dataclass
class ProcessingContext:
    """Контекст обработки запроса"""
    request_id: str
    user_input: Any
    input_type: str  # 'text', 'audio', 'image'
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    modules_responses: Dict[str, Any] = None
    final_response: Optional[Any] = None
    processing_time: Optional[float] = None
    security_status: Optional[str] = None
    
    def __post_init__(self):
        if self.modules_responses is None:
            self.modules_responses = {}
        if self.context is None:
            self.context = {}

class Coordinator:
    """Главный координатор системы"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('core.coordinator')
        self.communication_bus = None
        self.intent_analyzer = None
        self.response_synthesizer = None
        self.module_manager = None
        self.security_gateway = None
        self.performance_monitor = None
        
        # Состояние системы
        self.is_running = False
        self.active_requests = {}
        self.system_context = {}
        
        self.logger.info("Координатор инициализирован")

    async def initialize(self):
        """Инициализация всех компонентов координатора"""
        try:
            # Инициализация компонентов
            from .communication_bus import CommunicationBus
            from .intent_analyzer import IntentAnalyzer
            from .response_synthesizer import ResponseSynthesizer
            from .module_manager import ModuleManager
            from .security_gateway import SecurityGateway
            from .performance_monitor import PerformanceMonitor
            
            self.communication_bus = CommunicationBus(self.config.get('communication', {}))
            await self.communication_bus.initialize()
            
            self.security_gateway = SecurityGateway(self.config.get('security', {}))
            await self.security_gateway.initialize()
            
            self.performance_monitor = PerformanceMonitor(self.config.get('performance', {}))
            await self.performance_monitor.initialize()
            
            self.intent_analyzer = IntentAnalyzer(self.config.get('intent_analysis', {}))
            await self.intent_analyzer.initialize()
            
            self.response_synthesizer = ResponseSynthesizer(self.config.get('response_synthesis', {}))
            await self.response_synthesizer.initialize()
            
            self.module_manager = ModuleManager(self.config.get('modules', {}))
            await self.module_manager.initialize()
            
            self.is_running = True
            self.logger.info("Все компоненты координатора успешно инициализированы")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации координатора: {e}")
            raise

    async def process_request(self, user_input: Any, input_type: str = 'text', user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Основной метод обработки запроса
        
        Args:
            user_input: Входные данные пользователя
            input_type: Тип ввода ('text', 'audio', 'image')
            user_context: Контекст пользователя
            
        Returns:
            Dict с результатом обработки
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Создаем контекст обработки
        context = ProcessingContext(
            request_id=request_id,
            user_input=user_input,
            input_type=input_type,
            context=user_context or {}
        )
        
        self.active_requests[request_id] = context
        self.logger.info(f"Начало обработки запроса {request_id}")
        
        try:
            # 1. Проверка безопасности
            security_result = await self.security_gateway.validate_request(context)
            if not security_result['allowed']:
                context.security_status = 'blocked'
                return await self._create_error_response(context, security_result['reason'])
            
            context.security_status = 'approved'
            
            # 2. Анализ намерений
            intent_result = await self.intent_analyzer.analyze(context)
            context.intent = intent_result.get('intent')
            context.entities = intent_result.get('entities', {})
            
            # 3. Маршрутизация к модулям через шину сообщений
            modules_result = await self._route_to_modules(context)
            context.modules_responses = modules_result
            
            # 4. Синтез финального ответа
            final_response = await self.response_synthesizer.synthesize(context)
            context.final_response = final_response
            
            # 5. Запись метрик производительности
            context.processing_time = time.time() - start_time
            await self.performance_monitor.record_request(context)
            
            self.logger.info(f"Запрос {request_id} обработан за {context.processing_time:.2f}с")
            
            return {
                'request_id': request_id,
                'response': final_response,
                'intent': context.intent,
                'processing_time': context.processing_time,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса {request_id}: {e}")
            return await self._create_error_response(context, str(e))
            
        finally:
            # Очистка
            if request_id in self.active_requests:
                del self.active_requests[request_id]

    async def _route_to_modules(self, context: ProcessingContext) -> Dict[str, Any]:
        """Маршрутизация запроса к соответствующим модулям"""
        modules_result = {}
        
        try:
            # Определяем какие модули должны обработать запрос
            target_modules = await self._determine_target_modules(context)
            
            # Отправляем запросы модулям через шину сообщений
            tasks = []
            for module_name in target_modules:
                task = self.communication_bus.send_to_module(
                    module_name=module_name,
                    message_type=f"process_{context.input_type}",
                    data={
                        'input': context.user_input,
                        'intent': context.intent,
                        'entities': context.entities,
                        'context': context.context
                    }
                )
                tasks.append(task)
            
            # Ждем ответы от всех модулей
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Собираем результаты
            for i, module_name in enumerate(target_modules):
                if isinstance(responses[i], Exception):
                    self.logger.error(f"Ошибка модуля {module_name}: {responses[i]}")
                    modules_result[module_name] = {'error': str(responses[i])}
                else:
                    modules_result[module_name] = responses[i]
                    
        except Exception as e:
            self.logger.error(f"Ошибка маршрутизации: {e}")
            
        return modules_result

    async def _determine_target_modules(self, context: ProcessingContext) -> List[str]:
        """Определение целевых модулей для обработки запроса"""
        base_modules = []
        
        # Базовые модули в зависимости от типа ввода
        if context.input_type == 'text':
            base_modules = ['text_understander', 'memory_short_term']
        elif context.input_type == 'audio':
            base_modules = ['speech_recognizer', 'text_understander', 'memory_short_term']
        elif context.input_type == 'image':
            base_modules = ['visual_processor', 'memory_short_term']
        
        # Добавляем модули в зависимости от намерения
        intent_modules = {
            'weather': ['search_agent', 'api_caller'],
            'calculation': ['logic_analyzer'],
            'creative': ['creativity'],
            'planning': ['task_planner', 'goals'],
            'emotional': ['emotional_engine']
        }
        
        if context.intent in intent_modules:
            base_modules.extend(intent_modules[context.intent])
        
        return list(set(base_modules))  # Убираем дубликаты

    async def _create_error_response(self, context: ProcessingContext, error_msg: str) -> Dict[str, Any]:
        """Создание ответа об ошибке"""
        return {
            'request_id': context.request_id,
            'response': {
                'text': f"Извините, произошла ошибка: {error_msg}",
                'type': 'error'
            },
            'processing_time': getattr(context, 'processing_time', 0),
            'status': 'error',
            'error': error_msg
        }

    async def shutdown(self):
        """Корректное завершение работы координатора"""
        self.is_running = False
        
        if self.module_manager:
            await self.module_manager.shutdown()
        if self.communication_bus:
            await self.communication_bus.shutdown()
        if self.performance_monitor:
            await self.performance_monitor.shutdown()
            
        self.logger.info("Координатор завершил работу")

    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            'is_running': self.is_running,
            'active_requests': len(self.active_requests),
            'components': {
                'communication_bus': self.communication_bus is not None,
                'security_gateway': self.security_gateway is not None,
                'performance_monitor': self.performance_monitor is not None,
                'intent_analyzer': self.intent_analyzer is not None,
                'response_synthesizer': self.response_synthesizer is not None,
                'module_manager': self.module_manager is not None
            }
        }
