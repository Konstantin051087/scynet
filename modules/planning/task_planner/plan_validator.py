# planning/task_planner/plan_validator.py
"""
Валидатор планов на реализуемость
Проверка планов на корректность и выполнимость
"""

import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from .plan_generator import TaskPlan, PlanStep

@dataclass
class ValidationResult:
    """Результат валидации плана"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    validation_score: float

class PlanValidator:
    """Валидатор планов выполнения"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Загрузка правил валидации"""
        return {
            'check_dependencies': True,
            'validate_resources': True,
            'check_timing': True,
            'validate_parameters': True,
            'check_constraints': True,
            'verify_goal_alignment': True
        }
    
    def validate_plan(self, plan: TaskPlan, available_resources: Dict[str, Any] = None) -> ValidationResult:
        """
        Полная валидация плана
        
        Args:
            plan: План для валидации
            available_resources: Доступные ресурсы
            
        Returns:
            ValidationResult: Результат валидации
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Применяем различные проверки
            if self.validation_rules['check_dependencies']:
                dep_errors, dep_warnings = self._validate_dependencies(plan.steps)
                errors.extend(dep_errors)
                warnings.extend(dep_warnings)
            
            if self.validation_rules['validate_resources']:
                res_errors, res_warnings, res_suggestions = self._validate_resources(
                    plan, available_resources or {})
                errors.extend(res_errors)
                warnings.extend(res_warnings)
                suggestions.extend(res_suggestions)
            
            if self.validation_rules['check_timing']:
                time_errors, time_warnings = self._validate_timing(plan)
                errors.extend(time_errors)
                warnings.extend(time_warnings)
            
            if self.validation_rules['validate_parameters']:
                param_errors, param_warnings = self._validate_parameters(plan.steps)
                errors.extend(param_errors)
                warnings.extend(param_warnings)
            
            if self.validation_rules['check_constraints']:
                constraint_errors, constraint_warnings = self._validate_constraints(plan)
                errors.extend(constraint_errors)
                warnings.extend(constraint_warnings)
            
            if self.validation_rules['verify_goal_alignment']:
                goal_errors, goal_suggestions = self._validate_goal_alignment(plan)
                errors.extend(goal_errors)
                suggestions.extend(goal_suggestions)
            
            # Вычисляем общий score валидации
            validation_score = self._calculate_validation_score(len(errors), len(warnings), len(plan.steps))
            
            self.logger.info(f"Валидация плана {plan.task_id} завершена. Score: {validation_score:.2f}")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                validation_score=validation_score
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка во время валидации плана: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Критическая ошибка валидации: {str(e)}"],
                warnings=[],
                suggestions=[],
                validation_score=0.0
            )
    
    def _validate_dependencies(self, steps: List[PlanStep]) -> Tuple[List[str], List[str]]:
        """Валидация зависимостей между шагами"""
        errors = []
        warnings = []
        
        step_names = {step.action for step in steps}
        
        for step in steps:
            # Проверяем существование зависимостей
            for dependency in step.dependencies:
                if dependency not in step_names:
                    errors.append(f"Зависимость '{dependency}' для шага '{step.action}' не существует")
            
            # Проверяем циклические зависимости
            if self._has_cyclic_dependency(step, steps):
                errors.append(f"Обнаружена циклическая зависимость для шага '{step.action}'")
            
            # Проверяем избыточные зависимости
            redundant_deps = self._find_redundant_dependencies(step, steps)
            if redundant_deps:
                warnings.append(f"Избыточные зависимости для шага '{step.action}': {', '.join(redundant_deps)}")
        
        return errors, warnings
    
    def _has_cyclic_dependency(self, step: PlanStep, steps: List[PlanStep]) -> bool:
        """Проверка на циклические зависимости"""
        visited = set()
        
        def check_cycle(current_step_action, target_step_action):
            if current_step_action == target_step_action:
                return True
            
            if current_step_action in visited:
                return False
            
            visited.add(current_step_action)
            current_step = next((s for s in steps if s.action == current_step_action), None)
            
            if not current_step:
                return False
            
            for dep in current_step.dependencies:
                if check_cycle(dep, target_step_action):
                    return True
            
            return False
        
        for dependency in step.dependencies:
            if check_cycle(dependency, step.action):
                return True
        
        return False
    
    def _find_redundant_dependencies(self, step: PlanStep, steps: List[PlanStep]) -> List[str]:
        """Поиск избыточных зависимостей"""
        redundant = []
        step_dict = {s.action: s for s in steps}
        
        for dep1 in step.dependencies:
            for dep2 in step.dependencies:
                if dep1 != dep2 and dep1 in step_dict and dep2 in step_dict:
                    # Проверяем, является ли dep1 транзитивной зависимостью для dep2
                    if self._is_transitive_dependency(dep1, dep2, step_dict):
                        redundant.append(dep1)
        
        return list(set(redundant))
    
    def _is_transitive_dependency(self, dep1: str, dep2: str, step_dict: Dict) -> bool:
        """Проверка является ли зависимость транзитивной"""
        visited = set()
        
        def check_transitive(current):
            if current in visited:
                return False
            visited.add(current)
            
            if current not in step_dict:
                return False
            
            for next_dep in step_dict[current].dependencies:
                if next_dep == dep1:
                    return True
                if check_transitive(next_dep):
                    return True
            
            return False
        
        return check_transitive(dep2)
    
    def _validate_resources(self, plan: TaskPlan, available_resources: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
        """Валидация ресурсов"""
        errors = []
        warnings = []
        suggestions = []
        
        # Анализ требуемых ресурсов
        required_resources = {}
        for step in plan.steps:
            for resource in step.resources:
                resource_type = resource.split(':')[0] if ':' in resource else resource
                quantity = 1
                
                if ':' in resource:
                    try:
                        quantity = int(resource.split(':')[1])
                    except ValueError:
                        pass
                
                if resource_type in required_resources:
                    required_resources[resource_type] += quantity
                else:
                    required_resources[resource_type] = quantity
        
        # Проверка доступности ресурсов
        for resource_type, required_quantity in required_resources.items():
            available_quantity = available_resources.get(resource_type, 0)
            
            if available_quantity < required_quantity:
                errors.append(
                    f"Недостаточно ресурса '{resource_type}': "
                    f"требуется {required_quantity}, доступно {available_quantity}"
                )
            elif available_quantity > required_quantity * 1.5:
                suggestions.append(
                    f"Ресурс '{resource_type}' используется неэффективно: "
                    f"доступно {available_quantity}, требуется {required_quantity}"
                )
        
        # Проверка конфликтов ресурсов
        resource_conflicts = self._find_resource_conflicts(plan.steps)
        if resource_conflicts:
            warnings.append(f"Обнаружены потенциальные конфликты ресурсов: {', '.join(resource_conflicts)}")
        
        return errors, warnings, suggestions
    
    def _find_resource_conflicts(self, steps: List[PlanStep]) -> List[str]:
        """Поиск потенциальных конфликтов ресурсов"""
        conflicts = []
        resource_usage = {}
        
        for step in steps:
            for resource in step.resources:
                resource_type = resource.split(':')[0] if ':' in resource else resource
                
                if resource_type in resource_usage:
                    resource_usage[resource_type].append(step.action)
                else:
                    resource_usage[resource_type] = [step.action]
        
        for resource_type, using_steps in resource_usage.items():
            if len(using_steps) > 1:
                # Проверяем, могут ли шаги выполняться параллельно
                if not self._can_steps_run_parallel(using_steps, steps):
                    conflicts.append(f"{resource_type} (используется в: {', '.join(using_steps)})")
        
        return conflicts
    
    def _can_steps_run_parallel(self, step_names: List[str], steps: List[PlanStep]) -> bool:
        """Проверка возможности параллельного выполнения шагов"""
        step_dict = {step.action: step for step in steps}
        
        for i, step1_name in enumerate(step_names):
            step1 = step_dict[step1_name]
            for step2_name in step_names[i+1:]:
                step2 = step_dict[step2_name]
                
                # Если один шаг зависит от другого, они не могут выполняться параллельно
                if (step1_name in step2.dependencies or 
                    step2_name in step1.dependencies or
                    self._have_common_dependency(step1, step2, step_dict)):
                    return False
        
        return True
    
    def _have_common_dependency(self, step1: PlanStep, step2: PlanStep, step_dict: Dict) -> bool:
        """Проверка наличия общих зависимостей"""
        def get_all_dependencies(step_action):
            dependencies = set()
            visited = set()
            
            def collect_deps(current):
                if current in visited:
                    return
                visited.add(current)
                
                if current in step_dict:
                    for dep in step_dict[current].dependencies:
                        dependencies.add(dep)
                        collect_deps(dep)
            
            collect_deps(step_action)
            return dependencies
        
        deps1 = get_all_dependencies(step1.action)
        deps2 = get_all_dependencies(step2.action)
        
        return bool(deps1.intersection(deps2))
    
    def _validate_timing(self, plan: TaskPlan) -> Tuple[List[str], List[str]]:
        """Валидация временных параметров"""
        errors = []
        warnings = []
        
        # Проверка общей длительности
        if plan.total_duration <= 0:
            errors.append("Общая длительность плана должна быть положительной")
        
        # Проверка длительности отдельных шагов
        for step in plan.steps:
            if step.duration <= 0:
                errors.append(f"Шаг '{step.action}' имеет некорректную длительность: {step.duration}")
            elif step.duration > 480:  # 8 часов
                warnings.append(f"Шаг '{step.action}' имеет большую длительность: {step.duration} минут")
        
        # Проверка реалистичности временных оценок
        unrealistic_steps = self._find_unrealistic_timings(plan.steps)
        if unrealistic_steps:
            warnings.append(f"Возможно нереалистичные временные оценки для шагов: {', '.join(unrealistic_steps)}")
        
        return errors, warnings
    
    def _find_unrealistic_timings(self, steps: List[PlanStep]) -> List[str]:
        """Поиск шагов с возможно нереалистичными временными оценками"""
        unrealistic = []
        
        for step in steps:
            # Эвристики для определения нереалистичных временных оценок
            action_lower = step.action.lower()
            
            # Быстрые действия с большой длительностью
            if any(keyword in action_lower for keyword in ['проверка', 'анализ', 'подготовка']):
                if step.duration > 120:  # 2 часа
                    unrealistic.append(step.action)
            
            # Медленные действия с малой длительностью
            elif any(keyword in action_lower for keyword in ['обучение', 'изучение', 'разработка']):
                if step.duration < 30:  # 30 минут
                    unrealistic.append(step.action)
        
        return unrealistic
    
    def _validate_parameters(self, steps: List[PlanStep]) -> Tuple[List[str], List[str]]:
        """Валидация параметров шагов"""
        errors = []
        warnings = []
        
        required_parameters = {
            'cooking': ['ingredients', 'temperature', 'time'],
            'travel': ['destination', 'transport', 'accommodation'],
            'work': ['deadline', 'priority', 'resources'],
            'learning': ['topic', 'materials', 'duration']
        }
        
        for step in steps:
            # Проверка обязательных параметров для различных типов действий
            action_lower = step.action.lower()
            
            for domain, params in required_parameters.items():
                if any(domain_keyword in action_lower for domain_keyword in [domain, domain[:-1]]):
                    missing_params = [p for p in params if p not in step.parameters]
                    if missing_params:
                        warnings.append(
                            f"Шаг '{step.action}' может требовать параметры: {', '.join(missing_params)}"
                        )
            
            # Проверка корректности значений параметров
            param_errors = self._validate_parameter_values(step.parameters)
            errors.extend([f"Шаг '{step.action}': {error}" for error in param_errors])
        
        return errors, warnings
    
    def _validate_parameter_values(self, parameters: Dict[str, Any]) -> List[str]:
        """Валидация значений параметров"""
        errors = []
        
        for key, value in parameters.items():
            if value is None:
                errors.append(f"Параметр '{key}' имеет значение None")
            elif isinstance(value, str) and not value.strip():
                errors.append(f"Параметр '{key}' пустой")
            elif isinstance(value, (int, float)) and value < 0:
                errors.append(f"Параметр '{key}' имеет отрицательное значение: {value}")
        
        return errors
    
    def _validate_constraints(self, plan: TaskPlan) -> Tuple[List[str], List[str]]:
        """Валидация ограничений"""
        errors = []
        warnings = []
        
        # Проверка временных ограничений
        max_duration = plan.constraints.get('max_duration')
        if max_duration and plan.total_duration > max_duration:
            errors.append(
                f"План превышает максимальную длительность: {plan.total_duration} > {max_duration}"
            )
        
        # Проверка бюджетных ограничений
        max_cost = plan.constraints.get('max_cost')
        estimated_cost = plan.constraints.get('estimated_cost', 0)
        if max_cost and estimated_cost > max_cost:
            errors.append(
                f"План превышает бюджет: {estimated_cost} > {max_cost}"
            )
        
        # Проверка других ограничений
        for constraint_name, constraint_value in plan.constraints.items():
            if constraint_value is None:
                warnings.append(f"Ограничение '{constraint_name}' имеет значение None")
        
        return errors, warnings
    
    def _validate_goal_alignment(self, plan: TaskPlan) -> Tuple[List[str], List[str]]:
        """Проверка соответствия плана цели"""
        errors = []
        suggestions = []
        
        goal_lower = plan.goal.lower()
        step_actions = ' '.join(step.action.lower() for step in plan.steps)
        
        # Простая проверка ключевых слов
        goal_keywords = set(goal_lower.split())
        step_keywords = set(step_actions.split())
        
        missing_keywords = goal_keywords - step_keywords
        if missing_keywords:
            suggestions.append(
                f"В плане отсутствуют ключевые слова цели: {', '.join(missing_keywords)}"
            )
        
        # Проверка полноты плана
        if len(plan.steps) < 2:
            warnings.append("План содержит менее 2 шагов, возможно он неполный")
        
        # Проверка наличия заключительных шагов
        final_actions = ['проверка', 'завершение', 'отчет', 'результат']
        has_final_step = any(any(keyword in step.action.lower() for keyword in final_actions) 
                           for step in plan.steps[-2:])  # Проверяем последние 2 шага
        
        if not has_final_step:
            suggestions.append("Рекомендуется добавить завершающий шаг для проверки результатов")
        
        return errors, suggestions
    
    def _calculate_validation_score(self, error_count: int, warning_count: int, step_count: int) -> float:
        """Вычисление общего score валидации"""
        if step_count == 0:
            return 0.0
        
        base_score = 100.0
        
        # Штрафы за ошибки и предупреждения
        error_penalty = error_count * 10
        warning_penalty = warning_count * 2
        
        # Бонус за сложность плана
        complexity_bonus = min(step_count * 0.5, 10)
        
        final_score = base_score - error_penalty - warning_penalty + complexity_bonus
        return max(0.0, min(100.0, final_score))
    
    def generate_validation_report(self, validation_result: ValidationResult) -> str:
        """Генерация отчета о валидации"""
        report = []
        report.append("=" * 50)
        report.append("ОТЧЕТ О ВАЛИДАЦИИ ПЛАНА")
        report.append("=" * 50)
        
        report.append(f"Статус: {'ПРОЙДЕНА' if validation_result.is_valid else 'НЕ ПРОЙДЕНА'}")
        report.append(f"Score валидации: {validation_result.validation_score:.2f}/100")
        
        if validation_result.errors:
            report.append("\nОШИБКИ:")
            for error in validation_result.errors:
                report.append(f"  ❌ {error}")
        
        if validation_result.warnings:
            report.append("\nПРЕДУПРЕЖДЕНИЯ:")
            for warning in validation_result.warnings:
                report.append(f"  ⚠️  {warning}")
        
        if validation_result.suggestions:
            report.append("\nПРЕДЛОЖЕНИЯ:")
            for suggestion in validation_result.suggestions:
                report.append(f"  💡 {suggestion}")
        
        if not any([validation_result.errors, validation_result.warnings, validation_result.suggestions]):
            report.append("\nПлан прошел все проверки без замечаний! ✅")
        
        report.append("=" * 50)
        return "\n".join(report)