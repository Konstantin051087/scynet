"""
Создатель умозаключений
"""
import logging
from typing import Dict, List, Any, Optional
from enum import Enum

class InferenceType(Enum):
    DEDUCTIVE = "дедуктивное"
    INDUCTIVE = "индуктивное" 
    ABDUCTIVE = "абдуктивное"
    DEFAULT = "умозаключение по умолчанию"

class InferenceMaker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.inference_history = []
        
    def make_inference(self, premises: List[str], inference_type: InferenceType = InferenceType.DEDUCTIVE) -> Dict[str, Any]:
        """Создание умозаключения на основе посылок"""
        try:
            if not premises:
                return {"error": "Нет посылок для умозаключения"}
                
            if inference_type == InferenceType.DEDUCTIVE:
                return self._deductive_inference(premises)
            elif inference_type == InferenceType.INDUCTIVE:
                return self._inductive_inference(premises)
            elif inference_type == InferenceType.ABDUCTIVE:
                return self._abductive_inference(premises)
            else:
                return self._default_inference(premises)
                
        except Exception as e:
            self.logger.error(f"Ошибка создания умозаключения: {e}")
            return {"error": str(e)}
            
    def _deductive_inference(self, premises: List[str]) -> Dict[str, Any]:
        """Дедуктивное умозаключение"""
        # Анализ общих терминов
        all_words = []
        for premise in premises:
            all_words.extend(premise.split())
            
        common_words = [word for word in set(all_words) if all_words.count(word) > 1 and len(word) > 2]
        
        conclusion = f"На основе {len(premises)} посылок можно сделать дедуктивный вывод"
        
        result = {
            "type": "дедуктивное",
            "conclusion": conclusion,
            "premises_count": len(premises),
            "common_terms": common_words,
            "certainty": "высокая"
        }
        
        self._save_inference(result)
        return result
        
    def _inductive_inference(self, premises: List[str]) -> Dict[str, Any]:
        """Индуктивное умозаключение"""
        # Поиск закономерностей
        patterns = self._find_patterns(premises)
        
        conclusion = f"На основе {len(premises)} примеров можно сделать индуктивное обобщение"
        
        result = {
            "type": "индуктивное", 
            "conclusion": conclusion,
            "patterns_found": patterns,
            "certainty": "средняя",
            "generalization": f"Вероятно, это закономерность из {len(premises)} случаев"
        }
        
        self._save_inference(result)
        return result
        
    def _abductive_inference(self, premises: List[str]) -> Dict[str, Any]:
        """Абдуктивное умозаключение (нахождение наилучшего объяснения)"""
        observations = premises
        possible_explanations = self._generate_explanations(observations)
        
        best_explanation = self._select_best_explanation(possible_explanations, observations)
        
        result = {
            "type": "абдуктивное",
            "observations": observations,
            "possible_explanations": possible_explanations,
            "best_explanation": best_explanation,
            "certainty": "низкая",
            "conclusion": f"Наиболее вероятное объяснение: {best_explanation}"
        }
        
        self._save_inference(result)
        return result
        
    def _default_inference(self, premises: List[str]) -> Dict[str, Any]:
        """Умозаключение по умолчанию"""
        return {
            "type": "по умолчанию",
            "conclusion": f"На основе {len(premises)} посылок сделан общий вывод",
            "premises": premises,
            "certainty": "неопределенная"
        }
        
    def _find_patterns(self, premises: List[str]) -> List[str]:
        """Поиск паттернов в посылках"""
        patterns = []
        
        # Поиск повторяющихся слов
        word_counts = {}
        for premise in premises:
            for word in premise.split():
                if len(word) > 3:  # Игнорируем короткие слова
                    word_counts[word] = word_counts.get(word, 0) + 1
                    
        common_words = [word for word, count in word_counts.items() if count > len(premises) * 0.5]
        if common_words:
            patterns.append(f"Общие термины: {', '.join(common_words)}")
            
        # Поиск структурных паттернов
        if all('если' in p.lower() for p in premises):
            patterns.append("Условные конструкции")
            
        return patterns
        
    def _generate_explanations(self, observations: List[str]) -> List[str]:
        """Генерация возможных объяснений"""
        explanations = []
        
        for obs in observations[:3]:  # Ограничиваем количество
            explanation = f"Это может быть связано с {obs.split()[0] if obs.split() else 'неизвестным фактором'}"
            explanations.append(explanation)
            
        # Добавляем общие объяснения
        explanations.append("Возможно, это случайное совпадение")
        explanations.append("Вероятно, существует скрытая закономерность")
        
        return explanations
        
    def _select_best_explanation(self, explanations: List[str], observations: List[str]) -> str:
        """Выбор наилучшего объяснения"""
        # Простая эвристика: выбираем самое конкретное объяснение
        if explanations:
            return max(explanations, key=len)  # Самый длинный текст
        return "Недостаточно данных для выбора объяснения"
        
    def _save_inference(self, inference: Dict[str, Any]):
        """Сохранение умозаключения в историю"""
        inference_record = {
            "timestamp": self._get_timestamp(),
            "inference": inference
        }
        self.inference_history.append(inference_record)
        
    def _get_timestamp(self) -> str:
        """Получить временную метку"""
        from datetime import datetime
        return datetime.now().isoformat()
        
    def get_inference_statistics(self) -> Dict[str, Any]:
        """Получить статистику умозаключений"""
        type_counts = {}
        for record in self.inference_history:
            inf_type = record["inference"].get("type", "unknown")
            type_counts[inf_type] = type_counts.get(inf_type, 0) + 1
            
        return {
            "total_inferences": len(self.inference_history),
            "type_distribution": type_counts,
            "success_rate": len([r for r in self.inference_history if "error" not in r["inference"]]) / len(self.inference_history) if self.inference_history else 0
        }