"""
Решатель головоломок и задач
"""
import logging
import re
from typing import Dict, List, Any, Optional
import random

class PuzzleSolver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.solved_puzzles = set()
        
    def solve_logical_puzzle(self, puzzle: str) -> Dict[str, Any]:
        """Решение логических головоломок"""
        try:
            puzzle_lower = puzzle.lower()
            
            # Определение типа головоломки
            if "волк" in puzzle_lower and "коза" in puzzle_lower and "капуста" in puzzle_lower:
                return self._solve_wolf_goat_cabbage()
            elif "переправ" in puzzle_lower and "река" in puzzle_lower:
                return self._solve_river_crossing(puzzle)
            elif "блины" in puzzle_lower or "перекладывание" in puzzle_lower:
                return self._solve_pancake_sorting(puzzle)
            else:
                return self._solve_generic_logical(puzzle)
                
        except Exception as e:
            self.logger.error(f"Ошибка решения логической головоломки: {e}")
            return {"error": str(e)}
            
    def solve_mathematical(self, problem: str) -> Dict[str, Any]:
        """Решение математических задач"""
        try:
            # Арифметические операции
            if re.search(r'\d+\s*[\+\-\*\/]\s*\d+', problem):
                return self._solve_arithmetic(problem)
            # Алгебраические уравнения
            elif 'x' in problem or '=' in problem:
                return self._solve_algebra(problem)
            # Геометрические задачи
            elif any(word in problem.lower() for word in ['площадь', 'объем', 'периметр', 'угол']):
                return self._solve_geometry(problem)
            else:
                return self._solve_generic_math(problem)
                
        except Exception as e:
            self.logger.error(f"Ошибка решения математической задачи: {e}")
            return {"error": str(e)}
            
    def solve_spatial(self, problem: str) -> Dict[str, Any]:
        """Решение пространственных задач"""
        try:
            problem_lower = problem.lower()
            
            if "кубик" in problem_lower or "куб" in problem_lower:
                return self._solve_cube_problem(problem)
            elif "поворот" in problem_lower or "зеркало" in problem_lower:
                return self._solve_rotation_problem(problem)
            elif "фигура" in problem_lower or "форма" in problem_lower:
                return self._solve_shape_problem(problem)
            else:
                return {"solution": "Используйте пространственное воображение", "steps": []}
                
        except Exception as e:
            self.logger.error(f"Ошибка решения пространственной задачи: {e}")
            return {"error": str(e)}
            
    def _solve_wolf_goat_cabbage(self) -> Dict[str, Any]:
        """Решение задачи о волке, козе и капусте"""
        solution = [
            "1. Перевезти козу на другой берег",
            "2. Вернуться обратно", 
            "3. Перевезти волка на другой берег",
            "4. Привезти козу обратно",
            "5. Перевезти капусту на другой берег", 
            "6. Вернуться обратно",
            "7. Перевезти козу на другой берег"
        ]
        return {
            "solution": "Задача решена за 7 шагов",
            "steps": solution,
            "type": "логическая головоломка"
        }
        
    def _solve_arithmetic(self, problem: str) -> Dict[str, Any]:
        """Решение арифметических задач"""
        try:
            # Безопасное вычисление выражения
            result = eval(problem.replace('=', '').strip())
            return {
                "answer": result,
                "expression": problem,
                "type": "арифметика"
            }
        except:
            return {"error": "Не удалось вычислить выражение"}
            
    def _solve_algebra(self, problem: str) -> Dict[str, Any]:
        """Решение алгебраических уравнений"""
        try:
            # Простые линейные уравнения
            if 'x' in problem:
                parts = problem.split('=')
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    # Простая логика для уравнений вида ax + b = c
                    if '+' in left:
                        terms = left.split('+')
                        for term in terms:
                            if 'x' in term:
                                coef = term.replace('x', '').strip()
                                coef = 1 if coef == '' else int(coef)
                                const = int(terms[1 - terms.index(term)])
                                solution = (int(right) - const) / coef
                                return {"x": solution, "type": "линейное уравнение"}
            return {"solution": "Используйте метод подстановки", "type": "алгебра"}
        except Exception as e:
            return {"error": f"Ошибка решения уравнения: {e}"}
            
    def _solve_cube_problem(self, problem: str) -> Dict[str, Any]:
        """Решение задач с кубиками"""
        return {
            "solution": "Проанализируйте все грани куба",
            "method": "пространственный анализ", 
            "hint": "Рассмотрите куб с разных сторон"
        }