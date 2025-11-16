"""
Модуль эмоционального интеллекта
Обеспечивает детекцию эмоций, симуляцию эмоциональных реакций и эмпатию
"""

from .emotion_detector import EmotionDetector
from .emotion_simulator import EmotionSimulator
from .empathy_engine import EmpathyEngine
from .mood_tracker import MoodTracker

class EmotionalEngine:
    """Основной класс модуля эмоционального интеллекта"""
    
    def __init__(self, config_path="config/emotional_engine.yaml"):
        self.emotion_detector = EmotionDetector()
        self.emotion_simulator = EmotionSimulator()
        self.empathy_engine = EmpathyEngine()
        self.mood_tracker = MoodTracker()
        
        self.current_mood = "neutral"
        self.emotional_state = {}
        
    def process_input(self, text, user_id=None):
        """Основной метод обработки входящих данных"""
        try:
            # Детекция эмоций в тексте
            detected_emotions = self.emotion_detector.detect_emotions(text)
            
            # Обновление настроения системы
            self.current_mood = self.emotion_simulator.simulate_response(
                detected_emotions, self.current_mood
            )
            
            # Генерация эмпатического ответа
            empathic_response = self.empathy_engine.generate_response(
                detected_emotions, self.current_mood, text
            )
            
            # Логирование эмоционального состояния
            self.mood_tracker.track_mood(
                user_id, detected_emotions, self.current_mood
            )
            
            return {
                "detected_emotions": detected_emotions,
                "system_mood": self.current_mood,
                "empathic_response": empathic_response,
                "emotional_state": self.emotional_state
            }
            
        except Exception as e:
            print(f"Error in emotional engine: {e}")
            return {
                "detected_emotions": {"neutral": 1.0},
                "system_mood": "neutral",
                "empathic_response": "",
                "emotional_state": {}
            }

__all__ = ['EmotionalEngine', 'EmotionDetector', 'EmotionSimulator', 'EmpathyEngine', 'MoodTracker']