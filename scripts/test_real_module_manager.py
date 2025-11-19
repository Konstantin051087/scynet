#!/usr/bin/env python3
"""
Тестирование реального состояния module_manager
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_real_module_manager():
    """Тестирование реального состояния module_manager"""
    from core.module_manager import ModuleManager
    
    print("🧪 Тестирование реального состояния module_manager...")
    
    # Конфигурация как в system.yaml
    config = {
        'enabled': ['module_manager', 'text_understander', 'memory_short_term'],
        'modules': {
            'module_manager': {
                'enabled': True,
                'category': 'core'
            }
        }
    }
    
    try:
        # Создаем и инициализируем менеджер модулей
        manager = ModuleManager(config)
        await manager.initialize()
        
        print("✅ ModuleManager успешно инициализирован")
        
        # Получаем реальный статус
        stats = await manager.get_manager_stats()
        print(f"📊 Статистика менеджера: {stats}")
        
        # Получаем статус самого module_manager
        module_status = await manager.get_module_status('module_manager')
        print(f"📈 Статус module_manager: {module_status}")
        
        # Проверяем, что module_manager в списке загруженных
        loaded_modules = stats['available_modules']
        if 'module_manager' in loaded_modules:
            print("✅ module_manager в списке загруженных модулей")
        else:
            print("❌ module_manager НЕ в списке загруженных модулей")
        
        # Проверяем состояние
        if module_status.get('status') == 'initialized':
            print("✅ module_manager в состоянии 'initialized'")
        else:
            print(f"❌ module_manager в состоянии: {module_status.get('status')}")
        
        await manager.shutdown()
        print("✅ ModuleManager корректно завершил работу")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_module_manager())
    sys.exit(0 if success else 1)