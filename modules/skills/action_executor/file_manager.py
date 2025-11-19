"""
Менеджер файловых операций - создание, чтение, запись, удаление файлов
"""

import os
import shutil
import logging
from typing import Dict, Any, List
from pathlib import Path

class FileManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Инициализация менеджера файлов"""
        self.logger.info("FileManager инициализирован")
    
    async def execute_operation(self, operation: str, path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение файловой операции
        
        Args:
            operation: Тип операции
            path: Путь к файлу/директории
            parameters: Параметры операции
            
        Returns:
            Dict: Результат операции
        """
        try:
            path_obj = Path(path)
            
            if operation == 'create_file':
                return await self._create_file(path_obj, parameters)
            elif operation == 'read_file':
                return await self._read_file(path_obj, parameters)
            elif operation == 'write_file':
                return await self._write_file(path_obj, parameters)
            elif operation == 'delete_file':
                return await self._delete_file(path_obj, parameters)
            elif operation == 'create_directory':
                return await self._create_directory(path_obj, parameters)
            elif operation == 'list_directory':
                return await self._list_directory(path_obj, parameters)
            else:
                return {
                    "status": "error",
                    "operation": operation,
                    "error": f"Операция '{operation}' не поддерживается"
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения операции {operation}: {e}")
            return {
                "status": "error",
                "operation": operation,
                "error": str(e)
            }
    
    async def _create_file(self, path: Path, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Создание файла"""
        try:
            path.touch(exist_ok=parameters.get('exist_ok', True))
            return {
                "status": "success",
                "operation": "create_file",
                "path": str(path),
                "message": "Файл создан успешно"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _read_file(self, path: Path, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение файла"""
        try:
            if not path.exists():
                return {"status": "error", "error": "Файл не существует"}
            
            encoding = parameters.get('encoding', 'utf-8')
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                "status": "success",
                "operation": "read_file",
                "path": str(path),
                "content": content
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _write_file(self, path: Path, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Запись в файл"""
        try:
            content = parameters.get('content', '')
            mode = 'w' if parameters.get('overwrite', True) else 'a'
            encoding = parameters.get('encoding', 'utf-8')
            
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            return {
                "status": "success",
                "operation": "write_file",
                "path": str(path),
                "message": "Файл записан успешно"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _delete_file(self, path: Path, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Удаление файла"""
        try:
            if not path.exists():
                return {"status": "error", "error": "Файл не существует"}
            
            path.unlink()
            return {
                "status": "success",
                "operation": "delete_file",
                "path": str(path),
                "message": "Файл удален успешно"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _create_directory(self, path: Path, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Создание директории"""
        try:
            path.mkdir(parents=parameters.get('parents', True), exist_ok=True)
            return {
                "status": "success",
                "operation": "create_directory",
                "path": str(path),
                "message": "Директория создана успешно"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _list_directory(self, path: Path, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Список содержимого директории"""
        try:
            if not path.exists():
                return {"status": "error", "error": "Директория не существует"}
            
            items = []
            for item in path.iterdir():
                items.append({
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else 0
                })
            
            return {
                "status": "success",
                "operation": "list_directory",
                "path": str(path),
                "items": items
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}