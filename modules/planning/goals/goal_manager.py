# goal_manager.py
"""
Менеджер целей - создание, отслеживание и управление целями системы
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

class GoalStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class GoalPriority(Enum):
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1

class Goal:
    """Класс представления цели"""
    
    def __init__(self, goal_id: str, title: str, description: str, 
                 priority: GoalPriority = GoalPriority.MEDIUM,
                 deadline: Optional[datetime] = None):
        self.goal_id = goal_id
        self.title = title
        self.description = description
        self.priority = priority
        self.status = GoalStatus.PENDING
        self.created_at = datetime.now()
        self.deadline = deadline
        self.subgoals: List['Goal'] = []
        self.progress = 0.0
        self.dependencies: List[str] = []
        self.metrics: Dict[str, Any] = {}
        self.tags: List[str] = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация цели в словарь"""
        return {
            'goal_id': self.goal_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'progress': self.progress,
            'dependencies': self.dependencies,
            'metrics': self.metrics,
            'tags': self.tags,
            'subgoals': [sg.to_dict() for sg in self.subgoals]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Goal':
        """Десериализация цели из словаря"""
        goal = cls(
            goal_id=data['goal_id'],
            title=data['title'],
            description=data['description'],
            priority=GoalPriority(data['priority']),
            deadline=datetime.fromisoformat(data['deadline']) if data['deadline'] else None
        )
        goal.status = GoalStatus(data['status'])
        goal.progress = data['progress']
        goal.dependencies = data['dependencies']
        goal.metrics = data['metrics']
        goal.tags = data['tags']
        goal.subgoals = [Goal.from_dict(sg) for sg in data.get('subgoals', [])]
        return goal

class GoalManager:
    """Основной менеджер целей системы"""
    
    def __init__(self, storage_path: str = "data/runtime/goals.json"):
        self.storage_path = storage_path
        self.logger = logging.getLogger('goals.GoalManager')
        self.active_goals: Dict[str, Goal] = {}
        self.completed_goals: Dict[str, Goal] = {}
        self.goal_templates: Dict[str, Dict] = {}
        
        self._load_goal_library()
        self._load_goals()
    
    def _load_goal_library(self) -> None:
        """Загрузка библиотеки типовых целей"""
        try:
            # Загрузка персональных целей
            with open('modules/planning/goals/goal_library/personal_goals.goal', 'r', encoding='utf-8') as f:
                personal_data = json.load(f)
                self.goal_templates.update(personal_data.get('templates', {}))
            
            # Загрузка рабочих целей  
            with open('modules/planning/goals/goal_library/work_goals.goal', 'r', encoding='utf-8') as f:
                work_data = json.load(f)
                self.goal_templates.update(work_data.get('templates', {}))
            
            # Загрузка учебных целей
            with open('modules/planning/goals/goal_library/learning_goals.goal', 'r', encoding='utf-8') as f:
                learning_data = json.load(f)
                self.goal_templates.update(learning_data.get('templates', {}))
                
            self.logger.info(f"Загружено {len(self.goal_templates)} шаблонов целей")
            
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить библиотеку целей: {e}")
    
    def _load_goals(self) -> None:
        """Загрузка сохраненных целей"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.active_goals = {
                goal_id: Goal.from_dict(goal_data) 
                for goal_id, goal_data in data.get('active_goals', {}).items()
            }
            self.completed_goals = {
                goal_id: Goal.from_dict(goal_data)
                for goal_id, goal_data in data.get('completed_goals', {}).items()
            }
            
            self.logger.info(f"Загружено {len(self.active_goals)} активных и {len(self.completed_goals)} завершенных целей")
            
        except FileNotFoundError:
            self.logger.info("Файл целей не найден, создается новый")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки целей: {e}")
    
    def _save_goals(self) -> None:
        """Сохранение целей в файл"""
        try:
            data = {
                'active_goals': {goal_id: goal.to_dict() for goal_id, goal in self.active_goals.items()},
                'completed_goals': {goal_id: goal.to_dict() for goal_id, goal in self.completed_goals.items()}
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения целей: {e}")
    
    def create_goal(self, title: str, description: str, priority: GoalPriority = GoalPriority.MEDIUM,
                   deadline: Optional[datetime] = None, template_id: Optional[str] = None) -> Goal:
        """Создание новой цели"""
        
        goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Если указан шаблон, используем его
        if template_id and template_id in self.goal_templates:
            template = self.goal_templates[template_id]
            goal = Goal(
                goal_id=goal_id,
                title=template.get('title', title),
                description=template.get('description', description),
                priority=GoalPriority(template.get('priority', priority.value)),
                deadline=deadline
            )
            goal.tags = template.get('tags', [])
            goal.metrics = template.get('metrics', {})
        else:
            goal = Goal(goal_id, title, description, priority, deadline)
        
        goal.status = GoalStatus.ACTIVE
        self.active_goals[goal_id] = goal
        self._save_goals()
        
        self.logger.info(f"Создана новая цель: {title} (ID: {goal_id})")
        return goal
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Получение цели по ID"""
        return self.active_goals.get(goal_id) or self.completed_goals.get(goal_id)
    
    def update_goal_progress(self, goal_id: str, progress: float) -> bool:
        """Обновление прогресса цели"""
        goal = self.active_goals.get(goal_id)
        if not goal:
            self.logger.warning(f"Цель {goal_id} не найдена среди активных")
            return False
        
        goal.progress = max(0.0, min(1.0, progress))
        
        # Проверка завершения цели
        if goal.progress >= 1.0:
            goal.status = GoalStatus.COMPLETED
            self.completed_goals[goal_id] = goal
            del self.active_goals[goal_id]
            self.logger.info(f"Цель {goal.title} завершена!")
        
        self._save_goals()
        return True
    
    def cancel_goal(self, goal_id: str, reason: str = "") -> bool:
        """Отмена цели"""
        goal = self.active_goals.get(goal_id)
        if not goal:
            return False
        
        goal.status = GoalStatus.CANCELLED
        goal.metrics['cancellation_reason'] = reason
        self.completed_goals[goal_id] = goal
        del self.active_goals[goal_id]
        
        self._save_goals()
        self.logger.info(f"Цель {goal.title} отменена: {reason}")
        return True
    
    def get_active_goals(self) -> List[Goal]:
        """Получение списка активных целей"""
        return list(self.active_goals.values())
    
    def get_completed_goals(self) -> List[Goal]:
        """Получение списка завершенных целей"""
        return list(self.completed_goals.values())
    
    def get_goals_by_priority(self, priority: GoalPriority) -> List[Goal]:
        """Получение целей по приоритету"""
        return [goal for goal in self.active_goals.values() if goal.priority == priority]
    
    def add_subgoal(self, parent_goal_id: str, subgoal: Goal) -> bool:
        """Добавление подцели"""
        parent_goal = self.active_goals.get(parent_goal_id)
        if not parent_goal:
            return False
        
        parent_goal.subgoals.append(subgoal)
        self._save_goals()
        return True
    
    def get_goal_templates(self) -> Dict[str, Dict]:
        """Получение доступных шаблонов целей"""
        return self.goal_templates.copy()