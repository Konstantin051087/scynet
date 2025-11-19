"""
Оценщик достоверности источников информации
"""

import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import datetime
import logging

logger = logging.getLogger(__name__)

class SourceEvaluator:
    """Система оценки достоверности и надежности источников"""
    
    def __init__(self):
        self.trust_domains = self._load_trusted_domains()
        self.suspicious_patterns = [
            r'fake', r'false', r'hoax', r'conspiracy', r'unverified',
            r'clickbait', r'sensational', r'exaggerated'
        ]
        
    async def evaluate_source(self, url: str, content: str = None) -> Dict:
        """
        Комплексная оценка источника
        
        Args:
            url: URL источника
            content: контент для анализа (опционально)
            
        Returns:
            Dict: результаты оценки
        """
        domain_analysis = self._analyze_domain(url)
        credibility_score = self._calculate_credibility_score(domain_analysis)
        
        if content:
            content_analysis = await self._analyze_content(content)
            credibility_score = (credibility_score + content_analysis['score']) / 2
        else:
            content_analysis = {'score': 0.5, 'flags': []}
        
        trust_level = self._determine_trust_level(credibility_score)
        
        return {
            'url': url,
            'domain': domain_analysis['domain'],
            'credibility_score': round(credibility_score, 2),
            'trust_level': trust_level,
            'domain_analysis': domain_analysis,
            'content_analysis': content_analysis,
            'recommendation': self._get_recommendation(credibility_score)
        }
    
    def _analyze_domain(self, url: str) -> Dict:
        """Анализ домена источника"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        analysis = {
            'domain': domain,
            'is_trusted': domain in self.trust_domains,
            'domain_age_score': 0.5,  # Заглушка - в реальности нужен WHOIS
            'ssl_score': 1.0 if parsed.scheme == 'https' else 0.0,
            'suspicious_keywords': []
        }
        
        # Проверка на подозрительные ключевые слова в домене
        for pattern in self.suspicious_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                analysis['suspicious_keywords'].append(pattern)
        
        # Бонус за известные доверенные домены
        if analysis['is_trusted']:
            analysis['domain_age_score'] = 0.9
        
        return analysis
    
    async def _analyze_content(self, content: str) -> Dict:
        """Анализ контента на достоверность"""
        flags = []
        score = 0.7  # Базовый скор
        
        # Проверка эмоциональной окраски
        emotional_words = self._detect_emotional_language(content)
        if emotional_words:
            flags.append(f"Эмоциональный язык: {emotional_words}")
            score -= 0.1
        
        # Проверка на наличие утверждений без источников
        unsourced_claims = self._find_unsourced_claims(content)
        if unsourced_claims > 3:
            flags.append(f"Много утверждений без источников: {unsourced_claims}")
            score -= 0.15
        
        # Проверка на наличие конкретных данных
        has_specific_data = self._has_specific_data(content)
        if has_specific_data:
            score += 0.1
        
        # Проверка структуры контента
        structure_score = self._analyze_content_structure(content)
        score += (structure_score - 0.5) * 0.2  # Нормализация
        
        return {
            'score': max(0.0, min(1.0, score)),
            'flags': flags,
            'emotional_words': emotional_words,
            'unsourced_claims': unsourced_claims,
            'has_specific_data': has_specific_data,
            'structure_score': structure_score
        }
    
    def _detect_emotional_language(self, content: str) -> List[str]:
        """Обнаружение эмоционально окрашенного языка"""
        emotional_patterns = [
            r'шок[а-я]*', r'сенсац[а-я]*', r'невероятн[а-я]*', r'потрясающ[а-я]*',
            r'ужас[а-я]*', r'кошмар[а-я]*', r'чудовищн[а-я]*', r'скандал[а-я]*',
            r'разоблач[а-я]*', r'шокирующ[а-я]*'
        ]
        
        found_words = []
        for pattern in emotional_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                found_words.extend(matches)
        
        return list(set(found_words))
    
    def _find_unsourced_claims(self, content: str) -> int:
        """Поиск утверждений без указания источников"""
        claim_indicators = [
            r'ученые сказали', r'эксперты считают', r'исследования показали',
            r'было установлено', r'доказано что', r'известно что'
        ]
        
        count = 0
        for indicator in claim_indicators:
            count += len(re.findall(indicator, content.lower()))
        
        return count
    
    def _has_specific_data(self, content: str) -> bool:
        """Проверка наличия конкретных данных (цифры, даты, имена)"""
        # Поиск цифр
        has_numbers = bool(re.search(r'\b\d+\b', content))
        
        # Поиск дат
        has_dates = bool(re.search(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}', content))
        
        # Поиск имен собственных (заглавные буквы)
        has_proper_names = bool(re.search(r'\b[А-Я][а-я]+\s[А-Я][а-я]+\b', content))
        
        return has_numbers or has_dates or has_proper_names
    
    def _analyze_content_structure(self, content: str) -> float:
        """Анализ структуры контента"""
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        
        if len(sentences) == 0 or len(words) == 0:
            return 0.3
        
        # Средняя длина предложения
        avg_sentence_length = len(words) / len(sentences)
        
        # Оценка читабельности
        if 10 <= avg_sentence_length <= 25:
            readability_score = 0.8
        elif 5 <= avg_sentence_length < 10 or 25 < avg_sentence_length <= 35:
            readability_score = 0.6
        else:
            readability_score = 0.3
        
        # Наличие структуры (абзацы, списки)
        has_structure = len(content.split('\n\n')) > 2 or '•' in content or '-' in content
        structure_score = 0.7 if has_structure else 0.3
        
        return (readability_score + structure_score) / 2
    
    def _calculate_credibility_score(self, domain_analysis: Dict) -> float:
        """Расчет общего скора достоверности"""
        score = 0.5  # Базовый скор
        
        # Вклад доменного анализа
        if domain_analysis['is_trusted']:
            score += 0.3
        else:
            score += domain_analysis['domain_age_score'] * 0.2
        
        score += domain_analysis['ssl_score'] * 0.1
        
        # Штраф за подозрительные ключевые слова
        penalty = len(domain_analysis['suspicious_keywords']) * 0.1
        score -= penalty
        
        return max(0.0, min(1.0, score))
    
    def _determine_trust_level(self, score: float) -> str:
        """Определение уровня доверия"""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "untrusted"
    
    def _get_recommendation(self, score: float) -> str:
        """Рекомендация по использованию источника"""
        if score >= 0.8:
            return "Надежный источник, можно использовать"
        elif score >= 0.6:
            return "Условно надежный источник, рекомендуется перепроверка"
        elif score >= 0.4:
            return "Низкая надежность, использовать с осторожностью"
        else:
            return "Ненадежный источник, не рекомендуется к использованию"
    
    def _load_trusted_domains(self) -> set:
        """Загрузка списка доверенных доменов"""
        try:
            with open('skills/search_agent/trusted_sources.list', 'r', encoding='utf-8') as f:
                domains = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parsed = urlparse(line if '://' in line else 'https://' + line)
                        domains.add(parsed.netloc.lower())
                return domains
        except FileNotFoundError:
            return {
                'wikipedia.org', 'ru.wikipedia.org', 'habr.com', 'stackoverflow.com',
                'github.com', 'arxiv.org', 'nasa.gov', 'bbc.com', 'reuters.com'
            }