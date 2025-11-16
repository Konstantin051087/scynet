"""
Трекер настроения системы
Отслеживает и анализирует эмоциональные состояния системы и пользователей
"""

import time
import json
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

class MoodTracker:
    def __init__(self, db_path="data/runtime/mood_tracking.db"):
        self.db_path = db_path
        self.user_mood_history = {}
        self.system_mood_history = []
        
        self.initialize_database()
    
    def initialize_database(self):
        """Инициализация базы данных для трекинга настроения"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица для настроения системы
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_mood (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    mood TEXT NOT NULL,
                    intensity REAL NOT NULL,
                    context TEXT,
                    trigger_emotion TEXT
                )
            ''')
            
            # Таблица для настроения пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_mood (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    detected_emotions TEXT NOT NULL,
                    dominant_emotion TEXT,
                    intensity REAL NOT NULL,
                    interaction_context TEXT
                )
            ''')
            
            # Таблица для эмоциональных паттернов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    pattern_type TEXT NOT NULL,
                    emotion_data TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_observed DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error initializing mood database: {e}")
    
    def track_mood(self, user_id: Optional[str], detected_emotions: Dict[str, float], 
                   system_mood: str, context: str = ""):
        """Трекинг настроения пользователя и системы"""
        timestamp = datetime.now()
        
        # Трекинг настроения системы
        self._track_system_mood(system_mood, detected_emotions, context, timestamp)
        
        # Трекинг настроения пользователя
        if user_id:
            self._track_user_mood(user_id, detected_emotions, context, timestamp)
        
        # Анализ эмоциональных паттернов
        if user_id:
            self._analyze_emotion_patterns(user_id, detected_emotions, timestamp)
    
    def _track_system_mood(self, system_mood: str, detected_emotions: Dict[str, float],
                          context: str, timestamp: datetime):
        """Трекинг настроения системы"""
        mood_record = {
            'timestamp': timestamp,
            'mood': system_mood,
            'intensity': max(detected_emotions.values()) if detected_emotions else 0.5,
            'context': context,
            'trigger_emotion': max(detected_emotions.items(), key=lambda x: x[1])[0] if detected_emotions else 'neutral'
        }
        
        self.system_mood_history.append(mood_record)
        
        # Сохранение в базу данных
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_mood (timestamp, mood, intensity, context, trigger_emotion)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp.isoformat(), system_mood, mood_record['intensity'], context, mood_record['trigger_emotion']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving system mood: {e}")
        
        # Ограничение размера истории в памяти
        if len(self.system_mood_history) > 1000:
            self.system_mood_history = self.system_mood_history[-500:]
    
    def _track_user_mood(self, user_id: str, detected_emotions: Dict[str, float],
                        context: str, timestamp: datetime):
        """Трекинг настроения пользователя"""
        if user_id not in self.user_mood_history:
            self.user_mood_history[user_id] = []
        
        dominant_emotion = max(detected_emotions.items(), key=lambda x: x[1]) if detected_emotions else ('neutral', 1.0)
        
        user_mood_record = {
            'timestamp': timestamp,
            'detected_emotions': detected_emotions,
            'dominant_emotion': dominant_emotion[0],
            'intensity': dominant_emotion[1],
            'context': context
        }
        
        self.user_mood_history[user_id].append(user_mood_record)
        
        # Сохранение в базу данных
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            emotions_json = json.dumps(detected_emotions)
            
            cursor.execute('''
                INSERT INTO user_mood (user_id, timestamp, detected_emotions, dominant_emotion, intensity, interaction_context)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, timestamp.isoformat(), emotions_json, dominant_emotion[0], dominant_emotion[1], context))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving user mood: {e}")
        
        # Ограничение размера истории в памяти
        if len(self.user_mood_history[user_id]) > 500:
            self.user_mood_history[user_id] = self.user_mood_history[user_id][-250:]
    
    def _analyze_emotion_patterns(self, user_id: str, detected_emotions: Dict[str, float],
                                timestamp: datetime):
        """Анализ эмоциональных паттернов пользователя"""
        dominant_emotion = max(detected_emotions.items(), key=lambda x: x[1])[0]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем существование паттерна
            cursor.execute('''
                SELECT id, frequency FROM emotion_patterns 
                WHERE user_id = ? AND pattern_type = ? AND emotion_data = ?
            ''', (user_id, 'dominant_emotion', dominant_emotion))
            
            result = cursor.fetchone()
            
            if result:
                # Обновляем существующий паттерн
                pattern_id, frequency = result
                cursor.execute('''
                    UPDATE emotion_patterns 
                    SET frequency = ?, last_observed = ?
                    WHERE id = ?
                ''', (frequency + 1, timestamp.isoformat(), pattern_id))
            else:
                # Создаем новый паттерн
                cursor.execute('''
                    INSERT INTO emotion_patterns (user_id, pattern_type, emotion_data, frequency)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, 'dominant_emotion', dominant_emotion, 1))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error analyzing emotion patterns: {e}")
    
    def get_user_mood_summary(self, user_id: str, days: int = 7) -> Dict:
        """Получение сводки настроения пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Получаем историю настроений за указанный период
            cursor.execute('''
                SELECT dominant_emotion, intensity, timestamp 
                FROM user_mood 
                WHERE user_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (user_id, cutoff_date))
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return {"error": "No mood data found for user"}
            
            # Анализируем данные
            emotion_counts = {}
            total_intensity = 0
            recent_emotions = []
            
            for emotion, intensity, timestamp in records:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                total_intensity += intensity
                recent_emotions.append({
                    'emotion': emotion,
                    'intensity': intensity,
                    'timestamp': timestamp
                })
            
            # Определяем преобладающую эмоцию
            predominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
            avg_intensity = total_intensity / len(records)
            
            return {
                'predominant_emotion': predominant_emotion,
                'average_intensity': avg_intensity,
                'emotion_distribution': emotion_counts,
                'recent_emotions': recent_emotions[:10],  # Последние 10 записей
                'total_interactions': len(records)
            }
            
        except Exception as e:
            return {"error": f"Error generating mood summary: {e}"}
    
    def get_system_mood_analytics(self, hours: int = 24) -> Dict:
        """Аналитика настроения системы"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT mood, intensity, trigger_emotion 
                FROM system_mood 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return {"error": "No system mood data found"}
            
            # Анализ данных
            mood_distribution = {}
            trigger_analysis = {}
            intensity_trend = []
            
            for mood, intensity, trigger in records:
                mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
                trigger_analysis[trigger] = trigger_analysis.get(trigger, 0) + 1
                intensity_trend.append(intensity)
            
            # Вычисляем среднюю интенсивность
            avg_intensity = sum(intensity_trend) / len(intensity_trend)
            
            # Определяем наиболее частые настроения и триггеры
            most_common_mood = max(mood_distribution.items(), key=lambda x: x[1])[0]
            most_common_trigger = max(trigger_analysis.items(), key=lambda x: x[1])[0]
            
            return {
                'mood_distribution': mood_distribution,
                'trigger_analysis': trigger_analysis,
                'average_intensity': avg_intensity,
                'most_common_mood': most_common_mood,
                'most_common_trigger': most_common_trigger,
                'stability_score': self._calculate_stability_score(intensity_trend),
                'total_records': len(records)
            }
            
        except Exception as e:
            return {"error": f"Error generating system analytics: {e}"}
    
    def _calculate_stability_score(self, intensity_values: List[float]) -> float:
        """Вычисление показателя стабильности настроения"""
        if len(intensity_values) < 2:
            return 1.0
        
        # Вычисляем стандартное отклонение и нормализуем
        mean = sum(intensity_values) / len(intensity_values)
        variance = sum((x - mean) ** 2 for x in intensity_values) / len(intensity_values)
        std_dev = variance ** 0.5
        
        # Преобразуем в оценку стабильности (1.0 - максимальная стабильность)
        stability = max(0.0, 1.0 - std_dev)
        
        return round(stability, 2)