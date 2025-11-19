# planning/task_planner/step_optimizer.py
"""
Оптимизатор шагов выполнения
Оптимизирует последовательность и параметры шагов плана
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from .plan_generator import PlanStep, TaskPlan

@dataclass
class OptimizationResult:
    """Результат оптимизации"""
    original_plan: TaskPlan
    optimized_plan: TaskPlan
    improvements: Dict[str, float]
    optimization_log: List[str]

class StepOptimizer:
    """Оптимизатор последовательности шагов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.optimization_rules = self._load_optimization_rules()
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Загрузка правил оптимизации"""
        return {
            'parallel_execution': True,
            'resource_balancing': True,
            'critical_path_optimization': True,
            'dependency_resolution': True,
            'duration_optimization': True
        }
    
    def optimize_plan(self, plan: TaskPlan, constraints: Dict[str, Any] = None) -> OptimizationResult:
        """
        Оптимизация плана выполнения
        
        Args:
            plan: Исходный план
            constraints: Дополнительные ограничения
            
        Returns:
            OptimizationResult: Результат оптимизации
        """
        if constraints is None:
            constraints = {}
        
        optimization_log = []
        improvements = {}
        
        try:
            # Создаем копию плана для оптимизации
            optimized_plan = self._copy_plan(plan)
            
            # Применяем различные методы оптимизации
            if self.optimization_rules['dependency_resolution']:
                optimized_plan, dep_improvement = self._optimize_dependencies(optimized_plan)
                improvements['dependency_optimization'] = dep_improvement
                optimization_log.append("Оптимизированы зависимости между шагами")
            
            if self.optimization_rules['parallel_execution']:
                optimized_plan, parallel_improvement = self._optimize_parallel_execution(optimized_plan)
                improvements['parallel_execution'] = parallel_improvement
                optimization_log.append("Добавлено параллельное выполнение шагов")
            
            if self.optimization_rules['critical_path_optimization']:
                optimized_plan, critical_path_improvement = self._optimize_critical_path(optimized_plan)
                improvements['critical_path_optimization'] = critical_path_improvement
                optimization_log.append("Оптимизирован критический путь")
            
            if self.optimization_rules['duration_optimization']:
                optimized_plan, duration_improvement = self._optimize_durations(optimized_plan, constraints)
                improvements['duration_optimization'] = duration_improvement
                optimization_log.append("Оптимизированы длительности шагов")
            
            # Пересчитываем общую длительность
            optimized_plan.total_duration = self._calculate_total_duration(optimized_plan.steps)
            
            total_improvement = self._calculate_total_improvement(plan, optimized_plan)
            improvements['total_improvement'] = total_improvement
            
            self.logger.info(f"План оптимизирован. Улучшение: {total_improvement:.2f}%")
            
            return OptimizationResult(
                original_plan=plan,
                optimized_plan=optimized_plan,
                improvements=improvements,
                optimization_log=optimization_log
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка оптимизации плана: {e}")
            # Возвращаем исходный план в случае ошибки
            return OptimizationResult(
                original_plan=plan,
                optimized_plan=plan,
                improvements={'error': 0},
                optimization_log=[f"Ошибка оптимизации: {str(e)}"]
            )
    
    def _copy_plan(self, plan: TaskPlan) -> TaskPlan:
        """Создание копии плана"""
        copied_steps = []
        for step in plan.steps:
            copied_steps.append(PlanStep(
                action=step.action,
                parameters=step.parameters.copy(),
                duration=step.duration,
                dependencies=step.dependencies.copy(),
                resources=step.resources.copy(),
                priority=step.priority
            ))
        
        return TaskPlan(
            task_id=plan.task_id,
            goal=plan.goal,
            steps=copied_steps,
            total_duration=plan.total_duration,
            required_resources=plan.required_resources.copy(),
            constraints=plan.constraints.copy()
        )
    
    def _optimize_dependencies(self, plan: TaskPlan) -> tuple:
        """Оптимизация зависимостей между шагами"""
        original_duration = plan.total_duration
        
        # Анализ и упрощение зависимостей
        steps_dict = {step.action: step for step in plan.steps}
        
        for step in plan.steps:
            # Удаление избыточных зависимостей
            simplified_deps = self._simplify_dependencies(step.dependencies, steps_dict)
            step.dependencies = simplified_deps
        
        # Пересчет длительности после оптимизации зависимостей
        plan.total_duration = self._calculate_total_duration(plan.steps)
        return plan, self._calculate_improvement(original_duration, plan.total_duration)
    
    def _simplify_dependencies(self, dependencies: List[str], steps_dict: Dict) -> List[str]:
        """Упрощение списка зависимостей"""
        if not dependencies:
            return []
        
        # Удаление транзитивных зависимостей
        direct_dependencies = set(dependencies)
        
        for dep in dependencies:
            if dep in steps_dict:
                # Удаляем зависимости, которые уже включены через другие зависимости
                transitive_deps = set(steps_dict[dep].dependencies)
                direct_dependencies -= transitive_deps
        
        return list(direct_dependencies)
    
    def _optimize_parallel_execution(self, plan: TaskPlan) -> tuple:
        """Оптимизация параллельного выполнения"""
        original_duration = plan.total_duration
        
        # Группировка шагов по приоритету и ресурсам
        step_groups = self._group_steps_for_parallel(plan.steps)
        
        # Перераспределение шагов для параллельного выполнения
        optimized_steps = []
        for group in step_groups:
            # Для шагов в одной группе добавляем возможность параллельного выполнения
            for step in group:
                # Уменьшаем приоритет для шагов, которые могут выполняться параллельно
                if len(group) > 1:
                    step.priority = max(1, step.priority - 1)
                optimized_steps.append(step)
        
        plan.steps = optimized_steps
        # Пересчет длительности после оптимизации параллельного выполнения
        plan.total_duration = self._calculate_total_duration(plan.steps)
        return plan, self._calculate_improvement(original_duration, plan.total_duration)
    
    def _group_steps_for_parallel(self, steps: List[PlanStep]) -> List[List[PlanStep]]:
        """Группировка шагов для параллельного выполнения"""
        groups = []
        used_steps = set()
        
        for i, step in enumerate(steps):
            if i in used_steps:
                continue
                
            group = [step]
            used_steps.add(i)
            
            # Ищем шаги, которые могут выполняться параллельно
            for j, other_step in enumerate(steps[i+1:], i+1):
                if (j not in used_steps and 
                    not set(other_step.dependencies).intersection({s.action for s in group}) and
                    not set(other_step.resources).intersection({r for s in group for r in s.resources})):
                    
                    group.append(other_step)
                    used_steps.add(j)
            
            groups.append(group)
        
        return groups
    
    def _optimize_critical_path(self, plan: TaskPlan) -> tuple:
        """Оптимизация критического пути"""
        original_duration = plan.total_duration
        
        # Определение критического пути
        critical_path = self._find_critical_path(plan.steps)
        
        # Ускорение шагов на критическом пути
        for step in plan.steps:
            if step.action in critical_path:
                # Уменьшаем длительность критических шагов
                step.duration = max(1, int(step.duration * 0.8))  # Уменьшаем на 20%
        
        # Пересчет длительности после оптимизации критического пути
        plan.total_duration = self._calculate_total_duration(plan.steps)
        return plan, self._calculate_improvement(original_duration, plan.total_duration)
    
    def _find_critical_path(self, steps: List[PlanStep]) -> List[str]:
        """Поиск критического пути"""
        if not steps:
            return []
        
        # Простой алгоритм поиска самого длинного пути
        step_durations = {step.action: step.duration for step in steps}
        step_dependencies = {step.action: step.dependencies for step in steps}
        
        # Вычисляем полное время для каждого шага с учетом зависимостей
        total_times = {}
        
        def calculate_total_time(step_action):
            if step_action in total_times:
                return total_times[step_action]
            
            duration = step_durations[step_action]
            deps = step_dependencies[step_action]
            
            if not deps:
                total_times[step_action] = duration
            else:
                max_dep_time = max(calculate_total_time(dep) for dep in deps)
                total_times[step_action] = duration + max_dep_time
            
            return total_times[step_action]
        
        # Вычисляем для всех шагов
        for step in steps:
            calculate_total_time(step.action)
        
        # Находим шаг с максимальным общим временем
        max_step = max(total_times, key=total_times.get)
        
        # Восстанавливаем критический путь
        critical_path = [max_step]
        current_step = max_step
        
        while step_dependencies[current_step]:
            # Находим зависимость с максимальным временем
            next_step = max(step_dependencies[current_step], 
                          key=lambda x: total_times.get(x, 0))
            critical_path.append(next_step)
            current_step = next_step
        
        return critical_path[::-1]  # Возвращаем в правильном порядке
    
    def _optimize_durations(self, plan: TaskPlan, constraints: Dict[str, Any]) -> tuple:
        """Оптимизация длительностей шагов"""
        original_duration = plan.total_duration
        max_duration = constraints.get('max_duration')
        
        if not max_duration or plan.total_duration <= max_duration:
            return plan, 0
        
        # Необходимо уменьшить общее время
        reduction_needed = plan.total_duration - max_duration
        reduction_per_step = reduction_needed / len(plan.steps)
        
        for step in plan.steps:
            # Уменьшаем каждый шаг пропорционально
            new_duration = max(1, int(step.duration - reduction_per_step))
            step.duration = new_duration
        
        # Пересчет длительности после оптимизации длительностей
        plan.total_duration = self._calculate_total_duration(plan.steps)
        return plan, self._calculate_improvement(original_duration, plan.total_duration)
    
    def _calculate_total_duration(self, steps: List[PlanStep]) -> int:
        """Пересчет общей длительности с учетом зависимостей"""
        if not steps:
            return 0
        
        step_times = {}
        
        def get_step_end_time(step_action):
            if step_action in step_times:
                return step_times[step_action]
            
            step = next((s for s in steps if s.action == step_action), None)
            if not step:
                return 0
            
            if not step.dependencies:
                step_times[step_action] = step.duration
            else:
                max_dep_time = max(get_step_end_time(dep) for dep in step.dependencies)
                step_times[step_action] = step.duration + max_dep_time
            
            return step_times[step_action]
        
        # Находим максимальное время окончания
        max_time = 0
        for step in steps:
            end_time = get_step_end_time(step.action)
            max_time = max(max_time, end_time)
        
        return max_time
    
    def _calculate_improvement(self, original: float, optimized: float) -> float:
        """Расчет процента улучшения"""
        if original == 0:
            return 0
        return ((original - optimized) / original) * 100
    
    def _calculate_total_improvement(self, original_plan: TaskPlan, optimized_plan: TaskPlan) -> float:
        """Расчет общего улучшения"""
        return self._calculate_improvement(original_plan.total_duration, optimized_plan.total_duration)