"""
Поисковик в памяти - осуществляет поиск и извлечение информации из памяти
"""

import sqlite3
import logging
from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MemoryRetriever:
    """Осуществляет поиск и извлечение информации из памяти"""
    
    def __init__(self, config):
        self.config = config
    
    def retrieve_related_facts(self, query: str, limit: int = 10) -> List[Dict]:
        """Извлекает факты, связанные с запросом"""
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        
        try:
            # Поиск по всем полям факта
            search_pattern = f"%{query}%"
            cursor.execute('''
                SELECT id, subject, predicate, object, confidence, source, 
                       last_accessed, access_count
                FROM facts 
                WHERE subject LIKE ? OR predicate LIKE ? OR object LIKE ?
                ORDER BY confidence DESC, access_count DESC
                LIMIT ?
            ''', (search_pattern, search_pattern, search_pattern, limit))
            
            facts = []
            for row in cursor.fetchall():
                fact = {
                    'id': row[0],
                    'subject': row[1],
                    'predicate': row[2],
                    'object': row[3],
                    'confidence': row[4],
                    'source': row[5],
                    'last_accessed': row[6],
                    'access_count': row[7],
                    'relevance_score': self._calculate_relevance(query, row[1], row[2], row[3])
                }
                facts.append(fact)
            
            # Сортировка по релевантности
            facts.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Обновляем счетчик обращений
            for fact in facts:
                self._update_access_count(fact['id'])
            
            logger.debug(f"Найдено {len(facts)} фактов для запроса '{query}'")
            return facts
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка поиска фактов: {e}")
            return []
        finally:
            conn.close()
    
    def find_similar_episodes(self, description: str, user_id: str = None) -> List[Dict]:
        """Находит похожие эпизоды в памяти"""
        conn = sqlite3.connect(self.config.episodic_memory_path)
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('''
                    SELECT id, user_id, event_type, description, timestamp, 
                           emotional_context, importance_score
                    FROM episodes 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 50
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT id, user_id, event_type, description, timestamp, 
                           emotional_context, importance_score
                    FROM episodes 
                    ORDER BY timestamp DESC
                    LIMIT 50
                ''')
            
            episodes = []
            for row in cursor.fetchall():
                episode = {
                    'id': row[0],
                    'user_id': row[1],
                    'event_type': row[2],
                    'description': row[3],
                    'timestamp': row[4],
                    'emotional_context': json.loads(row[5]) if row[5] else {},
                    'importance_score': row[6],
                    'similarity_score': self._calculate_episode_similarity(description, row[3])
                }
                
                # Фильтруем по минимальной схожести
                if episode['similarity_score'] > 0.3:
                    episodes.append(episode)
            
            # Сортировка по схожести
            episodes.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.debug(f"Найдено {len(episodes)} похожих эпизодов")
            return episodes[:10]  # возвращаем топ-10
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка поиска похожих эпизодов: {e}")
            return []
        finally:
            conn.close()
    
    def get_user_episodes(self, user_id: str, days_back: int = 30, 
                         event_type: str = None) -> List[Dict]:
        """Получает эпизоды пользователя за указанный период"""
        conn = sqlite3.connect(self.config.episodic_memory_path)
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d %H:%M:%S')
            
            if event_type:
                cursor.execute('''
                    SELECT id, event_type, description, timestamp, emotional_context, importance_score
                    FROM episodes 
                    WHERE user_id = ? AND timestamp > ? AND event_type = ?
                    ORDER BY timestamp DESC
                ''', (user_id, cutoff_date, event_type))
            else:
                cursor.execute('''
                    SELECT id, event_type, description, timestamp, emotional_context, importance_score
                    FROM episodes 
                    WHERE user_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                ''', (user_id, cutoff_date))
            
            episodes = []
            for row in cursor.fetchall():
                episode = {
                    'id': row[0],
                    'event_type': row[1],
                    'description': row[2],
                    'timestamp': row[3],
                    'emotional_context': json.loads(row[4]) if row[4] else {},
                    'importance_score': row[5]
                }
                episodes.append(episode)
            
            return episodes
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения эпизодов пользователя: {e}")
            return []
        finally:
            conn.close()
    
    def search_knowledge_graph(self, entity_name: str, relationship_type: str = None) -> List[Dict]:
        """Ищет связи в графе знаний"""
        conn = sqlite3.connect(self.config.knowledge_graph_path)
        cursor = conn.cursor()
        
        try:
            # Сначала находим entity
            cursor.execute('''
                SELECT id, name, type, attributes 
                FROM entities 
                WHERE name LIKE ?
            ''', (f"%{entity_name}%",))
            
            entities = cursor.fetchall()
            if not entities:
                return []
            
            results = []
            for entity in entities:
                entity_id, name, entity_type, attributes = entity
                
                # Находим связи
                if relationship_type:
                    cursor.execute('''
                        SELECT r.relationship_type, r.confidence, e2.name, e2.type
                        FROM relationships r
                        JOIN entities e2 ON r.target_id = e2.id
                        WHERE r.source_id = ? AND r.relationship_type = ?
                        UNION
                        SELECT r.relationship_type, r.confidence, e2.name, e2.type
                        FROM relationships r
                        JOIN entities e2 ON r.source_id = e2.id
                        WHERE r.target_id = ? AND r.relationship_type = ?
                    ''', (entity_id, relationship_type, entity_id, relationship_type))
                else:
                    cursor.execute('''
                        SELECT r.relationship_type, r.confidence, e2.name, e2.type
                        FROM relationships r
                        JOIN entities e2 ON r.target_id = e2.id
                        WHERE r.source_id = ?
                        UNION
                        SELECT r.relationship_type, r.confidence, e2.name, e2.type
                        FROM relationships r
                        JOIN entities e2 ON r.source_id = e2.id
                        WHERE r.target_id = ?
                    ''', (entity_id, entity_id))
                
                relationships = cursor.fetchall()
                
                for rel in relationships:
                    result = {
                        'source_entity': name,
                        'source_type': entity_type,
                        'relationship': rel[0],
                        'confidence': rel[1],
                        'target_entity': rel[2],
                        'target_type': rel[3],
                        'attributes': json.loads(attributes) if attributes else {}
                    }
                    results.append(result)
            
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка поиска в графе знаний: {e}")
            return []
        finally:
            conn.close()
    
    def _calculate_relevance(self, query: str, subject: str, predicate: str, object: str) -> float:
        """Вычисляет релевантность факта запросу"""
        query_words = set(re.findall(r'\w+', query.lower()))
        fact_text = f"{subject} {predicate} {object}".lower()
        fact_words = set(re.findall(r'\w+', fact_text))
        
        common_words = query_words.intersection(fact_words)
        
        if not query_words:
            return 0.0
        
        return len(common_words) / len(query_words)
    
    def _calculate_episode_similarity(self, desc1: str, desc2: str) -> float:
        """Вычисляет схожесть между описаниями эпизодов"""
        if not desc1 or not desc2:
            return 0.0
        
        words1 = set(re.findall(r'\w+', desc1.lower()))
        words2 = set(re.findall(r'\w+', desc2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        common_words = words1.intersection(words2)
        union_words = words1.union(words2)
        
        return len(common_words) / len(union_words) if union_words else 0.0
    
    def _update_access_count(self, fact_id: int):
        """Обновляет счетчик обращений к факту"""
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE facts 
                SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (fact_id,))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления счетчика обращений: {e}")
        finally:
            conn.close()