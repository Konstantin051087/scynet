"""
Генератор шуток и юмора
"""

import random
import json
import logging
from typing import Dict, Any, List
from pathlib import Path

class JokeEngine:
    """Движок генерации шуток и юмористического контента"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.patterns_file = Path("modules/cognitive/creativity/creative_patterns/joke_patterns.creat")
        
        # Загрузка паттернов шуток
        self.joke_patterns = self._load_joke_patterns()
        self.joke_templates = self._load_joke_templates()
        self.punchline_database = self._load_punchline_database()
        
        self.humor_style = config.get('humor_style', 'универсальный')
        self.complexity_level = config.get('complexity_level', 2)
        
        self.logger.info("Генератор шуток инициализирован")
    
    def _load_joke_patterns(self) -> List[Dict[str, Any]]:
        """Загрузка паттернов шуток"""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                return patterns.get('joke_patterns', [])
            else:
                return self._get_default_patterns()
        except Exception as e:
            self.logger.error(f"Ошибка загрузки паттернов шуток: {e}")
            return self._get_default_patterns()
    
    def _get_default_patterns(self) -> List[Dict[str, Any]]:
        """Стандартные паттерны шуток"""
        return [
            {
                "type": "вопрос_ответ",
                "pattern": "Что будет, если {A}? — {B}!",
                "weight": 0.25
            },
            {
                "type": "сравнение", 
                "pattern": "{A} как {B}: {C}",
                "weight": 0.2
            },
            {
                "type": "анекдот",
                "pattern": "Идет {A} по улице, а навстречу {B}. Говорит {A}: '{C}'",
                "weight": 0.15
            },
            {
                "type": "каламбур",
                "pattern": "{A} — это когда {B}",
                "weight": 0.15
            },
            {
                "type": "абсурд",
                "pattern": "Почему {A}? Потому что {B}!",
                "weight": 0.1
            },
            {
                "type": "наблюдение",
                "pattern": "Заметил, что {A}? Вот и {B} тоже.",
                "weight": 0.1
            },
            {
                "type": "ирония", 
                "pattern": "Люблю, когда {A}. Особенно, когда {B}.",
                "weight": 0.05
            }
        ]
    
    def _load_joke_templates(self) -> Dict[str, List[str]]:
        """Шаблоны для различных типов шуток"""
        return {
            "животные": ["кошка", "собака", "хомяк", "попугай", "бегемот", "енот"],
            "профессии": ["программист", "врач", "учитель", "инженер", "бухгалтер"],
            "еда": ["помидор", "огурец", "пицца", "суп", "бутерброд", "кофе"],
            "технологии": ["компьютер", "смартфон", "интернет", "гаджет", "приложение"],
            "погода": ["дождь", "солнце", "снег", "ветер", "туман"]
        }
    
    def _load_punchline_database(self) -> Dict[str, List[str]]:
        """База данных кульминаций шуток"""
        return {
            "неожиданные": [
                "оказалось, это был не он",
                "а он и не знал, что так можно",
                "вот так сюрприз!",
                "ожидали? а я нет!",
                "сюжетный поворот"
            ],
            "смешные": [
                "и все засмеялись",
                "юмор ситуации был очевиден",
                "смех до слез",
                "шутка удалась",
                "комичный исход"
            ],
            "абсурдные": [
                "потому что марсиане так велели",
                "оказалось, это были инопланетяне",
                "таковы правила квантовой физики",
                "так решил вселенский разум"
            ]
        }
    
    def generate(self, topic: str = None, joke_type: str = "авто", style: str = None) -> Dict[str, Any]:
        """Генерация шутки на заданную тему"""
        
        try:
            if not topic:
                topic = self._select_random_topic()
            
            if joke_type == "авто":
                joke_type = self._select_joke_type()
            
            if not style:
                style = self.humor_style
            
            # Генерация шутки
            joke_content = self._create_joke(topic, joke_type, style)
            
            # Оценка качества шутки
            quality_score = self._evaluate_joke_quality(joke_content, joke_type)
            
            return {
                'content': joke_content,
                'type': 'joke',
                'topic': topic,
                'joke_type': joke_type,
                'style': style,
                'quality_score': quality_score,
                'length': len(joke_content)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации шутки: {e}")
            return {
                'content': "Почему программисты любят природу? Потому что в ней нет багов!",
                'type': 'joke',
                'error': str(e)
            }
    
    def _select_random_topic(self) -> str:
        """Выбор случайной темы"""
        all_topics = []
        for category, topics in self.joke_templates.items():
            all_topics.extend(topics)
        return random.choice(all_topics)
    
    def _select_joke_type(self) -> str:
        """Выбор типа шутки"""
        types = [p["type"] for p in self.joke_patterns]
        weights = [p["weight"] for p in self.joke_patterns]
        return random.choices(types, weights=weights)[0]
    
    def _create_joke(self, topic: str, joke_type: str, style: str) -> str:
        """Создание шутки по выбранному типу"""
        pattern = next((p for p in self.joke_patterns if p["type"] == joke_type), None)
        
        if not pattern:
            pattern = self.joke_patterns[0]
        
        joke_template = pattern["pattern"]
        
        # Заполнение шаблона
        filled_joke = self._fill_joke_template(joke_template, topic, style)
        
        # Применение стиля
        styled_joke = self._apply_humor_style(filled_joke, style)
        
        return styled_joke
    
    def _fill_joke_template(self, template: str, topic: str, style: str) -> str:
        """Заполнение шаблона шутки"""
        result = template
        
        # Замена плейсхолдеров
        placeholders = ["{A}", "{B}", "{C}"]
        
        for placeholder in placeholders:
            if placeholder in result:
                if placeholder == "{A}":
                    replacement = topic
                elif placeholder == "{B}":
                    replacement = self._generate_punchline(style)
                else:  # {C}
                    replacement = self._generate_additional_element()
                
                result = result.replace(placeholder, replacement)
        
        return result
    
    def _generate_punchline(self, style: str) -> str:
        """Генерация кульминации шутки"""
        if style == "абсурдный":
            punchlines = self.punchline_database["абсурдные"]
        elif style == "неожиданный":
            punchlines = self.punchline_database["неожиданные"]
        else:
            punchlines = self.punchline_database["смешные"]
        
        return random.choice(punchlines)
    
    def _generate_additional_element(self) -> str:
        """Генерация дополнительного элемента шутки"""
        elements = [
            "и тут началось самое интересное",
            "а вы как думали?",
            "вот так история",
            "невероятно, но факт",
            "и все из-за этого"
        ]
        return random.choice(elements)
    
    def _apply_humor_style(self, joke: str, style: str) -> str:
        """Применение юмористического стиля"""
        if style == "ироничный" and not joke.endswith("."):
            joke += " Ирония судьбы."
        elif style == "сатиричный" and not joke.endswith("."):
            joke += " Вот такая сатира."
        
        return joke
    
    def _evaluate_joke_quality(self, joke: str, joke_type: str) -> float:
        """Оценка качества шутки"""
        base_score = 0.5
        
        # Бонусы за длину
        if 20 <= len(joke) <= 100:
            base_score += 0.2
        
        # Бонусы за тип шутки
        if joke_type in ["вопрос_ответ", "каламбур"]:
            base_score += 0.1
        
        # Бонус за наличие ключевых слов
        funny_words = ["смех", "юмор", "шутка", "забавно", "прикол"]
        if any(word in joke.lower() for word in funny_words):
            base_score += 0.2
        
        return min(1.0, base_score)