"""
Генератор идей и решений
"""

import random
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum

class IdeaDomain(Enum):
    """Домены идей"""
    TECHNOLOGY = "технологии"
    BUSINESS = "бизнес"
    ART = "искусство"
    SCIENCE = "наука"
    EDUCATION = "образование"
    SOCIAL = "социальные"
    PERSONAL = "личностные"

class IdeaGenerator:
    """Генератор творческих идей и инновационных решений"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Базы знаний для различных доменов
        self.domain_knowledge = self._build_domain_knowledge()
        self.creative_techniques = self._load_creative_techniques()
        self.idea_patterns = self._load_idea_patterns()
        
        self.logger.info("Генератор идей инициализирован")
    
    def _build_domain_knowledge(self) -> Dict[IdeaDomain, List[str]]:
        """Построение базы знаний по доменам"""
        return {
            IdeaDomain.TECHNOLOGY: [
                "искусственный интеллект", "блокчейн", "интернет вещей", "виртуальная реальность",
                "кибербезопасность", "большие данные", "облачные вычисления", "мобильные приложения"
            ],
            IdeaDomain.BUSINESS: [
                "стартапы", "маркетинг", "управление проектами", "клиентский опыт",
                "оптимизация процессов", "инновации в retail", "удаленная работа", "устойчивое развитие"
            ],
            IdeaDomain.ART: [
                "цифровое искусство", "интерактивные инсталляции", "генеративный дизайн",
                "иммерсивный театр", "социальное искусство", "экологический арт", "нейроэстетика"
            ],
            IdeaDomain.SCIENCE: [
                "биотехнологии", "нанотехнологии", "квантовые вычисления", "исследование космоса",
                "изменение климата", "нейробиология", "генная инженерия", "возобновляемая энергия"
            ],
            IdeaDomain.EDUCATION: [
                "персонализированное обучение", "геймификация", "микрообучение",
                "виртуальные классы", "адаптивные платформы", "проектное обучение", "пожизненное образование"
            ],
            IdeaDomain.SOCIAL: [
                "социальное предпринимательство", "волонтерство", "общественные инициативы",
                "городское планирование", "доступная среда", "межкультурный диалог", "экологические движения"
            ],
            IdeaDomain.PERSONAL: [
                "саморазвитие", "тайм-менеджмент", "осознанность", "творческие привычки",
                "здоровый образ жизни", "финансовая грамотность", "эмоциональный интеллект"
            ]
        }
    
    def _load_creative_techniques(self) -> List[Dict[str, Any]]:
        """Загрузка творческих техник"""
        return [
            {
                "name": "мозговой штурм",
                "description": "Генерация множества идей без критики",
                "steps": ["Определить проблему", "Генерировать идеи", "Объединять и улучшать", "Выбирать лучшие"],
                "applicability": "универсальная"
            },
            {
                "name": "SCAMPER",
                "description": "Техника модификации существующих идей",
                "steps": ["Заменить", "Комбинировать", "Адаптировать", "Модифицировать", "Применить иначе", "Устранить", "Перевернуть"],
                "applicability": "инновации"
            },
            {
                "name": "шесть шляп мышления",
                "description": "Рассмотрение проблемы с разных перспектив",
                "steps": ["Белая шляпа (факты)", "Красная шляпа (эмоции)", "Черная шляпа (критика)", "Желтая шляпа (оптимизм)", "Зеленая шляпа (творчество)", "Синяя шляпа (процесс)"],
                "applicability": "принятие решений"
            },
            {
                "name": "синектика",
                "description": "Использование аналогий для генерации идей",
                "steps": ["Определить проблему", "Найти аналогии", "Исследовать аналогии", "Применить insights к проблеме"],
                "applicability": "творческое решение проблем"
            },
            {
                "name": "ТРИЗ",
                "description": "Теория решения изобретательских задач",
                "steps": ["Анализ проблемы", "Определение противоречий", "Использование принципов изобретения", "Прогнозирование развития"],
                "applicability": "технические инновации"
            }
        ]
    
    def _load_idea_patterns(self) -> List[Dict[str, Any]]:
        """Загрузка паттернов идей"""
        return [
            {
                "pattern": "Объединение {A} и {B}",
                "description": "Создание нового через комбинацию существующих элементов",
                "examples": ["смартфон + фотоаппарат = камерафон", "социальная сеть + торговля = социальная коммерция"],
                "weight": 0.3
            },
            {
                "pattern": "Упрощение {A}",
                "description": "Удаление сложностей для создания более доступного решения",
                "examples": ["упрощенный интерфейс", "минималистичный дизайн", "однофункциональное устройство"],
                "weight": 0.2
            },
            {
                "pattern": "Адаптация {A} для {B}",
                "description": "Применение существующего решения в новом контексте",
                "examples": ["применение игровых механик в образовании", "использование технологий здравоохранения в фитнесе"],
                "weight": 0.15
            },
            {
                "pattern": "Обратный {A}",
                "description": "Рассмотрение проблемы или решения с противоположной стороны",
                "examples": ["обратный аукцион", "инвертированная классная комната", "реверсивный менторинг"],
                "weight": 0.1
            },
            {
                "pattern": "Масштабирование {A}",
                "description": "Изменение масштаба применения решения",
                "examples": ["глобализация локального сервиса", "создание микро-версии крупного продукта"],
                "weight": 0.1
            },
            {
                "pattern": "Персонализация {A}",
                "description": "Адаптация под индивидуальные потребности",
                "examples": ["персонализированные рекомендации", "кастомизируемые продукты", "адаптивные интерфейсы"],
                "weight": 0.1
            },
            {
                "pattern": "Экологизация {A}",
                "description": "Добавление экологической составляющей",
                "examples": ["устойчивые материалы", "энергоэффективные решения", "циркулярная экономика"],
                "weight": 0.05
            }
        ]
    
    def generate(self, problem: str, domain: IdeaDomain = None, 
                technique: str = "авто") -> Dict[str, Any]:
        """Генерация идей для решения проблемы"""
        
        try:
            if not domain:
                domain = self._identify_domain(problem)
            
            if technique == "авто":
                technique = self._select_technique(domain)
            
            # Анализ проблемы
            problem_analysis = self._analyze_problem(problem, domain)
            
            # Генерация идей
            ideas = self._generate_ideas(problem_analysis, domain, technique)
            
            # Оценка идей
            evaluated_ideas = self._evaluate_ideas(ideas, problem_analysis)
            
            return {
                'content': evaluated_ideas,
                'type': 'ideas',
                'problem': problem,
                'domain': domain.value,
                'technique_used': technique,
                'ideas_count': len(evaluated_ideas),
                'problem_analysis': problem_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации идей: {e}")
            return {
                'content': [{"idea": f"Рассмотреть проблему '{problem}' с новой перспективы", "score": 0.5}],
                'type': 'ideas',
                'error': str(e)
            }
    
    def _identify_domain(self, problem: str) -> IdeaDomain:
        """Идентификация домена проблемы"""
        problem_lower = problem.lower()
        
        for domain, keywords in self.domain_knowledge.items():
            if any(keyword in problem_lower for keyword in keywords):
                return domain
        
        # Если не нашли, анализируем ключевые слова
        domain_keywords = {
            IdeaDomain.TECHNOLOGY: ["технологи", "программ", "приложен", "интернет", "данн"],
            IdeaDomain.BUSINESS: ["бизнес", "компани", "прибыл", "маркетинг", "клиент"],
            IdeaDomain.ART: ["искусств", "творчеств", "дизайн", "красот", "эстет"],
            IdeaDomain.SCIENCE: ["наук", "исследован", "открыт", "эксперимент", "гипотез"],
            IdeaDomain.EDUCATION: ["образовани", "обучен", "знания", "студент", "учитель"],
            IdeaDomain.SOCIAL: ["обществ", "социальн", "помощь", "волонтер", "сообществ"],
            IdeaDomain.PERSONAL: ["личн", "развити", "успех", "цел", "привычк"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in problem_lower for keyword in keywords):
                return domain
        
        return random.choice(list(IdeaDomain))
    
    def _select_technique(self, domain: IdeaDomain) -> str:
        """Выбор творческой техники"""
        applicable_techniques = [
            tech for tech in self.creative_techniques 
            if tech["applicability"] in ["универсальная", domain.value]
        ]
        
        if not applicable_techniques:
            applicable_techniques = self.creative_techniques
        
        return random.choice(applicable_techniques)["name"]
    
    def _analyze_problem(self, problem: str, domain: IdeaDomain) -> Dict[str, Any]:
        """Анализ проблемы"""
        keywords = self._extract_keywords(problem)
        constraints = self._identify_constraints(problem)
        goals = self._identify_goals(problem)
        
        return {
            'keywords': keywords,
            'constraints': constraints,
            'goals': goals,
            'domain': domain.value,
            'complexity': self._assess_complexity(problem)
        }
    
    def _extract_keywords(self, problem: str) -> List[str]:
        """Извлечение ключевых слов из проблемы"""
        # Упрощенная реализация
        stop_words = ["как", "что", "для", "на", "в", "с", "о", "по", "за", "из"]
        words = problem.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        return list(set(keywords))[:5]  # Уникальные ключевые слова
    
    def _identify_constraints(self, problem: str) -> List[str]:
        """Идентификация ограничений"""
        constraints = []
        problem_lower = problem.lower()
        
        constraint_indicators = {
            "бюджет": ["дешев", "бюджет", "стоимость", "цена"],
            "время": ["быстр", "срочн", "время", "срок"],
            "ресурсы": ["ресурс", "материал", "оборудование", "персонал"],
            "технологии": ["технологи", "платформ", "совместим"],
            "регуляции": ["закон", "правил", "стандарт", "требован"]
        }
        
        for constraint_type, indicators in constraint_indicators.items():
            if any(indicator in problem_lower for indicator in indicators):
                constraints.append(constraint_type)
        
        return constraints if constraints else ["общие ограничения"]
    
    def _identify_goals(self, problem: str) -> List[str]:
        """Идентификация целей"""
        goals = []
        problem_lower = problem.lower()
        
        goal_indicators = {
            "эффективность": ["эффектив", "производительн", "оптимиз"],
            "качество": ["качеств", "улучш", "повыш"],
            "инновации": ["инновац", "новый", "уникальн"],
            "доступность": ["доступн", "просто", "удобн"],
            "масштабируемость": ["масштаб", "рост", "расширен"]
        }
        
        for goal_type, indicators in goal_indicators.items():
            if any(indicator in problem_lower for indicator in indicators):
                goals.append(goal_type)
        
        return goals if goals else ["решение проблемы"]
    
    def _assess_complexity(self, problem: str) -> str:
        """Оценка сложности проблемы"""
        word_count = len(problem.split())
        if word_count < 10:
            return "низкая"
        elif word_count < 20:
            return "средняя"
        else:
            return "высокая"
    
    def _generate_ideas(self, problem_analysis: Dict[str, Any], 
                       domain: IdeaDomain, technique: str) -> List[str]:
        """Генерация идей на основе анализа"""
        ideas = []
        keywords = problem_analysis['keywords']
        domain_concepts = self.domain_knowledge[domain]
        
        # Количество идей в зависимости от сложности
        complexity_map = {"низкая": 3, "средняя": 5, "высокая": 8}
        num_ideas = complexity_map.get(problem_analysis['complexity'], 5)
        
        for _ in range(num_ideas):
            # Выбор паттерна идеи
            pattern = self._select_idea_pattern()
            idea_pattern = pattern["pattern"]
            
            # Заполнение паттерна
            idea = self._fill_idea_pattern(idea_pattern, keywords, domain_concepts)
            ideas.append(idea)
        
        # Добавление специфических идей на основе техники
        technique_ideas = self._apply_creative_technique(technique, problem_analysis)
        ideas.extend(technique_ideas)
        
        return list(set(ideas))  # Уникальные идеи
    
    def _select_idea_pattern(self) -> Dict[str, Any]:
        """Выбор паттерна идеи"""
        patterns = self.idea_patterns
        weights = [p["weight"] for p in patterns]
        return random.choices(patterns, weights=weights)[0]
    
    def _fill_idea_pattern(self, pattern: str, keywords: List[str], 
                          domain_concepts: List[str]) -> str:
        """Заполнение паттерна идеи"""
        result = pattern
        
        if "{A}" in result and keywords:
            result = result.replace("{A}", random.choice(keywords))
        
        if "{B}" in result and domain_concepts:
            result = result.replace("{B}", random.choice(domain_concepts))
        
        # Если остались незаполненные плейсхолдеры
        result = result.replace("{A}", "технология").replace("{B}", "инновация")
        
        return result
    
    def _apply_creative_technique(self, technique: str, 
                                 problem_analysis: Dict[str, Any]) -> List[str]:
        """Применение творческой техники"""
        technique_info = next((t for t in self.creative_techniques if t["name"] == technique), None)
        
        if not technique_info:
            return []
        
        ideas = []
        
        if technique == "мозговой штурм":
            # Генерация разнообразных идей
            for _ in range(5):
                idea = f"Рассмотреть {random.choice(problem_analysis['keywords'])} с точки зрения {random.choice(self.domain_knowledge[IdeaDomain.TECHNOLOGY])}"
                ideas.append(idea)
        
        elif technique == "SCAMPER":
            # Применение SCAMPER к проблеме
            scamper_actions = ["Заменить", "Комбинировать", "Адаптировать", "Увеличить", "Уменьшить", "Использовать иначе", "Устранить", "Перевернуть"]
            for action in scamper_actions[:3]:  # Берем первые 3 действия
                idea = f"{action} аспект {random.choice(problem_analysis['keywords'])} для решения проблемы"
                ideas.append(idea)
        
        return ideas
    
    def _evaluate_ideas(self, ideas: List[str], problem_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Оценка сгенерированных идей"""
        evaluated_ideas = []
        
        for idea in ideas:
            score = self._calculate_idea_score(idea, problem_analysis)
            evaluation = self._provide_feedback(idea, score)
            
            evaluated_ideas.append({
                "idea": idea,
                "score": score,
                "evaluation": evaluation,
                "feasibility": self._assess_feasibility(idea),
                "innovativeness": self._assess_innovativeness(idea)
            })
        
        # Сортировка по оценке
        evaluated_ideas.sort(key=lambda x: x["score"], reverse=True)
        
        return evaluated_ideas
    
    def _calculate_idea_score(self, idea: str, problem_analysis: Dict[str, Any]) -> float:
        """Расчет оценки идеи"""
        base_score = 0.5
        
        # Бонусы за релевантность ключевым словам
        relevant_keywords = sum(1 for keyword in problem_analysis['keywords'] if keyword in idea.lower())
        base_score += relevant_keywords * 0.1
        
        # Бонус за соответствие целям
        if any(goal in idea.lower() for goal in problem_analysis['goals']):
            base_score += 0.2
        
        # Бонус за учет ограничений
        if any(constraint in idea.lower() for constraint in problem_analysis['constraints']):
            base_score += 0.1
        
        # Штраф за слишком общие формулировки
        generic_phrases = ["рассмотреть", "изучить", "проанализировать"]
        if any(phrase in idea.lower() for phrase in generic_phrases):
            base_score -= 0.1
        
        return max(0.1, min(1.0, base_score))
    
    def _assess_feasibility(self, idea: str) -> str:
        """Оценка реализуемости идеи"""
        feasibility_indicators = {
            "высокая": ["использовать существующие", "адаптировать", "упростить"],
            "средняя": ["разработать новую", "интегрировать", "модифицировать"],
            "низкая": ["революционный", "прорывной", "полностью новый"]
        }
        
        idea_lower = idea.lower()
        for level, indicators in feasibility_indicators.items():
            if any(indicator in idea_lower for indicator in indicators):
                return level
        
        return "средняя"
    
    def _assess_innovativeness(self, idea: str) -> str:
        """Оценка инновационности идеи"""
        innovative_indicators = {
            "высокая": ["уникальный", "инновационный", "прорывной", "революционный"],
            "средняя": ["улучшенный", "модифицированный", "адаптированный"],
            "низкая": ["стандартный", "традиционный", "общепринятый"]
        }
        
        idea_lower = idea.lower()
        for level, indicators in innovative_indicators.items():
            if any(indicator in idea_lower for indicator in indicators):
                return level
        
        return "средняя"
    
    def _provide_feedback(self, idea: str, score: float) -> str:
        """Предоставление обратной связи по идее"""
        if score >= 0.8:
            return "Отличная идея! Хорошо проработана и соответствует критериям."
        elif score >= 0.6:
            return "Хорошая идея, но требует дополнительной проработки."
        elif score >= 0.4:
            return "Интересное направление, но нужно больше конкретики."
        else:
            return "Идея требует существенной доработки и уточнения."