"""
Движок логического вывода
"""
import logging
from typing import Dict, List, Any, Optional
import sympy
from sympy import symbols, And, Or, Not, Implies, Equivalent

class ReasoningEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.knowledge_base = {}
        self.rules = []
        
    def add_fact(self, fact: str, value: bool = True):
        """Добавить факт в базу знаний"""
        self.knowledge_base[fact] = value
        self.logger.info(f"Добавлен факт: {fact} = {value}")
        
    def add_rule(self, premise: str, conclusion: str):
        """Добавить правило вывода"""
        rule = {"premise": premise, "conclusion": conclusion}
        self.rules.append(rule)
        self.logger.info(f"Добавлено правило: ЕСЛИ {premise} ТО {conclusion}")
        
    def logical_inference(self, query: str) -> Optional[bool]:
        """Логический вывод на основе базы знаний"""
        try:
            # Простой вывод через прямую цепочку
            if query in self.knowledge_base:
                return self.knowledge_base[query]
                
            # Применение правил
            for rule in self.rules:
                if self.evaluate_expression(rule["premise"]):
                    self.knowledge_base[rule["conclusion"]] = True
                    if rule["conclusion"] == query:
                        return True
                        
            return None
        except Exception as e:
            self.logger.error(f"Ошибка логического вывода: {e}")
            return None
            
    def evaluate_expression(self, expression: str) -> bool:
        """Оценка логического выражения"""
        try:
            # Простая замена фактов на их значения
            for fact, value in self.knowledge_base.items():
                expression = expression.replace(fact, str(value))
                
            # Безопасное вычисление
            return eval(expression, {"__builtins__": {}}, {})
        except:
            return False
            
    def symbolic_reasoning(self, premises: List[str], conclusion: str) -> bool:
        """Символьное логическое рассуждение"""
        try:
            # Создание символьных переменных
            vars_dict = {}
            for premise in premises:
                for word in premise.split():
                    if word.isalpha() and len(word) > 1:
                        vars_dict[word] = symbols(word)
                        
            # Построение логических выражений
            premise_expr = And(*[eval(p, vars_dict) for p in premises])
            conclusion_expr = eval(conclusion, vars_dict)
            
            # Проверка логического следования
            return sympy.Implies(premise_expr, conclusion_expr).is_tautology()
            
        except Exception as e:
            self.logger.error(f"Ошибка символьного рассуждения: {e}")
            return False
            
    def clear_knowledge_base(self):
        """Очистка базы знаний"""
        self.knowledge_base.clear()
        self.rules.clear()
        self.logger.info("База знаний очищена")