# tests/mock_visual_processor.py
"""
Мок-версия visual_processor для тестирования без зависимостей
"""

class MockImageRecognizer:
    def __init__(self):
        self.is_initialized = False
        
    def initialize(self):
        self.is_initialized = True
        return True
        
    def detect_objects(self, image_path):
        return [
            {'class': 'person', 'confidence': 0.9, 'bbox': [100, 100, 200, 200]},
            {'class': 'car', 'confidence': 0.8, 'bbox': [300, 300, 400, 400]}
        ]


class MockFaceDetector:
    def __init__(self):
        self.is_initialized = False
        
    def initialize(self):
        self.is_initialized = True
        return True
        
    def detect_faces(self, image_path):
        return [
            {'face_id': 0, 'bbox': [150, 150, 250, 250], 'confidence': 0.9}
        ]
        
    def analyze_emotions(self, image_path):
        return [
            {'face_id': 0, 'dominant_emotion': 'happy', 'emotion_confidence': 0.8}
        ]


class MockSceneAnalyzer:
    def __init__(self):
        self.is_initialized = False
        
    def initialize(self):
        self.is_initialized = True
        return True
        
    def analyze_scene(self, image_path):
        return {
            'scene_type': {'indoor': 0.7, 'outdoor': 0.3},
            'description': 'Тестовая сцена'
        }


class MockVisualProcessor:
    """Мок-версия основного процессора"""
    
    def __init__(self):
        self.image_recognizer = MockImageRecognizer()
        self.face_detector = MockFaceDetector()
        self.scene_analyzer = MockSceneAnalyzer()
        self.is_initialized = False
        
    def initialize(self):
        self.image_recognizer.initialize()
        self.face_detector.initialize() 
        self.scene_analyzer.initialize()
        self.is_initialized = True
        return True
        
    def process_image(self, image_path, tasks=None):
        if tasks is None:
            tasks = ['object_detection', 'face_detection', 'scene_analysis']
            
        results = {
            'image_path': image_path,
            'processing_time': 0.5,
            'tasks_performed': tasks
        }
        
        if 'object_detection' in tasks:
            results['objects'] = self.image_recognizer.detect_objects(image_path)
            
        if 'face_detection' in tasks:
            results['faces'] = self.face_detector.detect_faces(image_path)
            results['emotions'] = self.face_detector.analyze_emotions(image_path)
            
        if 'scene_analysis' in tasks:
            results['scene'] = self.scene_analyzer.analyze_scene(image_path)
            
        return results