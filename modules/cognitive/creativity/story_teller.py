"""
Рассказчик историй
"""

import random
import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from enum import Enum

class StoryGenre(Enum):
    """Жанры историй"""
    FANTASY = "фэнтези"
    SCI_FI = "научная фантастика"
    MYSTERY = "детектив"
    ROMANCE = "романтика"
    ADVENTURE = "приключения"
    HUMOR = "юмор"
    DRAMA = "драма"

class StoryTeller:
    """Генератор рассказов и историй"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.story_arcs_file = Path("modules/cognitive/creativity/creative_patterns/story_arcs.creat")
        
        # Загрузка сюжетных арок
        self.story_arcs = self._load_story_arcs()
        self.character_templates = self._load_character_templates()
        self.setting_database = self._load_setting_database()
        self.plot_devices = self._load_plot_devices()
        
        self.logger.info("Рассказчик историй инициализирован")
    
    def _load_story_arcs(self) -> List[Dict[str, Any]]:
        """Загрузка сюжетных арок"""
        try:
            if self.story_arcs_file.exists():
                with open(self.story_arcs_file, 'r', encoding='utf-8') as f:
                    arcs = json.load(f)
                return arcs.get('story_arcs', [])
            else:
                return self._get_default_story_arcs()
        except Exception as e:
            self.logger.error(f"Ошибка загрузки сюжетных арок: {e}")
            return self._get_default_story_arcs()
    
    def _get_default_story_arcs(self) -> List[Dict[str, Any]]:
        """Стандартные сюжетные арки"""
        return [
            {
                "name": "Героическое путешествие",
                "structure": ["завязка", "призыв к приключению", "испытания", "кульминация", "возвращение"],
                "genre": "приключения",
                "weight": 0.25
            },
            {
                "name": "Тайна и раскрытие",
                "structure": ["загадка", "расследование", "ложные следы", "разгадка", "последствия"],
                "genre": "детектив", 
                "weight": 0.2
            },
            {
                "name": "Любовная история",
                "structure": ["встреча", "развитие отношений", "конфликт", "разрешение", "счастливый конец"],
                "genre": "романтика",
                "weight": 0.15
            },
            {
                "name": "Преодоление себя",
                "structure": ["статус кво", "вызов", "борьба", "преодоление", "преображение"],
                "genre": "драма",
                "weight": 0.15
            },
            {
                "name": "Комедийная ситуация",
                "structure": ["обычная ситуация", "неожиданный поворот", "нарастание хаоса", "кульминация", "развязка"],
                "genre": "юмор",
                "weight": 0.1
            },
            {
                "name": "Научное открытие",
                "structure": ["гипотеза", "эксперимент", "открытие", "последствия", "новый мир"],
                "genre": "научная фантастика",
                "weight": 0.1
            },
            {
                "name": "Магическое превращение", 
                "structure": ["обычный мир", "обнаружение магии", "обучение", "испытание", "новое понимание"],
                "genre": "фэнтези",
                "weight": 0.05
            }
        ]
    
    def _load_character_templates(self) -> Dict[str, List[Dict]]:
        """Шаблоны персонажей"""
        return {
            "герой": [
                {"name": "смелый искатель", "traits": ["смелость", "решительность", "честность"]},
                {"name": "мудрый наставник", "traits": ["мудрость", "терпение", "опыт"]},
                {"name": "веселый компаньон", "traits": ["юмор", "верность", "оптимизм"]}
            ],
            "антагонист": [
                {"name": "коварный злодей", "traits": ["хитрость", "амбиции", "жестокость"]},
                {"name": "загадочный незнакомец", "traits": ["таинственность", "непредсказуемость", "скрытность"]},
                {"name": "внутренний демон", "traits": ["сомнения", "страхи", "слабости"]}
            ],
            "второстепенный": [
                {"name": "верный друг", "traits": ["преданность", "поддержка", "надежность"]},
                {"name": "мудрый старец", "traits": ["опыт", "знания", "спокойствие"]},
                {"name": "непредсказуемый союзник", "traits": ["независимость", "ресурсность", "переменчивость"]}
            ]
        }
    
    def _load_setting_database(self) -> Dict[str, List[str]]:
        """База данных мест действия"""
        return {
            "фэнтези": ["древний лес", "замок дракона", "магическая академия", "подземелье", "эльфийский город"],
            "научная фантастика": ["космическая станция", "далекая планета", "подводная база", "виртуальная реальность", "город будущего"],
            "реализм": ["маленький городок", "большой город", "заброшенный дом", "уютное кафе", "библиотека"],
            "исторические": ["древний Рим", "средневековый замок", "викторианский Лондон", "дикий запад", "дворцовый комплекс"]
        }
    
    def _load_plot_devices(self) -> List[Dict[str, Any]]:
        """Сюжетные ходы и приемы"""
        return [
            {"device": "неожиданная встреча", "impact": "средний", "genre": "универсальный"},
            {"device": "обнаружение тайны", "impact": "высокий", "genre": "детектив"},
            {"device": "изменение отношений", "impact": "средний", "genre": "романтика"},
            {"device": "технологический прорыв", "impact": "высокий", "genre": "научная фантастика"},
            {"device": "магическое событие", "impact": "высокий", "genre": "фэнтези"},
            {"device": "комическое недоразумение", "impact": "низкий", "genre": "юмор"},
            {"device": "трагическая потеря", "impact": "высокий", "genre": "драма"},
            {"device": "героическое спасение", "impact": "высокий", "genre": "приключения"}
        ]
    
    def generate(self, theme: str, genre: StoryGenre = None, length: str = "короткий") -> Dict[str, Any]:
        """Генерация рассказа на заданную тему"""
        
        try:
            if not genre:
                genre = self._select_genre_for_theme(theme)
            
            # Выбор сюжетной арки
            story_arc = self._select_story_arc(genre)
            
            # Создание персонажей
            characters = self._create_characters(story_arc["genre"])
            
            # Выбор места действия
            setting = self._select_setting(genre)
            
            # Генерация сюжета
            plot = self._develop_plot(story_arc, characters, setting, theme)
            
            # Написание текста
            story_text = self._write_story(plot, length)
            
            return {
                'content': story_text,
                'type': 'story',
                'theme': theme,
                'genre': genre.value,
                'length': length,
                'story_arc': story_arc["name"],
                'characters': [char["name"] for char in characters],
                'setting': setting,
                'word_count': len(story_text.split())
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации рассказа: {e}")
            return {
                'content': f"История о {theme} начинается там, где заканчиваются обычные дороги. Это рассказ о том, как мечты становятся реальностью, а реальность превращается в легенду.",
                'type': 'story', 
                'error': str(e)
            }
    
    def _select_genre_for_theme(self, theme: str) -> StoryGenre:
        """Выбор жанра на основе темы"""
        theme_lower = theme.lower()
        
        genre_keywords = {
            StoryGenre.FANTASY: ["магия", "дракон", "волшеб", "фэнтези", "заклинание"],
            StoryGenre.SCI_FI: ["космос", "робот", "технологи", "будущ", "наука"],
            StoryGenre.MYSTERY: ["тайна", "загадк", "детектив", "расследование", "преступление"],
            StoryGenre.ROMANCE: ["любов", "роман", "чувства", "сердце", "отношения"],
            StoryGenre.ADVENTURE: ["приключен", "путешеств", "опасность", "исследование", "экспедиция"],
            StoryGenre.HUMOR: ["смех", "юмор", "комеди", "шутк", "забав"],
            StoryGenre.DRAMA: ["драма", "трагедия", "конфликт", "чувства", "эмоции"]
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in theme_lower for keyword in keywords):
                return genre
        
        # Если не нашли соответствий, выбираем случайно
        return random.choice(list(StoryGenre))
    
    def _select_story_arc(self, genre: StoryGenre) -> Dict[str, Any]:
        """Выбор сюжетной арки для жанра"""
        genre_arcs = [arc for arc in self.story_arcs if arc["genre"] == genre.value]
        
        if not genre_arcs:
            # Если нет арок для жанра, берем универсальные
            genre_arcs = [arc for arc in self.story_arcs if arc["genre"] in ["приключения", "драма"]]
        
        if not genre_arcs:
            genre_arcs = self.story_arcs
        
        weights = [arc["weight"] for arc in genre_arcs]
        return random.choices(genre_arcs, weights=weights)[0]
    
    def _create_characters(self, genre: str) -> List[Dict[str, Any]]:
        """Создание персонажей для истории"""
        characters = []
        
        # Главный герой
        hero_templates = self.character_templates["герой"]
        hero = random.choice(hero_templates).copy()
        hero["role"] = "главный герой"
        characters.append(hero)
        
        # Антагонист (не всегда)
        if random.random() > 0.3:  # 70% chance
            antagonist_templates = self.character_templates["антагонист"]
            antagonist = random.choice(antagonist_templates).copy()
            antagonist["role"] = "антагонист"
            characters.append(antagonist)
        
        # Второстепенные персонажи (1-2)
        secondary_count = random.randint(1, 2)
        secondary_templates = self.character_templates["второстепенный"]
        for _ in range(secondary_count):
            secondary = random.choice(secondary_templates).copy()
            secondary["role"] = "второстепенный"
            characters.append(secondary)
        
        return characters
    
    def _select_setting(self, genre: StoryGenre) -> str:
        """Выбор места действия"""
        genre_key = genre.value
        if genre_key in self.setting_database:
            return random.choice(self.setting_database[genre_key])
        else:
            # Универсальные настройки
            all_settings = [setting for settings in self.setting_database.values() for setting in settings]
            return random.choice(all_settings)
    
    def _develop_plot(self, story_arc: Dict[str, Any], characters: List[Dict], 
                     setting: str, theme: str) -> Dict[str, Any]:
        """Разработка сюжета"""
        plot_points = []
        
        for plot_stage in story_arc["structure"]:
            plot_point = self._create_plot_point(plot_stage, characters, setting, theme)
            plot_points.append(plot_point)
        
        # Добавление сюжетных ходов
        if random.random() > 0.5:
            plot_device = random.choice(self.plot_devices)
            insertion_point = random.randint(1, len(plot_points) - 2)
            plot_points.insert(insertion_point, {
                "stage": "сюжетный поворот",
                "description": plot_device["device"],
                "impact": plot_device["impact"]
            })
        
        return {
            "arc": story_arc["name"],
            "setting": setting,
            "characters": characters,
            "plot_points": plot_points,
            "theme": theme
        }
    
    def _create_plot_point(self, stage: str, characters: List[Dict], 
                          setting: str, theme: str) -> Dict[str, Any]:
        """Создание точки сюжета"""
        stage_templates = {
            "завязка": [
                f"В {setting} появляется {characters[0]['name']}, сталкивающийся с проблемой, связанной с {theme}",
                f"История начинается в {setting}, где {characters[0]['name']} обнаруживает нечто удивительное о {theme}"
            ],
            "призыв к приключению": [
                f"{characters[0]['name']} получает возможность изменить свою жизнь, связанную с {theme}",
                f"Судьба предоставляет {characters[0]['name']} шанс исследовать тайны {theme}"
            ],
            "испытания": [
                f"На пути к пониманию {theme} {characters[0]['name']} сталкивается с серьезными трудностями",
                f"{characters[0]['name']} проходит через серию испытаний, раскрывающих суть {theme}"
            ],
            "кульминация": [
                f"Все сходится в решающий момент, когда истина о {theme} становится ясна",
                f"Кульминация истории наступает, когда {characters[0]['name']} сталкивается с главным вызовом, связанным с {theme}"
            ],
            "развязка": [
                f"История завершается, оставляя {characters[0]['name']} с новым пониманием {theme}",
                f"После всех событий {characters[0]['name']} обретает новый взгляд на {theme}"
            ]
        }
        
        description = random.choice(stage_templates.get(stage, [f"На этапе {stage} происходит развитие темы {theme}"]))
        
        return {
            "stage": stage,
            "description": description,
            "characters_involved": [characters[0]["name"]]  # главный герой всегда участвует
        }
    
    def _write_story(self, plot: Dict[str, Any], length: str) -> str:
        """Написание текста рассказа"""
        story_parts = []
        
        # Введение
        introduction = self._write_introduction(plot)
        story_parts.append(introduction)
        
        # Основная часть
        for plot_point in plot["plot_points"]:
            part = self._write_plot_point(plot_point, plot["characters"], plot["setting"])
            story_parts.append(part)
        
        # Заключение
        conclusion = self._write_conclusion(plot)
        story_parts.append(conclusion)
        
        full_story = " ".join(story_parts)
        
        # Корректировка длины
        return self._adjust_story_length(full_story, length)
    
    def _write_introduction(self, plot: Dict[str, Any]) -> str:
        """Написание введения"""
        templates = [
            f"Эта история происходит в {plot['setting']}, где живет {plot['characters'][0]['name']}. ",
            f"В мире, где {plot['setting']} становится фоном для невероятных событий, мы знакомимся с {plot['characters'][0]['name']}. ",
            f"Все началось в {plot['setting']}, когда {plot['characters'][0]['name']} столкнулся с загадкой, связанной с {plot['theme']}. "
        ]
        return random.choice(templates)
    
    def _write_plot_point(self, plot_point: Dict[str, Any], characters: List[Dict], setting: str) -> str:
        """Написание части рассказа для точки сюжета"""
        return plot_point["description"] + ". "
    
    def _write_conclusion(self, plot: Dict[str, Any]) -> str:
        """Написание заключения"""
        templates = [
            f"Так завершилась эта история о {plot['theme']}, оставив {plot['characters'][0]['name']} с ценным опытом. ",
            f"И вот, когда все страсти улеглись, {plot['characters'][0]['name']} понял истинный смысл {plot['theme']}. ",
            f"История подошла к концу, но уроки, связанные с {plot['theme']}, остались с {plot['characters'][0]['name']} навсегда. "
        ]
        return random.choice(templates)
    
    def _adjust_story_length(self, story: str, target_length: str) -> str:
        """Корректировка длины рассказа"""
        words = story.split()
        current_length = len(words)
        
        target_word_counts = {
            "короткий": (100, 200),
            "средний": (300, 500),
            "длинный": (600, 1000)
        }
        
        min_words, max_words = target_word_counts.get(target_length, (200, 400))
        
        if current_length < min_words:
            # Добавляем описания
            additional_descriptions = [
                " Воздух был наполнен тайнами. ",
                " Каждый шаг приводил к новым открытиям. ",
                " Время будто замедлило свой бег. ",
                " Окружающий мир замер в ожидании. "
            ]
            while current_length < min_words and additional_descriptions:
                story += random.choice(additional_descriptions)
                current_length = len(story.split())
        
        elif current_length > max_words:
            # Сокращаем рассказ
            words = words[:max_words]
            story = " ".join(words) + "..."
        
        return story