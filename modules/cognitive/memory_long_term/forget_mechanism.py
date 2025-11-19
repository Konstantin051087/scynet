"""
Механизм забывания - очищает устаревшие и неважные воспоминания
"""

import sqlite3
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class ForgetMechanism:
    """Управляет процессом забывания ненужной информации"""
    
    def __init__(self, config):
        self.config = config
        self.last_cleanup = datetime.now()
    
    def cleanup(self) -> Dict[str, int]:
        """Выполняет очистку устаревших воспоминаний"""
        results = {
            'old_episodes_removed': 0,
            'low_importance_episodes_removed': 0,
            'low_confidence_facts_removed': 0,
            'unused_facts_removed': 0
        }
        
        # Очистка старых эпизодов
        results['old_episodes_removed'] = self._remove_old_episodes()
        
        # Очистка неважных эпизодов
        results['low_importance_episodes_removed'] = self._remove_low_importance_episodes()
        
        # Очистка фактов с низкой уверенностью
        results['low_confidence_facts_removed'] = self._remove_low_confidence_facts()
        
        # Очистка неиспользуемых фактов
        results['unused_facts_removed'] = self._remove_unused_facts()
        
        # Очистка устаревших профилей пользователей
        self._cleanup_user_profiles()
        
        self.last_cleanup = datetime.now()
        logger.info(f"Очистка памяти завершена: {results}")
        
        return results
    
    def _remove_old_episodes(self, days_threshold: int = 365) -> int:
        """Удаляет старые эпизоды"""
        conn = sqlite3.connect(self.config.episodic_memory_path)
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                SELECT COUNT(*) FROM episodes 
                WHERE timestamp < ? AND importance_score < 0.3
            ''', (cutoff_date,))
            
            count_before = cursor.fetchone()[0]
            
            cursor.execute('''
                DELETE FROM episodes 
                WHERE timestamp < ? AND importance_score < 0.3
            ''', (cutoff_date,))
            
            removed_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Удалено {removed_count} старых эпизодов")
            return removed_count
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления старых эпизодов: {e}")
            return 0
        finally:
            conn.close()
    
    def _remove_low_importance_episodes(self, importance_threshold: float = 0.1) -> int:
        """Удаляет эпизоды с низкой важностью"""
        conn = sqlite3.connect(self.config.episodic_memory_path)
        cursor = conn.cursor()
        
        try:
            # Удаляем только если общее количество эпизодов превышает лимит
            cursor.execute('SELECT COUNT(*) FROM episodes')
            total_episodes = cursor.fetchone()[0]
            
            if total_episodes <= self.config.max_memory_entries * 0.8:
                return 0
            
            cursor.execute('''
                DELETE FROM episodes 
                WHERE importance_score < ?
                ORDER BY importance_score ASC, timestamp ASC
                LIMIT ?
            ''', (importance_threshold, total_episodes - self.config.max_memory_entries))
            
            removed_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Удалено {removed_count} неважных эпизодов")
            return removed_count
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления неважных эпизодов: {e}")
            return 0
        finally:
            conn.close()
    
    def _remove_low_confidence_facts(self, confidence_threshold: float = 0.3) -> int:
        """Удаляет факты с низкой уверенностью"""
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM facts 
                WHERE confidence < ? AND access_count < 5
            ''', (confidence_threshold,))
            
            removed_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Удалено {removed_count} фактов с низкой уверенностью")
            return removed_count
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления фактов с низкой уверенностью: {e}")
            return 0
        finally:
            conn.close()
    
    def _remove_unused_facts(self, unused_days: int = 180, min_access_count: int = 2) -> int:
        """Удаляет неиспользуемые факты"""
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=unused_days)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                DELETE FROM facts 
                WHERE last_accessed < ? AND access_count < ?
            ''', (cutoff_date, min_access_count))
            
            removed_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Удалено {removed_count} неиспользуемых фактов")
            return removed_count
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления неиспользуемых фактов: {e}")
            return 0
        finally:
            conn.close()
    
    def _cleanup_user_profiles(self):
        """Очищает устаревшие профили пользователей"""
        profiles_path = self.config.user_profiles_path
        
        if not os.path.exists(profiles_path):
            return
        
        for filename in os.listdir(profiles_path):
            if filename.endswith('.profile'):
                profile_path = os.path.join(profiles_path, filename)
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        import json
                        profile = json.load(f)
                    
                    # Проверяем, когда профиль последний раз обновлялся
                    last_updated = datetime.fromisoformat(profile.get('last_updated', '2000-01-01'))
                    days_since_update = (datetime.now() - last_updated).days
                    
                    # Удаляем профили, не обновлявшиеся более года
                    if days_since_update > 365:
                        os.remove(profile_path)
                        logger.info(f"Удален устаревший профиль: {filename}")
                        
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Ошибка чтения профиля {filename}: {e}")
                    # Удаляем поврежденные профили
                    os.remove(profile_path)
    
    def optimize_databases(self):
        """Оптимизирует базы данных для улучшения производительности"""
        databases = [
            self.config.knowledge_graph_path,
            self.config.episodic_memory_path,
            self.config.semantic_memory_path
        ]
        
        for db_path in databases:
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Выполняем VACUUM для оптимизации базы данных
                    cursor.execute('VACUUM')
                    conn.commit()
                    conn.close()
                    
                    logger.debug(f"Оптимизирована база данных: {db_path}")
                    
                except sqlite3.Error as e:
                    logger.error(f"Ошибка оптимизации базы данных {db_path}: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования памяти"""
        stats = {}
        
        # Статистика эпизодической памяти
        conn_episodic = sqlite3.connect(self.config.episodic_memory_path)
        cursor_episodic = conn_episodic.cursor()
        
        cursor_episodic.execute('SELECT COUNT(*) FROM episodes')
        stats['total_episodes'] = cursor_episodic.fetchone()[0]
        
        cursor_episodic.execute('SELECT COUNT(DISTINCT user_id) FROM episodes')
        stats['unique_users'] = cursor_episodic.fetchone()[0]
        
        cursor_episodic.execute('SELECT AVG(importance_score) FROM episodes')
        stats['avg_episode_importance'] = round(cursor_episodic.fetchone()[0] or 0, 2)
        
        conn_episodic.close()
        
        # Статистика семантической памяти
        conn_semantic = sqlite3.connect(self.config.semantic_memory_path)
        cursor_semantic = conn_semantic.cursor()
        
        cursor_semantic.execute('SELECT COUNT(*) FROM facts')
        stats['total_facts'] = cursor_semantic.fetchone()[0]
        
        cursor_semantic.execute('SELECT AVG(confidence) FROM facts')
        stats['avg_fact_confidence'] = round(cursor_semantic.fetchone()[0] or 0, 2)
        
        cursor_semantic.execute('SELECT AVG(access_count) FROM facts')
        stats['avg_fact_access_count'] = round(cursor_semantic.fetchone()[0] or 0, 2)
        
        conn_semantic.close()
        
        # Статистика графа знаний
        conn_knowledge = sqlite3.connect(self.config.knowledge_graph_path)
        cursor_knowledge = conn_knowledge.cursor()
        
        cursor_knowledge.execute('SELECT COUNT(*) FROM entities')
        stats['total_entities'] = cursor_knowledge.fetchone()[0]
        
        cursor_knowledge.execute('SELECT COUNT(*) FROM relationships')
        stats['total_relationships'] = cursor_knowledge.fetchone()[0]
        
        conn_knowledge.close()
        
        stats['last_cleanup'] = self.last_cleanup.isoformat()
        stats['memory_usage_percent'] = min(100, stats['total_episodes'] / self.config.max_memory_entries * 100)
        
        return stats