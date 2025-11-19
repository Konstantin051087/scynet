# feedback_evaluator.py
"""
Оценщик фидбека - анализ обратной связи и коррекция целей
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from textblob import TextBlob  # для анализа тональности

from .goal_manager import Goal, GoalStatus, GoalPriority

@dataclass
class Feedback:
    """Структура обратной связи"""
    feedback_id: str
    goal_id: str
    source: str  # 'user', 'system', 'external'
    content: str
    sentiment: float  # -1.0 to 1.0
    timestamp: datetime
    metrics: Dict[str, Any]

class FeedbackEvaluator:
    """Система оценки обратной связи и коррекции целей"""
    
    def __init__(self):
        self.logger = logging.getLogger('goals.FeedbackEvaluator')
        self.feedback_history: Dict[str, List[Feedback]] = {}
        self.adaptation_rules: List[Dict] = []
        
        self._load_adaptation_rules()
    
    def _load_adaptation_rules(self) -> None:
        """Загрузка правил адаптации на основе фидбека"""
        self.adaptation_rules = [
            {
                'condition': lambda f: f.sentiment < -0.5,
                'action': 'increase_priority',
                'message': 'Негативная обратная связь - повышение приоритета исправления'
            },
            {
                'condition': lambda f: f.sentiment > 0.7 and 'complete' in f.content.lower(),
                'action': 'mark_completed', 
                'message': 'Позитивная обратная связь указывает на завершение'
            },
            {
                'condition': lambda f: any(word in f.content.lower() for word in ['сложно', 'трудно', 'невозможно']),
                'action': 'decompose_further',
                'message': 'Жалобы на сложность - требуется декомпозиция'
            },
            {
                'condition': lambda f: any(word in f.content.lower() for word in ['срочно', 'быстрее', 'скорее']),
                'action': 'increase_urgency',
                'message': 'Запрос на ускорение - повышение срочности'
            }
        ]
    
    def analyze_feedback(self, goal: Goal, feedback_text: str, source: str = 'user') -> Feedback:
        """
        Анализ текстовой обратной связи
        
        Args:
            goal: Цель, к которой относится фидбек
            feedback_text: Текст обратной связи
            source: Источник фидбека
            
        Returns:
            Feedback: Проанализированная обратная связь
        """
        # Анализ тональности
        sentiment = self._analyze_sentiment(feedback_text)
        
        # Извлечение ключевых метрик
        metrics = self._extract_metrics(feedback_text)
        
        # Создание объекта фидбека
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        feedback = Feedback(
            feedback_id=feedback_id,
            goal_id=goal.goal_id,
            source=source,
            content=feedback_text,
            sentiment=sentiment,
            timestamp=datetime.now(),
            metrics=metrics
        )
        
        # Сохранение в историю
        if goal.goal_id not in self.feedback_history:
            self.feedback_history[goal.goal_id] = []
        self.feedback_history[goal.goal_id].append(feedback)
        
        self.logger.info(f"Проанализирован фидбек для цели {goal.title}: sentiment={sentiment:.2f}")
        
        return feedback
    
    def _analyze_sentiment(self, text: str) -> float:
        """Анализ тональности текста"""
        try:
            # Используем TextBlob для анализа тональности (требует установки)
            blob = TextBlob(text)
            # TextBlob возвращает тональность от -1 до 1
            return blob.sentiment.polarity
        except Exception as e:
            self.logger.warning(f"Ошибка анализа тональности, используется fallback: {e}")
            # Fallback метод на основе ключевых слов
            return self._fallback_sentiment_analysis(text)
    
    def _fallback_sentiment_analysis(self, text: str) -> float:
        """Резервный анализ тональности на основе ключевых слов"""
        positive_words = ['хорош', 'отличн', 'прекрасн', 'супер', 'замечательн', 'успешн', 'нравится']
        negative_words = ['плох', 'ужасн', 'кошмарн', 'не нравится', 'неудобн', 'сложн', 'трудн']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, sentiment))
    
    def _extract_metrics(self, text: str) -> Dict[str, Any]:
        """Извлечение численных метрик из текста"""
        metrics = {}
        
        # Поиск процентов
        percent_pattern = r'(\d+)%'
        percent_matches = re.findall(percent_pattern, text)
        if percent_matches:
            metrics['mentioned_percentage'] = int(percent_matches[0]) / 100
        
        # Поиск оценок по шкале
        scale_pattern = r'(\d+)/10'
        scale_matches = re.findall(scale_pattern, text)
        if scale_matches:
            metrics['scale_rating'] = int(scale_matches[0]) / 10
        
        # Поиск временных упоминаний
        time_patterns = [
            (r'(\d+)\s*час', 'hours_mentioned'),
            (r'(\d+)\s*дн', 'days_mentioned'), 
            (r'(\d+)\s*недел', 'weeks_mentioned')
        ]
        
        for pattern, key in time_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                metrics[key] = int(matches[0])
        
        return metrics
    
    def evaluate_feedback_impact(self, feedback: Feedback, goal: Goal) -> List[Dict[str, Any]]:
        """
        Оценка влияния фидбека на цель
        
        Returns:
            List[Dict]: Список рекомендованных действий
        """
        recommendations = []
        
        # Применение правил адаптации
        for rule in self.adaptation_rules:
            if rule['condition'](feedback):
                recommendation = {
                    'action': rule['action'],
                    'message': rule['message'],
                    'feedback_id': feedback.feedback_id,
                    'confidence': 0.8  # Базовая уверенность
                }
                recommendations.append(recommendation)
        
        # Анализ метрик для дополнительных рекомендаций
        if 'mentioned_percentage' in feedback.metrics:
            mentioned_progress = feedback.metrics['mentioned_percentage']
            current_progress = goal.progress
            
            if abs(mentioned_progress - current_progress) > 0.2:
                recommendations.append({
                    'action': 'adjust_progress',
                    'message': f'Коррекция прогресса с {current_progress:.0%} на {mentioned_progress:.0%} по фидбеку',
                    'new_progress': mentioned_progress,
                    'confidence': 0.7
                })
        
        self.logger.info(f"Сгенерировано {len(recommendations)} рекомендаций по фидбеку")
        return recommendations
    
    def get_feedback_summary(self, goal_id: str, time_period: Optional[int] = None) -> Dict[str, Any]:
        """
        Получение сводки по фидбеку за период
        
        Args:
            goal_id: ID цели
            time_period: Период в днях (None - весь период)
            
        Returns:
            Dict: Сводка фидбека
        """
        feedback_list = self.feedback_history.get(goal_id, [])
        
        if time_period:
            cutoff_date = datetime.now() - timedelta(days=time_period)
            feedback_list = [fb for fb in feedback_list if fb.timestamp >= cutoff_date]
        
        if not feedback_list:
            return {}
        
        sentiments = [fb.sentiment for fb in feedback_list]
        sources = [fb.source for fb in feedback_list]
        
        summary = {
            'total_feedback': len(feedback_list),
            'average_sentiment': sum(sentiments) / len(sentiments),
            'positive_feedback': len([s for s in sentiments if s > 0.3]),
            'negative_feedback': len([s for s in sentiments if s < -0.3]),
            'neutral_feedback': len([s for s in sentiments if -0.3 <= s <= 0.3]),
            'source_breakdown': {source: sources.count(source) for source in set(sources)},
            'latest_feedback': feedback_list[-1].timestamp.isoformat(),
            'trend': self._calculate_feedback_trend(feedback_list)
        }
        
        return summary
    
    def _calculate_feedback_trend(self, feedback_list: List[Feedback]) -> float:
        """Вычисление тренда тональности фидбека"""
        if len(feedback_list) < 2:
            return 0.0
        
        # Сортируем по времени
        sorted_feedback = sorted(feedback_list, key=lambda x: x.timestamp)
        
        # Простая линейная регрессия для тренда
        timestamps = [fb.timestamp.timestamp() for fb in sorted_feedback]
        sentiments = [fb.sentiment for fb in sorted_feedback]
        
        # Нормализация временных меток
        min_time = min(timestamps)
        normalized_times = [t - min_time for t in timestamps]
        
        if max(normalized_times) == 0:
            return 0.0
        
        # Вычисление тренда
        n = len(normalized_times)
        sum_x = sum(normalized_times)
        sum_y = sum(sentiments)
        sum_xy = sum(x * y for x, y in zip(normalized_times, sentiments))
        sum_x2 = sum(x * x for x in normalized_times)
        
        trend = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        
        return trend
    
    def apply_feedback_recommendations(self, goal: Goal, recommendations: List[Dict]) -> Goal:
        """
        Применение рекомендаций по фидбеку к цели
        
        Returns:
            Goal: Обновленная цель
        """
        applied_actions = []
        
        for recommendation in recommendations:
            action = recommendation['action']
            confidence = recommendation.get('confidence', 0.5)
            
            if confidence < 0.6:  # Порог уверенности
                continue
            
            if action == 'increase_priority':
                # Повышение приоритета
                if goal.priority.value < GoalPriority.CRITICAL.value:
                    new_priority_value = min(GoalPriority.CRITICAL.value, goal.priority.value + 1)
                    goal.priority = GoalPriority(new_priority_value)
                    applied_actions.append('priority_increased')
            
            elif action == 'mark_completed':
                # Отметка как завершенной
                goal.status = GoalStatus.COMPLETED
                goal.progress = 1.0
                applied_actions.append('marked_completed')
            
            elif action == 'adjust_progress':
                # Коррекция прогресса
                new_progress = recommendation.get('new_progress')
                if new_progress is not None:
                    goal.progress = new_progress
                    applied_actions.append('progress_adjusted')
            
            elif action == 'increase_urgency':
                # Увеличение срочности (установка дедлайна)
                if not goal.deadline:
                    goal.deadline = datetime.now() + timedelta(days=1)
                    applied_actions.append('deadline_set')
            
        if applied_actions:
            self.logger.info(f"Применены действия к цели {goal.title}: {applied_actions}")
        
        return goal
    
    def get_goal_health_score(self, goal_id: str) -> float:
        """
        Вычисление показателя здоровья цели на основе фидбека
        
        Returns:
            float: Оценка здоровья (0.0 - 1.0)
        """
        feedback_summary = self.get_feedback_summary(goal_id)
        
        if not feedback_summary:
            return 0.7  # Нейтральная оценка при отсутствии фидбека
        
        base_score = 0.5
        
        # Влияние средней тональности
        sentiment = feedback_summary['average_sentiment']
        base_score += sentiment * 0.3
        
        # Влияние тренда
        trend = feedback_summary.get('trend', 0)
        base_score += trend * 0.2
        
        # Влияние соотношения позитивного/негативного фидбека
        total = feedback_summary['total_feedback']
        if total > 0:
            positive_ratio = feedback_summary['positive_feedback'] / total
            negative_ratio = feedback_summary['negative_feedback'] / total
            base_score += (positive_ratio - negative_ratio) * 0.2
        
        return max(0.0, min(1.0, base_score))