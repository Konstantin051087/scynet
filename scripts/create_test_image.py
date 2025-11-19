# scripts/create_test_image.py
"""
Скрипт для создания тестового изображения
"""

import cv2
import numpy as np
import os
from pathlib import Path

def create_test_image(output_path: str = "test_data/test_images/test_image.jpg"):
    """Создание тестового изображения с различными объектами"""
    
    # Создаем директорию если не существует
    os.makedirs(Path(output_path).parent, exist_ok=True)
    
    # Создаем изображение 800x600
    image = np.ones((600, 800, 3), dtype=np.uint8) * 255  # Белый фон
    
    # Добавляем различные объекты для тестирования
    
    # 1. Красный автомобиль
    cv2.rectangle(image, (100, 300), (300, 400), (0, 0, 255), -1)
    cv2.rectangle(image, (150, 250), (250, 300), (0, 0, 255), -1)
    
    # 2. Зеленое дерево
    cv2.rectangle(image, (500, 350), (520, 450), (0, 100, 0), -1)
    cv2.circle(image, (510, 300), 60, (0, 150, 0), -1)
    
    # 3. Синий стул
    pts = np.array([[400, 400], [350, 500], [450, 500]], np.int32)
    cv2.fillPoly(image, [pts], (255, 0, 0))
    
    # 4. Желтое солнце
    cv2.circle(image, (700, 100), 40, (0, 255, 255), -1)
    
    # 5. Простое лицо (упрощенное)
    cv2.circle(image, (200, 150), 50, (200, 200, 200), -1)  # Голова
    cv2.circle(image, (180, 140), 10, (0, 0, 0), -1)  # Левый глаз
    cv2.circle(image, (220, 140), 10, (0, 0, 0), -1)  # Правый глаз
    cv2.ellipse(image, (200, 170), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Рот
    
    # Сохраняем изображение
    cv2.imwrite(output_path, image)
    print(f"Тестовое изображение создано: {output_path}")
    
    return output_path

if __name__ == "__main__":
    create_test_image()