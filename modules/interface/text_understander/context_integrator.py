import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import yaml

class ContextIntegrator:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Инициализация базы данных контекста
        self.db_path = self.config.get('context_db_path', 'data/runtime/context.db')
        self._init_database()
        
        # Параметры контекста
        self.max_context_length = self.config.get('max_context_length', 10)
        self.context_timeout = self.config.get('context_timeout', 3600)  # 1 час
    
    def _init_database(self):
        """Инициализация базы данных контекста"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_context (
                user_id TEXT,
                timestamp DATETIME,
                text TEXT,
                intent TEXT,
                entities TEXT,
                sentiment TEXT,
                PRIMARY KEY (user_id, timestamp)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dialogue_history (
                user_id TEXT,
                sequence_id INTEGER,
                speaker TEXT,
                text TEXT,
                timestamp DATETIME,
                PRIMARY KEY (user_id, sequence_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_context(self, user_id: str, external_context: Dict = None) -> Dict[str, Any]:
        """Получение контекста пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получение последних сообщений
        cursor.execute('''
            SELECT text, intent, entities, sentiment, timestamp
            FROM user_context 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, self.max_context_length))
        
        recent_context = cursor.fetchall()
        
        # Получение истории диалога
        cursor.execute('''
            SELECT speaker, text, timestamp
            FROM dialogue_history
            WHERE user_id = ?
            ORDER BY sequence_id DESC
            LIMIT ?
        ''', (user_id, self.max_context_length * 2))
        
        dialogue_history = cursor.fetchall()
        
        conn.close()
        
        # Очистка устаревшего контекста
        self._clean_old_context(user_id)
        
        return {
            "user_id": user_id,
            "recent_messages": [
                {
                    "text": row[0],
                    "intent": row[1],
                    "entities": json.loads(row[2]) if row[2] else [],
                    "sentiment": row[3],
                    "timestamp": row[4]
                } for row in recent_context
            ],
            "dialogue_history": [
                {
                    "speaker": row[0],
                    "text": row[1],
                    "timestamp": row[2]
                } for row in dialogue_history
            ],
            "external_context": external_context or {}
        }
    
    def update_context(self, user_id: str, text: str, intent: Dict, entities: List[Dict]):
        """Обновление контекста пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        # Сохранение в контекст
        cursor.execute('''
            INSERT OR REPLACE INTO user_context 
            (user_id, timestamp, text, intent, entities, sentiment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, 
            current_time, 
            text,
            json.dumps(intent, ensure_ascii=False),
            json.dumps(entities, ensure_ascii=False),
            "neutral"  # Будет обновлено после анализа тональности
        ))
        
        # Сохранение в историю диалога
        cursor.execute('''
            SELECT COALESCE(MAX(sequence_id), 0) FROM dialogue_history WHERE user_id = ?
        ''', (user_id,))
        
        next_sequence = cursor.fetchone()[0] + 1
        
        cursor.execute('''
            INSERT INTO dialogue_history 
            (user_id, sequence_id, speaker, text, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, next_sequence, "user", text, current_time))
        
        conn.commit()
        conn.close()
    
    def _clean_old_context(self, user_id: str):
        """Очистка устаревшего контекста"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Удаление контекста старше timeout
        cursor.execute('''
            DELETE FROM user_context 
            WHERE user_id = ? AND datetime(timestamp) < datetime('now', ?)
        ''', (user_id, f'-{self.context_timeout} seconds'))
        
        # Сохранение только последних N записей в истории
        cursor.execute('''
            DELETE FROM dialogue_history 
            WHERE user_id = ? AND sequence_id NOT IN (
                SELECT sequence_id FROM dialogue_history 
                WHERE user_id = ? 
                ORDER BY sequence_id DESC 
                LIMIT ?
            )
        ''', (user_id, user_id, self.max_context_length * 3))
        
        conn.commit()
        conn.close()
    
    def add_system_response(self, user_id: str, text: str):
        """Добавление ответа системы в историю диалога"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            SELECT COALESCE(MAX(sequence_id), 0) FROM dialogue_history WHERE user_id = ?
        ''', (user_id,))
        
        next_sequence = cursor.fetchone()[0] + 1
        
        cursor.execute('''
            INSERT INTO dialogue_history 
            (user_id, sequence_id, speaker, text, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, next_sequence, "system", text, current_time))
        
        conn.commit()
        conn.close()