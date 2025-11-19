# planning/task_planner/__init__.py
"""
Модуль планирования задач
Генерация, оптимизация и валидация планов выполнения задач
"""

import logging
from typing import Dict, Any, Optional
from .plan_generator import PlanGenerator, TaskPlan
from .step_optimizer import StepOptimizer
from .resource_allocator import ResourceAllocator
from .plan_validator import PlanValidator

class TaskPlanner:
    """Основной класс планировщика задач"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.plan_generator = PlanGenerator()
        self.step_optimizer = StepOptimizer()
        self.resource_allocator = ResourceAllocator()
        self.plan_validator = PlanValidator()
        
        self.initialized = False
    
    async def initialize(self):
        """Инициализация модуля"""
        try:
            # Инициализация компонентов
            # (если потребуется асинхронная инициализация в будущем)
            self.initialized = True
            self.logger.info("TaskPlanner успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации TaskPlanner: {e}")
            self.initialized = False
    
    def create_plan(self, task_description: str, goal: str, 
                   constraints: Dict[str, Any] = None) -> TaskPlan:
        """
        Создание плана для задачи
        
        Args:
            task_description: Описание задачи
            goal: Цель задачи
            constraints: Ограничения и параметры
            
        Returns:
            TaskPlan: Сгенерированный план
        """
        if not self.initialized:
            self.logger.warning("TaskPlanner не инициализирован, но используется")
        
        constraints = constraints or {}
        return self.plan_generator.generate_plan(task_description, goal, constraints)
    
    def optimize_plan(self, plan: TaskPlan, constraints: Dict[str, Any] = None):
        """
        Оптимизация плана
        
        Args:
            plan: План для оптимизации
            constraints: Дополнительные ограничения
            
        Returns:
            OptimizationResult: Результат оптимизации
        """
        return self.step_optimizer.optimize_plan(plan, constraints)
    
    def validate_plan(self, plan: TaskPlan, available_resources: Dict[str, Any] = None):
        """
        Валидация плана
        
        Args:
            plan: План для валидации
            available_resources: Доступные ресурсы
            
        Returns:
            ValidationResult: Результат валидации
        """
        return self.plan_validator.validate_plan(plan, available_resources)
    
    def allocate_resources(self, plan: TaskPlan, start_time: int = 0):
        """
        Распределение ресурсов для плана
        
        Args:
            plan: План задачи
            start_time: Время начала выполнения
            
        Returns:
            Dict: Распределения ресурсов по шагам
        """
        return self.resource_allocator.allocate_resources_for_plan(plan, start_time)
    
    def get_module_info(self) -> Dict[str, Any]:
        """Получение информации о модуле"""
        return {
            "name": "task_planner",
            "version": "1.0",
            "description": "Модуль планирования и оптимизации задач",
            "initialized": self.initialized,
            "components": {
                "plan_generator": True,
                "step_optimizer": True,
                "resource_allocator": True,
                "plan_validator": True
            }
        }

# Экспорт основного класса
__all__ = ['TaskPlanner', 'PlanGenerator', 'StepOptimizer', 
           'ResourceAllocator', 'PlanValidator', 'TaskPlan']