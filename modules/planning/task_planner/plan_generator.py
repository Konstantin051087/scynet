# planning/task_planner/plan_generator.py
"""
Генератор планов и последовательностей
Создает планы на основе шаблонов и анализа задачи
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PlanStep:
    """Шаг плана"""
    action: str
    parameters: Dict[str, Any]
    duration: int  # в минутах
    dependencies: List[str]
    resources: List[str]
    priority: int

@dataclass
class TaskPlan:
    """Полный план задачи"""
    task_id: str
    goal: str
    steps: List[PlanStep]
    total_duration: int
    required_resources: List[str]
    constraints: Dict[str, Any]

class PlanGenerator:
    """Генератор планов на основе шаблонов и анализа"""
    
    def __init__(self, plan_library_path: str = "planning/task_planner/plan_library"):
        self.plan_library_path = Path(plan_library_path)
        self.plan_templates = {}
        self.logger = logging.getLogger(__name__)
        self._load_plan_templates()
    
    def _load_plan_templates(self):
        """Загрузка шаблонов планов из библиотеки"""
        try:
            plan_files = {
                'cooking': self.plan_library_path / 'cooking.plans',
                'travel': self.plan_library_path / 'travel.plans', 
                'work': self.plan_library_path / 'work.plans',
                'learning': self.plan_library_path / 'learning.plans'
            }
            
            for domain, file_path in plan_files.items():
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.plan_templates[domain] = json.load(f)
                    self.logger.info(f"Загружены шаблоны планов для домена: {domain}")
                else:
                    self.logger.warning(f"Файл шаблонов не найден: {file_path}")
                    
        except Exception as e:
            self.logger.error(f"Ошибка загрузки шаблонов планов: {e}")
    
    def generate_plan(self, task_description: str, goal: str, constraints: Dict[str, Any]) -> TaskPlan:
        """
        Генерация плана для задачи
        
        Args:
            task_description: Описание задачи
            goal: Цель задачи
            constraints: Ограничения и параметры
            
        Returns:
            TaskPlan: Сгенерированный план
        """
        try:
            # Определение домена задачи
            domain = self._identify_domain(task_description, goal)
            
            # Поиск подходящего шаблона
            template = self._find_best_template(domain, task_description, constraints)
            
            # Адаптация шаблона под конкретную задачу
            plan = self._adapt_template(template, task_description, goal, constraints)
            
            # Генерация уникального ID
            plan.task_id = self._generate_task_id(task_description)
            
            self.logger.info(f"Сгенерирован план для задачи: {task_description}")
            return plan
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации плана: {e}")
            return self._generate_fallback_plan(task_description, goal, constraints)
    
    def _identify_domain(self, task_description: str, goal: str) -> str:
        """Определение домена задачи"""
        description_lower = task_description.lower()
        goal_lower = goal.lower()
        
        cooking_keywords = ['приготовить', 'рецепт', 'кухня', 'еда', 'готовка', 'блюдо']
        travel_keywords = ['путешествие', 'поездка', 'отпуск', 'билет', 'отель', 'маршрут']
        work_keywords = ['проект', 'работа', 'задача', 'дедлайн', 'отчет', 'презентация']
        learning_keywords = ['изучить', 'обучение', 'курс', 'материал', 'практика', 'теория']
        
        if any(keyword in description_lower or keyword in goal_lower for keyword in cooking_keywords):
            return 'cooking'
        elif any(keyword in description_lower or keyword in goal_lower for keyword in travel_keywords):
            return 'travel'
        elif any(keyword in description_lower or keyword in goal_lower for keyword in work_keywords):
            return 'work'
        elif any(keyword in description_lower or keyword in goal_lower for keyword in learning_keywords):
            return 'learning'
        else:
            return 'general'
    
    def _find_best_template(self, domain: str, task_description: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Поиск лучшего шаблона для задачи"""
        if domain in self.plan_templates:
            templates = self.plan_templates[domain].get('templates', [])
            
            # Простой алгоритм подбора по ключевым словам
            description_words = set(task_description.lower().split())
            best_template = None
            best_score = 0
            
            for template in templates:
                template_keywords = set(template.get('keywords', []))
                score = len(description_words.intersection(template_keywords))
                
                if score > best_score:
                    best_score = score
                    best_template = template
            
            return best_template or templates[0] if templates else {}
        
        return {}
    
    def _adapt_template(self, template: Dict[str, Any], task_description: str, 
                       goal: str, constraints: Dict[str, Any]) -> TaskPlan:
        """Адаптация шаблона под конкретную задачу"""
        steps = []
        total_duration = 0
        required_resources = set()
        
        # Преобразование шагов шаблона
        for template_step in template.get('steps', []):
            step = PlanStep(
                action=self._customize_action(template_step['action'], task_description),
                parameters=self._customize_parameters(template_step.get('parameters', {}), constraints),
                duration=template_step.get('duration', 30),
                dependencies=template_step.get('dependencies', []),
                resources=template_step.get('resources', []),
                priority=template_step.get('priority', 1)
            )
            steps.append(step)
            total_duration += step.duration
            required_resources.update(step.resources)
        
        return TaskPlan(
            task_id="",
            goal=goal,
            steps=steps,
            total_duration=total_duration,
            required_resources=list(required_resources),
            constraints=constraints
        )
    
    def _customize_action(self, action: str, task_description: str) -> str:
        """Кастомизация действия под задачу"""
        # Базовая реализация - можно расширить для конкретных доменов
        return action
    
    def _customize_parameters(self, parameters: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Кастомизация параметров под ограничения"""
        customized = parameters.copy()
        customized.update(constraints)
        return customized
    
    def _generate_task_id(self, task_description: str) -> str:
        """Генерация уникального ID задачи"""
        import hashlib
        import time
        
        timestamp = str(int(time.time()))
        hash_input = task_description + timestamp
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    def _generate_fallback_plan(self, task_description: str, goal: str, constraints: Dict[str, Any]) -> TaskPlan:
        """Создание резервного плана при ошибках"""
        self.logger.warning("Использован резервный план")
        
        fallback_steps = [
            PlanStep(
                action="Анализ задачи",
                parameters={},
                duration=10,
                dependencies=[],
                resources=[],
                priority=1
            ),
            PlanStep(
                action="Выполнение основной задачи",
                parameters={},
                duration=60,
                dependencies=["Анализ задачи"],
                resources=[],
                priority=2
            ),
            PlanStep(
                action="Проверка результата",
                parameters={},
                duration=10,
                dependencies=["Выполнение основной задачи"],
                resources=[],
                priority=3
            )
        ]
        
        return TaskPlan(
            task_id=self._generate_task_id(task_description),
            goal=goal,
            steps=fallback_steps,
            total_duration=80,
            required_resources=[],
            constraints=constraints
        )