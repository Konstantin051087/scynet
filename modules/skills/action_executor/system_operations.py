"""
Системные операции - управление системными ресурсами и процессами
"""

import os
import psutil
import logging
from typing import Dict, Any

class SystemOperations:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация системных операций"""
        self.logger.info("SystemOperations инициализирован")
    
    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение системной операции
        
        Args:
            operation: Тип операции
            parameters: Параметры операции
            
        Returns:
            Dict: Результат операции
        """
        try:
            if operation == 'get_system_info':
                return await self._get_system_info()
            elif operation == 'get_memory_usage':
                return await self._get_memory_usage()
            elif operation == 'get_cpu_usage':
                return await self._get_cpu_usage()
            elif operation == 'get_disk_usage':
                return await self._get_disk_usage()
            else:
                return {
                    "status": "error",
                    "operation": operation,
                    "error": f"Операция '{operation}' не поддерживается"
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения системной операции {operation}: {e}")
            return {
                "status": "error",
                "operation": operation,
                "error": str(e)
            }
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Получение информации о системе"""
        try:
            return {
                "status": "success",
                "operation": "get_system_info",
                "system": os.name,
                "platform": os.uname().sysname if hasattr(os, 'uname') else 'Unknown',
                "release": os.uname().release if hasattr(os, 'uname') else 'Unknown',
                "version": os.uname().version if hasattr(os, 'uname') else 'Unknown',
                "machine": os.uname().machine if hasattr(os, 'uname') else 'Unknown'
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_memory_usage(self) -> Dict[str, Any]:
        """Получение информации об использовании памяти"""
        try:
            memory = psutil.virtual_memory()
            return {
                "status": "success",
                "operation": "get_memory_usage",
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_cpu_usage(self) -> Dict[str, Any]:
        """Получение информации об использовании CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            return {
                "status": "success",
                "operation": "get_cpu_usage",
                "percent": cpu_percent,
                "count": cpu_count
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_disk_usage(self) -> Dict[str, Any]:
        """Получение информации об использовании диска"""
        try:
            disk = psutil.disk_usage('/')
            return {
                "status": "success",
                "operation": "get_disk_usage",
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}