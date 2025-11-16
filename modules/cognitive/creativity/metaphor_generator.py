"""
Генератор метафор и аналогий
"""

import random
import json
import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path

class MetaphorGenerator:
    """Генератор метафор, аналогий и образных сравнений"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.patterns_file = Path("modules/cognitive/creativity/creative_patterns/metaphor_patterns.creat")
        
        # Загрузка паттернов метафор
        self.metaphor_patterns = self._load_metaphor_patterns()
        self.concept_database = self._load_concept_database()
        
        self.logger.info("Генератор метафор инициализирован")
    
    def _load_metaphor_patterns(self) -> List[Dict[str, Any]]:
        """Загрузка паттернов метафор из файла"""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                return patterns.get('metaphor_patterns', [])
            else:
                # Стандартные паттерны
                return [
                    {"pattern": "{A} это как {B}", "weight": 0.3},
                    {"pattern": "{A} подобно {B} в том, что {C}", "weight": 0.25},
                    {"pattern": "Если бы {A} был {B}, то он бы {C}", "weight": 0.2},
                    {"pattern": "{A} — это {B} мира {C}", "weight": 0.15},
                    {"pattern": "Как {B} для {C}, так и {A} для {D}", "weight": 0.1}
                ]
        except Exception as e:
            self.logger.error(f"Ошибка загрузки паттернов метафор: {e}")
            return []
    
    def _load_concept_database(self) -> Dict[str, List[str]]:
        """База концепций для метафор"""
        return {
            "природа": ["ветер", "огонь", "вода", "земля", "дерево", "камень", "цветок", "птица"],
            "технологии": ["компьютер", "интернет", "робот", "искусственный интеллект", "алгоритм"],
            "эмоции": ["любовь", "радость", "грусть", "гнев", "надежда", "страх"],
            "общество": ["дружба", "семья", "работа", "общество", "культура", "традиция"],
            "абстрактные": ["время", "пространство", "мысль", "идея", "красота", "истина"]
        }
    
    def generate(self, concept: str, style: str = "поэтический", complexity: int = 2) -> Dict[str, Any]:
        """Генерация метафоры для заданного концепта"""
        
        try:
            # Анализ концепта
            concept_category = self._categorize_concept(concept)
            related_concepts = self._get_related_concepts(concept_category)
            
            # Выбор паттерна
            pattern = self._select_pattern()
            
            # Генерация метафоры
            metaphor = self._fill_pattern(pattern, concept, related_concepts, complexity)
            
            # Улучшение стиля
            metaphor = self._apply_style(metaphor, style)
            
            return {
                'content': metaphor,
                'type': 'metaphor',
                'concept': concept,
                'style': style,
                'complexity': complexity,
                'pattern_used': pattern
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации метафоры: {e}")
            return {
                'content': f"Метафора для '{concept}': как свежий взгляд на знакомые вещи",
                'type': 'metaphor',
                'error': str(e)
            }
    
    def _categorize_concept(self, concept: str) -> str:
        """Категоризация концепта"""
        concept_lower = concept.lower()
        
        for category, concepts in self.concept_database.items():
            if any(c in concept_lower for c in concepts):
                return category
        
        return "абстрактные"
    
    def _get_related_concepts(self, category: str) -> List[str]:
        """Получение связанных концептов"""
        return self.concept_database.get(category, self.concept_database["абстрактные"])
    
    def _select_pattern(self) -> str:
        """Выбор паттерна метафоры"""
        patterns = [p["pattern"] for p in self.metaphor_patterns]
        weights = [p["weight"] for p in self.metaphor_patterns]
        return random.choices(patterns, weights=weights)[0]
    
    def _fill_pattern(self, pattern: str, concept: str, related_concepts: List[str], complexity: int) -> str:
        """Заполнение паттерна конкретными концептами"""
        result = pattern
        
        # Замена плейсхолдеров
        if "{A}" in result:
            result = result.replace("{A}", concept)
        
        if "{B}" in result:
            result = result.replace("{B}", random.choice(related_concepts))
        
        if "{C}" in result and complexity >= 2:
            result = result.replace("{C}", random.choice(related_concepts))
        elif "{C}" in result:
            result = result.replace("{C}", "обладает схожими свойствами")
        
        if "{D}" in result and complexity >= 3:
            result = result.replace("{D}", random.choice(related_concepts))
        elif "{D}" in result:
            result = result.replace("{D}", "своего окружения")
        
        return result.capitalize()
    
    def _apply_style(self, metaphor: str, style: str) -> str:
        """Применение стилистических улучшений"""
        if style == "поэтический":
            poetic_enhancements = [" подобно ", " словно ", " точно ", " будто "]
            for enh in poetic_enhancements:
                if " как " in metaphor:
                    metaphor = metaphor.replace(" как ", random.choice(poetic_enhancements))
                    break
        
        elif style == "философский":
            if not metaphor.endswith("."):
                metaphor += ", что заставляет задуматься о сущности бытия."
        
        elif style == "юмористический":
            funny_endings = [" но только лучше!", " или примерно так.", " если присмотреться."]
            metaphor += random.choice(funny_endings)
        
        return metaphor