"""
Движок дедуктивного мышления
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class Fact:
    statement: str
    confidence: float = 1.0
    source: str = "unknown"

class DeductionEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.facts: List[Fact] = []
        self.hypotheses = []
        self.inference_chain = []
        
    def add_fact(self, fact: Fact):
        """Добавить факт для дедукции"""
        self.facts.append(fact)
        self.logger.info(f"Добавлен факт: {fact.statement}")
        
    def create_hypothesis(self, hypothesis: str) -> str:
        """Создать гипотезу для проверки"""
        hyp_id = f"hyp_{len(self.hypotheses) + 1}"
        self.hypotheses.append({"id": hyp_id, "statement": hypothesis, "status": "pending"})
        return hyp_id
        
    def deductive_reasoning(self, target: str) -> Dict[str, Any]:
        """Дедуктивное рассуждение от общего к частному"""
        try:
            relevant_facts = [f for f in self.facts if any(word in target for word in f.statement.split())]
            
            if not relevant_facts:
                return {"conclusion": "Недостаточно данных для дедукции", "confidence": 0.0}
                
            # Построение цепочки рассуждений
            reasoning_chain = []
            current_target = target
            
            for fact in relevant_facts[:3]:  # Ограничиваем глубину
                reasoning_step = {
                    "premise": fact.statement,
                    "target": current_target,
                    "inference": f"Из '{fact.statement}' следует часть '{current_target}'"
                }
                reasoning_chain.append(reasoning_step)
                
            confidence = min(f.confidence for f in relevant_facts)
            
            return {
                "conclusion": f"На основе {len(relevant_facts)} фактов можно заключить: {target}",
                "confidence": confidence,
                "reasoning_chain": reasoning_chain,
                "facts_used": [f.statement for f in relevant_facts]
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка дедуктивного рассуждения: {e}")
            return {"error": str(e)}
            
    def syllogism(self, major_premise: str, minor_premise: str) -> Dict[str, Any]:
        """Силлогизм - классическая дедуктивная логика"""
        try:
            # Простой анализ силлогизма
            major_terms = major_premise.split()
            minor_terms = minor_premise.split()
            
            # Поиск общего термина
            common_terms = set(major_terms) & set(minor_terms)
            
            if common_terms:
                conclusion = f"На основе '{major_premise}' и '{minor_premise}' можно сделать вывод"
                return {
                    "type": "силлогизм",
                    "conclusion": conclusion,
                    "common_terms": list(common_terms),
                    "valid": True
                }
            else:
                return {
                    "type": "силлогизм", 
                    "conclusion": "Нельзя сделать валидный вывод",
                    "valid": False
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка в силлогизме: {e}")
            return {"error": str(e)}
            
    def eliminate_possibilities(self, possibilities: List[str], constraints: List[str]) -> List[str]:
        """Исключение возможностей на основе ограничений"""
        remaining = possibilities.copy()
        
        for constraint in constraints:
            remaining = [p for p in remaining if self._satisfies_constraint(p, constraint)]
            
        return remaining
        
    def _satisfies_constraint(self, possibility: str, constraint: str) -> bool:
        """Проверка удовлетворения ограничению"""
        # Простая проверка по ключевым словам
        constraint_words = set(constraint.lower().split())
        possibility_words = set(possibility.lower().split())
        
        # Если ограничение отрицательное
        if "не" in constraint_words:
            positive_constraint = constraint_words - {"не"}
            return not positive_constraint.issubset(possibility_words)
        else:
            return constraint_words.issubset(possibility_words)
            
    def get_deduction_report(self) -> Dict[str, Any]:
        """Получить отчет о дедуктивном процессе"""
        return {
            "total_facts": len(self.facts),
            "active_hypotheses": len([h for h in self.hypotheses if h["status"] == "pending"]),
            "reasoning_chain_length": len(self.inference_chain),
            "confidence_level": sum(f.confidence for f in self.facts) / len(self.facts) if self.facts else 0
        }