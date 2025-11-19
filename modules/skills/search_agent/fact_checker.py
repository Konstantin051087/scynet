"""
Система проверки фактов и достоверности информации
"""

import re
import asyncio
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FactChecker:
    """Система верификации фактов и проверки достоверности информации"""
    
    def __init__(self):
        self.known_facts = self._load_known_facts()
        self.contradiction_patterns = [
            (r'всегда', r'никогда'),
            (r'полностью', r'частично'),
            (r'точно', r'возможно'),
            (r'доказано', r'опровергнуто')
        ]
        
    async def verify_fact(self, content: str, context: Dict = None) -> Dict:
        """
        Проверка факта в контенте
        
        Args:
            content: текст для проверки
            context: дополнительный контекст
            
        Returns:
            Dict: результаты проверки
        """
        # Извлечение утверждений из контента
        claims = self._extract_claims(content)
        
        verification_results = []
        overall_confidence = 0.0
        verified_claims = 0
        
        for claim in claims:
            result = await self._verify_single_claim(claim, context)
            verification_results.append(result)
            
            if result['status'] == 'verified':
                verified_claims += 1
                overall_confidence += result['confidence']
            elif result['status'] == 'partially_verified':
                verified_claims += 0.5
                overall_confidence += result['confidence'] * 0.5
        
        total_claims = len(claims)
        verification_ratio = verified_claims / total_claims if total_claims > 0 else 1.0
        
        # Определение общего статуса проверки
        if verification_ratio >= 0.8:
            overall_status = 'highly_verified'
        elif verification_ratio >= 0.6:
            overall_status = 'mostly_verified'
        elif verification_ratio >= 0.4:
            overall_status = 'partially_verified'
        else:
            overall_status = 'poorly_verified'
        
        return {
            'content_preview': content[:200] + '...' if len(content) > 200 else content,
            'total_claims': total_claims,
            'verified_claims': verified_claims,
            'verification_ratio': round(verification_ratio, 2),
            'overall_status': overall_status,
            'overall_confidence': round(overall_confidence / total_claims, 2) if total_claims > 0 else 0.0,
            'detailed_results': verification_results,
            'check_timestamp': datetime.now().isoformat()
        }
    
    def _extract_claims(self, content: str) -> List[str]:
        """Извлечение утверждений из текста"""
        # Паттерны для идентификации утверждений
        claim_patterns = [
            r'[А-Я][^.!?]*\b(является|это|составляет|равен|находится)\b[^.!?]*[.!?]',
            r'[А-Я][^.!?]*\b(доказано|установлено|известно)\b[^.!?]*[.!?]',
            r'[А-Я][^.!?]*\b(согласно|по данным|по информации)\b[^.!?]*[.!?]',
        ]
        
        claims = []
        for pattern in claim_patterns:
            matches = re.findall(pattern, content)
            claims.extend(matches)
        
        # Если утверждений не найдено, разбиваем на предложения
        if not claims:
            sentences = re.split(r'[.!?]+', content)
            claims = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return claims[:10]  # Ограничение количества утверждений
    
    async def _verify_single_claim(self, claim: str, context: Dict = None) -> Dict:
        """Проверка отдельного утверждения"""
        # Нормализация утверждения
        normalized_claim = self._normalize_claim(claim)
        
        # Проверка на внутреннюю противоречивость
        internal_consistency = self._check_internal_consistency(normalized_claim)
        
        # Проверка против базы известных фактов
        fact_check = await self._check_against_known_facts(normalized_claim)
        
        # Анализ уверенности в утверждении
        confidence_indicators = self._analyze_confidence_indicators(claim)
        
        # Определение статуса проверки
        status, confidence = self._determine_verification_status(
            internal_consistency, fact_check, confidence_indicators
        )
        
        return {
            'original_claim': claim,
            'normalized_claim': normalized_claim,
            'status': status,
            'confidence': confidence,
            'internal_consistency': internal_consistency,
            'fact_check': fact_check,
            'confidence_indicators': confidence_indicators,
            'flags': self._identify_red_flags(claim)
        }
    
    def _normalize_claim(self, claim: str) -> str:
        """Нормализация утверждения для сравнения"""
        # Приведение к нижнему регистру
        normalized = claim.lower()
        
        # Удаление лишних пробелов
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Удаление некоторых модификаторов
        modifiers = [
            r'возможно\s+', r'вероятно\s+', r'скорее всего\s+', 
            r'очевидно\s+', r'несомненно\s+', r'точно\s+'
        ]
        
        for modifier in modifiers:
            normalized = re.sub(modifier, '', normalized)
        
        return normalized.strip()
    
    def _check_internal_consistency(self, claim: str) -> Dict:
        """Проверка внутренней противоречивости утверждения"""
        flags = []
        score = 1.0
        
        # Проверка на абсолютные утверждения
        absolute_terms = ['всегда', 'никогда', 'все', 'никто', 'абсолютно']
        found_absolutes = [term for term in absolute_terms if term in claim]
        if found_absolutes:
            flags.append(f"Абсолютные утверждения: {found_absolutes}")
            score -= 0.3
        
        # Проверка на противоречивые пары
        for term1, term2 in self.contradiction_patterns:
            if re.search(term1, claim) and re.search(term2, claim):
                flags.append(f"Противоречивые термины: {term1}/{term2}")
                score -= 0.5
        
        # Проверка на двойное отрицание
        negation_count = len(re.findall(r'\bне\b', claim))
        if negation_count >= 2:
            flags.append("Множественное отрицание")
            score -= 0.2
        
        return {
            'score': max(0.0, score),
            'flags': flags,
            'is_consistent': score >= 0.7
        }
    
    async def _check_against_known_facts(self, claim: str) -> Dict:
        """Проверка утверждения против базы известных фактов"""
        best_match = None
        best_score = 0.0
        
        for known_fact, fact_data in self.known_facts.items():
            similarity = self._calculate_similarity(claim, known_fact)
            
            if similarity > best_score and similarity > 0.6:
                best_score = similarity
                best_match = {
                    'known_fact': known_fact,
                    'similarity': similarity,
                    'fact_data': fact_data
                }
        
        if best_match:
            return {
                'status': 'matched',
                'match_confidence': best_score,
                'known_fact': best_match['known_fact'],
                'fact_veracity': best_match['fact_data']['veracity']
            }
        else:
            return {
                'status': 'unknown',
                'match_confidence': 0.0,
                'known_fact': None,
                'fact_veracity': None
            }
    
    def _analyze_confidence_indicators(self, claim: str) -> Dict:
        """Анализ индикаторов уверенности в утверждении"""
        confidence_score = 0.5  # Базовый скор
        
        # Положительные индикаторы
        positive_indicators = [
            (r'согласно исследованию', 0.3),
            (r'по данным', 0.2),
            (r'статистика показывает', 0.2),
            (r'эксперты подтверждают', 0.2),
            (r'доказано', 0.3)
        ]
        
        # Отрицательные индикаторы
        negative_indicators = [
            (r'возможно', -0.2),
            (r'вероятно', -0.2),
            (r'может быть', -0.2),
            (r'скорее всего', -0.1),
            (r'говорят что', -0.3),
            (r'ходят слухи', -0.4)
        ]
        
        # Применение индикаторов
        for pattern, weight in positive_indicators:
            if re.search(pattern, claim.lower()):
                confidence_score += weight
        
        for pattern, weight in negative_indicators:
            if re.search(pattern, claim.lower()):
                confidence_score += weight
        
        return {
            'score': max(0.0, min(1.0, confidence_score)),
            'indicators_found': len([p for p, _ in positive_indicators if re.search(p, claim.lower())]) +
                              len([p for p, _ in negative_indicators if re.search(p, claim.lower())])
        }
    
    def _identify_red_flags(self, claim: str) -> List[str]:
        """Идентификация красных флагов в утверждении"""
        red_flags = []
        
        red_flag_patterns = {
            'emotional_language': [r'шок', r'сенсац', r'невероятн', r'потрясающ'],
            'urgency': [r'срочно', r'немедленно', r'только сейчас', r'успей'],
            'conspiracy': [r'заговор', r'скрывают', r'правда которую', r'они не хотят'],
            'pseudoscience': [r'энергия', r'вибрац', r'аура', r'биополе']
        }
        
        for flag_type, patterns in red_flag_patterns.items():
            for pattern in patterns:
                if re.search(pattern, claim.lower()):
                    red_flags.append(flag_type)
                    break
        
        return red_flags
    
    def _determine_verification_status(self, consistency: Dict, 
                                    fact_check: Dict, 
                                    confidence: Dict) -> Tuple[str, float]:
        """Определение итогового статуса проверки"""
        base_confidence = (
            consistency['score'] * 0.3 +
            (fact_check['match_confidence'] if fact_check['status'] == 'matched' else 0.2) * 0.4 +
            confidence['score'] * 0.3
        )
        
        if fact_check['status'] == 'matched':
            if fact_check['fact_veracity'] == 'true':
                return 'verified', min(base_confidence + 0.2, 1.0)
            elif fact_check['fact_veracity'] == 'false':
                return 'refuted', min(base_confidence + 0.1, 1.0)
        
        if base_confidence >= 0.7:
            return 'likely_true', base_confidence
        elif base_confidence >= 0.5:
            return 'partially_verified', base_confidence
        elif base_confidence >= 0.3:
            return 'uncertain', base_confidence
        else:
            return 'likely_false', base_confidence
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Расчет схожести между двумя текстами"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _load_known_facts(self) -> Dict:
        """Загрузка базы известных фактов"""
        # В реальной системе это должна быть полноценная база данных
        return {
            "земля вращается вокруг солнца": {
                "veracity": "true",
                "category": "science",
                "confidence": 0.99
            },
            "вода кипит при 100 градусах цельсия": {
                "veracity": "true", 
                "category": "science",
                "confidence": 0.95
            },
            "холодная вода закипает быстрее горячей": {
                "veracity": "false",
                "category": "science", 
                "confidence": 0.90
            },
            "великая китайская стена видна из космоса": {
                "veracity": "false",
                "category": "geography",
                "confidence": 0.85
            }
        }