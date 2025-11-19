# minimal_example.py
"""
Минимальный пример использования visual_processor
"""

import asyncio
import yaml

async def minimal_example():
    """Минимальный пример работы с visual_processor"""
    
    # 1. Загружаем конфигурацию
    with open('config/system.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # 2. Создаем координатор
    from core.coordinator import Coordinator
    coordinator = Coordinator(config)
    await coordinator.initialize()
    
    # 3. Обрабатываем изображение
    result = await coordinator.process_request(
        user_input="/home/konstanin/GitHub/scynet/test_data/test_images/test_images.jpg",
        input_type="image"
    )
    
    # 4. Работаем с результатом
    if result['status'] == 'success':
        print("✅ Изображение успешно обработано!")
        print(f"📊 Результаты: {result['response']}")
    else:
        print(f"❌ Ошибка: {result.get('error')}")
    
    # 5. Завершаем работу
    await coordinator.shutdown()

# Запуск
if __name__ == "__main__":
    asyncio.run(minimal_example())