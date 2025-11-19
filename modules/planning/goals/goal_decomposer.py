# goal_decomposer.py
"""
Декомпозитор целей - разбиение сложных целей на подцели и задачи
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .goal_manager import Goal, GoalPriority

@dataclass
class DecompositionRule:
    """Правило декомпозиции для определенных типов целей"""
    pattern: str
    template: List[Dict[str, Any]]
    complexity_threshold: float = 0.7

class GoalDecomposer:
    """Система декомпозиции целей на подцели"""
    
    def __init__(self):
        self.logger = logging.getLogger('goals.GoalDecomposer')
        self.decomposition_rules: List[DecompositionRule] = []
        self._load_decomposition_rules()
    
    def _load_decomposition_rules(self) -> None:
        """Загрузка правил декомпозиции"""
        # Правила для учебных целей
        self.decomposition_rules.append(
            DecompositionRule(
                pattern=r"(изучить|освоить|выучить).*",
                template=[
                    {"title": "Изучение теории", "description": "Теоретическое изучение материала", "priority": "MEDIUM"},
                    {"title": "Практические упражнения", "description": "Выполнение практических заданий", "priority": "HIGH"},
                    {"title": "Тестирование знаний", "description": "Проверка усвоенного материала", "priority": "MEDIUM"}
                ]
            )
        )
        
        # Правила для разработки
        self.decomposition_rules.append(
            DecompositionRule(
                pattern=r"(разработать|создать|реализовать).*(модуль|систему|функцию)",
                template=[
                    {"title": "Проектирование архитектуры", "description": "Разработка архитектуры решения", "priority": "HIGH"},
                    {"title": "Реализация базового функционала", "description": "Разработка основной функциональности", "priority": "HIGH"},
                    {"title": "Тестирование", "description": "Тестирование и отладка", "priority": "MEDIUM"},
                    {"title": "Документирование", "description": "Создание документации", "priority": "LOW"}
                ]
            )
        )
        
        # Правила для анализа
        self.decomposition_rules.append(
            DecompositionRule(
                pattern=r"(проанализировать|исследовать|изучить).*(данные|систему|процесс)",
                template=[
                    {"title": "Сбор данных", "description": "Сбор необходимых данных для анализа", "priority": "MEDIUM"},
                    {"title": "Предварительная обработка", "description": "Очистка и подготовка данных", "priority": "MEDIUM"},
                    {"title": "Анализ данных", "description": "Проведение основного анализа", "priority": "HIGH"},
                    {"title": "Интерпретация результатов", "description": "Анализ и выводы из результатов", "priority": "HIGH"},
                    {"title": "Подготовка отчета", "description": "Формирование итогового отчета", "priority": "LOW"}
                ]
            )
        )
    
    def decompose_goal(self, goal: Goal, max_depth: int = 3) -> List[Goal]:
        """
        Декомпозиция цели на подцели
        
        Args:
            goal: Цель для декомпозиции
            max_depth: Максимальная глубина декомпозиции
            
        Returns:
            List[Goal]: Список подцелей
        """
        self.logger.info(f"Декомпозиция цели: {goal.title}")
        
        subgoals = []
        
        # Поиск подходящего правила декомпозиции
        matching_rule = self._find_matching_rule(goal)
        
        if matching_rule:
            subgoals = self._apply_decomposition_rule(goal, matching_rule)
        else:
            # Общая декомпозиция по умолчанию
            subgoals = self._default_decomposition(goal)
        
        # Рекурсивная декомпозиция если необходимо
        if max_depth > 1:
            for subgoal in subgoals[:]:  # Копируем список для безопасной итерации
                if self._needs_further_decomposition(subgoal):
                    deeper_subgoals = self.decompose_goal(subgoal, max_depth - 1)
                    subgoals.remove(subgoal)
                    subgoals.extend(deeper_subgoals)
        
        self.logger.info(f"Создано {len(subgoals)} подцелей для '{goal.title}'")
        return subgoals
    
    def _find_matching_rule(self, goal: Goal) -> Optional[DecompositionRule]:
        """Поиск подходящего правила декомпозиции"""
        goal_text = f"{goal.title} {goal.description}".lower()
        
        for rule in self.decomposition_rules:
            if re.search(rule.pattern, goal_text, re.IGNORECASE):
                return rule
        
        return None
    
    def _apply_decomposition_rule(self, goal: Goal, rule: DecompositionRule) -> List[Goal]:
        """Применение правила декомпозиции"""
        subgoals = []
        
        for i, subtemplate in enumerate(rule.template):
            subgoal_id = f"{goal.goal_id}_sub{i+1:02d}"
            
            subgoal = Goal(
                goal_id=subgoal_id,
                title=subtemplate['title'],
                description=subtemplate['description'],
                priority=GoalPriority[subtemplate['priority']]
            )
            
            # Наследование тегов и метрик
            subgoal.tags = goal.tags + ['subgoal']
            subgoal.metrics = {**goal.metrics, 'parent_goal': goal.goal_id}
            
            subgoals.append(subgoal)
        
        return subgoals
    
    def _default_decomposition(self, goal: Goal) -> List[Goal]:
        """Декомпозиция по умолчанию для целей без специфических правил"""
        # Анализ сложности цели для определения количества подцелй
        complexity = self._estimate_goal_complexity(goal)
        
        if complexity < 0.3:
            # Простая цель - минимальная декомпозиция
            return self._create_simple_decomposition(goal)
        elif complexity < 0.7:
            # Средняя сложность
            return self._create_medium_decomposition(goal)
        else:
            # Сложная цель - детальная декомпозиция
            return self._create_complex_decomposition(goal)
    
    def _estimate_goal_complexity(self, goal: Goal) -> float:
        """Оценка сложности цели"""
        complexity_score = 0.0
        
        # Длина описания
        complexity_score += min(0.3, len(goal.description) / 1000)
        
        # Количество упоминаний сложных действий
        complex_indicators = ['разработать', 'проанализировать', 'оптимизировать', 'интегрировать']
        for indicator in complex_indicators:
            if indicator in goal.description.lower():
                complexity_score += 0.1
        
        # Приоритет как индикатор сложности
        if goal.priority in [GoalPriority.HIGH, GoalPriority.CRITICAL]:
            complexity_score += 0.2
        
        return min(1.0, complexity_score)
    
    def _create_simple_decomposition(self, goal: Goal) -> List[Goal]:
        """Декомпозиция для простых целей"""
        return [
            Goal(
                goal_id=f"{goal.goal_id}_sub01",
                title=f"Выполнение: {goal.title}",
                description=f"Основной этап выполнения цели: {goal.description}",
                priority=goal.priority
            )
        ]
    
    def _create_medium_decomposition(self, goal: Goal) -> List[Goal]:
        """Декомпозиция для целей средней сложности"""
        return [
            Goal(
                goal_id=f"{goal.goal_id}_sub01",
                title=f"Подготовка: {goal.title}",
                description="Подготовительный этап",
                priority=GoalPriority.MEDIUM
            ),
            Goal(
                goal_id=f"{goal.goal_id}_sub02", 
                title=f"Основной этап: {goal.title}",
                description="Основной этап выполнения",
                priority=goal.priority
            ),
            Goal(
                goal_id=f"{goal.goal_id}_sub03",
                title=f"Завершение: {goal.title}",
                description="Финальный этап и проверка",
                priority=GoalPriority.MEDIUM
            )
        ]
    
    def _create_complex_decomposition(self, goal: Goal) -> List[Goal]:
        """Декомпозиция для сложных целей"""
        stages = [
            ("Анализ требований", "Детальный анализ требований и ограничений"),
            ("Планирование", "Разработка детального плана выполнения"),
            ("Подготовка ресурсов", "Подготовка необходимых ресурсов и инструментов"),
            ("Основная реализация", "Реализация основной функциональности"),
            ("Тестирование и отладка", "Тестирование и исправление ошибок"),
            ("Оптимизация", "Оптимизация производительности и качества"),
            ("Документирование", "Создание документации и отчетности")
        ]
        
        subgoals = []
        for i, (stage_title, stage_desc) in enumerate(stages):
            subgoal = Goal(
                goal_id=f"{goal.goal_id}_sub{i+1:02d}",
                title=f"{stage_title}: {goal.title}",
                description=stage_desc,
                priority=GoalPriority.HIGH if i == 3 else GoalPriority.MEDIUM  # Основная реализация - высокий приоритет
            )
            subgoal.tags = goal.tags + ['subgoal', f'stage_{i+1}']
            subgoals.append(subgoal)
        
        return subgoals
    
    def _needs_further_decomposition(self, goal: Goal) -> bool:
        """Проверка необходимости дальнейшей декомпозиции"""
        # Проверяем сложность подцели
        complexity = self._estimate_goal_complexity(goal)
        
        # Длинное описание или сложные ключевые слова указывают на необходимость декомпозиции
        needs_decomposition = (
            complexity > 0.5 or
            len(goal.description) > 200 or
            any(word in goal.description.lower() for word in ['комплексн', 'сложн', 'многоэтапн'])
        )
        
        return needs_decomposition
    
    def add_custom_decomposition_rule(self, pattern: str, template: List[Dict[str, Any]]) -> None:
        """Добавление пользовательского правила декомпозиции"""
        new_rule = DecompositionRule(pattern=pattern, template=template)
        self.decomposition_rules.append(new_rule)
        self.logger.info(f"Добавлено новое правило декомпозиции: {pattern}")