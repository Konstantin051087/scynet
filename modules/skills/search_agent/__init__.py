"""
Модуль поискового агента - отвечает за поиск и верификацию информации из внешних источников
"""

import logging
from typing import Dict, Any, Optional, List

from .web_crawler import WebCrawler
from .search_engine import SearchEngine
from .source_evaluator import SourceEvaluator
from .information_filter import InformationFilter
from .fact_checker import FactChecker

class SearchAgentModule:
    """Основной класс поискового агента"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.crawler = WebCrawler()
        self.engine = SearchEngine()
        self.evaluator = SourceEvaluator()
        self.filter = InformationFilter()
        self.fact_checker = FactChecker()
        
        self.initialized = False
    
    async def initialize(self):
        """Инициализация модуля"""
        try:
            # Инициализация компонентов (если потребуется асинхронная инициализация)
            # Для компонентов без метода initialize просто пропускаем
            if hasattr(self.crawler, 'initialize'):
                await self.crawler.initialize()
            
            if hasattr(self.engine, 'initialize'):
                await self.engine.initialize()
            else:
                # Для SearchEngine создаем сессию вручную
                self.engine.session = None  # Будет создан при первом использовании
            
            if hasattr(self.evaluator, 'initialize'):
                await self.evaluator.initialize()
            
            if hasattr(self.filter, 'initialize'):
                await self.filter.initialize()
            
            if hasattr(self.fact_checker, 'initialize'):
                await self.fact_checker.initialize()
            
            self.initialized = True
            self.logger.info("SearchAgentModule успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации SearchAgentModule: {e}")
            self.initialized = False
    
    async def search(self, query: str, max_results: int = 10) -> dict:
        """
        Основной метод поиска информации
        
        Args:
            query: поисковый запрос
            max_results: максимальное количество результатов
            
        Returns:
            dict: структурированные результаты поиска
        """
        if not self.initialized:
            self.logger.warning("SearchAgentModule не инициализирован, но используется")
        
        try:
            # Поиск через поисковый движок
            search_results = await self.engine.search(query, max_results)
            
            # Оценка источников
            evaluated_results = []
            for result in search_results:
                evaluation = await self.evaluator.evaluate_source(result['url'])
                result['source_credibility'] = evaluation['score']
                result['source_trust_level'] = evaluation['trust_level']
                evaluated_results.append(result)
            
            # Фильтрация по релевантности
            filtered_results = await self.filter.filter_by_relevance(
                evaluated_results, query
            )
            
            # Проверка фактов для топ-результатов
            verified_results = []
            for result in filtered_results[:3]:  # Проверяем только топ-3
                verification_result = await self.fact_checker.verify_fact(result.get('content', ''))
                result['fact_verified'] = verification_result.get('overall_status') in ['highly_verified', 'mostly_verified']
                verified_results.append(result)
            
            return {
                'query': query,
                'total_results': len(filtered_results),
                'verified_results': verified_results,
                'all_results': filtered_results
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска для запроса '{query}': {e}")
            return {
                'query': query,
                'total_results': 0,
                'verified_results': [],
                'all_results': [],
                'error': str(e)
            }
    
    async def crawl_website(self, url: str, max_pages: int = 10) -> Dict[str, Any]:
        """
        Обход веб-сайта
        
        Args:
            url: URL сайта для обхода
            max_pages: максимальное количество страниц
            
        Returns:
            Dict: Результаты обхода
        """
        try:
            return await self.crawler.crawl(url, max_pages)
        except Exception as e:
            self.logger.error(f"Ошибка обхода сайта {url}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def evaluate_source(self, url: str) -> Dict[str, Any]:
        """
        Оценка достоверности источника
        
        Args:
            url: URL источника
            
        Returns:
            Dict: Результаты оценки
        """
        try:
            return await self.evaluator.evaluate_source(url)
        except Exception as e:
            self.logger.error(f"Ошибка оценки источника {url}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def verify_fact(self, fact: str) -> Dict[str, Any]:
        """
        Проверка факта
        
        Args:
            fact: Факт для проверки
            
        Returns:
            Dict: Результаты проверки
        """
        try:
            result = await self.fact_checker.verify_fact(fact)
            return {"status": "success", "verified": result}
        except Exception as e:
            self.logger.error(f"Ошибка проверки факта '{fact}': {e}")
            return {"status": "error", "error": str(e)}
    
    def get_module_info(self) -> Dict[str, Any]:
        """Получение информации о модуле"""
        return {
            "name": "search_agent",
            "version": "1.0",
            "description": "Модуль поиска и верификации информации",
            "initialized": self.initialized,
            "components": {
                "web_crawler": True,
                "search_engine": True,
                "source_evaluator": True,
                "information_filter": True,
                "fact_checker": True
            }
        }

# Экспортируем основной класс и все остальные
__all__ = [
    'SearchAgentModule',
    'WebCrawler',
    'SearchEngine', 
    'SourceEvaluator',
    'InformationFilter',
    'FactChecker'
]