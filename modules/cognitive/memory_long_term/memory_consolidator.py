"""
Консолидатор памяти - переносит информацию из кратковременной в долговременную память
"""

import sqlite3
import logging
from typing import Dict, Any, List
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryConsolidator:
    """Управляет консолидацией памяти"""
    
    def __init__(self, config):
        self.config = config
    
    def store_episode(self, user_id: str, event_type: str, description: str,
                     emotional_context: Dict = None, importance: float = 0.5) -> int:
        """Сохраняет эпизод в эпизодическую память"""
        conn = sqlite3.connect(self.config.episodic_memory_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO episodes 
                (user_id, event_type, description, emotional_context, importance_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, event_type, description, 
                  json.dumps(emotional_context or {}), importance))
            
            episode_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Сохранен эпизод {episode_id} для пользователя {user_id}")
            return episode_id
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка сохранения эпизода: {e}")
            return -1
        finally:
            conn.close()
    
    def store_fact(self, subject: str, predicate: str, object: str,
                  confidence: float = 1.0, source: str = None) -> int:
        """Сохраняет факт в семантическую память"""
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        
        try:
            # Проверяем, не существует ли уже такой факт
            cursor.execute('''
                SELECT id FROM facts 
                WHERE subject = ? AND predicate = ? AND object = ?
            ''', (subject, predicate, object))
            
            existing = cursor.fetchone()
            if existing:
                # Обновляем существующий факт
                cursor.execute('''
                    UPDATE facts 
                    SET confidence = ?, last_accessed = CURRENT_TIMESTAMP, 
                        access_count = access_count + 1
                    WHERE id = ?
                ''', (confidence, existing[0]))
                fact_id = existing[0]
                logger.debug(f"Обновлен факт {fact_id}")
            else:
                # Создаем новый факт
                cursor.execute('''
                    INSERT INTO facts 
                    (subject, predicate, object, confidence, source)
                    VALUES (?, ?, ?, ?, ?)
                ''', (subject, predicate, object, confidence, source))
                fact_id = cursor.lastrowid
                logger.debug(f"Создан новый факт {fact_id}")
            
            conn.commit()
            return fact_id
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка сохранения факта: {e}")
            return -1
        finally:
            conn.close()
    
    def consolidate_from_short_term(self, short_term_memories: List[Dict]) -> Dict[str, int]:
        """Консолидирует memories из кратковременной памяти"""
        results = {
            'episodes_stored': 0,
            'facts_stored': 0,
            'associations_created': 0
        }
        
        for memory in short_term_memories:
            memory_type = memory.get('type')
            
            if memory_type == 'episode':
                episode_id = self.store_episode(
                    memory.get('user_id', 'unknown'),
                    memory.get('event_type', 'unknown'),
                    memory.get('description', ''),
                    memory.get('emotional_context'),
                    memory.get('importance', 0.5)
                )
                if episode_id != -1:
                    results['episodes_stored'] += 1
            
            elif memory_type == 'fact':
                fact_id = self.store_fact(
                    memory.get('subject', ''),
                    memory.get('predicate', ''),
                    memory.get('object', ''),
                    memory.get('confidence', 1.0),
                    memory.get('source', 'user_input')
                )
                if fact_id != -1:
                    results['facts_stored'] += 1
        
        logger.info(f"Консолидировано: {results}")
        return results
    
    def extract_facts_from_episode(self, episode_id: int) -> List[int]:
        """Извлекает факты из эпизода для сохранения в семантической памяти"""
        conn_episodic = sqlite3.connect(self.config.episodic_memory_path)
        cursor_episodic = conn_episodic.cursor()
        
        try:
            cursor_episodic.execute('''
                SELECT description FROM episodes WHERE id = ?
            ''', (episode_id,))
            
            episode = cursor_episodic.fetchone()
            if not episode:
                return []
            
            description = episode[0]
            # Упрощенная экстракция фактов из описания
            # В реальной системе здесь будет NLP-обработка
            
            extracted_facts = self._simple_fact_extraction(description)
            fact_ids = []
            
            for fact in extracted_facts:
                fact_id = self.store_fact(
                    fact['subject'],
                    fact['predicate'],
                    fact['object'],
                    confidence=0.7,  # Меньшая уверенность для извлеченных фактов
                    source=f'episode_{episode_id}'
                )
                if fact_id != -1:
                    fact_ids.append(fact_id)
            
            logger.info(f"Извлечено {len(fact_ids)} фактов из эпизода {episode_id}")
            return fact_ids
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка извлечения фактов из эпизода: {e}")
            return []
        finally:
            conn_episodic.close()
    
    def _simple_fact_extraction(self, text: str) -> List[Dict]:
        """Упрощенное извлечение фактов из текста"""
        # Это упрощенная реализация
        # В реальной системе будет использоваться NLP
        facts = []
        
        # Простые паттерны для демонстрации
        if "живет в" in text or "проживает в" in text:
            parts = text.split()
            for i, word in enumerate(parts):
                if word in ["живет", "проживает"] and i + 2 < len(parts) and parts[i + 1] == "в":
                    facts.append({
                        'subject': ' '.join(parts[:i]),  # имя
                        'predicate': 'живет_в',
                        'object': ' '.join(parts[i + 2:])
                    })
        
        if "любит" in text or "нравится" in text:
            parts = text.split()
            for i, word in enumerate(parts):
                if word in ["любит", "нравится"]:
                    facts.append({
                        'subject': ' '.join(parts[:i]),
                        'predicate': 'любит',
                        'object': ' '.join(parts[i + 1:])
                    })
        
        return facts
    
    def update_memory_importance(self, memory_id: int, memory_type: str, 
                               new_importance: float):
        """Обновляет важность памяти"""
        if memory_type == 'episode':
            conn = sqlite3.connect(self.config.episodic_memory_path)
            table = 'episodes'
        elif memory_type == 'fact':
            conn = sqlite3.connect(self.config.semantic_memory_path)
            table = 'facts'
        else:
            return
        
        try:
            cursor = conn.cursor()
            if memory_type == 'episode':
                cursor.execute(f'''
                    UPDATE {table} 
                    SET importance_score = ? 
                    WHERE id = ?
                ''', (new_importance, memory_id))
            elif memory_type == 'fact':
                cursor.execute(f'''
                    UPDATE {table} 
                    SET confidence = ? 
                    WHERE id = ?
                ''', (new_importance, memory_id))
            
            conn.commit()
            logger.debug(f"Обновлена важность {memory_type} {memory_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления важности памяти: {e}")
        finally:
            conn.close()