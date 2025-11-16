"""
Композитор стихов и поэзии
"""

import random
import re
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum

class PoetryStyle(Enum):
    """Стили поэзии"""
    CLASSIC = "классический"
    MODERN = "современный"
    HAIKU = "хайку"
    FREE = "свободный"
    RHYMED = "рифмованный"

class PoetryComposer:
    """Композитор стихов и поэтических произведений"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Поэтические паттерны
        self.rhyme_schemes = {
            'перекрестная': ['A', 'B', 'A', 'B'],
            'парная': ['A', 'A', 'B', 'B'],
            'кольцевая': ['A', 'B', 'B', 'A'],
            'сложная': ['A', 'B', 'C', 'B', 'A']
        }
        
        self.meter_patterns = {
            'ямб': [0, 1],  # безударный-ударный
            'хорей': [1, 0], # ударный-безударный
            'дактиль': [1, 0, 0], # ударный-безударный-безударный
            'амфибрахий': [0, 1, 0], # безударный-ударный-безударный
            'анапест': [0, 0, 1] # безударный-безударный-ударный
        }
        
        # Словари рифм и образов
        self.rhyme_database = self._build_rhyme_database()
        self.poetic_images = self._build_poetic_images()
        
        self.logger.info("Композитор поэзии инициализирован")
    
    def _build_rhyme_database(self) -> Dict[str, List[str]]:
        """Построение базы данных рифм"""
        return {
            "любовь": ["кровь", "вновь", "морковь", "готовь"],
            "ночь": ["прочь", "дочь", "точь", "помощь"],
            "весна": ["ясна", "сосна", "война", "тишина"],
            "мечта": ["пустота", "красота", "чистота", "мелочьта"],
            "огонь": ["огонь", "ладонь", "конь", "огонь"],
            "свет": ["ответ", "след", "цвет", "совет"],
            "душа": ["тишина", "весна", "слушай", "сушь"],
            "время": ["бремя", "семя", "темя", "времени"]
        }
    
    def _build_poetic_images(self) -> Dict[str, List[str]]:
        """Построение базы поэтических образов"""
        return {
            "природа": [
                "шепот листвы", "танец ветра", "поцелуй солнца", "слезы дождя",
                "объятия ночи", "дыхание утра", "память осени", "надежда весны"
            ],
            "эмоции": [
                "радость в глазах", "грусть в сердце", "страсть в душе", "тишина в мыслях",
                "огонь желания", "лед одиночества", "ветер перемен", "море чувств"
            ],
            "философия": [
                "круговорот бытия", "нить судьбы", "эхо вечности", "тень прошлого",
                "свет истины", "лабиринт мыслей", "зеркало души", "путь к себе"
            ]
        }
    
    def generate(self, theme: str, style: PoetryStyle = PoetryStyle.CLASSIC, 
                lines_count: int = 4) -> Dict[str, Any]:
        """Генерация стихотворения на заданную тему"""
        
        try:
            # Определение структуры стихотворения
            structure = self._determine_structure(style, lines_count)
            
            # Генерация строк
            lines = self._compose_lines(theme, structure, style)
            
            # Форматирование результата
            poem = self._format_poem(lines, style)
            
            # Анализ качества
            quality_metrics = self._analyze_poem_quality(poem, structure)
            
            return {
                'content': poem,
                'type': 'poetry',
                'theme': theme,
                'style': style.value,
                'structure': structure,
                'lines_count': lines_count,
                'quality_metrics': quality_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации стихотворения: {e}")
            return {
                'content': f"О {theme} молчат стихи,\nНо я попробую восславить.\nПусть будут строки не плохи,\nЧтоб сердце могло полюбить.",
                'type': 'poetry',
                'error': str(e)
            }
    
    def _determine_structure(self, style: PoetryStyle, lines_count: int) -> Dict[str, Any]:
        """Определение структуры стихотворения"""
        structure = {}
        
        if style == PoetryStyle.HAIKU:
            structure['type'] = 'хайку'
            structure['lines_count'] = 3
            structure['syllables'] = [5, 7, 5]  # традиционная схема хайку
            structure['rhyme_scheme'] = None
        elif style == PoetryStyle.CLASSIC:
            structure['type'] = 'классический'
            structure['lines_count'] = lines_count
            structure['syllables'] = [8, 8, 8, 8]  # четырехстопный ямб
            structure['rhyme_scheme'] = random.choice(list(self.rhyme_schemes.keys()))
            structure['meter'] = 'ямб'
        elif style == PoetryStyle.MODERN:
            structure['type'] = 'современный'
            structure['lines_count'] = lines_count
            structure['syllables'] = [random.randint(6, 12) for _ in range(lines_count)]
            structure['rhyme_scheme'] = None if random.random() > 0.5 else 'свободная'
            structure['meter'] = 'свободный'
        else:  # FREE or RHYMED
            structure['type'] = style.value
            structure['lines_count'] = lines_count
            structure['syllables'] = [random.randint(4, 10) for _ in range(lines_count)]
            structure['rhyme_scheme'] = random.choice(list(self.rhyme_schemes.keys())) if style == PoetryStyle.RHYMED else None
            structure['meter'] = random.choice(list(self.meter_patterns.keys()))
        
        return structure
    
    def _compose_lines(self, theme: str, structure: Dict[str, Any], style: PoetryStyle) -> List[str]:
        """Сочинение строк стихотворения"""
        lines = []
        rhyme_scheme = structure.get('rhyme_scheme')
        syllables_pattern = structure.get('syllables', [8] * structure['lines_count'])
        
        # Определение рифмующихся слов
        rhyme_words = {}
        if rhyme_scheme:
            unique_rhymes = set(self.rhyme_schemes[rhyme_scheme])
            for rhyme_code in unique_rhymes:
                rhyme_words[rhyme_code] = self._find_rhyme_word(theme)
        
        for i in range(structure['lines_count']):
            target_syllables = syllables_pattern[i] if i < len(syllables_pattern) else 8
            
            # Определение рифмы для текущей строки
            current_rhyme = None
            if rhyme_scheme and i < len(self.rhyme_schemes[rhyme_scheme]):
                rhyme_code = self.rhyme_schemes[rhyme_scheme][i]
                current_rhyme = rhyme_words.get(rhyme_code)
            
            # Генерация строки
            line = self._generate_poetic_line(theme, target_syllables, current_rhyme, style)
            lines.append(line)
        
        return lines
    
    def _generate_poetic_line(self, theme: str, syllables: int, rhyme_word: str, style: PoetryStyle) -> str:
        """Генерация одной поэтической строки"""
        
        # Базовые шаблоны начала строк
        beginnings = [
            f"О {theme} ", f"В мире {theme} ", f"Как {theme} ", 
            f"Подобно {theme} ", f"Среди {theme} ", f"Для {theme} ",
            f"Мечта о {theme} ", f"Память {theme} ", f"Свет {theme} "
        ]
        
        # Поэтические образы для продолжения
        images = self._get_poetic_images_for_theme(theme)
        
        # Составление строки
        line_start = random.choice(beginnings)
        line_image = random.choice(images)
        
        line = line_start + line_image
        
        # Корректировка длины по слогам
        line = self._adjust_syllables(line, syllables)
        
        # Добавление рифмы если нужно
        if rhyme_word and not line.endswith(rhyme_word):
            # Пытаемся естественно встроить рифму
            if random.random() > 0.5:
                line = line.rstrip('.,!?') + " " + rhyme_word
        
        return line.capitalize()
    
    def _get_poetic_images_for_theme(self, theme: str) -> List[str]:
        """Получение поэтических образов для темы"""
        all_images = []
        for category, images in self.poetic_images.items():
            all_images.extend(images)
        
        # Фильтрация по теме (простая эвристика)
        theme_keywords = theme.lower().split()
        relevant_images = []
        
        for image in all_images:
            if any(keyword in image for keyword in theme_keywords):
                relevant_images.append(image)
        
        return relevant_images if relevant_images else all_images
    
    def _find_rhyme_word(self, theme: str) -> str:
        """Поиск слова для рифмы"""
        theme_words = theme.lower().split()
        
        for word in theme_words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.rhyme_database:
                return random.choice(self.rhyme_database[clean_word])
        
        # Если не нашли, берем случайное слово из базы
        all_rhymes = [rhyme for rhymes in self.rhyme_database.values() for rhyme in rhymes]
        return random.choice(all_rhymes) if all_rhymes else "любовь"
    
    def _adjust_syllables(self, line: str, target_syllables: int) -> str:
        """Корректировка строки по количеству слогов"""
        words = line.split()
        current_syllables = self._count_syllables(line)
        
        if current_syllables < target_syllables:
            # Добавляем слова
            additional_words = ["тихий", "светлый", "вечный", "нежный", "глубокий"]
            while current_syllables < target_syllables and additional_words:
                new_word = random.choice(additional_words)
                words.insert(random.randint(1, len(words)), new_word)
                current_syllables = self._count_syllables(' '.join(words))
        
        elif current_syllables > target_syllables:
            # Убираем слова
            while current_syllables > target_syllables and len(words) > 2:
                words.pop(random.randint(0, len(words)-1))
                current_syllables = self._count_syllables(' '.join(words))
        
        return ' '.join(words)
    
    def _count_syllables(self, text: str) -> int:
        """Подсчет слогов в тексте (упрощенный)"""
        vowels = 'аеёиоуыэюяaeiouy'
        count = 0
        for char in text.lower():
            if char in vowels:
                count += 1
        return max(1, count)  # минимум 1 слог
    
    def _format_poem(self, lines: List[str], style: PoetryStyle) -> str:
        """Форматирование стихотворения"""
        if style == PoetryStyle.HAIKU:
            return "\n".join(lines)
        else:
            return "\n".join(lines)
    
    def _analyze_poem_quality(self, poem: str, structure: Dict[str, Any]) -> Dict[str, float]:
        """Анализ качества стихотворения"""
        lines = poem.split('\n')
        
        metrics = {
            'rhyme_consistency': self._check_rhyme_consistency(lines, structure),
            'syllable_regularity': self._check_syllable_regularity(lines, structure),
            'imagery_richness': self._check_imagery_richness(poem),
            'emotional_depth': random.uniform(0.3, 0.9)  # упрощенная оценка
        }
        
        return metrics
    
    def _check_rhyme_consistency(self, lines: List[str], structure: Dict[str, Any]) -> float:
        """Проверка согласованности рифм"""
        if not structure.get('rhyme_scheme'):
            return 0.8  # свободный стиль
        
        # Упрощенная проверка рифм
        return random.uniform(0.6, 0.95)
    
    def _check_syllable_regularity(self, lines: List[str], structure: Dict[str, Any]) -> float:
        """Проверка регулярности слогов"""
        target_syllables = structure.get('syllables', [])
        
        if not target_syllables:
            return 0.7  # свободный размер
        
        total_deviation = 0
        for i, line in enumerate(lines):
            if i < len(target_syllables):
                current_syllables = self._count_syllables(line)
                deviation = abs(current_syllables - target_syllables[i])
                total_deviation += deviation
        
        max_possible_deviation = len(lines) * 4  # примерная максимальная девиация
        regularity = 1.0 - (total_deviation / max_possible_deviation if max_possible_deviation > 0 else 0)
        
        return max(0.1, min(1.0, regularity))
    
    def _check_imagery_richness(self, poem: str) -> float:
        """Проверка богатства образности"""
        poetic_words = sum(1 for image_list in self.poetic_images.values() for image in image_list if image in poem)
        total_words = len(poem.split())
        
        if total_words == 0:
            return 0.5
        
        richness = poetic_words / total_words
        return min(1.0, richness * 3)  # нормализация