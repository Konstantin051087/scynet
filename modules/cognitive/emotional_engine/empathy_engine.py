"""
Движок эмпатии
Генерирует эмпатические ответы на основе эмоционального состояния пользователя
"""

import random
import logging
from typing import Dict, List
import yaml
import os

class EmpathyEngine:
    def __init__(self):
        try:
            self.logger = logging.getLogger("EmpathyEngine")
            self.empathy_responses = {}
            self.emotional_support_patterns = {}
            
            self.load_empathy_responses()
            self.load_support_patterns()
            self.logger.info("✅ Empathy Engine инициализирован")
        except Exception as e:
            self.logger = logging.getLogger("EmpathyEngine")
            self.logger.error(f"❌ Ошибка инициализации Empathy Engine: {e}")
            self.empathy_responses = {}
            self.emotional_support_patterns = {}
    
    def load_empathy_responses(self):
        """Загрузка шаблонов эмпатических ответов"""
        try:
            config_path = os.path.join('config', 'emotional_rules.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.empathy_responses = config.get('empathy_responses', {})
        except FileNotFoundError:
            self.logger.warning("⚠️ Файл emotional_rules.yaml не найден, используются значения по умолчанию")
            # Ответы по умолчанию
            self.empathy_responses = {
                'joy': [
                    "Рад разделить с вами эту радость!",
                    "Здорово слышать, что вы в хорошем настроении!",
                    "Ваше счастье заразительно!",
                    "Как прекрасно, что у вас все хорошо!"
                ],
                'sadness': [
                    "Мне жаль, что вам грустно. Хотите рассказать подробнее?",
                    "Понимаю, что вам тяжело. Я здесь, чтобы помочь.",
                    "Грусть - это нормально. Вы не одни.",
                    "Сочувствую вашим переживаниям."
                ],
                'anger': [
                    "Понимаю ваше раздражение. Давайте разберемся с этим вместе.",
                    "Вижу, что ситуация вас расстроила. Хотите обсудить?",
                    "Гнев - естественная реакция. Давайте найдем решение.",
                    "Понимаю ваше негодование. Чем могу помочь?"
                ],
                'fear': [
                    "Понимаю ваше беспокойство. Давайте посмотрим на ситуацию спокойно.",
                    "Страх - это нормально. Вы в безопасности.",
                    "Вижу, что вы волнуетесь. Давайте обсудим ваши тревоги.",
                    "Понимаю вашу озабоченность. Вместе мы справимся."
                ],
                'frustration': [
                    "Понимаю ваше разочарование. Иногда все бывает сложно.",
                    "Вижу, что ситуация вас расстраивает. Давайте поищем выход.",
                    "Разочарование - это часть процесса. Не сдавайтесь!",
                    "Понимаю ваше недовольство. Предлагаю поискать альтернативы."
                ]
            }
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки эмпатических ответов: {e}")
            self.empathy_responses = {
                'neutral': ["Понимаю. Продолжайте, пожалуйста."]
            }
    
    def load_support_patterns(self):
        """Загрузка паттернов эмоциональной поддержки"""
        try:
            self.emotional_support_patterns = {
                'validation': [
                    "Понимаю ваши чувства.",
                    "Ваши эмоции совершенно оправданы.",
                    "Это естественная реакция в такой ситуации."
                ],
                'normalization': [
                    "Многие люди чувствуют то же самое в подобных обстоятельствах.",
                    "Вы не одиноки в своих переживаниях.",
                    "Это нормально - испытывать такие эмоции."
                ],
                'encouragement': [
                    "Вы справитесь с этой ситуацией.",
                    "Верю в ваши силы.",
                    "У вас есть все необходимое, чтобы преодолеть это."
                ],
                'active_listening': [
                    "Расскажите подробнее, что вас беспокоит.",
                    "Я внимательно вас слушаю.",
                    "Продолжайте, я здесь, чтобы помочь."
                ]
            }
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки паттернов поддержки: {e}")
            self.emotional_support_patterns = {
                'active_listening': ["Расскажите подробнее, что вас беспокоит."]
            }
    
    def generate_response(self, detected_emotions: Dict[str, float], 
                         system_mood: str, user_input: str) -> str:
        """Генерация эмпатического ответа"""
        try:
            if not detected_emotions:
                return self._get_neutral_response()
            
            # Определение доминирующей эмоции
            dominant_emotion = max(detected_emotions.items(), key=lambda x: x[1])
            emotion_name, emotion_intensity = dominant_emotion
            
            # Выбор типа ответа на основе интенсивности эмоции
            if emotion_intensity < 0.3:
                response_type = "light_empathy"
            elif emotion_intensity < 0.7:
                response_type = "moderate_empathy"
            else:
                response_type = "deep_empathy"
            
            # Генерация ответа
            empathic_response = self._construct_empathic_response(
                emotion_name, response_type, system_mood, user_input
            )
            
            return empathic_response
        except Exception as e:
            self.logger.error(f"❌ Ошибка генерации эмпатического ответа: {e}")
            return "Понимаю. Продолжайте, пожалуйста."
    
    def _construct_empathic_response(self, emotion: str, response_type: str,
                                   system_mood: str, user_input: str) -> str:
        """Конструктор эмпатического ответа"""
        try:
            base_responses = self.empathy_responses.get(emotion, [])
            
            if not base_responses:
                return self._get_neutral_response()
            
            # Выбор базового ответа
            base_response = random.choice(base_responses)
            
            # Добавление эмоциональной окраски системы
            mood_adjusted_response = self._adjust_for_system_mood(
                base_response, system_mood
            )
            
            # Добавление элементов активного слушания
            if response_type in ["moderate_empathy", "deep_empathy"]:
                listening_element = random.choice(
                    self.emotional_support_patterns['active_listening']
                )
                mood_adjusted_response += f" {listening_element}"
            
            # Добавление валидации для сильных эмоций
            if response_type == "deep_empathy":
                validation_element = random.choice(
                    self.emotional_support_patterns['validation']
                )
                mood_adjusted_response += f" {validation_element}"
            
            return mood_adjusted_response
        except Exception as e:
            self.logger.error(f"❌ Ошибка конструирования эмпатического ответа: {e}")
            return self._get_neutral_response()
    
    def _adjust_for_system_mood(self, response: str, system_mood: str) -> str:
        """Корректировка ответа на основе настроения системы"""
        try:
            mood_adjustments = {
                'joy': {
                    'prefixes': ['С радостью отвечаю: ', 'Охотно говорю: '],
                    'suffixes': [' 😊', '! Замечательно!']
                },
                'sadness': {
                    'prefixes': ['С пониманием отвечаю: ', 'Сочувственно: '],
                    'suffixes': [' 💙', '.']
                },
                'neutral': {
                    'prefixes': [''],
                    'suffixes': ['']
                },
                'excitement': {
                    'prefixes': ['С энтузиазмом: ', 'С воодушевлением: '],
                    'suffixes': ['! 🎉', '! Это интересно!']
                }
            }
            
            adjustment = mood_adjustments.get(system_mood, mood_adjustments['neutral'])
            
            prefix = random.choice(adjustment['prefixes'])
            suffix = random.choice(adjustment['suffixes'])
            
            return f"{prefix}{response}{suffix}"
        except Exception as e:
            self.logger.error(f"❌ Ошибка корректировки настроения системы: {e}")
            return response
    
    def _get_neutral_response(self) -> str:
        """Получение нейтрального ответа"""
        neutral_responses = [
            "Понимаю. Продолжайте, пожалуйста.",
            "Спасибо, что поделились. Чем еще могу помочь?",
            "Интересно. Расскажите подробнее.",
            "Понял вас. Что еще вас беспокоит?"
        ]
        return random.choice(neutral_responses)
    
    def analyze_emotional_needs(self, emotion_scores: Dict[str, float]) -> List[str]:
        """Анализ эмоциональных потребностей пользователя"""
        try:
            needs = []
            
            if emotion_scores.get('sadness', 0) > 0.5:
                needs.append('comfort')
                needs.append('validation')
            
            if emotion_scores.get('fear', 0) > 0.5:
                needs.append('reassurance')
                needs.append('safety')
            
            if emotion_scores.get('anger', 0) > 0.5:
                needs.append('understanding')
                needs.append('solution_focused')
            
            if emotion_scores.get('joy', 0) > 0.5:
                needs.append('celebration')
                needs.append('sharing')
            
            return needs if needs else ['connection']
        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа эмоциональных потребностей: {e}")
            return ['connection']