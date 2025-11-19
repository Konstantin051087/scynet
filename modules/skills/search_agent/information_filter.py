"""
Фильтр информации по релевантности и качеству
"""

import re
from typing import List, Dict, Set
from datetime import datetime, timedelta
import logging
from collections import Counter

logger = logging.getLogger(__name__)

class InformationFilter:
    """Система фильтрации и ранжирования информации"""
    
    def __init__(self):
        self.spam_indicators = [
            r'купит[ье]', r'закажит[ье]', r'скидк[аи]', r'акци[яи]', r'распродаж',
            r'бесплатно', r'только сегодня', r'успей', r'выгодно', r'предложени[ея]'
        ]
        self.quality_indicators = [
            r'исследовани[ея]', r'анализ', r'эксперт', r'учен[ыые]', 
            r'доказано', r'статистик', r'данные', r'источник'
        ]
    
    async def filter_by_relevance(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Фильтрация результатов по релевантности запросу
        
        Args:
            results: список результатов
            query: оригинальный запрос
            
        Returns:
            List[Dict]: отфильтрованные и отсортированные результаты
        """
        filtered_results = []
        
        for result in results:
            # Расчет релевантности
            relevance_score = self._calculate_relevance(result, query)
            
            # Проверка на спам
            spam_score = self._calculate_spam_score(result)
            
            # Проверка качества
            quality_score = self._calculate_quality_score(result)
            
            # Общий скор
            total_score = (
                relevance_score * 0.5 + 
                (1 - spam_score) * 0.3 + 
                quality_score * 0.2
            )
            
            result['relevance_score'] = relevance_score
            result['spam_score'] = spam_score
            result['quality_score'] = quality_score
            result['total_score'] = total_score
            
            # Фильтрация по минимальному порогу
            if total_score >= 0.3 and spam_score <= 0.7:
                filtered_results.append(result)
        
        # Сортировка по общему скору
        return sorted(filtered_results, key=lambda x: x['total_score'], reverse=True)
    
    async def filter_by_date(self, results: List[Dict], 
                           days_back: int = 30) -> List[Dict]:
        """Фильтрация по дате (актуальность)"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        filtered_results = []
        for result in results:
            # Предполагаем, что timestamp есть в результате
            result_time = datetime.fromtimestamp(result.get('timestamp', 0))
            
            if result_time >= cutoff_date:
                result['days_old'] = (datetime.now() - result_time).days
                filtered_results.append(result)
        
        return sorted(filtered_results, key=lambda x: x.get('timestamp', 0), reverse=True)
    
    async def filter_by_source_quality(self, results: List[Dict], 
                                     min_trust_level: str = "medium") -> List[Dict]:
        """Фильтрация по качеству источника"""
        trust_levels = {"untrusted": 0, "low": 1, "medium": 2, "high": 3}
        min_level = trust_levels[min_trust_level]
        
        filtered_results = []
        for result in results:
            source_trust = result.get('source_trust_level', 'untrusted')
            if trust_levels.get(source_trust, 0) >= min_level:
                filtered_results.append(result)
        
        return filtered_results
    
    def _calculate_relevance(self, result: Dict, query: str) -> float:
        """Расчет релевантности результата запросу"""
        content = f"{result.get('title', '')} {result.get('description', '')} {result.get('content', '')}"
        content_lower = content.lower()
        query_lower = query.lower()
        
        query_terms = query_lower.split()
        
        if not query_terms:
            return 0.0
        
        # Простой подсчет совпадений
        term_matches = sum(1 for term in query_terms if term in content_lower)
        base_score = term_matches / len(query_terms)
        
        # Бонус за точное совпадение фразы
        phrase_bonus = 0.3 if query_lower in content_lower else 0.0
        
        # Бонус за совпадение в title
        title_bonus = 0.2
        if 'title' in result:
            title_matches = sum(1 for term in query_terms if term in result['title'].lower())
            title_bonus = (title_matches / len(query_terms)) * 0.2
        
        return min(base_score + phrase_bonus + title_bonus, 1.0)
    
    def _calculate_spam_score(self, result: Dict) -> float:
        """Расчет скора спамности контента"""
        content = f"{result.get('title', '')} {result.get('description', '')}"
        content_lower = content.lower()
        
        spam_indicators_found = 0
        for pattern in self.spam_indicators:
            if re.search(pattern, content_lower):
                spam_indicators_found += 1
        
        # Нормализация по количеству индикаторов
        spam_score = min(spam_indicators_found / len(self.spam_indicators), 1.0)
        
        # Дополнительные факторы спама
        url = result.get('url', '')
        if self._is_suspicious_url(url):
            spam_score = max(spam_score, 0.7)
        
        return spam_score
    
    def _calculate_quality_score(self, result: Dict) -> float:
        """Расчет скора качества контента"""
        content = result.get('content', '')
        if not content:
            return 0.3
        
        quality_indicators_found = 0
        for pattern in self.quality_indicators:
            if re.search(pattern, content.lower()):
                quality_indicators_found += 1
        
        base_score = min(quality_indicators_found / len(self.quality_indicators), 1.0)
        
        # Бонусы за структуру контента
        structure_bonus = 0.0
        
        # Длина контента
        content_length = len(content.split())
        if content_length > 500:
            structure_bonus += 0.2
        elif content_length > 200:
            structure_bonus += 0.1
        
        # Наличие структуры
        if '\n\n' in content or '•' in content or '-' in content:
            structure_bonus += 0.1
        
        return min(base_score + structure_bonus, 1.0)
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Проверка URL на подозрительные паттерны"""
        suspicious_patterns = [
            r'bit\.ly', r'tinyurl\.com', r'goo\.gl', r'click\.ru',
            r'[0-9]{4,}', r'[a-z0-9]{10,}',  # Длинные случайные строки
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url.lower()):
                return True
        
        return False
    
    async def remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Удаление дубликатов контента"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            content_signature = self._create_content_signature(result)
            
            if content_signature not in seen_content:
                seen_content.add(content_signature)
                unique_results.append(result)
        
        return unique_results
    
    def _create_content_signature(self, result: Dict) -> str:
        """Создание сигнатуры контента для обнаружения дубликатов"""
        key_content = f"{result.get('title', '')} {result.get('description', '')}"
        
        # Упрощение контента для сравнения
        simplified = re.sub(r'\s+', ' ', key_content.lower())
        words = simplified.split()
        
        # Используем первые 10 слов как сигнатуру
        return ' '.join(words[:10]) if words else ''