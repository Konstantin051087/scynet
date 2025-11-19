"""
Модуль долговременной памяти системы Синтетический Разум
Отвечает за хранение и управление постоянными знаниями системы
"""

import os
import logging
import asyncio
import sqlite3
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime

# Импорты компонентов (будут созданы позже)
try:
    from .fact_associator import FactAssociator
    from .memory_consolidator import MemoryConsolidator
    from .memory_retriever import MemoryRetriever
    from .forget_mechanism import ForgetMechanism
except ImportError:
    # Заглушки для отсутствующих компонентов
    class FactAssociator: pass
    class MemoryConsolidator: pass  
    class MemoryRetriever: pass
    class ForgetMechanism: pass

logger = logging.getLogger(__name__)

@dataclass
class MemoryConfig:
    """Конфигурация модуля долговременной памяти"""
    knowledge_graph_path: str = "data/runtime/knowledge_graph.db"
    episodic_memory_path: str = "data/runtime/episodic_memory.db" 
    semantic_memory_path: str = "data/runtime/semantic_memory.db"
    user_profiles_path: str = "data/runtime/user_profiles"
    max_memory_entries: int = 100000
    auto_cleanup_interval: int = 3600
    association_threshold: float = 0.7

class MemoryLongTerm:
    """Главный класс модуля долговременной памяти"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config_dict = config
        self.config = MemoryConfig()
        self._apply_config(config)
        
        self.communication_bus = None
        self.is_initialized = False
        
        # Инициализация компонентов
        self.fact_associator = FactAssociator(self.config)
        self.memory_consolidator = MemoryConsolidator(self.config)
        self.memory_retriever = MemoryRetriever(self.config) 
        self.forget_mechanism = ForgetMechanism(self.config)
        
        logger.info("Модуль долговременной памяти создан")

    def _apply_config(self, config: Dict[str, Any]):
        """Применяет конфигурацию из system.yaml"""
        if 'knowledge_graph_path' in config:
            self.config.knowledge_graph_path = config['knowledge_graph_path']
        if 'episodic_memory_path' in config:
            self.config.episodic_memory_path = config['episodic_memory_path']
        if 'semantic_memory_path' in config:
            self.config.semantic_memory_path = config['semantic_memory_path']
        if 'user_profiles_path' in config:
            self.config.user_profiles_path = config['user_profiles_path']

    async def initialize(self, communication_bus) -> bool:
        """Асинхронная инициализация модуля"""
        try:
            self.communication_bus = communication_bus
            
            # Создание директорий
            self._ensure_directories()
            
            # Инициализация баз данных
            self._init_databases()
            
            # Настройка коммуникации
            await self._setup_communication()
            
            self.is_initialized = True
            logger.info("✅ Модуль долговременной памяти инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации модуля памяти: {e}")
            return False

    async def _setup_communication(self):
        """Настройка коммуникации с шиной сообщений"""
        self.communication_bus.subscribe("memory_store_request", self._handle_store_request)
        self.communication_bus.subscribe("memory_retrieve_request", self._handle_retrieve_request)
        self.communication_bus.subscribe("memory_search_request", self._handle_search_request)
        self.communication_bus.subscribe("module_health_check", self._handle_health_check)
        
        logger.debug("Коммуникация с шиной сообщений настроена")

    async def _handle_store_request(self, message):
        """Обработка запроса на сохранение в память"""
        try:
            data = message.data
            memory_type = data.get('type', 'episodic')
            
            if memory_type == 'episodic':
                result = self.store_episode(
                    data['user_id'],
                    data['event_type'], 
                    data['description'],
                    data.get('emotional_context'),
                    data.get('importance', 0.5)
                )
            elif memory_type == 'semantic':
                result = self.store_fact(
                    data['subject'],
                    data['predicate'],
                    data['object'],
                    data.get('confidence', 1.0),
                    data.get('source')
                )
            
            # Отправка ответа
            await self.communication_bus.send_message({
                'source': 'memory_long_term',
                'destination': message.source,
                'message_type': 'memory_store_response',
                'data': {
                    'request_id': data.get('request_id'),
                    'memory_id': result,
                    'status': 'success'
                }
            })
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в память: {e}")
            await self._send_error_response(message, str(e))

    async def _handle_retrieve_request(self, message):
        """Обработка запроса на извлечение из памяти"""
        try:
            data = message.data
            memory_type = data.get('type', 'semantic')
            
            if memory_type == 'semantic':
                result = self.retrieve_related_facts(
                    data['query'],
                    data.get('limit', 10)
                )
            elif memory_type == 'episodic':
                result = self.find_similar_episodes(
                    data['description'],
                    data.get('user_id')
                )
            
            await self.communication_bus.send_message({
                'source': 'memory_long_term', 
                'destination': message.source,
                'message_type': 'memory_retrieve_response',
                'data': {
                    'request_id': data.get('request_id'),
                    'results': result,
                    'status': 'success'
                }
            })
            
        except Exception as e:
            logger.error(f"Ошибка извлечения из памяти: {e}")
            await self._send_error_response(message, str(e))

    async def _handle_search_request(self, message):
        """Обработка запроса поиска в памяти"""
        # Заглушка для поиска
        await self.communication_bus.send_message({
            'source': 'memory_long_term',
            'destination': message.source, 
            'message_type': 'memory_search_response',
            'data': {
                'request_id': message.data.get('request_id'),
                'results': [],
                'status': 'success'
            }
        })

    async def _handle_health_check(self, message):
        """Обработка проверки здоровья модуля"""
        health_status = await self.get_status()
        
        await self.communication_bus.send_message({
            'source': 'memory_long_term',
            'destination': message.source,
            'message_type': 'health_check_response', 
            'data': health_status
        })

    async def _send_error_response(self, original_message, error_text):
        """Отправка сообщения об ошибке"""
        await self.communication_bus.send_message({
            'source': 'memory_long_term',
            'destination': original_message.source,
            'message_type': 'memory_error_response',
            'data': {
                'request_id': original_message.data.get('request_id'),
                'error': error_text,
                'status': 'error'
            }
        })

    def _ensure_directories(self):
        """Создает необходимые директории"""
        os.makedirs(self.config.user_profiles_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.config.knowledge_graph_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.config.episodic_memory_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.config.semantic_memory_path), exist_ok=True)

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

    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса модуля для ModuleManager"""
        return {
            'status': 'initialized' if self.is_initialized else 'error',
            'is_initialized': self.is_initialized,
            'databases': {
                'knowledge_graph': os.path.exists(self.config.knowledge_graph_path),
                'episodic_memory': os.path.exists(self.config.episodic_memory_path),
                'semantic_memory': os.path.exists(self.config.semantic_memory_path)
            },
            'health': 'healthy' if self.is_initialized else 'unhealthy'
        }

    async def shutdown(self):
        """Корректное завершение работы модуля"""
        try:
            # Отписка от шины сообщений
            if self.communication_bus:
                self.communication_bus.unsubscribe("memory_store_request")
                self.communication_bus.unsubscribe("memory_retrieve_request") 
                self.communication_bus.unsubscribe("memory_search_request")
                self.communication_bus.unsubscribe("module_health_check")
            
            self.is_initialized = False
            logger.info("Модуль долговременной памяти завершил работу")
            
        except Exception as e:
            logger.error(f"Ошибка завершения работы модуля: {e}")

    # Существующие методы модуля (оставляем без изменений)
    def store_episode(self, user_id: str, event_type: str, description: str, 
                     emotional_context: Dict = None, importance: float = 0.5) -> int:
        """Сохраняет эпизод в память"""
        # Временная реализация
        conn = sqlite3.connect(self.config.episodic_memory_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO episodes (user_id, event_type, description, emotional_context, importance_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, event_type, description, 
              json.dumps(emotional_context) if emotional_context else None, 
              importance))
        episode_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return episode_id
    
    def store_fact(self, subject: str, predicate: str, object: str, 
                  confidence: float = 1.0, source: str = None) -> int:
        """Сохраняет факт в семантическую память"""
        # Временная реализация
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO facts (subject, predicate, object, confidence, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (subject, predicate, object, confidence, source))
        fact_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return fact_id
    
    def retrieve_related_facts(self, query: str, limit: int = 10) -> List[Dict]:
        """Извлекает связанные факты"""
        # Временная реализация
        conn = sqlite3.connect(self.config.semantic_memory_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM facts 
            WHERE subject LIKE ? OR predicate LIKE ? OR object LIKE ?
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'subject': row[1],
                'predicate': row[2],
                'object': row[3],
                'confidence': row[4],
                'source': row[5]
            })
        conn.close()
        return results
    
    def find_similar_episodes(self, description: str, user_id: str = None) -> List[Dict]:
        """Находит похожие эпизоды"""
        # Временная реализация
        conn = sqlite3.connect(self.config.episodic_memory_path)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT * FROM episodes 
                WHERE user_id = ? AND description LIKE ?
            ''', (user_id, f'%{description}%'))
        else:
            cursor.execute('''
                SELECT * FROM episodes 
                WHERE description LIKE ?
            ''', (f'%{description}%',))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'user_id': row[1],
                'event_type': row[2],
                'description': row[3],
                'timestamp': row[4],
                'importance_score': row[6]
            })
        conn.close()
        return results

    def associate_facts(self, fact1_id: int, fact2_id: int, relationship: str):
        """Создает ассоциацию между фактами"""
        # Временная реализация
        pass

    def cleanup_old_memories(self):
        """Очищает старые и неважные воспоминания"""
        # Временная реализация
        pass

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

# Глобальный экземпляр и функции для ModuleManager
_memory_long_term = None

async def init_module(config: Dict[str, Any], communication_bus) -> MemoryLongTerm:
    """Инициализация модуля"""
    global _memory_long_term
    _memory_long_term = MemoryLongTerm(config)
    await _memory_long_term.initialize(communication_bus)
    return _memory_long_term

def get_instance() -> MemoryLongTerm:
    """Получить экземпляр модуля"""
    if _memory_long_term is None:
        raise RuntimeError("Модуль долговременной памяти не инициализирован")
    return _memory_long_term