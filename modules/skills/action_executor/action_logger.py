"""
Логгер действий - запись всех выполненных действий для аудита и отладки
"""

import logging
import json
import datetime
from typing import Dict, Any, List
from pathlib import Path

class ActionLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.log_file = Path("logs/modules/skills/action_executor.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Инициализация логгера действий"""
        self.logger.info("ActionLogger инициализирован")
    
    async def log_action(self, action_type: str, **kwargs):
        """
        Логирование действия
        
        Args:
            action_type: Тип действия
            **kwargs: Дополнительные параметры для логирования
        """
        try:
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "action_type": action_type,
                **kwargs
            }
            
            # Запись в файл
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            # Также логируем в системный лог
            self.logger.info(f"Действие записано: {action_type}")
            
        except Exception as e:
            self.logger.error(f"Ошибка записи действия в лог: {e}")
    
    async def get_action_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение последних записей лога
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            List: Список записей лога
        """
        try:
            if not self.log_file.exists():
                return []
            
            logs = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            return logs[-limit:]
            
        except Exception as e:
            self.logger.error(f"Ошибка чтения логов: {e}")
            return []