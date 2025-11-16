"""
Ассоциатор фактов - создает связи между знаниями в памяти
"""

import sqlite3
import logging
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class FactAssociator:
    """Создает и управляет ассоциациями между фактами"""
    
    def __init__(self, config):
        self.config = config
        self.association_rules = self._load_association_rules()
    
    def _load_association_rules(self) -> List[Dict]:
        """Загружает правила ассоциации"""
        # Базовые правила ассоциации
        return [
            {"pattern": ["is_a", "type_of"], "relationship": "categorical"},
            {"pattern": ["part_of", "contains"], "relationship": "compositional"},
            {"pattern": ["causes", "leads_to"], "relationship": "causal"},
            {"pattern": ["similar_to", "like"], "relationship": "similarity"},
            {"pattern": ["opposite_of", "different_from"], "relationship": "opposition"}
        ]
    
    def create_association(self, entity1_id: int, entity2_id: int, 
                          relationship_type: str, confidence: float = 1.0,
                          metadata: Dict = None) -> int:
        """Создает ассоциацию между сущностями"""
        conn = sqlite3.connect(self.config.knowledge_graph_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO relationships 
                (source_id, target_id, relationship_type, confidence, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (entity1_id, entity2_id, relationship_type, confidence, 
                  json.dumps(metadata or {})))
            
            relationship_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Создана ассоциация {relationship_id} между {entity1_id} и {entity2_id}")
            
            return relationship_id
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания ассоциации: {e}")
            return -1
        finally:
            conn.close()
    
    def find_related_entities(self, entity_id: int, relationship_type: str = None) -> List[Dict]:
        """Находит связанные сущности"""
        conn = sqlite3.connect(self.config.knowledge_graph_path)
        cursor = conn.cursor()
        
        try:
            if relationship_type:
                cursor.execute('''
                    SELECT e.*, r.relationship_type, r.confidence
                    FROM entities e
                    JOIN relationships r ON e.id = r.target_id
                    WHERE r.source_id = ? AND r.relationship_type = ?
                    UNION
                    SELECT e.*, r.relationship_type, r.confidence
                    FROM entities e
                    JOIN relationships r ON e.id = r.source_id
                    WHERE r.target_id = ? AND r.relationship_type = ?
                ''', (entity_id, relationship_type, entity_id, relationship_type))
            else:
                cursor.execute('''
                    SELECT e.*, r.relationship_type, r.confidence
                    FROM entities e
                    JOIN relationships r ON e.id = r.target_id
                    WHERE r.source_id = ?
                    UNION
                    SELECT e.*, r.relationship_type, r.confidence
                    FROM entities e
                    JOIN relationships r ON e.id = r.source_id
                    WHERE r.target_id = ?
                ''', (entity_id, entity_id))
            
            results = []
            for row in cursor.fetchall():
                entity = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'attributes': json.loads(row[3]) if row[3] else {},
                    'relationship_type': row[5],
                    'confidence': row[6]
                }
                results.append(entity)
            
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка поиска связанных сущностей: {e}")
            return []
        finally:
            conn.close()
    
    def auto_associate_new_fact(self, fact_data: Dict) -> List[int]:
        """Автоматически создает ассоциации для нового факта"""
        associations_created = []
        
        # Поиск похожих фактов в семантической памяти
        similar_facts = self._find_similar_facts(fact_data)
        
        for similar_fact in similar_facts:
            # Создание ассоциации если уверенность выше порога
            if similar_fact['similarity_score'] > self.config.association_threshold:
                association_id = self.create_association(
                    fact_data.get('entity_id'),
                    similar_fact['entity_id'],
                    'similar_to',
                    similar_fact['similarity_score']
                )
                if association_id != -1:
                    associations_created.append(association_id)
        
        logger.info(f"Создано {len(associations_created)} автоматических ассоциаций")
        return associations_created
    
    def _find_similar_facts(self, fact_data: Dict) -> List[Dict]:
        """Находит похожие факты для ассоциации"""
        # Упрощенная реализация поиска похожих фактов
        # В реальной системе здесь будет сложная логика сравнения
        
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, subject, predicate, object 
                FROM facts 
                WHERE subject = ? OR predicate = ? OR object = ?
            ''', (fact_data.get('subject'), fact_data.get('predicate'), fact_data.get('object')))
            
            similar_facts = []
            for row in cursor.fetchall():
                similarity_score = self._calculate_similarity(fact_data, {
                    'id': row[0],
                    'subject': row[1],
                    'predicate': row[2],
                    'object': row[3]
                })
                
                if similarity_score > 0.3:  # минимальный порог схожести
                    similar_facts.append({
                        'fact_id': row[0],
                        'entity_id': fact_data.get('entity_id'),
                        'similarity_score': similarity_score
                    })
            
            return similar_facts
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка поиска похожих фактов: {e}")
            return []
        finally:
            conn.close()
    
    def _calculate_similarity(self, fact1: Dict, fact2: Dict) -> float:
        """Вычисляет схожесть между двумя фактами"""
        score = 0.0
        matches = 0
        
        if fact1.get('subject') == fact2.get('subject'):
            score += 0.4
            matches += 1
        if fact1.get('predicate') == fact2.get('predicate'):
            score += 0.4
            matches += 1
        if fact1.get('object') == fact2.get('object'):
            score += 0.2
            matches += 1
        
        # Дополнительные баллы за множественные совпадения
        if matches >= 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def get_relationship_strength(self, entity1_id: int, entity2_id: int) -> float:
        """Вычисляет силу связи между сущностями"""
        conn = sqlite3.connect(self.config.knowledge_graph_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT confidence 
                FROM relationships 
                WHERE (source_id = ? AND target_id = ?) 
                   OR (source_id = ? AND target_id = ?)
            ''', (entity1_id, entity2_id, entity2_id, entity1_id))
            
            results = cursor.fetchall()
            if not results:
                return 0.0
            
            # Возвращаем максимальную уверенность среди всех связей
            return max(row[0] for row in results)
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка вычисления силы связи: {e}")
            return 0.0
        finally:
            conn.close()