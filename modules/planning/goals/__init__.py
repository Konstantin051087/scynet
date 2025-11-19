# planning/goals/__init__.py
"""
Модуль управления целями - Goal Management System
Отвечает за постановку, отслеживание и декомпозицию целей системы
"""

import logging
from typing import Dict, Any, Optional, List

from .goal_manager import GoalManager
from .priority_calculator import PriorityCalculator
from .goal_decomposer import GoalDecomposer
from .progress_tracker import ProgressTracker
from .feedback_evaluator import FeedbackEvaluator

class GoalsModule:
    """Основной класс модуля управления целями"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.goal_manager = GoalManager()
        self.priority_calculator = PriorityCalculator()
        self.goal_decomposer = GoalDecomposer()
        self.progress_tracker = ProgressTracker()
        self.feedback_evaluator = FeedbackEvaluator()
        
        self.initialized = False
    
    async def initialize(self):
        """Инициализация модуля"""
        try:
            # Инициализация компонентов (если потребуется асинхронная инициализация)
            self.initialized = True
            self.logger.info("GoalsModule успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации GoalsModule: {e}")
            self.initialized = False
    
    def create_goal(self, goal_description: str, priority: int = 1, 
                   constraints: Dict[str, Any] = None) -> str:
        """
        Создание новой цели
        
        Args:
            goal_description: Описание цели
            priority: Приоритет цели
            constraints: Ограничения
            
        Returns:
            str: ID созданной цели
        """
        if not self.initialized:
            self.logger.warning("GoalsModule не инициализирован, но используется")
        
        return self.goal_manager.create_goal(goal_description, priority, constraints or {})
    
    def decompose_goal(self, goal_id: str) -> List[Dict[str, Any]]:
        """
        Декомпозиция цели на подцели
        
        Args:
            goal_id: ID цели
            
        Returns:
            List[Dict]: Список подцелей
        """
        return self.goal_decomposer.decompose_goal(goal_id)
    
    def get_goal_progress(self, goal_id: str) -> float:
        """
        Получение прогресса по цели
        
        Args:
            goal_id: ID цели
            
        Returns:
            float: Прогресс в процентах
        """
        return self.progress_tracker.get_progress(goal_id)
    
    def update_goal_feedback(self, goal_id: str, feedback: Dict[str, Any]):
        """
        Обновление обратной связи по цели
        
        Args:
            goal_id: ID цели
            feedback: Данные обратной связи
        """
        self.feedback_evaluator.process_feedback(goal_id, feedback)
    
    def get_goal_priority(self, goal_id: str) -> int:
        """
        Получение приоритета цели
        
        Args:
            goal_id: ID цели
            
        Returns:
            int: Приоритет
        """
        return self.priority_calculator.calculate_priority(goal_id)
    
    def get_module_info(self) -> Dict[str, Any]:
        """Получение информации о модуле"""
        return {
            "name": "goals",
            "version": "1.0",
            "description": "Модуль управления целями",
            "initialized": self.initialized,
            "components": {
                "goal_manager": True,
                "priority_calculator": True,
                "goal_decomposer": True,
                "progress_tracker": True,
                "feedback_evaluator": True
            }
        }

# Экспортируем основной класс и все остальные
__all__ = [
    'GoalsModule',
    'GoalManager',
    'PriorityCalculator', 
    'GoalDecomposer',
    'ProgressTracker',
    'FeedbackEvaluator'
]