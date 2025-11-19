#!/usr/bin/env python3
"""
Тестирование базового функционала ядра системы
"""

import asyncio
import sys
import os
import yaml
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication_bus import CommunicationBus
from core.security_gateway import SecurityGateway
from core.performance_monitor import PerformanceMonitor

def create_test_config():
    """Создание тестовой конфигурации"""
    return {
        'system': {
            'name': 'Test System',
            'version': '1.0',
            'environment': 'test'
        },
        'communication': {
            'use_redis': False,
            'redis_host': 'localhost',
            'redis_port': 6379
        },
        'security': {
            'enabled': True,
            'security_level': 'medium'
        },
        'performance': {
            'monitoring': True,
            'metrics_collection': True
        },
        'modules': {
            'enabled': ['coordinator', 'communication_bus', 'security_gateway', 'performance_monitor']
        }
    }

async def test_core_functionality():
    """Тест базового функционала ядра"""
    print("🧪 Тестирование ядра системы...")
    
    # Создаем тестовую конфигурацию
    test_config = create_test_config()
    
    try:
        # Инициализация компонентов с конфигурацией
        bus = CommunicationBus(test_config)
        security = SecurityGateway(test_config.get('security', {}))
        monitor = PerformanceMonitor(test_config)
        
        # Тест шины сообщений
        await bus.initialize()
        print("✅ Шина сообщений работает")
        
        # Тест безопасности - используем validate_request вместо validate_input
        test_data = {"type": "text", "content": "Hello", "timestamp": "2024-01-01"}
        security_check = await security.validate_request(test_data)
        print(f"✅ SecurityGateway: {security_check}")
        
        # Тест мониторинга
        await monitor.initialize()
        print("✅ PerformanceMonitor запущен")
        
        # Проверка здоровья компонентов
        bus_health = await bus.is_healthy()
        security_health = await security.is_healthy()
        monitor_health = await monitor.is_healthy()
        
        print(f"✅ Health checks - Bus: {bus_health}, Security: {security_health}, Monitor: {monitor_health}")
        
        # Корректное завершение
        await bus.shutdown()
        await security.shutdown()
        await monitor.shutdown()
        
        print("🎉 Базовое ядро системы работает корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в ядре системы: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_individual_components():
    """Тестирование отдельных компонентов"""
    print("\n🔍 Детальное тестирование компонентов...")
    
    test_config = create_test_config()
    
    # Тест CommunicationBus
    try:
        bus = CommunicationBus(test_config)
        await bus.initialize()
        print("✅ CommunicationBus - инициализация успешна")
        await bus.shutdown()
        print("✅ CommunicationBus - завершение успешно")
    except Exception as e:
        print(f"❌ CommunicationBus ошибка: {e}")
        return False
    
    # Тест SecurityGateway
    try:
        security = SecurityGateway(test_config.get('security', {}))
        await security.initialize()
        print("✅ SecurityGateway - инициализация успешна")
        
        # Тест валидации - используем validate_request вместо validate_input
        test_cases = [
            {"type": "text", "content": "Hello world", "timestamp": "2024-01-01"},
            {"type": "audio", "content": "audio_data", "timestamp": "2024-01-01"}
        ]
        
        for i, test_case in enumerate(test_cases):
            result = await security.validate_request(test_case)
            print(f"✅ SecurityGateway тест {i+1}: {result}")
        
        await security.shutdown()
        print("✅ SecurityGateway - завершение успешно")
    except Exception as e:
        print(f"❌ SecurityGateway ошибка: {e}")
        return False
    
    # Тест PerformanceMonitor
    try:
        monitor = PerformanceMonitor(test_config)
        await monitor.initialize()
        print("✅ PerformanceMonitor - инициализация успешна")
        
        # Тест сбора метрик
        metrics = await monitor.collect_metrics()
        print(f"✅ PerformanceMonitor метрики: {len(metrics)} collected")
        
        await monitor.shutdown()
        print("✅ PerformanceMonitor - завершение успешно")
    except Exception as e:
        print(f"❌ PerformanceMonitor ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск тестов ядра системы...")
    
    # Запуск основного теста
    success1 = asyncio.run(test_core_functionality())
    
    # Запуск детального тестирования
    success2 = asyncio.run(test_individual_components())
    
    if success1 and success2:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("\n💥 НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        sys.exit(1)