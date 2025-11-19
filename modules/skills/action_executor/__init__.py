# skills/action_executor/__init__.py
"""
Модуль исполнения действий - Action Executor
Отвечает за выполнение системных команд, управление устройствами, файловые операции и логирование действий.
"""

import logging
from typing import Dict, Any, Optional, List

from .command_dispatcher import CommandDispatcher
from .device_controller import DeviceController
from .file_manager import FileManager
from .system_operations import SystemOperations
from .action_logger import ActionLogger

class ActionExecutorModule:
    """Основной класс модуля исполнения действий"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.command_dispatcher = CommandDispatcher()
        self.device_controller = DeviceController()
        self.file_manager = FileManager()
        self.system_operations = SystemOperations()
        self.action_logger = ActionLogger()
        
        self.initialized = False
    
    async def initialize(self):
        """Инициализация модуля"""
        try:
            # Инициализация компонентов (если потребуется асинхронная инициализация)
            await self.command_dispatcher.initialize()
            await self.device_controller.initialize()
            await self.file_manager.initialize()
            await self.system_operations.initialize()
            await self.action_logger.initialize()
            
            self.initialized = True
            self.logger.info("ActionExecutorModule успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации ActionExecutorModule: {e}")
            self.initialized = False
    
    async def execute_command(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Выполнение системной команды
        
        Args:
            command: Команда для выполнения
            parameters: Параметры команды
            
        Returns:
            Dict: Результат выполнения команды
        """
        if not self.initialized:
            self.logger.warning("ActionExecutorModule не инициализирован, но используется")
        
        parameters = parameters or {}
        result = await self.command_dispatcher.dispatch(command, parameters)
        
        # Логируем действие
        await self.action_logger.log_action(
            action_type="command_execution",
            command=command,
            parameters=parameters,
            result=result
        )
        
        return result
    
    async def control_device(self, device_id: str, action: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Управление устройством
        
        Args:
            device_id: Идентификатор устройства
            action: Действие (включить, выключить, etc.)
            parameters: Параметры действия
            
        Returns:
            Dict: Результат управления устройством
        """
        parameters = parameters or {}
        result = await self.device_controller.control(device_id, action, parameters)
        
        await self.action_logger.log_action(
            action_type="device_control",
            device_id=device_id,
            action=action,
            parameters=parameters,
            result=result
        )
        
        return result
    
    async def perform_file_operation(self, operation: str, path: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Выполнение файловой операции
        
        Args:
            operation: Тип операции (create, read, update, delete, etc.)
            path: Путь к файлу/директории
            parameters: Дополнительные параметры
            
        Returns:
            Dict: Результат операции
        """
        parameters = parameters or {}
        result = await self.file_manager.execute_operation(operation, path, parameters)
        
        await self.action_logger.log_action(
            action_type="file_operation",
            operation=operation,
            path=path,
            parameters=parameters,
            result=result
        )
        
        return result
    
    async def perform_system_operation(self, operation: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Выполнение системной операции
        
        Args:
            operation: Тип операции (shutdown, restart, etc.)
            parameters: Параметры операции
            
        Returns:
            Dict: Результат операции
        """
        parameters = parameters or {}
        result = await self.system_operations.execute(operation, parameters)
        
        await self.action_logger.log_action(
            action_type="system_operation",
            operation=operation,
            parameters=parameters,
            result=result
        )
        
        return result
    
    def get_module_info(self) -> Dict[str, Any]:
        """Получение информации о модуле"""
        return {
            "name": "action_executor",
            "version": "1.0",
            "description": "Модуль исполнения системных действий и операций",
            "initialized": self.initialized,
            "components": {
                "command_dispatcher": True,
                "device_controller": True,
                "file_manager": True,
                "system_operations": True,
                "action_logger": True
            }
        }

# Экспортируем основной класс и все остальные
__all__ = [
    'ActionExecutorModule',
    'CommandDispatcher',
    'DeviceController',
    'FileManager',
    'SystemOperations',
    'ActionLogger'
]