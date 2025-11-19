#!/usr/bin/env python3
"""
Скрипт для включения и диагностики module_manager
"""

import logging
import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

async def enable_module_manager():
    """Включение module_manager"""
    
    # Создаем необходимые директории
    Path('config/modules').mkdir(parents=True, exist_ok=True)
    Path('logs/system').mkdir(parents=True, exist_ok=True)
    
    # Настраиваем логгирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/system/module_manager_activation.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('module_manager_enabler')
    
    try:
        logger.info("🎯 Начало активации module_manager...")
        
        # 1. Создаем конфигурационный файл module_manager.yaml
        config_content = """module:
  name: "module_manager"
  enabled: true
  category: "core"
  dependencies: []
  initialization_priority: 1
  config:
    auto_reload: false
    dependency_check: true
    health_check_interval: 30
    log_level: "INFO"

logging:
  enabled: true
  log_file: "logs/system/module_manager.log"
  max_file_size: 10485760
  backup_count: 5

performance:
  track_loading_times: true
  monitor_memory_usage: true
"""
        
        config_path = Path('config/modules/module_manager.yaml')
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        logger.info(f"✅ Конфигурационный файл создан: {config_path}")
        
        # 2. Проверяем наличие module_manager в system.yaml
        system_config_path = Path('config/system.yaml')
        if system_config_path.exists():
            with open(system_config_path, 'r', encoding='utf-8') as f:
                system_config = f.read()
            
            if 'module_manager' in system_config:
                logger.info("✅ module_manager присутствует в system.yaml")
            else:
                logger.warning("⚠️ module_manager не найден в system.yaml - требуется ручная проверка")
        else:
            logger.error("❌ Файл system.yaml не найден")
        
        # 3. Проверяем наличие исправленного module_manager.py
        module_manager_path = Path('core/module_manager.py')
        if module_manager_path.exists():
            with open(module_manager_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем ключевые исправления
            checks = [
                'module_manager' in content,  # Упоминание самого себя
                'loaded_modules[' in content,  # Регистрация модулей
                'initialize' in content,       # Метод инициализации
            ]
            
            if all(checks):
                logger.info("✅ Исправленный module_manager.py обнаружен")
            else:
                logger.warning("⚠️ module_manager.py может требовать дополнительных исправлений")
        else:
            logger.error("❌ Файл module_manager.py не найден")
        
        # 4. Создаем тестовый скрипт для проверки реального состояния
        test_script = """#!/usr/bin/env python3
\"\"\"
Тестирование реального состояния module_manager
\"\"\"

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_real_module_manager():
    \"\"\"Тестирование реального состояния module_manager\"\"\"
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
"""
        
        test_script_path = Path('scripts/test_real_module_manager.py')
        with open(test_script_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        logger.info(f"✅ Тестовый скрипт создан: {test_script_path}")
        
        logger.info("🎉 Активация module_manager завершена!")
        logger.info("📋 Дальнейшие действия:")
        logger.info("   1. Запустите: python scripts/test_real_module_manager.py")
        logger.info("   2. Проверьте логи: logs/system/module_manager_activation.log")
        logger.info("   3. Запустите основную систему: python main.py")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при активации module_manager: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(enable_module_manager())
    sys.exit(0 if success else 1)