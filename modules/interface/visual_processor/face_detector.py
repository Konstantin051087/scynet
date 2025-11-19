"""
МОДУЛЬ ДЕТЕКЦИИ ЛИЦ И ЭМОЦИЙ
"""

import cv2
import numpy as np
import dlib
from deepface import DeepFace
from typing import List, Dict, Any, Tuple
import os

class FaceDetector:
    """Класс для детекции лиц и анализа эмоций"""
    
    def __init__(self):
        self.DeepFace = None
        self.landmark_detector = None
        self.emotion_detector = None
        self.is_initialized = False
        
    def initialize(self):
        """Инициализация детекторов лиц и эмоций"""
        try:
            # Инициализация детектора лиц OpenCV
            self.DeepFace = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Инициализация dlib для landmarks (опционально)
            try:
                self.landmark_detector = dlib.shape_predictor(
                    'models/shape_predictor_68_face_landmarks.dat'
                )
            except:
                print("dlib landmarks недоступен, используется базовый детектор")
            
            # Инициализация детектора эмоций
            self.emotion_detector = DeepFace(mtcnn=True)
            
            self.is_initialized = True
            print("Детектор лиц и эмоций инициализирован")
            return True
            
        except Exception as e:
            print(f"Ошибка инициализации детектора лиц: {e}")
            return False
    
    def detect_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Детекция лиц на изображении
        
        Args:
            image_path (str): Путь к изображению
            
        Returns:
            list: Список обнаруженных лиц
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Не удалось загрузить изображение: {image_path}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Детекция лиц
            faces = self.DeepFace.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            detected_faces = []
            
            for i, (x, y, w, h) in enumerate(faces):
                face_info = {
                    'face_id': i,
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'center': [int(x + w/2), int(y + h/2)],
                    'area': w * h,
                    'confidence': 0.9  # Базовое значение для Haar cascades
                }
                
                # Анализ landmarks если доступен
                if self.landmark_detector:
                    landmarks = self._detect_landmarks(gray, x, y, w, h)
                    face_info['landmarks'] = landmarks
                
                detected_faces.append(face_info)
            
            return detected_faces
            
        except Exception as e:
            print(f"Ошибка детекции лиц: {e}")
            return []
    
    def _detect_landmarks(self, gray_image, x, y, w, h):
        """Детекция facial landmarks"""
        try:
            rect = dlib.rectangle(x, y, x + w, y + h)
            landmarks = self.landmark_detector(gray_image, rect)
            
            landmarks_data = []
            for i in range(68):
                point = landmarks.part(i)
                landmarks_data.append({
                    'x': point.x,
                    'y': point.y,
                    'type': self._get_landmark_type(i)
                })
            
            return landmarks_data
            
        except Exception as e:
            print(f"Ошибка детекции landmarks: {e}")
            return []
    
    def _get_landmark_type(self, landmark_index: int) -> str:
        """Определение типа landmark"""
        if 0 <= landmark_index <= 16:
            return 'jaw'
        elif 17 <= landmark_index <= 21:
            return 'right_eyebrow'
        elif 22 <= landmark_index <= 26:
            return 'left_eyebrow'
        elif 27 <= landmark_index <= 35:
            return 'nose'
        elif 36 <= landmark_index <= 41:
            return 'right_eye'
        elif 42 <= landmark_index <= 47:
            return 'left_eye'
        elif 48 <= landmark_index <= 67:
            return 'mouth'
        else:
            return 'unknown'
    
    def analyze_emotions(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Анализ эмоций на изображении
        
        Args:
            image_path (str): Путь к изображению
            
        Returns:
            list: Список эмоций для каждого лица
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            # Анализ эмоций с использованием DeepFace
            image = cv2.imread(image_path)
            emotion_results = self.emotion_detector.detect_emotions(image)
            
            emotions_data = []
            
            for i, result in enumerate(emotion_results):
                emotion_info = {
                    'face_id': i,
                    'bbox': result['box'],
                    'dominant_emotion': result['dominant_emotion'],
                    'emotions': result['emotions'],
                    'emotion_confidence': round(result['emotions'][result['dominant_emotion']], 3)
                }
                emotions_data.append(emotion_info)
            
            return emotions_data
            
        except Exception as e:
            print(f"Ошибка анализа эмоций: {e}")
            return []
    
    def get_demographics(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Базовая демографическая информация (возраст, пол)
        Note: Требует дополнительных моделей
        """
        # Заглушка для демографического анализа
        # В реальной реализации можно использовать модели типа DeepFace
        faces = self.detect_faces(image_path)
        
        demographics = []
        for face in faces:
            demo_info = {
                'face_id': face['face_id'],
                'age_estimate': None,  # Можно добавить модель возраста
                'gender_estimate': None,  # Можно добавить модель пола
                'bbox': face['bbox']
            }
            demographics.append(demo_info)
        
        return demographics
    
    def draw_faces_on_image(self, image_path: str, output_path: str = None):
        """
        Отрисовка обнаруженных лиц на изображении
        
        Args:
            image_path (str): Путь к исходному изображению
            output_path (str): Путь для сохранения результата
            
        Returns:
            numpy.ndarray: Изображение с отрисованными лицами
        """
        image = cv2.imread(image_path)
        faces = self.detect_faces(image_path)
        emotions = self.analyze_emotions(image_path)
        
        for face in faces:
            x, y, w, h = face['bbox']
            
            # Отрисовка bounding box
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Добавление информации о лице
            face_id_text = f"Face {face['face_id']}"
            cv2.putText(image, face_id_text, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Добавление информации об эмоциях
        for emotion in emotions:
            if emotion['face_id'] < len(faces):
                face = faces[emotion['face_id']]
                x, y, w, h = face['bbox']
                
                emotion_text = f"{emotion['dominant_emotion']}: {emotion['emotion_confidence']}"
                cv2.putText(image, emotion_text, (x, y + h + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        if output_path:
            cv2.imwrite(output_path, image)
        
        return image
