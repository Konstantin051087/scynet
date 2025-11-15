"""
Монитор производительности системы
Собирает метрики и отслеживает производительность всех компонентов
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import psutil
import json
from datetime import datetime
from pathlib import Path

@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    timestamp: float
    request_id: str
    processing_time: float
    module_times: Dict[str, float]
    memory_usage: float
    cpu_usage: float
    error_count: int

class PerformanceMonitor:
    """Монитор производительности системы"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('core.performance_monitor')
        
        # Хранилище метрик
        self.metrics_history: List[PerformanceMetrics] = []
        self.system_metrics: List[Dict[str, Any]] = []
        
        # Статистика
        self.request_count = 0
        self.error_count = 0
        self.average_response_time = 0.0
        
        # Настройки мониторинга
        self.metrics_retention = config.get('metrics_retention_days', 7)
        self.collection_interval = config.get('collection_interval', 60)  # секунды
        
        # Флаги состояния
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        self.is_initialized = False

    async def initialize(self):
        """Инициализация монитора производительности"""
        try:
            # Создаем папку для метрик если нужно
            metrics_path = Path('data/runtime/performance_metrics/')
            metrics_path.mkdir(parents=True, exist_ok=True)
            
            # Загружаем исторические данные если есть
            await self._load_historical_metrics()
            
            # Запускаем мониторинг системы
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._system_monitoring_loop())
            
            self.is_initialized = True
            self.logger.info("Монитор производительности инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации монитора производительности: {e}")
            raise

    async def record_request(self, context):
        """
        Запись метрик обработки запроса
        
        Args:
            context: Контекст обработки запроса
        """
        try:
            self.request_count += 1
            
            # Собираем метрики времени выполнения модулей
            module_times = {}
            if hasattr(context, 'modules_responses'):
                for module_name, response in context.modules_responses.items():
                    if isinstance(response, dict) and 'processing_time' in response:
                        module_times[module_name] = response['processing_time']
            
            # Получаем системные метрики
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # Создаем объект метрик
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                request_id=getattr(context, 'request_id', 'unknown'),
                processing_time=getattr(context, 'processing_time', 0),
                module_times=module_times,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                error_count=1 if hasattr(context, 'final_response') and 
                                isinstance(context.final_response, dict) and 
                                context.final_response.get('type') == 'error' else 0
            )
            
            # Добавляем в историю
            self.metrics_history.append(metrics)
            
            # Обновляем статистику
            await self._update_statistics(metrics)
            
            # Сохраняем если нужно
            if len(self.metrics_history) % 10 == 0:  # Сохраняем каждые 10 запросов
                await self._save_metrics()
            
            self.logger.debug(f"Метрики запроса {metrics.request_id} записаны")
            
        except Exception as e:
            self.logger.error(f"Ошибка записи метрик запроса: {e}")

    async def record_module_metrics(self, module_name: str, metrics: Dict[str, Any]):
        """
        Запись метрик конкретного модуля
        
        Args:
            module_name: Имя модуля
            metrics: Метрики модуля
        """
        try:
            # Здесь может быть дополнительная обработка метрик модуля
            self.logger.debug(f"Метрики модуля {module_name}: {metrics}")
            
        except Exception as e:
            self.logger.error(f"Ошибка записи метрик модуля {module_name}: {e}")

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Получение общего здоровья системы
        
        Returns:
            Статус здоровья системы
        """
        try:
            # Системные метрики
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            disk = psutil.disk_usage('/')
            
            # Метрики приложения
            app_metrics = await self._calculate_application_metrics()
            
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_usage_percent': cpu,
                    'memory_usage_percent': memory.percent,
                    'memory_available_gb': round(memory.available / (1024**3), 2),
                    'disk_usage_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024**3), 2)
                },
                'application': app_metrics,
                'overall_health': await self._calculate_overall_health(cpu, memory.percent, app_metrics)
            }
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Ошибка получения здоровья системы: {e}")
            return {'error': str(e)}

    async def get_performance_report(self, time_range: str = '1h') -> Dict[str, Any]:
        """
        Генерация отчета о производительности
        
        Args:
            time_range: Временной диапазон ('1h', '24h', '7d')
            
        Returns:
            Отчет о производительности
        """
        try:
            # Фильтруем метрики по временному диапазону
            time_ranges = {
                '1h': 3600,
                '24h': 86400,
                '7d': 604800
            }
            
            range_seconds = time_ranges.get(time_range, 3600)
            cutoff_time = time.time() - range_seconds
            
            recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
            
            if not recent_metrics:
                return {'error': 'Нет данных за указанный период'}
            
            # Анализируем метрики
            report = {
                'time_range': time_range,
                'total_requests': len(recent_metrics),
                'error_requests': sum(1 for m in recent_metrics if m.error_count > 0),
                'average_response_time': sum(m.processing_time for m in recent_metrics) / len(recent_metrics),
                'max_response_time': max(m.processing_time for m in recent_metrics),
                'min_response_time': min(m.processing_time for m in recent_metrics),
                'average_cpu_usage': sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
                'average_memory_usage': sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
                'module_performance': await self._analyze_module_performance(recent_metrics)
            }
            
            # Расчет процента ошибок
            report['error_rate'] = (report['error_requests'] / report['total_requests']) * 100
            
            return report
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")
            return {'error': str(e)}

    async def _system_monitoring_loop(self):
        """Цикл мониторинга системных метрик"""
        while self.is_monitoring:
            try:
                # Собираем системные метрики
                system_metrics = await self.get_system_health()
                self.system_metrics.append(system_metrics)
                
                # Сохраняем системные метрики
                if len(self.system_metrics) % 5 == 0:  # Сохраняем каждые 5 сборов
                    await self._save_system_metrics()
                
                # Очищаем старые данные
                await self._cleanup_old_metrics()
                
                # Ждем до следующего сбора
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(10)  # Ждем перед повторной попыткой

    async def _calculate_application_metrics(self) -> Dict[str, Any]:
        """Расчет метрик приложения"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-100:]  # Последние 100 запросов
        
        return {
            'total_requests': self.request_count,
            'recent_requests': len(recent_metrics),
            'average_response_time': self.average_response_time,
            'error_count': self.error_count,
            'error_rate': (self.error_count / max(self.request_count, 1)) * 100,
            'active_modules': await self._get_active_modules_count()
        }

    async def _calculate_overall_health(self, cpu: float, memory: float, app_metrics: Dict[str, Any]) -> str:
        """Расчет общего здоровья системы"""
        health_score = 100
        
        # Штрафы за высокую нагрузку
        if cpu > 80:
            health_score -= 20
        elif cpu > 90:
            health_score -= 40
            
        if memory > 80:
            health_score -= 20
        elif memory > 90:
            health_score -= 40
            
        if app_metrics.get('error_rate', 0) > 5:
            health_score -= 20
        elif app_metrics.get('error_rate', 0) > 10:
            health_score -= 40
        
        # Определяем статус
        if health_score >= 80:
            return 'healthy'
        elif health_score >= 60:
            return 'degraded'
        elif health_score >= 40:
            return 'unhealthy'
        else:
            return 'critical'

    async def _analyze_module_performance(self, metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Анализ производительности модулей"""
        module_stats = {}
        
        for metric in metrics:
            for module_name, module_time in metric.module_times.items():
                if module_name not in module_stats:
                    module_stats[module_name] = {
                        'total_time': 0,
                        'count': 0,
                        'times': []
                    }
                
                module_stats[module_name]['total_time'] += module_time
                module_stats[module_name]['count'] += 1
                module_stats[module_name]['times'].append(module_time)
        
        # Расчет статистики
        result = {}
        for module_name, stats in module_stats.items():
            if stats['count'] > 0:
                result[module_name] = {
                    'average_time': stats['total_time'] / stats['count'],
                    'max_time': max(stats['times']),
                    'min_time': min(stats['times']),
                    'request_count': stats['count']
                }
        
        return result

    async def _update_statistics(self, metrics: PerformanceMetrics):
        """Обновление общей статистики"""
        # Обновляем среднее время ответа
        total_time = self.average_response_time * (self.request_count - 1) + metrics.processing_time
        self.average_response_time = total_time / self.request_count
        
        # Обновляем счетчик ошибок
        if metrics.error_count > 0:
            self.error_count += 1

    async def _get_active_modules_count(self) -> int:
        """Получение количества активных модулей"""
        # В реальной системе здесь будет обращение к ModuleManager
        return len([m for m in self.metrics_history[-10:] if m.module_times]) if self.metrics_history else 0

    async def _save_metrics(self):
        """Сохранение метрик в файл"""
        try:
            metrics_path = Path('data/runtime/performance_metrics/request_metrics.json')
            
            # Сохраняем только последние метрики
            data_to_save = [
                {
                    'timestamp': m.timestamp,
                    'request_id': m.request_id,
                    'processing_time': m.processing_time,
                    'module_times': m.module_times,
                    'memory_usage': m.memory_usage,
                    'cpu_usage': m.cpu_usage,
                    'error_count': m.error_count
                }
                for m in self.metrics_history[-1000:]  # Сохраняем последние 1000 записей
            ]
            
            with open(metrics_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения метрик: {e}")

    async def _save_system_metrics(self):
        """Сохранение системных метрик"""
        try:
            metrics_path = Path('data/runtime/performance_metrics/system_metrics.json')
            
            with open(metrics_path, 'w', encoding='utf-8') as f:
                json.dump(self.system_metrics[-500:], f, indent=2, ensure_ascii=False)  # Последние 500 записей
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения системных метрик: {e}")

    async def _load_historical_metrics(self):
        """Загрузка исторических метрик"""
        try:
            metrics_path = Path('data/runtime/performance_metrics/request_metrics.json')
            
            if metrics_path.exists():
                with open(metrics_path, 'r', encoding='utf-8') as f:
                    historical_data = json.load(f)
                
                # Восстанавливаем объекты метрик
                for data in historical_data:
                    metrics = PerformanceMetrics(
                        timestamp=data['timestamp'],
                        request_id=data['request_id'],
                        processing_time=data['processing_time'],
                        module_times=data['module_times'],
                        memory_usage=data['memory_usage'],
                        cpu_usage=data['cpu_usage'],
                        error_count=data['error_count']
                    )
                    self.metrics_history.append(metrics)
                
                self.logger.info(f"Загружено {len(historical_data)} исторических метрик")
                
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить исторические метрики: {e}")

    async def _cleanup_old_metrics(self):
        """Очистка устаревших метрик"""
        try:
            retention_seconds = self.metrics_retention * 86400  # Перевод в секунды
            cutoff_time = time.time() - retention_seconds
            
            # Очищаем историю запросов
            self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
            
            # Очищаем системные метрики
            self.system_metrics = [m for m in self.system_metrics 
                                 if m.get('timestamp', 0) > cutoff_time]
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки старых метрик: {e}")

    async def get_monitor_stats(self) -> Dict[str, Any]:
        """Получение статистики монитора"""
        return {
            'is_monitoring': self.is_monitoring,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'average_response_time': self.average_response_time,
            'metrics_history_size': len(self.metrics_history),
            'system_metrics_size': len(self.system_metrics),
            'is_initialized': self.is_initialized
        }

    async def shutdown(self):
        """Корректное завершение работы монитора"""
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Сохраняем все метрики перед завершением
        await self._save_metrics()
        await self._save_system_metrics()
        
        self.logger.info("Монитор производительности завершил работу")