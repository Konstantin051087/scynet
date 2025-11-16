"""
Модуль логического анализа - инициализация
"""
from .reasoning_engine import ReasoningEngine
from .puzzle_solver import PuzzleSolver
from .deduction_engine import DeductionEngine
from .inference_maker import InferenceMaker

__all__ = [
    'ReasoningEngine',
    'PuzzleSolver', 
    'DeductionEngine',
    'InferenceMaker'
]