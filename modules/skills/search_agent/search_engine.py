"""
Поисковый движок для выполнения запросов к различным поисковым системам
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SearchEngine:
    """Унифицированный поисковый движок с поддержкой multiple источников"""
    
    def __init__(self):
        self.sources = {
            'duckduckgo': self._search_duckduckgo,
            'news_api': self._search_news_api,
            'custom_web': self._search_custom_web
        }
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search(self, query: str, max_results: int = 10, 
                    sources: List[str] = None) -> List[Dict]:
        """
        Выполнение поискового запроса
        
        Args:
            query: поисковый запрос
            max_results: максимальное количество результатов
            sources: список источников для поиска
            
        Returns:
            List[Dict]: список результатов поиска
        """
        if sources is None:
            sources = ['duckduckgo', 'custom_web']
        
        all_results = []
        
        # Асинхронный поиск по всем источникам
        tasks = []
        for source in sources:
            if source in self.sources:
                task = self.sources[source](query, max_results)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Объединение и сортировка результатов
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
        
        # Сортировка по релевантности (можно улучшить алгоритмом ранжирования)
        sorted_results = sorted(all_results, 
                              key=lambda x: x.get('relevance_score', 0), 
                              reverse=True)
        
        return sorted_results[:max_results]
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        """Поиск через DuckDuckGo Instant Answer API"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # Извлечение прямого ответа
                    if data.get('AbstractText'):
                        results.append({
                            'title': data.get('Heading', 'Прямой ответ'),
                            'url': data.get('AbstractURL', ''),
                            'description': data.get('AbstractText', ''),
                            'content': data.get('AbstractText', ''),
                            'source': 'duckduckgo_direct',
                            'relevance_score': 0.9
                        })
                    
                    # Извлечение связанных тем
                    for topic in data.get('RelatedTopics', [])[:max_results]:
                        if 'FirstURL' in topic and 'Text' in topic:
                            results.append({
                                'title': topic['Text'].split(' - ')[0] if ' - ' in topic['Text'] else topic['Text'],
                                'url': topic['FirstURL'],
                                'description': topic['Text'],
                                'content': topic['Text'],
                                'source': 'duckduckgo_related',
                                'relevance_score': 0.7
                            })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Ошибка поиска DuckDuckGo: {e}")
            
        return []
    
    async def _search_news_api(self, query: str, max_results: int) -> List[Dict]:
        """Поиск через NewsAPI (требует API ключ)"""
        # Заглушка - в реальной реализации требуется API ключ
        logger.info("NewsAPI поиск требует настройки API ключа")
        return []
    
    async def _search_custom_web(self, query: str, max_results: int) -> List[Dict]:
        """Кастомный веб-поиск через сканирование доверенных источников"""
        from .web_crawler import WebCrawler
        
        results = []
        trusted_sources = self._load_trusted_sources()
        
        async with WebCrawler() as crawler:
            # Поиск по доверенным источникам
            for source in trusted_sources[:3]:  # Ограничение для демонстрации
                try:
                    # Сканирование главной страницы источника
                    source_results = await crawler.crawl(source, max_pages=2)
                    
                    # Фильтрация по релевантности запросу
                    for page in source_results:
                        if self._is_relevant(page['content'], query):
                            page['source'] = 'custom_crawl'
                            page['relevance_score'] = self._calculate_relevance(
                                page['content'], query
                            )
                            results.append(page)
                            
                            if len(results) >= max_results:
                                return results
                                
                except Exception as e:
                    logger.error(f"Ошибка сканирования {source}: {e}")
        
        return results
    
    def _is_relevant(self, content: str, query: str) -> bool:
        """Проверка релевантности контента запросу"""
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        # Простой алгоритм релевантности
        matches = sum(1 for term in query_terms if term in content_lower)
        return matches >= len(query_terms) * 0.5  # 50% совпадений
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """Расчет скора релевантности"""
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        total_terms = len(query_terms)
        if total_terms == 0:
            return 0.0
            
        matches = sum(1 for term in query_terms if term in content_lower)
        base_score = matches / total_terms
        
        # Бонус за точное совпадение фразы
        if query.lower() in content_lower:
            base_score += 0.3
            
        return min(base_score, 1.0)
    
    def _load_trusted_sources(self) -> List[str]:
        """Загрузка списка доверенных источников"""
        try:
            with open('skills/search_agent/trusted_sources.list', 'r', encoding='utf-8') as f:
                sources = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return sources
        except FileNotFoundError:
            # Возвращаем источники по умолчанию
            return [
                'https://ru.wikipedia.org',
                'https://habr.com',
                'https://stackoverflow.com'
            ]