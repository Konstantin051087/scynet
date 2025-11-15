"""
МОДУЛЬ РАСПОЗНАВАНИЯ ОБЪЕКТОВ НА ИЗОБРАЖЕНИЯХ
"""

import cv2
import numpy as np
import torch
from PIL import Image
import os
import json
from typing import List, Dict, Any

class ImageRecognizer:
    """Класс для распознавания объектов на изображениях"""
    
    def __init__(self, model_name="yolov5s"):
        self.model_name = model_name
        self.model = None
        self.classes = None
        self.is_initialized = False
        
        # Минимальная уверенность для детекции
        self.confidence_threshold = 0.5
        self.iou_threshold = 0.45
        
    def initialize(self):
        """Инициализация модели распознавания"""
        try:
            # Загрузка YOLOv5 (можно заменить на другие модели)
            self.model = torch.hub.load('ultralytics/yolov5', 
                                      self.model_name, 
                                      pretrained=True)
            
            # Установка параметров
            self.model.conf = self.confidence_threshold
            self.model.iou = self.iou_threshold
            
            # Классы COCO
            self.classes = self.model.names
            
            self.is_initialized = True
            print(f"Модель распознавания изображений {self.model_name} загружена")
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            # Fallback на OpenCV DNN
            return self._initialize_opencv()
    
    def _initialize_opencv(self):
        """Инициализация OpenCV DNN как fallback"""
        try:
            # Загрузка модели OpenCV DNN
            net = cv2.dnn.readNetFromDarknet(
                'config/yolov3.cfg', 
                'models/yolov3.weights'
            )
            self.model = net
            
            # Загрузка классов COCO
            with open('config/coco.names', 'r') as f:
                self.classes = [line.strip() for line in f.readlines()]
            
            self.is_initialized = True
            print("Загружена OpenCV DNN модель как fallback")
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации OpenCV: {e}")
            return False
    
    def detect_objects(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Детекция объектов на изображении
        
        Args:
            image_path (str): Путь к изображению
            
        Returns:
            list: Список обнаруженных объектов
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            if isinstance(self.model, torch.nn.Module):
                return self._detect_yolov5(image_path)
            else:
                return self._detect_opencv(image_path)
                
        except Exception as e:
            print(f"Ошибка детекции объектов: {e}")
            return []
    
    def _detect_yolov5(self, image_path: str) -> List[Dict[str, Any]]:
        """Детекция с использованием YOLOv5"""
        results = self.model(image_path)
        detections = []
        
        for *xyxy, conf, cls in results.xyxy[0]:
            class_name = self.classes[int(cls)]
            confidence = float(conf)
            
            if confidence >= self.confidence_threshold:
                detection = {
                    'class': class_name,
                    'confidence': round(confidence, 3),
                    'bbox': [int(coord) for coord in xyxy],
                    'center': self._calculate_center(xyxy)
                }
                detections.append(detection)
        
        return detections
    
    def _detect_opencv(self, image_path: str) -> List[Dict[str, Any]]:
        """Детекция с использованием OpenCV DNN"""
        image = cv2.imread(image_path)
        height, width = image.shape[:2]
        
        # Подготовка изображения
        blob = cv2.dnn.blobFromImage(
            image, 1/255.0, (416, 416), swapRB=True, crop=False
        )
        self.model.setInput(blob)
        
        # Получение результатов
        output_layers = self.model.getUnconnectedOutLayersNames()
        outputs = self.model.forward(output_layers)
        
        detections = []
        boxes, confidences, class_ids = [], [], []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.confidence_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Применение NMS
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, 
            self.confidence_threshold, 
            self.iou_threshold
        )
        
        if len(indices) > 0:
            for i in indices.flatten():
                class_name = self.classes[class_ids[i]]
                detection = {
                    'class': class_name,
                    'confidence': round(confidences[i], 3),
                    'bbox': boxes[i],
                    'center': [boxes[i][0] + boxes[i][2]//2, 
                              boxes[i][1] + boxes[i][3]//2]
                }
                detections.append(detection)
        
        return detections
    
    def _calculate_center(self, bbox):
        """Вычисление центра bounding box"""
        x1, y1, x2, y2 = bbox
        return [int((x1 + x2) / 2), int((y1 + y2) / 2)]
    
    def get_object_count(self, image_path: str) -> Dict[str, int]:
        """Получение статистики по объектам"""
        detections = self.detect_objects(image_path)
        object_count = {}
        
        for detection in detections:
            class_name = detection['class']
            object_count[class_name] = object_count.get(class_name, 0) + 1
        
        return object_count
    
    def save_detection_results(self, image_path: str, output_path: str):
        """Сохранение результатов детекции"""
        detections = self.detect_objects(image_path)
        
        results = {
            'image_path': image_path,
            'detections': detections,
            'total_objects': len(detections),
            'object_count': self.get_object_count(image_path)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results