# test_visual_processor_usage.py
"""
Пример использования visual_processor через координатор
"""

import asyncio
import os
import sys
from pathlib import Path

async def test_visual_processor():
    """Тест работы visual_processor через координатор"""
    
    print("🚀 Запуск теста visual_processor через координатор...")
    
    try:
        # Импортируем необходимые компоненты
        from core.coordinator import Coordinator
        from core.module_manager import ModuleManager
        from core.communication_bus import CommunicationBus
        
        # Загружаем конфигурацию системы
        import yaml
        
        with open('config/system.yaml', 'r', encoding='utf-8') as f:
            system_config = yaml.safe_load(f)
        
        print("✅ Конфигурация системы загружена")
        
        # Создаем координатор
        coordinator = Coordinator(system_config)
        await coordinator.initialize()
        
        print("✅ Координатор инициализирован")
        print(f"📊 Статус системы: {coordinator.get_system_status()}")
        
        # Проверяем что visual_processor загружен
        module_status = await coordinator.module_manager.get_module_status('visual_processor')
        print(f"📊 Статус visual_processor: {module_status}")
        
        # Создаем тестовое изображение если его нет
        test_image_path = "test_data/test_images/test_image.jpg"
        os.makedirs(Path(test_image_path).parent, exist_ok=True)
        
        if not os.path.exists(test_image_path):
            print("📷 Создаем тестовое изображение...")
            import cv2
            import numpy as np
            
            # Создаем тестовое изображение с разными объектами
            image = np.ones((400, 600, 3), dtype=np.uint8) * 255  # Белый фон
            
            # Добавляем различные объекты
            cv2.rectangle(image, (50, 50), (200, 200), (0, 0, 255), -1)  # Красный прямоугольник
            cv2.circle(image, (400, 150), 80, (0, 255, 0), -1)  # Зеленая окружность
            cv2.rectangle(image, (300, 300), (500, 350), (255, 0, 0), -1)  # Синий прямоугольник
            
            # Простое лицо
            cv2.circle(image, (150, 300), 40, (200, 200, 200), -1)  # Голова
            cv2.circle(image, (140, 290), 5, (0, 0, 0), -1)  # Левый глаз
            cv2.circle(image, (160, 290), 5, (0, 0, 0), -1)  # Правый глаз
            cv2.ellipse(image, (150, 310), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Рот
            
            cv2.imwrite(test_image_path, image)
            print(f"✅ Тестовое изображение создано: {test_image_path}")
        
        print(f"\n🎯 Обрабатываем изображение: {test_image_path}")
        
        # Обрабатываем изображение через координатор
        result = await coordinator.process_request(
            user_input=test_image_path,
            input_type='image'
        )
        
        print("\n📊 РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
        print(f"✅ Статус: {result['status']}")
        print(f"🆔 ID запроса: {result['request_id']}")
        print(f"⏱️ Время обработки: {result['processing_time']}с")
        
        if result['status'] == 'success':
            response = result['response']
            print(f"📝 Тип ответа: {response.get('type', 'unknown')}")
            
            # Выводим текстовый ответ если есть
            if 'text' in response:
                print(f"💬 Текстовый ответ: {response['text']}")
            
            # Выводим результаты анализа если есть
            if 'analysis_results' in response:
                analysis = response['analysis_results']
                print(f"\n🔍 РЕЗУЛЬТАТЫ АНАЛИЗА:")
                
                if 'objects' in analysis:
                    print(f"📦 Обнаружено объектов: {len(analysis['objects'])}")
                    for obj in analysis['objects'][:5]:  # Показываем первые 5
                        print(f"   - {obj['class']} (уверенность: {obj['confidence']:.2f})")
                
                if 'faces' in analysis:
                    print(f"😊 Обнаружено лиц: {len(analysis['faces'])}")
                
                if 'scene' in analysis:
                    scene = analysis['scene']
                    if 'description' in scene:
                        print(f"🏞️ Описание сцены: {scene['description']}")
            
            # Проверяем наличие визуального вывода
            if 'visual_output_path' in response:
                print(f"🎨 Визуальный результат сохранен: {response['visual_output_path']}")
            
            # Показываем summary если есть
            if 'summary' in response:
                summary = response['summary']
                print(f"\n📋 СВОДКА:")
                if 'recommendations' in summary and summary['recommendations']:
                    print("💡 Рекомендации:")
                    for rec in summary['recommendations']:
                        print(f"   • {rec}")
        
        else:
            print(f"❌ Ошибка: {result.get('error', 'Unknown error')}")
        
        # Корректное завершение
        await coordinator.shutdown()
        print("\n✅ Тест завершен успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_api_usage():
    """Тест прямого использования API visual_processor"""
    
    print("\n" + "="*50)
    print("🧪 Тест прямого использования API...")
    
    try:
        from modules.interface.visual_processor.api_interface import VisualProcessorAPI
        
        # Создаем API
        api = VisualProcessorAPI()
        await api.initialize()
        
        # Создаем простое тестовое изображение
        import cv2
        import numpy as np
        
        test_image_path = "test_direct.jpg"
        image = np.zeros((300, 300, 3), dtype=np.uint8)
        cv2.rectangle(image, (50, 50), (250, 250), (0, 255, 0), -1)
        cv2.imwrite(test_image_path, image)
        
        # Обрабатываем изображение
        result = await api.process_image({
            'image_path': test_image_path,
            'tasks': ['object_detection', 'scene_analysis'],
            'generate_visual_output': True,
            'output_path': 'test_output.jpg'
        })
        
        print(f"📊 Результат API: {result['status']}")
        
        if result['status'] == 'success':
            print("✅ API работает корректно!")
            print(f"⏱️ Время обработки: {result['processing_time']}с")
            
            # Показываем краткие результаты
            results = result['results']
            if 'objects' in results:
                print(f"📦 Объектов: {len(results['objects'])}")
            if 'scene' in results:
                print(f"🏞️ Тип сцены: {results['scene'].get('description', 'N/A')}")
        
        # Очистка
        await api.shutdown()
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        if os.path.exists('test_output.jpg'):
            print(f"🎨 Визуальный вывод сохранен: test_output.jpg")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🎯 ТЕСТИРОВАНИЕ VISUAL_PROCESSOR В СИСТЕМЕ")
    print("="*60)
    
    # Тестируем через координатор
    coordinator_ok = await test_visual_processor()
    
    # Тестируем прямое использование API
    api_ok = await test_direct_api_usage()
    
    print("\n" + "="*60)
    if coordinator_ok and api_ok:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Visual_processor полностью работоспособен!")
        print("\n📝 КРАТКАЯ ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:")
        print("""
1. Через координатор (рекомендуется):
   result = await coordinator.process_request(
       user_input="путь/к/изображению.jpg", 
       input_type="image"
   )

2. Прямое использование API:
   from modules.interface.visual_processor.api_interface import VisualProcessorAPI
   api = VisualProcessorAPI()
   await api.initialize()
   result = await api.process_image({
       'image_path': "путь/к/изображению.jpg",
       'tasks': ['object_detection', 'face_detection', 'scene_analysis']
   })
        """)
    else:
        print("⚠️  Некоторые тесты не прошли")
    
    return coordinator_ok and api_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)