# planning/task_planner/resource_allocator.py
"""
Аллокатор ресурсов для задач
Распределение и управление ресурсами для выполнения плана
"""

import logging
from typing import Dict, List, Any, Set
from dataclasses import dataclass
from .plan_generator import PlanStep, TaskPlan

@dataclass
class ResourceAllocation:
    """Распределение ресурсов"""
    step_name: str
    resources: Dict[str, Any]
    allocation_time: int
    duration: int

@dataclass
class ResourcePool:
    """Пул доступных ресурсов"""
    available_resources: Dict[str, int]
    resource_properties: Dict[str, Dict[str, Any]]

class ResourceAllocator:
    """Аллокатор ресурсов для выполнения планов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.resource_pool = ResourcePool({}, {})
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.resource_usage_timeline: Dict[int, Dict[str, int]] = {}
    
    def initialize_resource_pool(self, resources_config: Dict[str, Any]):
        """
        Инициализация пула ресурсов
        
        Args:
            resources_config: Конфигурация ресурсов
        """
        try:
            self.resource_pool.available_resources = resources_config.get('available_resources', {})
            self.resource_pool.resource_properties = resources_config.get('resource_properties', {})
            self.logger.info("Пул ресурсов инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации пула ресурсов: {e}")
    
    def allocate_resources_for_plan(self, plan: TaskPlan, start_time: int = 0) -> Dict[str, ResourceAllocation]:
        """
        Распределение ресурсов для всего плана
        
        Args:
            plan: План задачи
            start_time: Время начала выполнения
            
        Returns:
            Dict: Распределения ресурсов по шагам
        """
        try:
            self.allocations = {}
            self.resource_usage_timeline = {}
            
            # Сортируем шаги по приоритету и зависимостям
            sorted_steps = self._sort_steps_by_dependencies(plan.steps)
            
            current_time = start_time
            
            for step in sorted_steps:
                # Выделяем ресурсы для шага
                allocation = self._allocate_step_resources(step, current_time)
                
                if allocation:
                    self.allocations[step.action] = allocation
                    
                    # Обновляем временную шкалу использования ресурсов
                    self._update_resource_timeline(allocation)
                    
                    # Увеличиваем время для следующего шага
                    current_time = self._get_next_available_time(current_time, step)
                else:
                    self.logger.warning(f"Не удалось выделить ресурсы для шага: {step.action}")
            
            self.logger.info(f"Ресурсы распределены для плана {plan.task_id}")
            return self.allocations
            
        except Exception as e:
            self.logger.error(f"Ошибка распределения ресурсов: {e}")
            return {}
    
    def _sort_steps_by_dependencies(self, steps: List[PlanStep]) -> List[PlanStep]:
        """Сортировка шагов по зависимостям"""
        step_dict = {step.action: step for step in steps}
        visited = set()
        sorted_steps = []
        
        def visit(step_action):
            if step_action in visited:
                return
            visited.add(step_action)
            
            step = step_dict[step_action]
            for dependency in step.dependencies:
                visit(dependency)
            
            sorted_steps.append(step)
        
        # Начинаем с шагов без зависимостей
        independent_steps = [step for step in steps if not step.dependencies]
        for step in independent_steps:
            visit(step.action)
        
        # Добавляем оставшиеся шаги
        for step in steps:
            if step not in sorted_steps:
                visit(step.action)
        
        return sorted_steps
    
    def _allocate_step_resources(self, step: PlanStep, start_time: int) -> ResourceAllocation:
        """Выделение ресурсов для конкретного шага"""
        try:
            allocated_resources = {}
            
            for resource in step.resources:
                resource_type = resource.split(':')[0] if ':' in resource else resource
                resource_quantity = 1
                
                # Парсим количество ресурса если указано
                if ':' in resource:
                    try:
                        resource_quantity = int(resource.split(':')[1])
                    except ValueError:
                        resource_quantity = 1
                
                # Проверяем доступность ресурса
                if self._is_resource_available(resource_type, resource_quantity, start_time, step.duration):
                    allocated_resources[resource_type] = {
                        'quantity': resource_quantity,
                        'duration': step.duration,
                        'properties': self.resource_pool.resource_properties.get(resource_type, {})
                    }
                else:
                    self.logger.warning(f"Ресурс {resource_type} недоступен для шага {step.action}")
                    return None
            
            return ResourceAllocation(
                step_name=step.action,
                resources=allocated_resources,
                allocation_time=start_time,
                duration=step.duration
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка выделения ресурсов для шага {step.action}: {e}")
            return None
    
    def _is_resource_available(self, resource_type: str, quantity: int, 
                             start_time: int, duration: int) -> bool:
        """Проверка доступности ресурса в указанный период"""
        available_quantity = self.resource_pool.available_resources.get(resource_type, 0)
        
        # Проверяем использование ресурса в указанный период
        for time_point in range(start_time, start_time + duration):
            current_usage = self.resource_usage_timeline.get(time_point, {}).get(resource_type, 0)
            if current_usage + quantity > available_quantity:
                return False
        
        return True
    
    def _update_resource_timeline(self, allocation: ResourceAllocation):
        """Обновление временной шкалы использования ресурсов"""
        for resource_type, resource_info in allocation.resources.items():
            quantity = resource_info['quantity']
            
            for time_point in range(allocation.allocation_time, 
                                 allocation.allocation_time + allocation.duration):
                
                if time_point not in self.resource_usage_timeline:
                    self.resource_usage_timeline[time_point] = {}
                
                current_usage = self.resource_usage_timeline[time_point].get(resource_type, 0)
                self.resource_usage_timeline[time_point][resource_type] = current_usage + quantity
    
    def _get_next_available_time(self, current_time: int, step: PlanStep) -> int:
        """Получение следующего доступного времени с учетом зависимостей"""
        # Учитываем длительность текущего шага
        next_time = current_time + step.duration
        
        # Учитываем приоритет - высокоприоритетные задачи могут "прерывать"
        if step.priority >= 3:  # Высокий приоритет
            return next_time
        else:
            # Для низкоприоритетных задач добавляем буфер
            return next_time + 5
    
    def get_resource_utilization(self) -> Dict[str, float]:
        """Получение статистики использования ресурсов"""
        utilization = {}
        total_time_slots = len(self.resource_usage_timeline)
        
        if total_time_slots == 0:
            return {}
        
        for resource_type, available_quantity in self.resource_pool.available_resources.items():
            total_usage = 0
            
            for time_slot in self.resource_usage_timeline.values():
                usage = time_slot.get(resource_type, 0)
                total_usage += usage
            
            avg_usage = total_usage / total_time_slots if total_time_slots > 0 else 0
            utilization[resource_type] = (avg_usage / available_quantity) * 100 if available_quantity > 0 else 0
        
        return utilization
    
    def suggest_resource_optimization(self, plan: TaskPlan) -> Dict[str, Any]:
        """
        Предложение по оптимизации использования ресурсов
        
        Args:
            plan: Анализируемый план
            
        Returns:
            Dict: Предложения по оптимизации
        """
        suggestions = {
            'resource_bottlenecks': [],
            'underutilized_resources': [],
            'scheduling_improvements': [],
            'resource_substitutions': []
        }
        
        # Анализ узких мест
        utilization = self.get_resource_utilization()
        for resource, util_rate in utilization.items():
            if util_rate > 80:
                suggestions['resource_bottlenecks'].append({
                    'resource': resource,
                    'utilization': util_rate,
                    'suggestion': f"Увеличить количество ресурса {resource} или оптимизировать его использование"
                })
            elif util_rate < 20:
                suggestions['underutilized_resources'].append({
                    'resource': resource,
                    'utilization': util_rate,
                    'suggestion': f"Рассмотреть возможность уменьшения количества ресурса {resource}"
                })
        
        # Анализ расписания
        max_concurrent_usage = self._analyze_concurrent_usage()
        for resource, max_usage in max_concurrent_usage.items():
            available = self.resource_pool.available_resources.get(resource, 0)
            if max_usage == available:
                suggestions['scheduling_improvements'].append(
                    f"Ресурс {resource} используется на 100% в пиковые моменты. "
                    "Рассмотреть перераспределение нагрузки."
                )
        
        return suggestions
    
    def _analyze_concurrent_usage(self) -> Dict[str, int]:
        """Анализ максимального одновременного использования ресурсов"""
        max_usage = {}
        
        for time_slot in self.resource_usage_timeline.values():
            for resource_type, usage in time_slot.items():
                current_max = max_usage.get(resource_type, 0)
                if usage > current_max:
                    max_usage[resource_type] = usage
        
        return max_usage
    
    def release_resources(self, step_name: str):
        """Освобождение ресурсов, выделенных для шага"""
        if step_name in self.allocations:
            allocation = self.allocations[step_name]
            
            # Удаляем использование из временной шкалы
            for time_point in range(allocation.allocation_time, 
                                 allocation.allocation_time + allocation.duration):
                
                if time_point in self.resource_usage_timeline:
                    for resource_type in allocation.resources.keys():
                        if resource_type in self.resource_usage_timeline[time_point]:
                            del self.resource_usage_timeline[time_point][resource_type]
                    
                    # Удаляем пустой временной слот
                    if not self.resource_usage_timeline[time_point]:
                        del self.resource_usage_timeline[time_point]
            
            del self.allocations[step_name]
            self.logger.info(f"Ресурсы освобождены для шага: {step_name}")