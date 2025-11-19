# priority_calculator.py
"""
Калькулятор приоритетов целей - вычисление и оптимизация приоритетов
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple
from enum import Enum
import numpy as np

from .goal_manager import Goal, GoalPriority

class PriorityFactor(Enum):
    URGENCY = "urgency"           # Срочность
    IMPORTANCE = "importance"     # Важность  
    COMPLEXITY = "complexity"     # Сложность
    DEPENDENCIES = "dependencies" # Зависимости
    RESOURCES = "resources"       # Доступность ресурсов
    IMPACT = "impact"             # Влияние на систему

class PriorityCalculator:
    """Калькулятор для вычисления приоритетов целей"""
    
    def __init__(self):
        self.logger = logging.getLogger('goals.PriorityCalculator')
        self.factor_weights = {
            PriorityFactor.URGENCY: 0.25,
            PriorityFactor.IMPORTANCE: 0.30,
            PriorityFactor.COMPLEXITY: 0.15,
            PriorityFactor.DEPENDENCIES: 0.10,
            PriorityFactor.RESOURCES: 0.10,
            PriorityFactor.IMPACT: 0.10
        }
        
    def calculate_goal_priority(self, goal: Goal, context: Dict = None) -> Tuple[GoalPriority, Dict]:
        """
        Вычисление приоритета цели на основе множества факторов
        
        Args:
            goal: Цель для оценки
            context: Контекст системы (ресурсы, текущая нагрузка и т.д.)
            
        Returns:
            Tuple: (приоритет, детальная оценка факторов)
        """
        context = context or {}
        
        factors_score = {}
        
        # Оценка срочности
        factors_score[PriorityFactor.URGENCY] = self._calculate_urgency(goal, context)
        
        # Оценка важности
        factors_score[PriorityFactor.IMPORTANCE] = self._calculate_importance(goal, context)
        
        # Оценка сложности
        factors_score[PriorityFactor.COMPLEXITY] = self._calculate_complexity(goal, context)
        
        # Оценка зависимостей
        factors_score[PriorityFactor.DEPENDENCIES] = self._calculate_dependencies(goal, context)
        
        # Оценка доступности ресурсов
        factors_score[PriorityFactor.RESOURCES] = self._calculate_resource_availability(goal, context)
        
        # Оценка влияния
        factors_score[PriorityFactor.IMPACT] = self._calculate_impact(goal, context)
        
        # Вычисление общего скора
        total_score = sum(
            score * self.factor_weights[factor] 
            for factor, score in factors_score.items()
        )
        
        # Преобразование в приоритет цели
        priority = self._score_to_priority(total_score)
        
        detailed_analysis = {
            'total_score': total_score,
            'factors': {factor.value: score for factor, score in factors_score.items()},
            'weights': {factor.value: weight for factor, weight in self.factor_weights.items()}
        }
        
        self.logger.debug(f"Приоритет цели '{goal.title}': {priority.value} (score: {total_score:.2f})")
        
        return priority, detailed_analysis
    
    def _calculate_urgency(self, goal: Goal, context: Dict) -> float:
        """Оценка срочности цели"""
        if not goal.deadline:
            return 0.3  # Средняя срочность без дедлайна
        
        now = datetime.now()
        time_remaining = (goal.deadline - now).total_seconds()
        
        if time_remaining <= 0:
            return 1.0  # Просроченная - максимальная срочность
        elif time_remaining < 3600:  # Менее часа
            return 0.9
        elif time_remaining < 86400:  # Менее дня
            return 0.7
        elif time_remaining < 604800:  # Менее недели
            return 0.5
        else:
            return 0.2  # Более недели - низкая срочность
    
    def _calculate_importance(self, goal: Goal, context: Dict) -> float:
        """Оценка важности цели"""
        # Анализ тегов и описания для определения важности
        importance_keywords = {
            'critical': 1.0, 'urgent': 0.9, 'important': 0.8, 
            'system': 0.7, 'user': 0.6, 'learning': 0.5, 'optional': 0.3
        }
        
        text_analysis = f"{goal.title} {goal.description} {' '.join(goal.tags)}".lower()
        
        max_score = 0.3  # Базовая важность
        
        for keyword, score in importance_keywords.items():
            if keyword in text_analysis:
                max_score = max(max_score, score)
        
        # Учет приоритета из шаблона
        if goal.priority != GoalPriority.MEDIUM:
            priority_bonus = {
                GoalPriority.CRITICAL: 0.4,
                GoalPriority.HIGH: 0.2,
                GoalPriority.LOW: -0.1,
                GoalPriority.MINIMAL: -0.2
            }
            max_score = min(1.0, max(0.0, max_score + priority_bonus.get(goal.priority, 0)))
        
        return max_score
    
    def _calculate_complexity(self, goal: Goal, context: Dict) -> float:
        """Оценка сложности цели (обратная зависимость - чем сложнее, тем ниже приоритет)"""
        complexity_indicators = 0
        
        # Количество подцелей
        complexity_indicators += len(goal.subgoals) * 0.1
        
        # Длина описания как индикатор сложности
        description_complexity = min(1.0, len(goal.description) / 500)
        complexity_indicators += description_complexity * 0.3
        
        # Количество метрик и зависимостей
        complexity_indicators += len(goal.metrics) * 0.05
        complexity_indicators += len(goal.dependencies) * 0.1
        
        # Обратная зависимость: высокая сложность = более низкий приоритет
        complexity_score = max(0.1, 1.0 - min(1.0, complexity_indicators))
        
        return complexity_score
    
    def _calculate_dependencies(self, goal: Goal, context: Dict) -> float:
        """Оценка зависимости от других целей"""
        if not goal.dependencies:
            return 0.8  # Высокий приоритет для независимых целей
        
        # Проверка статуса зависимостей
        active_goals = context.get('active_goals', {})
        completed_deps = 0
        
        for dep_id in goal.dependencies:
            dep_goal = active_goals.get(dep_id)
            if dep_goal and dep_goal.progress >= 1.0:
                completed_deps += 1
        
        completion_ratio = completed_deps / len(goal.dependencies) if goal.dependencies else 1.0
        
        # Чем больше завершено зависимостей, тем выше приоритет
        return 0.2 + (completion_ratio * 0.6)
    
    def _calculate_resource_availability(self, goal: Goal, context: Dict) -> float:
        """Оценка доступности ресурсов"""
        available_resources = context.get('available_resources', {})
        required_resources = goal.metrics.get('required_resources', {})
        
        if not required_resources:
            return 0.7  # Средний приоритет если ресурсы не указаны
        
        satisfaction_scores = []
        
        for resource, required in required_resources.items():
            available = available_resources.get(resource, 0)
            if available >= required:
                satisfaction_scores.append(1.0)
            else:
                satisfaction_scores.append(available / required if required > 0 else 1.0)
        
        avg_satisfaction = np.mean(satisfaction_scores) if satisfaction_scores else 0.5
        
        return avg_satisfaction
    
    def _calculate_impact(self, goal: Goal, context: Dict) -> float:
        """Оценка влияния цели на систему"""
        impact_indicators = 0
        
        # Анализ тегов на предмет влияния
        high_impact_tags = ['system', 'core', 'critical', 'user_experience', 'performance']
        medium_impact_tags = ['feature', 'improvement', 'optimization'] 
        low_impact_tags = ['optional', 'experimental', 'backup']
        
        for tag in goal.tags:
            if tag in high_impact_tags:
                impact_indicators += 0.3
            elif tag in medium_impact_tags:
                impact_indicators += 0.15
            elif tag in low_impact_tags:
                impact_indicators += 0.05
        
        # Анализ метрик влияния
        predefined_impact = goal.metrics.get('expected_impact', 0)
        impact_indicators += predefined_impact * 0.5
        
        return min(1.0, impact_indicators)
    
    def _score_to_priority(self, score: float) -> GoalPriority:
        """Преобразование численного скора в приоритет цели"""
        if score >= 0.8:
            return GoalPriority.CRITICAL
        elif score >= 0.6:
            return GoalPriority.HIGH
        elif score >= 0.4:
            return GoalPriority.MEDIUM
        elif score >= 0.2:
            return GoalPriority.LOW
        else:
            return GoalPriority.MINIMAL
    
    def optimize_priorities(self, goals: List[Goal], context: Dict = None) -> List[Tuple[Goal, GoalPriority, Dict]]:
        """
        Оптимизация приоритетов для списка целей
        
        Returns:
            List of tuples: (goal, optimized_priority, analysis_details)
        """
        optimized_goals = []
        
        for goal in goals:
            priority, analysis = self.calculate_goal_priority(goal, context)
            optimized_goals.append((goal, priority, analysis))
        
        # Сортировка по приоритету
        optimized_goals.sort(key=lambda x: x[1].value, reverse=True)
        
        self.logger.info(f"Оптимизированы приоритеты для {len(goals)} целей")
        
        return optimized_goals
    
    def update_factor_weights(self, new_weights: Dict[PriorityFactor, float]) -> None:
        """Обновление весов факторов приоритета"""
        # Проверка что сумма весов = 1.0
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            self.logger.warning(f"Сумма весов ({total}) не равна 1.0, нормализация...")
            # Нормализация
            for factor in new_weights:
                new_weights[factor] /= total
        
        self.factor_weights = new_weights
        self.logger.info("Веса факторов приоритета обновлены")