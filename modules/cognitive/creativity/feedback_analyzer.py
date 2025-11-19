"""
Анализатор обратной связи
"""

import random
import re
import json
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path

class FeedbackAnalyzer:
    """Анализатор обратной связи для оценки качества контента"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.feedback_file = Path("data/runtime/feedback_history.json")
        
        # База знаний для анализа
        self.quality_metrics = self._load_quality_metrics()
        self.sentiment_lexicon = self._load_sentiment_lexicon()
        self.improvement_suggestions = self._load_improvement_suggestions()
        
        # История обратной связи
        self.feedback_history = self._load_feedback_history()
        
        self.logger.info("Анализатор обратной связи инициализирован")
    
    def _load_quality_metrics(self) -> Dict[str, List[str]]:
        """Загрузка метрик качества"""
        return {
            "юмор": [
                "оригинальность шутки", "уместность юмора", "неожиданность кульминации",
                "культурная релевантность", "эмоциональный отклик"
            ],
            "поэзия": [
                "ритм и метр", "богатство образов", "эмоциональная глубина",
                "оригинальность метафор", "гармоничность композиции"
            ],
            "метафоры": [
                "новизна сравнения", "глубина аналогии", "ясность образа",
                "эмоциональная нагрузка", "культурная уместность"
            ],
            "истории": [
                "захватывающий сюжет", "развитие персонажей", "логичность повествования",
                "эмоциональное воздействие", "оригинальность идеи"
            ],
            "идеи": [
                "инновационность", "практическая применимость", "ясность формулировки",
                "потенциальное влияние", "оригинальность подхода"
            ]
        }
    
    def _load_sentiment_lexicon(self) -> Dict[str, float]:
        """Загрузка сентимент-лексикона"""
        return {
            # Положительные слова
            "отлично": 1.0, "превосходно": 1.0, "замечательно": 0.9, "великолепно": 0.9,
            "интересно": 0.8, "оригинально": 0.8, "креативно": 0.8, "смешно": 0.7,
            "трогательно": 0.7, "вдохновляюще": 0.9, "полезно": 0.7, "понравилось": 0.8,
            
            # Отрицательные слова
            "скучно": -0.8, "неинтересно": -0.7, "банально": -0.6, "предсказуемо": -0.5,
            "непонятно": -0.6, "сложно": -0.4, "неуместно": -0.7, "разочаровал": -0.8,
            "плохо": -0.9, "ужасно": -1.0, "не понравилось": -0.8, "слабо": -0.6
        }
    
    def _load_improvement_suggestions(self) -> Dict[str, List[str]]:
        """Загрузка предложений по улучшению"""
        return {
            "юмор": [
                "Попробуйте добавить неожиданный поворот",
                "Усильте кульминацию шутки",
                "Используйте более актуальные темы",
                "Поработайте над ритмом подачи",
                "Добавьте элемент абсурда"
            ],
            "поэзия": [
                "Усильте ритмический рисунок",
                "Добавьте более яркие образы",
                "Поработайте над оригинальностью метафор",
                "Углубите эмоциональную составляющую",
                "Улучшите гармонию строк"
            ],
            "метафоры": [
                "Сделайте сравнение более неожиданным",
                "Углубите аналогию",
                "Используйте более яркие образы",
                "Сделайте метафору более понятной",
                "Добавьте эмоциональной нагрузки"
            ],
            "истории": [
                "Усильте развитие персонажей",
                "Добавьте неожиданных поворотов сюжета",
                "Улучшите логику повествования",
                "Углубите эмоциональное воздействие",
                "Сделайте завязку более интригующей"
            ],
            "идеи": [
                "Конкретизируйте предложение",
                "Добавьте практические шаги реализации",
                "Усильте инновационную составляющую",
                "Рассмотрите больше аспектов проблемы",
                "Предложите измеримые результаты"
            ]
        }
    
    def _load_feedback_history(self) -> List[Dict[str, Any]]:
        """Загрузка истории обратной связи"""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            self.logger.error(f"Ошибка загрузки истории фидбека: {e}")
            return []
    
    def _save_feedback_history(self):
        """Сохранение истории обратной связи"""
        try:
            self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_history[-1000:], f, ensure_ascii=False, indent=2)  # Сохраняем последние 1000 записей
        except Exception as e:
            self.logger.error(f"Ошибка сохранения истории фидбека: {e}")
    
    def analyze(self, content: str, content_type: str, user_feedback: str = None) -> Dict[str, Any]:
        """Анализ контента и генерация обратной связи"""
        
        try:
            # Базовый анализ контента
            content_analysis = self._analyze_content(content, content_type)
            
            # Анализ сентимента если есть пользовательский фидбек
            sentiment_score = 0.5  # нейтральный по умолчанию
            if user_feedback:
                sentiment_score = self._analyze_sentiment(user_feedback)
                # Сохраняем пользовательский фидбек
                self._record_user_feedback(content, content_type, user_feedback, sentiment_score)
            
            # Интеграция оценок
            final_score = self._calculate_final_score(content_analysis, sentiment_score)
            
            # Генерация предложений по улучшению
            suggestions = self._generate_improvement_suggestions(content_analysis, content_type, final_score)
            
            # Анализ трендов
            trends = self._analyze_trends(content_type)
            
            return {
                'score': final_score,
                'content_analysis': content_analysis,
                'sentiment_score': sentiment_score,
                'suggestions': suggestions,
                'trends': trends,
                'content_type': content_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа фидбека: {e}")
            return {
                'score': 0.5,
                'suggestions': ["Продолжайте практиковаться и экспериментировать"],
                'error': str(e)
            }
    
    def _analyze_content(self, content: str, content_type: str) -> Dict[str, float]:
        """Анализ содержания контента"""
        analysis = {}
        
        # Получаем метрики для данного типа контента
        metrics = self.quality_metrics.get(content_type, [])
        
        for metric in metrics:
            # Упрощенная оценка каждой метрики
            score = self._evaluate_metric(content, metric, content_type)
            analysis[metric] = score
        
        # Дополнительные общие метрики
        analysis['оригинальность'] = self._assess_originality(content)
        analysis['ясность'] = self._assess_clarity(content)
        analysis['эмоциональность'] = self._assess_emotionality(content)
        analysis['структура'] = self._assess_structure(content, content_type)
        
        return analysis
    
    def _evaluate_metric(self, content: str, metric: str, content_type: str) -> float:
        """Оценка конкретной метрики"""
        # Упрощенная реализация на основе ключевых слов и паттернов
        base_score = 0.5
        
        metric_patterns = {
            "оригинальность шутки": {
                "positive": ["неожиданно", "оригинально", "свежо", "новый подход"],
                "negative": ["старо", "банально", "предсказуемо", "слышал"]
            },
            "богатство образов": {
                "positive": ["как", "словно", "подобно", "похоже", "напоминает"],
                "negative": ["просто", "обычно", "стандартно"]
            },
            "инновационность": {
                "positive": ["новый", "инновационный", "уникальный", "революционный"],
                "negative": ["традиционный", "стандартный", "общепринятый"]
            }
        }
        
        patterns = metric_patterns.get(metric, {})
        content_lower = content.lower()
        
        # Бонус за позитивные паттерны
        positive_bonus = sum(1 for word in patterns.get('positive', []) if word in content_lower) * 0.1
        
        # Штраф за негативные паттерны
        negative_penalty = sum(1 for word in patterns.get('negative', []) if word in content_lower) * 0.1
        
        score = base_score + positive_bonus - negative_penalty
        return max(0.1, min(1.0, score))
    
    def _assess_originality(self, content: str) -> float:
        """Оценка оригинальности контента"""
        # Проверка на часто используемые фразы
        common_phrases = [
            "в наше время", "как известно", "один раз", "так сказать",
            "в общем и целом", "на самом деле", "по большому счету"
        ]
        
        content_lower = content.lower()
        common_count = sum(1 for phrase in common_phrases if phrase in content_lower)
        
        originality = 1.0 - (common_count * 0.1)
        return max(0.1, originality)
    
    def _assess_clarity(self, content: str) -> float:
        """Оценка ясности контента"""
        # Анализ длины предложений и сложности
        sentences = re.split(r'[.!?]+', content)
        if not sentences:
            return 0.5
        
        avg_sentence_length = sum(len(sentence.split()) for sentence in sentences if sentence.strip()) / len(sentences)
        
        # Идеальная длина предложения 10-20 слов
        if 10 <= avg_sentence_length <= 20:
            return 0.8
        elif 5 <= avg_sentence_length <= 25:
            return 0.6
        else:
            return 0.4
    
    def _assess_emotionality(self, content: str) -> float:
        """Оценка эмоциональности контента"""
        emotional_words = [
            "любовь", "радость", "грусть", "гнев", "страх", "надежда", 
            "восхищение", "разочарование", "восторг", "печаль"
        ]
        
        content_lower = content.lower()
        emotional_count = sum(1 for word in emotional_words if word in content_lower)
        word_count = len(content.split())
        
        if word_count == 0:
            return 0.5
        
        emotional_density = emotional_count / word_count
        return min(1.0, emotional_density * 10)  # Нормализация
    
    def _assess_structure(self, content: str, content_type: str) -> float:
        """Оценка структуры контента"""
        if content_type == "поэзия":
            lines = content.split('\n')
            if len(lines) >= 3:
                return 0.7
            else:
                return 0.4
        elif content_type == "истории":
            # Проверка на наличие элементов повествования
            narrative_elements = ["когда", "потом", "вдруг", "оказалось", "затем"]
            content_lower = content.lower()
            element_count = sum(1 for element in narrative_elements if element in content_lower)
            return min(1.0, element_count * 0.2)
        else:
            return 0.6  # Базовая оценка для других типов
    
    def _analyze_sentiment(self, feedback: str) -> float:
        """Анализ сентимента пользовательского фидбека"""
        words = re.findall(r'\w+', feedback.lower())
        if not words:
            return 0.5
        
        total_score = 0
        matched_words = 0
        
        for word in words:
            if word in self.sentiment_lexicon:
                total_score += self.sentiment_lexicon[word]
                matched_words += 1
        
        if matched_words == 0:
            return 0.5
        
        average_score = total_score / matched_words
        # Нормализация от [-1, 1] к [0, 1]
        return (average_score + 1) / 2
    
    def _calculate_final_score(self, content_analysis: Dict[str, float], sentiment_score: float) -> float:
        """Расчет итоговой оценки"""
        # Среднее по метрикам контента
        content_score = sum(content_analysis.values()) / len(content_analysis) if content_analysis else 0.5
        
        # Взвешенное среднее с учетом сентимента
        final_score = (content_score * 0.7) + (sentiment_score * 0.3)
        
        return round(final_score, 2)
    
    def _generate_improvement_suggestions(self, content_analysis: Dict[str, float], 
                                        content_type: str, final_score: float) -> List[str]:
        """Генерация предложений по улучшению"""
        suggestions = []
        
        # Базовые предложения на основе оценки
        if final_score < 0.4:
            suggestions.append("Рекомендуется кардинально пересмотреть подход")
        elif final_score < 0.6:
            suggestions.append("Есть потенциал для значительного улучшения")
        elif final_score < 0.8:
            suggestions.append("Хороший результат, но можно сделать еще лучше")
        else:
            suggestions.append("Отличная работа! Продолжайте в том же духе")
        
        # Специфические предложения на основе слабых метрик
        weak_metrics = [metric for metric, score in content_analysis.items() if score < 0.6]
        
        for metric in weak_metrics[:2]:  # Берем 2 самых слабых метрики
            domain_suggestions = self.improvement_suggestions.get(content_type, [])
            if domain_suggestions:
                suggestions.append(random.choice(domain_suggestions))
        
        # Уникализация предложений
        return list(set(suggestions))[:3]  # Не более 3 предложений
    
    def _analyze_trends(self, content_type: str) -> Dict[str, Any]:
        """Анализ трендов на основе истории"""
        type_feedbacks = [fb for fb in self.feedback_history if fb.get('content_type') == content_type]
        
        if not type_feedbacks:
            return {"message": "Недостаточно данных для анализа трендов"}
        
        recent_feedbacks = type_feedbacks[-10:]  # Последние 10 фидбеков
        if not recent_feedbacks:
            return {"message": "Недостаточно данных для анализа трендов"}
        
        recent_scores = [fb.get('score', 0.5) for fb in recent_feedbacks]
        avg_score = sum(recent_scores) / len(recent_scores)
        
        # Анализ прогресса
        if len(recent_scores) >= 2:
            first_half = recent_scores[:len(recent_scores)//2]
            second_half = recent_scores[len(recent_scores)//2:]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            progress = avg_second - avg_first
        else:
            progress = 0
        
        return {
            'average_score': round(avg_score, 2),
            'progress': round(progress, 3),
            'samples_count': len(recent_feedbacks),
            'trend': 'улучшение' if progress > 0.05 else 'ухудшение' if progress < -0.05 else 'стабильность'
        }
    
    def _record_user_feedback(self, content: str, content_type: str, 
                            user_feedback: str, sentiment_score: float):
        """Запись пользовательского фидбека"""
        feedback_record = {
            'content_preview': content[:100] + "..." if len(content) > 100 else content,
            'content_type': content_type,
            'user_feedback': user_feedback,
            'sentiment_score': sentiment_score,
            'score': sentiment_score,  # Используем сентимент как оценку
            'timestamp': datetime.now().isoformat()
        }
        
        self.feedback_history.append(feedback_record)
        self._save_feedback_history()
    
    def learn_from_feedback(self, content: str, content_type: str, user_score: float):
        """Обучение на основе пользовательской оценки"""
        # Упрощенное обучение - записываем фидбек
        feedback_record = {
            'content_preview': content[:100] + "..." if len(content) > 100 else content,
            'content_type': content_type,
            'user_feedback': f"Оценка пользователя: {user_score}",
            'sentiment_score': user_score,
            'score': user_score,
            'timestamp': datetime.now().isoformat()
        }
        
        self.feedback_history.append(feedback_record)
        self._save_feedback_history()
        
        self.logger.info(f"Записан пользовательский фидбек для {content_type}: оценка {user_score}")