# progress_tracker.py
"""
Трекер прогресса - отслеживание выполнения целей и подцелей
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

from .goal_manager import Goal, GoalStatus

@dataclass
class ProgressSnapshot:
    """Снимок прогресса в определенный момент времени"""
    timestamp: datetime
    goal_id: str
    progress: float
    metrics: Dict[str, float]
    notes: str = ""

class ProgressTracker:
    """Система отслеживания прогресса выполнения целей"""
    
    def __init__(self, storage_path: str = "data/runtime/progress_data.json"):
        self.storage_path = storage_path
        self.logger = logging.getLogger('goals.ProgressTracker')
        self.progress_history: Dict[str, List[ProgressSnapshot]] = {}
        self.milestones: Dict[str, List[Tuple[float, str]]] = {}  # goal_id -> [(progress_threshold, milestone_name)]
        
        self._load_progress_data()
    
    def _load_progress_data(self) -> None:
        """Загрузка исторических данных прогресса"""
        try:
            import json
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for goal_id, snapshots_data in data.get('progress_history', {}).items():
                self.progress_history[goal_id] = [
                    ProgressSnapshot(
                        timestamp=datetime.fromisoformat(snap['timestamp']),
                        goal_id=snap['goal_id'],
                        progress=snap['progress'],
                        metrics=snap['metrics'],
                        notes=snap.get('notes', '')
                    )
                    for snap in snapshots_data
                ]
            
            self.milestones = data.get('milestones', {})
            
            self.logger.info(f"Загружена история прогресса для {len(self.progress_history)} целей")
            
        except FileNotFoundError:
            self.logger.info("Файл прогресса не найден, создается новый")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных прогресса: {e}")
    
    def _save_progress_data(self) -> None:
        """Сохранение данных прогресса"""
        try:
            import json
            data = {
                'progress_history': {
                    goal_id: [
                        {
                            'timestamp': snap.timestamp.isoformat(),
                            'goal_id': snap.goal_id,
                            'progress': snap.progress,
                            'metrics': snap.metrics,
                            'notes': snap.notes
                        }
                        for snap in snapshots
                    ]
                    for goal_id, snapshots in self.progress_history.items()
                },
                'milestones': self.milestones
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения прогресса: {e}")
    
    def record_progress(self, goal: Goal, progress: float, metrics: Dict[str, float] = None, notes: str = "") -> None:
        """
        Запись прогресса цели
        
        Args:
            goal: Цель
            progress: Текущий прогресс (0.0 - 1.0)
            metrics: Дополнительные метрики
            notes: Примечания
        """
        if goal.goal_id not in self.progress_history:
            self.progress_history[goal.goal_id] = []
        
        snapshot = ProgressSnapshot(
            timestamp=datetime.now(),
            goal_id=goal.goal_id,
            progress=max(0.0, min(1.0, progress)),
            metrics=metrics or {},
            notes=notes
        )
        
        self.progress_history[goal.goal_id].append(snapshot)
        
        # Проверка достижения milestones
        self._check_milestones(goal, progress)
        
        self._save_progress_data()
        
        self.logger.debug(f"Записан прогресс цели {goal.title}: {progress:.1%}")
    
    def _check_milestones(self, goal: Goal, current_progress: float) -> None:
        """Проверка достижения вех"""
        if goal.goal_id not in self.milestones:
            return
        
        milestones = self.milestones[goal.goal_id]
        previous_snapshots = self.progress_history.get(goal.goal_id, [])[:-1]  # Все кроме последнего
        
        previous_progress = previous_snapshots[-1].progress if previous_snapshots else 0.0
        
        for threshold, milestone_name in milestones:
            if previous_progress < threshold <= current_progress:
                self.logger.info(f"Достигнута веха '{milestone_name}' для цели '{goal.title}'!")
                # Здесь можно добавить уведомления или дополнительные действия
    
    def get_goal_progress_history(self, goal_id: str) -> List[ProgressSnapshot]:
        """Получение истории прогресса для цели"""
        return self.progress_history.get(goal_id, [])
    
    def calculate_progress_trend(self, goal_id: str, window: int = 5) -> Optional[float]:
        """
        Вычисление тренда прогресса (скорости изменения)
        
        Returns:
            float: Скорость прогресса (единиц прогресса в день), или None если недостаточно данных
        """
        history = self.progress_history.get(goal_id, [])
        
        if len(history) < 2:
            return None
        
        # Берем последние window снимков
        recent_snapshots = history[-window:]
        
        if len(recent_snapshots) < 2:
            return None
        
        # Вычисляем среднюю скорость
        total_days = (recent_snapshots[-1].timestamp - recent_snapshots[0].timestamp).total_seconds() / 86400
        if total_days == 0:
            return None
        
        progress_change = recent_snapshots[-1].progress - recent_snapshots[0].progress
        trend = progress_change / total_days
        
        return trend
    
    def predict_completion_date(self, goal_id: str) -> Optional[datetime]:
        """
        Прогнозирование даты завершения цели
        
        Returns:
            datetime: Предсказанная дата завершения, или None если невозможно предсказать
        """
        history = self.progress_history.get(goal_id, [])
        
        if not history:
            return None
        
        current_progress = history[-1].progress
        trend = self.calculate_progress_trend(goal_id)
        
        if trend is None or trend <= 0:
            return None
        
        remaining_progress = 1.0 - current_progress
        days_remaining = remaining_progress / trend
        
        predicted_date = datetime.now() + timedelta(days=days_remaining)
        
        return predicted_date
    
    def get_progress_summary(self, goal_id: str) -> Dict[str, Any]:
        """Получение сводки прогресса по цели"""
        history = self.progress_history.get(goal_id, [])
        
        if not history:
            return {}
        
        current = history[-1]
        first = history[0]
        
        total_duration = (current.timestamp - first.timestamp).total_seconds() / 86400  # в днях
        progress_per_day = current.progress / total_duration if total_duration > 0 else 0
        
        trend = self.calculate_progress_trend(goal_id)
        predicted_completion = self.predict_completion_date(goal_id)
        
        summary = {
            'current_progress': current.progress,
            'total_duration_days': total_duration,
            'progress_per_day': progress_per_day,
            'trend': trend,
            'predicted_completion': predicted_completion.isoformat() if predicted_completion else None,
            'snapshots_count': len(history),
            'last_update': current.timestamp.isoformat()
        }
        
        return summary
    
    def set_milestones(self, goal_id: str, milestones: List[Tuple[float, str]]) -> None:
        """Установка вех для цели"""
        self.milestones[goal_id] = sorted(milestones, key=lambda x: x[0])
        self._save_progress_data()
        self.logger.info(f"Установлено {len(milestones)} вех для цели {goal_id}")
    
    def create_progress_chart(self, goal_id: str, save_path: Optional[str] = None) -> bool:
        """
        Создание графика прогресса
        
        Args:
            goal_id: ID цели
            save_path: Путь для сохранения графика (опционально)
            
        Returns:
            bool: Успешно ли создан график
        """
        try:
            history = self.progress_history.get(goal_id, [])
            
            if len(history) < 2:
                self.logger.warning(f"Недостаточно данных для графика цели {goal_id}")
                return False
            
            timestamps = [snap.timestamp for snap in history]
            progress_values = [snap.progress * 100 for snap in history]  # в процентах
            
            plt.figure(figsize=(10, 6))
            plt.plot(timestamps, progress_values, 'b-', linewidth=2, marker='o')
            plt.fill_between(timestamps, progress_values, alpha=0.3)
            
            # Добавляем milestones
            if goal_id in self.milestones:
                for threshold, milestone_name in self.milestones[goal_id]:
                    plt.axhline(y=threshold * 100, color='r', linestyle='--', alpha=0.7)
                    plt.text(timestamps[0], threshold * 100 + 2, milestone_name, fontsize=8)
            
            plt.title(f'Прогресс выполнения цели {goal_id}')
            plt.xlabel('Дата')
            plt.ylabel('Прогресс (%)')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"График сохранен: {save_path}")
            else:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка создания графика: {e}")
            return False
    
    def get_overall_progress_stats(self) -> Dict[str, Any]:
        """Получение общей статистики по всем целям"""
        total_goals = len(self.progress_history)
        
        if total_goals == 0:
            return {}
        
        current_progresses = []
        trends = []
        
        for goal_id, history in self.progress_history.items():
            if history:
                current_progresses.append(history[-1].progress)
                trend = self.calculate_progress_trend(goal_id)
                if trend:
                    trends.append(trend)
        
        stats = {
            'total_tracked_goals': total_goals,
            'average_progress': np.mean(current_progresses) if current_progresses else 0,
            'median_progress': np.median(current_progresses) if current_progresses else 0,
            'average_trend': np.mean(trends) if trends else 0,
            'goals_completed': len([p for p in current_progresses if p >= 1.0]),
            'goals_in_progress': len([p for p in current_progresses if 0 < p < 1.0]),
            'goals_not_started': len([p for p in current_progresses if p == 0])
        }
        
        return stats