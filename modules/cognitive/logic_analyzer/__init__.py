"""
Модуль логического анализа - инициализация
"""

import logging
from typing import Dict, Any, Optional, List, Union

from .reasoning_engine import ReasoningEngine
from .puzzle_solver import PuzzleSolver
from .deduction_engine import DeductionEngine
from .inference_maker import InferenceMaker

class LogicAnalyzerModule:
    """Основной класс модуля логического анализа"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.reasoning_engine = ReasoningEngine()
        self.puzzle_solver = PuzzleSolver()
        self.deduction_engine = DeductionEngine()
        self.inference_maker = InferenceMaker()
        
        self.initialized = False
    
    async def initialize(self):
        """Инициализация модуля"""
        try:
            # Инициализация компонентов (если потребуется асинхронная инициализация)
            self.initialized = True
            self.logger.info("LogicAnalyzerModule успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации LogicAnalyzerModule: {e}")
            self.initialized = False
    
    def analyze_problem(self, problem_statement: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Анализ логической проблемы
        
        Args:
            problem_statement: Формулировка проблемы
            context: Контекст анализа
            
        Returns:
            Dict: Результаты анализа
        """
        if not self.initialized:
            self.logger.warning("LogicAnalyzerModule не инициализирован, но используется")
        
        context = context or {}
        
        # Используем reasoning engine для общего анализа
        reasoning_result = self.reasoning_engine.analyze(problem_statement, context)
        
        # Если проблема похожа на головоломку, используем puzzle solver
        if self._is_puzzle_problem(problem_statement):
            puzzle_result = self.puzzle_solver.solve(problem_statement, context)
            reasoning_result['puzzle_solution'] = puzzle_result
        
        # Применяем дедуктивный метод
        deduction_result = self.deduction_engine.deduce(reasoning_result, context)
        reasoning_result['deductions'] = deduction_result
        
        # Формируем выводы
        inferences = self.inference_maker.make_inferences(reasoning_result, context)
        reasoning_result['inferences'] = inferences
        
        return reasoning_result
    
    def solve_puzzle(self, puzzle_description: str, puzzle_type: str = None) -> Dict[str, Any]:
        """
        Решение головоломки
        
        Args:
            puzzle_description: Описание головоломки
            puzzle_type: Тип головоломки (опционально)
            
        Returns:
            Dict: Решение головоломки
        """
        return self.puzzle_solver.solve(puzzle_description, {'puzzle_type': puzzle_type})
    
    def make_deductions(self, facts: List[str], rules: List[str] = None) -> List[str]:
        """
        Выполнение дедуктивных выводов
        
        Args:
            facts: Список фактов
            rules: Список правил (опционально)
            
        Returns:
            List: Дедуктивные выводы
        """
        return self.deduction_engine.deduce_from_facts(facts, rules or [])
    
    def generate_inferences(self, data: Dict[str, Any], constraints: Dict[str, Any] = None) -> List[str]:
        """
        Генерация умозаключений
        
        Args:
            data: Входные данные
            constraints: Ограничения (опционально)
            
        Returns:
            List: Сгенерированные умозаключения
        """
        return self.inference_maker.make_inferences(data, constraints or {})
    
    def _is_puzzle_problem(self, problem_statement: str) -> bool:
        """Определение, является ли проблема головоломкой"""
        puzzle_keywords = [
            'головоломка', 'загадка', 'ребус', 'кроссворд', 'судоку',
            'puzzle', 'riddle', 'задача со спичками', 'логическая задача'
        ]
        
        problem_lower = problem_statement.lower()
        return any(keyword in problem_lower for keyword in puzzle_keywords)
    
    def get_module_info(self) -> Dict[str, Any]:
        """Получение информации о модуле"""
        return {
            "name": "logic_analyzer",
            "version": "1.0",
            "description": "Модуль логического анализа и решения задач",
            "initialized": self.initialized,
            "components": {
                "reasoning_engine": True,
                "puzzle_solver": True,
                "deduction_engine": True,
                "inference_maker": True
            }
        }

# Экспортируем основной класс и все остальные
__all__ = [
    'LogicAnalyzerModule',
    'ReasoningEngine',
    'PuzzleSolver', 
    'DeductionEngine',
    'InferenceMaker'
]