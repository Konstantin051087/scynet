"""
Модуль долговременной памяти системы Синтетический Разум
Отвечает за хранение и управление постоянными знаниями системы
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import json
import sqlite3
from datetime import datetime

from .fact_associator import FactAssociator
from .memory_consolidator import MemoryConsolidator
from .memory_retriever import MemoryRetriever
from .forget_mechanism import ForgetMechanism

logger = logging.getLogger(__name__)

@dataclass
class MemoryConfig:
    """Конфигурация модуля долговременной памяти"""
    knowledge_graph_path: str = "knowledge_graph.db"
    episodic_memory_path: str = "episodic_memory.db"
    semantic_memory_path: str = "semantic_memory.db"
    user_profiles_path: str = "user_profiles"
    max_memory_entries: int = 100000
    auto_cleanup_interval: int = 3600  # seconds
    association_threshold: float = 0.7

class MemoryLongTerm:
    """Главный класс модуля долговременной памяти"""
    
    def __init__(self, config: MemoryConfig = None):
        self.config = config or MemoryConfig()
        self._ensure_directories()
        
        # Инициализация компонентов
        self.fact_associator = FactAssociator(self.config)
        self.memory_consolidator = MemoryConsolidator(self.config)
        self.memory_retriever = MemoryRetriever(self.config)
        self.forget_mechanism = ForgetMechanism(self.config)
        
        self._init_databases()
        logger.info("Модуль долговременной памяти инициализирован")
    
    def _ensure_directories(self):
        """Создает необходимые директории"""
        os.makedirs(self.config.user_profiles_path, exist_ok=True)
    
    def _init_databases(self):
        """Инициализирует базы данных"""
        # Инициализация графа знаний
        conn = sqlite3.connect(self.config.knowledge_graph_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                attributes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES entities (id),
                FOREIGN KEY (target_id) REFERENCES entities (id)
            )
        ''')
        conn.commit()
        conn.close()
        
        # Инициализация эпизодической памяти
        conn = sqlite3.connect(self.config.episodic_memory_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                emotional_context TEXT,
                importance_score REAL DEFAULT 0.5,
                related_episodes TEXT,
                metadata TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        # Инициализация семантической памяти
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                description TEXT,
                FOREIGN KEY (parent_id) REFERENCES categories (id)
            )
        ''')
        conn.commit()
        conn.close()
    
    def store_episode(self, user_id: str, event_type: str, description: str, 
                     emotional_context: Dict = None, importance: float = 0.5) -> int:
        """Сохраняет эпизод в память"""
        return self.memory_consolidator.store_episode(
            user_id, event_type, description, emotional_context, importance
        )
    
    def store_fact(self, subject: str, predicate: str, object: str, 
                  confidence: float = 1.0, source: str = None) -> int:
        """Сохраняет факт в семантическую память"""
        return self.memory_consolidator.store_fact(
            subject, predicate, object, confidence, source
        )
    
    def retrieve_related_facts(self, query: str, limit: int = 10) -> List[Dict]:
        """Извлекает связанные факты"""
        return self.memory_retriever.retrieve_related_facts(query, limit)
    
    def find_similar_episodes(self, description: str, user_id: str = None) -> List[Dict]:
        """Находит похожие эпизоды"""
        return self.memory_retriever.find_similar_episodes(description, user_id)
    
    def associate_facts(self, fact1_id: int, fact2_id: int, relationship: str):
        """Создает ассоциацию между фактами"""
        self.fact_associator.create_association(fact1_id, fact2_id, relationship)
    
    def cleanup_old_memories(self):
        """Очищает старые и неважные воспоминания"""
        self.forget_mechanism.cleanup()
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Загружает профиль пользователя"""
        profile_path = os.path.join(self.config.user_profiles_path, f"{user_id}.profile")
        if os.path.exists(profile_path):
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._create_default_profile(user_id)
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Обновляет профиль пользователя"""
        profile = self.get_user_profile(user_id)
        profile.update(updates)
        profile['last_updated'] = datetime.now().isoformat()
        
        profile_path = os.path.join(self.config.user_profiles_path, f"{user_id}.profile")
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    
    def _create_default_profile(self, user_id: str) -> Dict[str, Any]:
        """Создает профиль пользователя по умолчанию"""
        default_profile = {
            "user_id": user_id,
            "preferences": {},
            "conversation_history": [],
            "learned_patterns": {},
            "emotional_baseline": "neutral",
            "trust_level": 0.5,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        profile_path = os.path.join(self.config.user_profiles_path, f"{user_id}.profile")
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(default_profile, f, ensure_ascii=False, indent=2)
        
        return default_profile

# Создаем экземпляр модуля для импорта
memory_long_term = MemoryLongTerm()