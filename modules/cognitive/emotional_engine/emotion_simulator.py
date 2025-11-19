"""
Симулятор эмоциональных реакций системы
Моделирует эмоциональное состояние ИИ на основе взаимодействий
"""

import random
import time
import logging
from typing import Dict, List, Optional
import yaml
import os

class EmotionSimulator:
    def __init__(self):
        try:
            self.logger = logging.getLogger("EmotionSimulator")
            self.current_mood = "neutral"
            self.mood_intensity = 0.5
            self.mood_history = []
            self.last_update = time.time()
            
            # Загрузка правил эмоциональных реакций
            self.load_emotional_rules()
            
            # Параметры эмоциональной модели
            self.mood_decay_rate = 0.1  # Скорость возврата к нейтральному состоянию
            self.max_mood_intensity = 1.0
            self.min_mood_intensity = 0.1
            self.logger.info("✅ Emotion Simulator инициализирован")
        except Exception as e:
            self.logger = logging.getLogger("EmotionSimulator")
            self.logger.error(f"❌ Ошибка инициализации Emotion Simulator: {e}")
            self.current_mood = "neutral"
            self.mood_intensity = 0.5
    
    def load_emotional_rules(self):
        """Загрузка правил эмоциональных реакций"""
        try:
            config_path = os.path.join('config', 'emotional_rules.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.emotional_rules = yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning("⚠️ Файл emotional_rules.yaml не найден, используются значения по умолчанию")
            self.emotional_rules = {
                'mood_transitions': {
                    'joy': {'neutral': 0.7, 'excitement': 0.3},
                    'sadness': {'neutral': 0.6, 'sadness': 0.4},
                    'anger': {'frustration': 0.5, 'neutral': 0.5},
                    'fear': {'neutral': 0.8, 'fear': 0.2},
                    'surprise': {'excitement': 0.4, 'neutral': 0.6}
                },
                'mood_persistence': {
                    'joy': 0.3,
                    'sadness': 0.4,
                    'anger': 0.6,
                    'fear': 0.5,
                    'neutral': 0.8
                }
            }
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки правил эмоций: {e}")
            self.emotional_rules = {
                'mood_transitions': {'neutral': {'neutral': 1.0}},
                'mood_persistence': {'neutral': 0.8}
            }
    
    def simulate_response(self, detected_emotions: Dict[str, float], 
                         current_context: str = "", current_mood: Optional[str] = None) -> str:
        """Симуляция эмоционального ответа системы"""
        try:
            # Обновление настроения на основе детектированных эмоций
            self._update_mood_state(detected_emotions)
            
            # Применение распада настроения со временем
            self._apply_mood_decay()
            
            # Учет контекста в эмоциональной реакции
            self._apply_contextual_influence(current_context)
            
            # Запись в историю настроений
            self._record_mood_history()
            
            return self.current_mood
        except Exception as e:
            self.logger.error(f"❌ Ошибка симуляции эмоционального ответа: {e}")
            return "neutral"
    
    def _update_mood_state(self, detected_emotions: Dict[str, float]):
        """Обновление состояния настроения на основе входных эмоций"""
        try:
            if not detected_emotions:
                return
            
            # Находим доминирующую эмоцию
            dominant_emotion = max(detected_emotions.items(), key=lambda x: x[1])
            emotion_name, emotion_intensity = dominant_emotion
            
            # Применяем правила перехода настроения
            transition_rules = self.emotional_rules.get('mood_transitions', {})
            current_transitions = transition_rules.get(emotion_name, {'neutral': 1.0})
            
            # Выбираем новое настроение на основе вероятностей
            new_mood = self._select_mood_by_probability(current_transitions)
            
            # Вычисляем интенсивность нового настроения
            persistence = self.emotional_rules.get('mood_persistence', {}).get(
                self.current_mood, 0.5
            )
            
            self.mood_intensity = (
                persistence * self.mood_intensity + 
                (1 - persistence) * emotion_intensity
            )
            
            # Ограничиваем интенсивность
            self.mood_intensity = max(self.min_mood_intensity, 
                                    min(self.max_mood_intensity, self.mood_intensity))
            
            self.current_mood = new_mood
            self.last_update = time.time()
        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления состояния настроения: {e}")
    
    def _select_mood_by_probability(self, transitions: Dict[str, float]) -> str:
        """Выбор настроения на основе вероятностного распределения"""
        try:
            moods = list(transitions.keys())
            probabilities = list(transitions.values())
            
            # Нормализуем вероятности
            total = sum(probabilities)
            normalized_probs = [p/total for p in probabilities]
            
            # Выбираем настроение
            rand_val = random.random()
            cumulative = 0
            
            for mood, prob in zip(moods, normalized_probs):
                cumulative += prob
                if rand_val <= cumulative:
                    return mood
            
            return moods[-1] if moods else "neutral"
        except Exception as e:
            self.logger.error(f"❌ Ошибка выбора настроения: {e}")
            return "neutral"
    
    def _apply_mood_decay(self):
        """Применение распада настроения со временем"""
        try:
            current_time = time.time()
            time_elapsed = current_time - self.last_update
            
            # Распад применяется только после значительного времени
            if time_elapsed > 300:  # 5 минут
                decay_factor = self.mood_decay_rate * (time_elapsed / 300)
                self.mood_intensity *= (1 - decay_factor)
                
                # Если интенсивность низкая, возвращаемся к нейтральному состоянию
                if self.mood_intensity < 0.2 and self.current_mood != "neutral":
                    self.current_mood = "neutral"
                    self.mood_intensity = 0.5
        except Exception as e:
            self.logger.error(f"❌ Ошибка применения распада настроения: {e}")
    
    def _apply_contextual_influence(self, context: str):
        """Учет контекстного влияния на настроение"""
        try:
            # В реальной реализации здесь будет сложная логика анализа контекста
            contextual_influences = {
                "утро": {"joy": 0.1, "excitement": 0.1},
                "вечер": {"sadness": 0.1, "contentment": 0.1},
                "проблема": {"frustration": 0.2, "sadness": 0.1},
                "успех": {"joy": 0.3, "excitement": 0.2}
            }
            
            for key, influence in contextual_influences.items():
                if key in context.lower():
                    for emotion, boost in influence.items():
                        if emotion == self.current_mood:
                            self.mood_intensity = min(
                                self.max_mood_intensity, 
                                self.mood_intensity + boost
                            )
        except Exception as e:
            self.logger.error(f"❌ Ошибка применения контекстного влияния: {e}")
    
    def _record_mood_history(self):
        """Запись текущего настроения в историю"""
        try:
            mood_record = {
                'timestamp': time.time(),
                'mood': self.current_mood,
                'intensity': self.mood_intensity
            }
            
            self.mood_history.append(mood_record)
            
            # Ограничиваем размер истории
            if len(self.mood_history) > 1000:
                self.mood_history = self.mood_history[-500:]
        except Exception as e:
            self.logger.error(f"❌ Ошибка записи истории настроения: {e}")
    
    def get_mood_trend(self) -> Dict[str, float]:
        """Анализ тренда настроения"""
        try:
            if len(self.mood_history) < 2:
                return {'trend': 'stable', 'change': 0.0}
            
            recent_moods = self.mood_history[-10:]  # Последние 10 записей
            
            # Простой анализ тренда
            positive_moods = ['joy', 'excitement', 'contentment']
            negative_moods = ['sadness', 'anger', 'fear', 'frustration']
            
            positive_count = sum(1 for m in recent_moods if m['mood'] in positive_moods)
            negative_count = sum(1 for m in recent_moods if m['mood'] in negative_moods)
            
            if positive_count > negative_count:
                return {'trend': 'improving', 'change': positive_count / len(recent_moods)}
            elif negative_count > positive_count:
                return {'trend': 'declining', 'change': negative_count / len(recent_moods)}
            else:
                return {'trend': 'stable', 'change': 0.0}
        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа тренда настроения: {e}")
            return {'trend': 'stable', 'change': 0.0}