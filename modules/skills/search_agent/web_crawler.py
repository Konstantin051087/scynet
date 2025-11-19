"""
Веб-краулер для обхода сайтов и сбора информации
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import time
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class WebCrawler:
    """Асинхронный веб-краулер с поддержкой robots.txt"""
    
    def __init__(self, rate_limit: float = 1.0, max_depth: int = 2):
        self.rate_limit = rate_limit  # Задержка между запросами
        self.max_depth = max_depth
        self.visited_urls = set()
        self.robot_parsers = {}
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Scynet-Search-Agent/1.0 (+https://github.com/scynet-ai)'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def can_fetch(self, url: str) -> bool:
        """Проверка разрешения на сканирование по robots.txt"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if base_url not in self.robot_parsers:
            robot_url = urljoin(base_url, '/robots.txt')
            parser = RobotFileParser()
            
            try:
                async with self.session.get(robot_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        parser.parse(content.splitlines())
                self.robot_parsers[base_url] = parser
            except Exception as e:
                logger.warning(f"Не удалось загрузить robots.txt для {base_url}: {e}")
                return True
        
        return self.robot_parsers[base_url].can_fetch('*', url)
    
    async def fetch_page(self, url: str) -> Optional[Dict]:
        """Получение и парсинг веб-страницы"""
        if url in self.visited_urls:
            return None
            
        if not await self.can_fetch(url):
            logger.info(f"Доступ запрещен robots.txt: {url}")
            return None
        
        try:
            await asyncio.sleep(self.rate_limit)  # Ограничение частоты запросов
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Извлечение основного контента
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else ""
                    
                    # Удаление скриптов и стилей
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Извлечение текста
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # Извлечение мета-описания
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    description = meta_desc['content'] if meta_desc else text[:200] + "..."
                    
                    self.visited_urls.add(url)
                    
                    return {
                        'url': url,
                        'title': title_text,
                        'description': description,
                        'content': text[:5000],  # Ограничение контента
                        'timestamp': time.time()
                    }
                    
        except Exception as e:
            logger.error(f"Ошибка при сканировании {url}: {e}")
            
        return None
    
    async def crawl(self, start_url: str, max_pages: int = 10) -> List[Dict]:
        """Рекурсивное сканирование сайта"""
        if not self.session:
            async with self as crawler:
                return await crawler._crawl_recursive(start_url, max_pages, 0)
        else:
            return await self._crawl_recursive(start_url, max_pages, 0)
    
    async def _crawl_recursive(self, url: str, max_pages: int, depth: int) -> List[Dict]:
        """Рекурсивная функция сканирования"""
        if depth > self.max_depth or len(self.visited_urls) >= max_pages:
            return []
        
        page_data = await self.fetch_page(url)
        if not page_data:
            return []
        
        results = [page_data]
        
        # Извлечение ссылок для дальнейшего сканирования
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    links = []
                    for link in soup.find_all('a', href=True):
                        absolute_url = urljoin(url, link['href'])
                        if self._is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                            links.append(absolute_url)
                    
                    # Рекурсивное сканирование найденных ссылок
                    for link in links[:5]:  # Ограничение количества ссылок для сканирования
                        if len(results) < max_pages:
                            sub_results = await self._crawl_recursive(link, max_pages, depth + 1)
                            results.extend(sub_results)
                            
        except Exception as e:
            logger.error(f"Ошибка при обработке ссылок на {url}: {e}")
        
        return results
    
    def _is_valid_url(self, url: str) -> bool:
        """Проверка валидности URL"""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme) and parsed.scheme in ['http', 'https']