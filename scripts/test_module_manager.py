#!/usr/bin/env python3
"""
Тестовый скрипт для проверки module_manager
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.module_manager import ModuleManager

async def test_module_manager():
    """Тестирование module_manager"""
    config = {
        'enabled': ['module_manager'],
        'modules': {}
    }
    
    manager = ModuleManager(config)
    
    try:
        await manager.initialize()
        print("✅ ModuleManager успешно инициализирован")
        
        stats = await manager.get_manager_stats()
        print(f"📊 Статистика: {stats}")
        
        status = await manager.get_module_status('module_manager')
        print(f"📈 Статус module_manager: {status}")
        
        await manager.shutdown()
        print("✅ ModuleManager корректно завершил работу")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_module_manager())
    sys.exit(0 if success else 1)
