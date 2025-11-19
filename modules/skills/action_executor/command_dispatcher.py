"""
Диспетчер команд - обработка и выполнение системных команд
"""

import logging
import asyncio
import subprocess
from typing import Dict, Any, List

class CommandDispatcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_commands = {
            'system_info': ['uname', '-a'],
            'disk_usage': ['df', '-h'],
            'memory_usage': ['free', '-h'],
            'list_processes': ['ps', 'aux'],
            'network_info': ['ifconfig']
        }
    
    async def initialize(self):
        """Инициализация диспетчера команд"""
        self.logger.info("CommandDispatcher инициализирован")
    
    async def dispatch(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение команды
        
        Args:
            command: Команда для выполнения
            parameters: Параметры команды
            
        Returns:
            Dict: Результат выполнения
        """
        try:
            if command in self.supported_commands:
                # Выполнение системной команды
                cmd_args = self.supported_commands[command]
                process = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                return {
                    "status": "success",
                    "command": command,
                    "exit_code": process.returncode,
                    "stdout": stdout.decode('utf-8') if stdout else "",
                    "stderr": stderr.decode('utf-8') if stderr else ""
                }
            else:
                return {
                    "status": "error",
                    "command": command,
                    "error": f"Команда '{command}' не поддерживается"
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения команды {command}: {e}")
            return {
                "status": "error",
                "command": command,
                "error": str(e)
            }
    
    def get_supported_commands(self) -> List[str]:
        """Получение списка поддерживаемых команд"""
        return list(self.supported_commands.keys())