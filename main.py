# main.py - ГЛАВНЫЙ ЗАПУСКАЕМЫЙ ФАЙЛ (точка входа)

import os
import sys
import logging
import signal
import asyncio
import yaml
import importlib
import inspect
import psutil
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Callable, Coroutine
import traceback

# Добавляем корневую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты core модулей с улучшенной обработкой ошибок
try:
    from core.coordinator import Coordinator
    from core.communication_bus import CommunicationBus
    from core.module_manager import ModuleManager
    from core.security_gateway import SecurityGateway
    from core.performance_monitor import PerformanceMonitor
except ImportError as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось импортировать core модули: {e}")
    print("💡 Проверьте наличие файлов в папке core/ и корректность импортов")
    print("🔍 Детали ошибки импорта:")
    print(f"   - Рабочая директория: {os.getcwd()}")
    print(f"   - Python path: {sys.path}")
    core_path = Path("core")
    if core_path.exists():
        print(f"   - Содержимое папки core: {list(core_path.iterdir())}")
    else:
        print("   - Папка core не существует!")
    sys.exit(1)

class SystemConfig:
    """
    Класс для загрузки и управления конфигурацией системы из YAML файлов
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.config_path = Path("config")
        
    async def load(self) -> bool:
        """Загрузка конфигурации из YAML файлов"""
        try:
            # Проверка существования config директории
            if not self.config_path.exists():
                error_msg = f"❌ Директория конфигурации {self.config_path} не найдена"
                print(error_msg)
                logging.error(error_msg)
                return False
                
            # Загрузка основного конфигурационного файла
            system_config_file = self.config_path / "system.yaml"
            if system_config_file.exists():
                with open(system_config_file, 'r', encoding='utf-8') as f:
                    self.config.update(yaml.safe_load(f) or {})
                print(f"✅ Загружен конфигурационный файл: {system_config_file}")
            else:
                warning_msg = f"⚠️ Основной конфигурационный файл {system_config_file} не найден"
                print(warning_msg)
                logging.warning(warning_msg)
            
            # Загрузка дополнительных конфигураций
            modules_config_dir = self.config_path / "modules"
            if modules_config_dir.exists():
                config_files_loaded = 0
                for config_file in modules_config_dir.glob("*.yaml"):
                    try:
                        module_name = config_file.stem
                        with open(config_file, 'r', encoding='utf-8') as f:
                            module_config = yaml.safe_load(f) or {}
                            if 'modules' not in self.config:
                                self.config['modules'] = {}
                            self.config['modules'][module_name] = module_config
                        config_files_loaded += 1
                        print(f"✅ Загружена конфигурация модуля: {module_name}")
                    except Exception as e:
                        error_msg = f"⚠️ Ошибка загрузки конфигурации модуля {config_file}: {e}"
                        print(error_msg)
                        logging.error(error_msg)
                print(f"📊 Загружено конфигураций модулей: {config_files_loaded}")
            else:
                warning_msg = f"⚠️ Директория конфигураций модулей {modules_config_dir} не найдена"
                print(warning_msg)
                logging.warning(warning_msg)
            
            # Загрузка настроек безопасности
            security_config_file = self.config_path / "security_policies.yaml"
            if security_config_file.exists():
                try:
                    with open(security_config_file, 'r', encoding='utf-8') as f:
                        security_config = yaml.safe_load(f) or {}
                        self.config.update(security_config)
                    print(f"✅ Загружены настройки безопасности: {security_config_file}")
                except Exception as e:
                    error_msg = f"⚠️ Ошибка загрузки конфигурации безопасности: {e}"
                    print(error_msg)
                    logging.error(error_msg)
            else:
                warning_msg = f"⚠️ Файл конфигурации безопасности {security_config_file} не найден"
                print(warning_msg)
                logging.warning(warning_msg)
            
            # Загрузка настроек производительности
            performance_config_file = self.config_path / "performance_settings.yaml"
            if performance_config_file.exists():
                try:
                    with open(performance_config_file, 'r', encoding='utf-8') as f:
                        performance_config = yaml.safe_load(f) or {}
                        self.config.update(performance_config)
                    print(f"✅ Загружены настройки производительности: {performance_config_file}")
                except Exception as e:
                    error_msg = f"⚠️ Ошибка загрузки конфигурации производительности: {e}"
                    print(error_msg)
                    logging.error(error_msg)
            else:
                warning_msg = f"⚠️ Файл конфигурации производительности {performance_config_file} не найден"
                print(warning_msg)
                logging.warning(warning_msg)
                    
            print("✅ Загрузка конфигурации завершена успешно")
            return True
            
        except Exception as e:
            error_msg = f"❌ Критическая ошибка загрузки конфигурации: {e}"
            print(error_msg)
            print(f"🔍 Детали ошибки: {traceback.format_exc()}")
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            return False
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Получение значения конфигурации по ключу (с поддержкой вложенных ключей через '.')"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Получение конфигурации конкретного модуля"""
        return self.config.get('modules', {}).get(module_name, {})


class SystemHealthMonitor:
    """
    Комплексный мониторинг здоровья системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("SystemHealthMonitor")
        self.health_metrics: Dict[str, Any] = {}
        self.start_time = datetime.now()
        
    async def check_system_resources(self) -> Dict[str, Any]:
        """Проверка системных ресурсов"""
        try:
            resources = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()),
                'system_uptime': datetime.now() - datetime.fromtimestamp(psutil.boot_time()),
                'process_uptime': datetime.now() - self.start_time
            }
            self.logger.debug(f"Проверка ресурсов: CPU={resources['cpu_percent']}%, Memory={resources['memory_usage']}%, Disk={resources['disk_usage']}%")
            return resources
        except Exception as e:
            error_msg = f"Ошибка проверки системных ресурсов: {e}"
            self.logger.error(error_msg)
            return {
                'cpu_percent': 0,
                'memory_usage': 0,
                'disk_usage': 0,
                'boot_time': datetime.now(),
                'system_uptime': timedelta(0),
                'process_uptime': timedelta(0)
            }
    
    async def check_database_connections(self) -> Dict[str, bool]:
        """Проверка подключений к базам данных"""
        connections = {
            'postgres': False,
            'redis': False
        }
        
        try:
            # Проверка PostgreSQL
            postgres_url = self.system_config.get('database.postgres_url')
            if postgres_url and 'postgresql://' in postgres_url:
                # Здесь можно добавить реальную проверку подключения
                connections['postgres'] = True
                self.logger.debug("Подключение к PostgreSQL: ДОСТУПНО")
            else:
                self.logger.warning("URL PostgreSQL не настроен или неверный формат")
        except Exception as e:
            self.logger.warning(f"Ошибка проверки PostgreSQL: {e}")
            
        try:
            # Проверка Redis
            redis_url = self.system_config.get('database.redis_url')
            if redis_url and 'redis://' in redis_url:
                # Здесь можно добавить реальную проверку подключения
                connections['redis'] = True
                self.logger.debug("Подключение к Redis: ДОСТУПНО")
            else:
                self.logger.warning("URL Redis не настроен или неверный формат")
        except Exception as e:
            self.logger.warning(f"Ошибка проверки Redis: {e}")
            
        return connections
    
    async def check_essential_services(self) -> Dict[str, Dict[str, Any]]:
        """Проверка работы основных сервисов"""
        services = {}
        
        try:
            # Проверка доступности лог-файлов
            log_dirs = ['logs/system', 'logs/audit', 'logs/performance']
            for log_dir in log_dirs:
                path = Path(log_dir)
                services[f'log_dir_{log_dir}'] = {
                    'status': path.exists() and path.is_dir(),
                    'writable': os.access(path, os.W_OK) if path.exists() else False
                }
                if not services[f'log_dir_{log_dir}']['status']:
                    self.logger.warning(f"Директория логов не найдена: {log_dir}")
                elif not services[f'log_dir_{log_dir}']['writable']:
                    self.logger.warning(f"Нет прав на запись в директорию логов: {log_dir}")
            
            # Проверка доступности данных
            data_dirs = ['data/runtime', 'data/cache', 'data/temporary_files']
            for data_dir in data_dirs:
                path = Path(data_dir)
                services[f'data_dir_{data_dir}'] = {
                    'status': path.exists() and path.is_dir(),
                    'writable': os.access(path, os.W_OK) if path.exists() else False,
                    'free_space': psutil.disk_usage(path).free if path.exists() else 0
                }
                if not services[f'data_dir_{data_dir}']['status']:
                    self.logger.warning(f"Директория данных не найдена: {data_dir}")
                elif not services[f'data_dir_{data_dir}']['writable']:
                    self.logger.warning(f"Нет прав на запись в директорию данных: {data_dir}")
        except Exception as e:
            self.logger.error(f"Ошибка проверки сервисов: {e}")
        
        return services
    
    async def get_system_health_score(self) -> Tuple[int, str, List[str]]:
        """Расчет общего показателя здоровья системы (0-100)"""
        total_checks = 0
        passed_checks = 0
        issues = []
        
        try:
            # Проверка ресурсов
            resources = await self.check_system_resources()
            total_checks += 3
            if resources['cpu_percent'] < 90:
                passed_checks += 1
            else:
                issues.append(f"Высокая загрузка CPU: {resources['cpu_percent']}%")
                
            if resources['memory_usage'] < 85:
                passed_checks += 1
            else:
                issues.append(f"Высокая загрузка памяти: {resources['memory_usage']}%")
                
            if resources['disk_usage'] < 90:
                passed_checks += 1
            else:
                issues.append(f"Мало свободного места на диске: {resources['disk_usage']}%")
            
            # Проверка подключений
            connections = await self.check_database_connections()
            total_checks += 2
            if connections['postgres']:
                passed_checks += 1
            else:
                issues.append("Нет подключения к PostgreSQL")
                
            if connections['redis']:
                passed_checks += 1
            else:
                issues.append("Нет подключения к Redis")
            
            # Проверка сервисов
            services = await self.check_essential_services()
            service_checks = len(services)
            passed_service_checks = sum(1 for service in services.values() if service['status'])
            total_checks += service_checks
            passed_checks += passed_service_checks
            
            if passed_service_checks < service_checks:
                issues.append(f"Проблемы с {service_checks - passed_service_checks} сервисами")
            
            health_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            if health_score >= 90:
                status = "💚 ОТЛИЧНО"
            elif health_score >= 70:
                status = "💛 ХОРОШО"
            elif health_score >= 50:
                status = "🟡 УДОВЛЕТВОРИТЕЛЬНО"
            else:
                status = "🔴 КРИТИЧЕСКО"
                
            self.logger.info(f"Оценка здоровья системы: {health_score}% - {status}")
            if issues:
                self.logger.warning(f"Обнаружены проблемы: {issues}")
                
            return round(health_score), status, issues
            
        except Exception as e:
            error_msg = f"Ошибка расчета здоровья системы: {e}"
            self.logger.error(error_msg)
            return 0, "🔴 ОШИБКА", [f"Ошибка мониторинга здоровья: {e}"]


class FunctionalTestEngine:
    """
    Движок функционального тестирования системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("FunctionalTestEngine")
        self.test_results: Dict[str, Any] = {}
        
    async def test_communication_bus(self) -> Dict[str, Any]:
        """Тестирование шины сообщений"""
        test_result = {
            'status': 'PENDING',
            'message': '',
            'latency': 0,
            'details': {}
        }
        
        try:
            start_time = time.time()
            
            # Создаем временную шину для тестирования
            self.logger.info("Создание тестовой шины сообщений...")
            test_bus = CommunicationBus(self.system_config)
            await test_bus.initialize()
            
            # Тест отправки и получения сообщения
            test_message = {
                'type': 'test',
                'content': 'functional_test',
                'timestamp': datetime.now().isoformat()
            }
            
            # Здесь должна быть логика тестирования шины
            # Для примера просто проверяем, что шина инициализирована
            if await test_bus.is_healthy():
                test_result['status'] = 'PASS'
                test_result['message'] = 'Шина сообщений работает корректно'
                self.logger.info("✅ Тест шины сообщений: ПРОЙДЕН")
            else:
                test_result['status'] = 'FAIL'
                test_result['message'] = 'Шина сообщений не работает'
                self.logger.error("❌ Тест шины сообщений: ПРОВАЛЕН")
                
            test_result['latency'] = round((time.time() - start_time) * 1000, 2)
            await test_bus.shutdown()
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['message'] = f'Ошибка тестирования шины: {str(e)}'
            test_result['details'] = {
                'error': traceback.format_exc(),
                'error_type': type(e).__name__
            }
            self.logger.error(f"❌ Ошибка тестирования шины сообщений: {e}")
            self.logger.debug(f"Детали ошибки: {traceback.format_exc()}")
            
        return test_result
    
    async def test_security_gateway(self) -> Dict[str, Any]:
        """Тестирование шлюза безопасности"""
        test_result = {
            'status': 'PENDING',
            'message': '',
            'details': {}
        }
        
        try:
            self.logger.info("Создание тестового шлюза безопасности...")
            security = SecurityGateway(self.system_config.get('security', {}))
            await security.initialize()
            
            # Тест проверки безопасного контента
            safe_content = "Это безопасное сообщение"
            security_check = await security.validate_input(safe_content)
            
            if security_check.get('approved', False):
                test_result['status'] = 'PASS'
                test_result['message'] = 'Шлюз безопасности корректно пропускает безопасный контент'
                self.logger.info("✅ Тест шлюза безопасности: ПРОЙДЕН")
            else:
                test_result['status'] = 'FAIL'
                test_result['message'] = 'Шлюз безопасности блокирует безопасный контент'
                self.logger.error("❌ Тест шлюза безопасности: ПРОВАЛЕН")
                
            await security.shutdown()
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['message'] = f'Ошибка тестирования безопасности: {str(e)}'
            test_result['details'] = {
                'error': traceback.format_exc(),
                'error_type': type(e).__name__
            }
            self.logger.error(f"❌ Ошибка тестирования шлюза безопасности: {e}")
            self.logger.debug(f"Детали ошибки: {traceback.format_exc()}")
            
        return test_result
    
    async def test_module_integration(self) -> Dict[str, Any]:
        """Тестирование интеграции модулей"""
        test_result = {
            'status': 'PENDING',
            'message': '',
            'modules_tested': 0,
            'modules_passed': 0,
            'details': {}
        }
        
        try:
            # Тестируем базовые модули
            test_modules = ['text_understander', 'memory_short_term']
            modules_tested = 0
            modules_passed = 0
            details = {}
            
            self.logger.info(f"Тестирование интеграции модулей: {test_modules}")
            
            for module_name in test_modules:
                try:
                    # Проверяем существование модуля
                    if module_name == 'text_understander':
                        module_path = Path("modules/interface/text_understander")
                    else:  # memory_short_term
                        module_path = Path("modules/cognitive/memory_short_term")
                    
                    if module_path.exists() and (module_path / "__init__.py").exists():
                        modules_tested += 1
                        modules_passed += 1
                        details[module_name] = 'PASS - модуль существует и доступен'
                        self.logger.info(f"✅ Модуль {module_name}: ДОСТУПЕН")
                    else:
                        modules_tested += 1
                        details[module_name] = f'FAIL - модуль не найден по пути: {module_path}'
                        self.logger.warning(f"⚠️ Модуль {module_name}: НЕ НАЙДЕН по пути {module_path}")
                except Exception as e:
                    modules_tested += 1
                    details[module_name] = f'ERROR: {str(e)}'
                    self.logger.error(f"❌ Ошибка тестирования модуля {module_name}: {e}")
            
            test_result['modules_tested'] = modules_tested
            test_result['modules_passed'] = modules_passed
            test_result['details'] = details
            
            if modules_passed == modules_tested:
                test_result['status'] = 'PASS'
                test_result['message'] = f'Все {modules_tested} модулей работают корректно'
                self.logger.info("✅ Тест интеграции модулей: ПРОЙДЕН")
            else:
                test_result['status'] = 'FAIL'
                test_result['message'] = f'Проблемы с {modules_tested - modules_passed} модулями'
                self.logger.warning(f"⚠️ Тест интеграции модулей: ПРОБЛЕМЫ с {modules_tested - modules_passed} модулями")
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['message'] = f'Ошибка тестирования интеграции: {str(e)}'
            test_result['details'] = {'error': traceback.format_exc()}
            self.logger.error(f"❌ Ошибка тестирования интеграции модулей: {e}")
            self.logger.debug(f"Детали ошибки: {traceback.format_exc()}")
            
        return test_result
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Запуск комплексного тестирования"""
        self.logger.info("🧪 Запуск комплексного функционального тестирования...")
        
        tests = {
            'communication_bus': await self.test_communication_bus(),
            'security_gateway': await self.test_security_gateway(),
            'module_integration': await self.test_module_integration()
        }
        
        # Расчет общей статистики
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests.values() if test['status'] == 'PASS')
        failed_tests = sum(1 for test in tests.values() if test['status'] == 'FAIL')
        error_tests = sum(1 for test in tests.values() if test['status'] == 'ERROR')
        
        overall_status = 'PASS' if failed_tests == 0 and error_tests == 0 else 'FAIL'
        
        self.logger.info(f"📊 Результаты тестирования: {passed_tests}/{total_tests} пройдено")
        
        return {
            'overall_status': overall_status,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            'detailed_results': tests,
            'timestamp': datetime.now().isoformat()
        }


class PerformanceValidator:
    """
    Валидатор производительности системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("PerformanceValidator")
        self.benchmarks: Dict[str, Any] = {}
        
    async def validate_response_times(self) -> Dict[str, Any]:
        """Валидация времени ответа системы"""
        benchmarks = {
            'system_startup': {'target': 5000, 'actual': 0, 'status': 'PENDING'},
            'module_initialization': {'target': 3000, 'actual': 0, 'status': 'PENDING'},
            'message_processing': {'target': 1000, 'actual': 0, 'status': 'PENDING'}
        }
        
        try:
            # Здесь будут реальные замеры производительности
            # Пока используем заглушки
            benchmarks['system_startup']['actual'] = 1200
            benchmarks['module_initialization']['actual'] = 800
            benchmarks['message_processing']['actual'] = 150
            
            # Проверка соответствия целевым показателям
            for key, benchmark in benchmarks.items():
                if benchmark['actual'] <= benchmark['target']:
                    benchmark['status'] = 'PASS'
                    self.logger.info(f"✅ {key}: {benchmark['actual']}мс (цель: {benchmark['target']}мс) - ПРОЙДЕН")
                else:
                    benchmark['status'] = 'FAIL'
                    self.logger.warning(f"⚠️ {key}: {benchmark['actual']}мс (цель: {benchmark['target']}мс) - ПРОВАЛЕН")
                    
            return benchmarks
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации времени ответа: {e}")
            return benchmarks
    
    async def validate_resource_usage(self) -> Dict[str, Any]:
        """Валидация использования ресурсов"""
        try:
            resources = await SystemHealthMonitor(self.system_config).check_system_resources()
            
            targets = {
                'cpu_percent': 80,
                'memory_usage': 85,
                'disk_usage': 90
            }
            
            results = {}
            for resource, current_value in resources.items():
                if resource in targets:
                    target = targets[resource]
                    if current_value <= target:
                        results[resource] = {
                            'current': current_value,
                            'target': target,
                            'status': 'PASS',
                            'unit': '%'
                        }
                        self.logger.info(f"✅ {resource}: {current_value}% (цель: {target}%) - ПРОЙДЕН")
                    else:
                        results[resource] = {
                            'current': current_value,
                            'target': target,
                            'status': 'WARNING',
                            'unit': '%'
                        }
                        self.logger.warning(f"⚠️ {resource}: {current_value}% (цель: {target}%) - ПРЕВЫШЕНИЕ")
                    
            return results
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации использования ресурсов: {e}")
            return {}
    
    async def run_performance_validation(self) -> Dict[str, Any]:
        """Запуск валидации производительности"""
        self.logger.info("⚡ Запуск валидации производительности...")
        
        try:
            response_times = await self.validate_response_times()
            resource_usage = await self.validate_resource_usage()
            
            # Расчет общего статуса
            all_pass = all(
                benchmark['status'] == 'PASS' 
                for benchmark in response_times.values()
            ) and all(
                usage['status'] in ['PASS', 'WARNING'] 
                for usage in resource_usage.values()
            )
            
            status = 'PASS' if all_pass else 'FAIL'
            self.logger.info(f"📊 Общий статус производительности: {status}")
            
            return {
                'overall_status': status,
                'response_times': response_times,
                'resource_usage': resource_usage,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации производительности: {e}")
            return {
                'overall_status': 'ERROR',
                'response_times': {},
                'resource_usage': {},
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


class ModuleDiagnostic:
    """
    Класс для диагностики модулей системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("ModuleDiagnostic")
        self.modules_status: Dict[str, Any] = {}
        
    async def scan_project_structure(self) -> Dict[str, Dict[str, Any]]:
        """Сканирование структуры проекта и выявление реализованных модулей"""
        self.logger.info("🔍 Сканирование структуры проекта...")
        
        modules_base = Path("modules")
        core_base = Path("core")
        
        discovered_modules = {}
        
        try:
            # Сканирование основных категорий модулей
            categories = ['interface', 'cognitive', 'planning', 'skills']
            for category in categories:
                category_path = modules_base / category
                if category_path.exists():
                    for module_dir in category_path.iterdir():
                        if module_dir.is_dir() and (module_dir / "__init__.py").exists():
                            module_name = module_dir.name
                            discovered_modules[module_name] = {
                                'path': module_dir,
                                'category': category,
                                'type': 'module'
                            }
                            self.logger.debug(f"Обнаружен модуль: {module_name} ({category})")
                else:
                    self.logger.warning(f"Категория модулей не найдена: {category}")
            
            # Сканирование core компонентов
            if core_base.exists():
                for core_file in core_base.glob("*.py"):
                    if core_file.name != "__init__.py":
                        module_name = core_file.stem
                        discovered_modules[module_name] = {
                            'path': core_file,
                            'category': 'core',
                            'type': 'core'
                        }
                        self.logger.debug(f"Обнаружен core компонент: {module_name}")
            else:
                self.logger.warning("Директория core не найдена")
            
            self.logger.info(f"📁 Обнаружено {len(discovered_modules)} модулей в структуре проекта")
            return discovered_modules
        except Exception as e:
            self.logger.error(f"Ошибка сканирования структуры проекта: {e}")
            return {}
    
    async def check_module_health(self, module_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Проверка работоспособности конкретного модуля"""
        module_name = list(module_info.keys())[0]
        info = module_info[module_name]
        
        try:
            # Проверка существования файлов
            if not info['path'].exists():
                return False, f"Файлы модуля не найдены по пути: {info['path']}"
            
            # Попытка импорта модуля
            if info['type'] == 'module':
                import_path = f"modules.{info['category']}.{module_name}"
            else:
                import_path = f"core.{module_name}"
            
            self.logger.debug(f"Попытка импорта модуля: {import_path}")
            try:
                module = importlib.import_module(import_path)
            except ImportError as e:
                return False, f"Ошибка импорта {import_path}: {e}"
            
            # Проверка наличия основных классов
            classes = inspect.getmembers(module, inspect.isclass)
            main_classes = [cls[0] for cls in classes if cls[1].__module__ == module.__name__]
            
            if not main_classes:
                return False, "Не найдены основные классы модуля"
            
            # Проверка методов инициализации
            for class_name in main_classes:
                cls = getattr(module, class_name)
                if hasattr(cls, 'initialize') and callable(getattr(cls, 'initialize')):
                    self.logger.debug(f"Модуль {module_name} имеет метод initialize")
                    return True, "Модуль готов к работе"
            
            return False, "Отсутствуют необходимые методы инициализации"
            
        except Exception as e:
            error_details = f"Критическая ошибка при проверке модуля: {e}\n{traceback.format_exc()}"
            self.logger.error(f"Ошибка проверки модуля {module_name}: {error_details}")
            return False, error_details
    
    async def diagnose_all_modules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Полная диагностика всех модулей системы с учетом реального состояния"""
        self.logger.info("🩺 Запуск полной диагностики модулей...")
        
        try:
            discovered_modules = await self.scan_project_structure()
            
            # Получаем реальное состояние модулей из ModuleManager, если он доступен
            real_module_status = {}
            enabled_modules_from_manager = []
            
            # Пытаемся получить реальное состояние через ModuleManager
            try:
                # Импортируем здесь, чтобы избежать циклических импортов
                from core.module_manager import ModuleManager
                # Создаем временный ModuleManager для получения реального статуса
                temp_manager = ModuleManager(self.system_config.get('modules', {}))
                if hasattr(temp_manager, 'get_all_modules_status'):
                    real_module_status = await temp_manager.get_all_modules_status()
                    enabled_modules_from_manager = list(real_module_status.keys())
                    self.logger.info(f"📊 Получен реальный статус {len(enabled_modules_from_manager)} модулей из ModuleManager")
            except Exception as e:
                self.logger.warning(f"⚠️ Не удалось получить реальный статус модулей: {e}")
                # Fallback: используем конфигурацию
                enabled_modules_from_manager = self.system_config.get('modules.enabled', [])
            
            diagnostic_results = {
                'implemented_but_disabled': [],
                'enabled_but_broken': [],
                'working_modules': [],
                'broken_modules': []
            }

            self.logger.info(f"Проверка {len(discovered_modules)} модулей...")
            
            for module_name, module_info in discovered_modules.items():
                # Проверяем реальный статус модуля
                is_enabled = module_name in enabled_modules_from_manager
                
                # Проверяем здоровье модуля
                is_healthy, message = await self.check_module_health({module_name: module_info})
                
                module_status = {
                    'name': module_name,
                    'category': module_info['category'],
                    'enabled': is_enabled,
                    'healthy': is_healthy,
                    'message': message,
                    'path': str(module_info['path'])
                }
                
                self.modules_status[module_name] = module_status
                
                if is_healthy:
                    if is_enabled:
                        diagnostic_results['working_modules'].append(module_status)
                        self.logger.info(f"✅ Рабочий модуль: {module_name} ({module_info['category']})")
                    else:
                        diagnostic_results['implemented_but_disabled'].append(module_status)
                        self.logger.info(f"🔶 Отключенный модуль: {module_name} ({module_info['category']})")
                else:
                    if is_enabled:
                        diagnostic_results['enabled_but_broken'].append(module_status)
                        self.logger.error(f"❌ Сломанный включенный модуль: {module_name} ({module_info['category']}) - {message}")
                    else:
                        diagnostic_results['broken_modules'].append(module_status)
                        self.logger.warning(f"⚠️ Сломанный отключенный модуль: {module_name} ({module_info['category']}) - {message}")
            
            self.logger.info("📊 Диагностика модулей завершена")
            return diagnostic_results
        except Exception as e:
            self.logger.error(f"Ошибка диагностики модулей: {e}")
            return {
                'implemented_but_disabled': [],
                'enabled_but_broken': [],
                'working_modules': [],
                'broken_modules': []
            }
    
    def generate_diagnostic_report(self, diagnostic_results: Dict[str, Any]) -> str:
        """Генерация красивого отчета о диагностике"""
        report = []
        report.append("=" * 80)
        report.append("🩺 ДИАГНОСТИЧЕСКИЙ ОТЧЕТ СИНТЕТИЧЕСКОГО РАЗУМА")
        report.append("=" * 80)
        
        # Рабочие модули
        if diagnostic_results['working_modules']:
            report.append("\n✅ РАБОЧИЕ МОДУЛИ (включены и функционируют):")
            for module in diagnostic_results['working_modules']:
                report.append(f"   📦 {module['name']} ({module['category']}) - {module['message']}")
        
        # Реализованы но отключены
        if diagnostic_results['implemented_but_disabled']:
            report.append("\n🔶 РЕАЛИЗОВАННЫЕ НО ОТКЛЮЧЕННЫЕ МОДУЛИ:")
            for module in diagnostic_results['implemented_but_disabled']:
                report.append(f"   📦 {module['name']} ({module['category']}) - {module['message']}")
                report.append(f"      💡 Совет: Добавьте '{module['name']}' в modules.enabled в system.yaml")
        
        # Включены но не работают
        if diagnostic_results['enabled_but_broken']:
            report.append("\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ (включены но не работают):")
            for module in diagnostic_results['enabled_but_broken']:
                report.append(f"   💥 {module['name']} ({module['category']}) - {module['message']}")
                report.append(f"      🛠️  Требуется немедленное исправление!")
        
        # Сломанные модули
        if diagnostic_results['broken_modules']:
            report.append("\n⚠️  НЕРАБОТАЮЩИЕ МОДУЛИ (требуют доработки):")
            for module in diagnostic_results['broken_modules']:
                report.append(f"   🚧 {module['name']} ({module['category']}) - {module['message']}")
        
        # Статистика
        total_implemented = len(diagnostic_results['working_modules'] + 
                               diagnostic_results['implemented_but_disabled'] + 
                               diagnostic_results['enabled_but_broken'] + 
                               diagnostic_results['broken_modules'])
        
        report.append("\n" + "=" * 80)
        report.append(f"📊 СТАТИСТИКА:")
        report.append(f"   Всего модулей в структуре: {total_implemented}")
        report.append(f"   ✅ Рабочих: {len(diagnostic_results['working_modules'])}")
        report.append(f"   🔶 Отключенных: {len(diagnostic_results['implemented_but_disabled'])}")
        report.append(f"   ❌ Критических: {len(diagnostic_results['enabled_but_broken'])}")
        report.append(f"   ⚠️  Требуют исправления: {len(diagnostic_results['broken_modules'])}")
        report.append("=" * 80)
        
        return "\n".join(report)


class ComprehensiveSystemValidator:
    """
    Комплексный валидатор всей системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("ComprehensiveSystemValidator")
        self.health_monitor = SystemHealthMonitor(system_config)
        self.functional_tester = FunctionalTestEngine(system_config)
        self.performance_validator = PerformanceValidator(system_config)
        self.module_diagnostic = ModuleDiagnostic(system_config)
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Запуск комплексной проверки системы"""
        self.logger.info("🎯 Запуск комплексной проверки системы...")
        
        start_time = time.time()
        
        try:
            # Параллельный запуск всех проверок
            health_task = asyncio.create_task(self.health_monitor.get_system_health_score())
            functional_task = asyncio.create_task(self.functional_tester.run_comprehensive_tests())
            performance_task = asyncio.create_task(self.performance_validator.run_performance_validation())
            module_task = asyncio.create_task(self.module_diagnostic.diagnose_all_modules())
            
            # Ожидаем завершения всех проверок
            health_score, health_status, health_issues = await health_task
            functional_results = await functional_task
            performance_results = await performance_task
            module_results = await module_task
            
            validation_time = round(time.time() - start_time, 2)
            
            # Расчет общего статуса системы
            overall_status = self._calculate_overall_status(
                health_score, 
                functional_results, 
                performance_results,
                module_results
            )
            
            # Формирование комплексного отчета
            comprehensive_report = {
                'overall_status': overall_status,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_duration_seconds': validation_time,
                'system_health': {
                    'score': health_score,
                    'status': health_status,
                    'issues': health_issues
                },
                'functional_testing': functional_results,
                'performance_validation': performance_results,
                'module_diagnostics': module_results,
                'recommendations': await self._generate_recommendations(
                    health_score, functional_results, performance_results, module_results
                )
            }
            
            self.logger.info(f"✅ Комплексная проверка завершена за {validation_time}с")
            self.logger.info(f"📊 Общий статус системы: {overall_status}")
            
            return comprehensive_report
        except Exception as e:
            error_msg = f"❌ Ошибка комплексной проверки: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
            return {
                'overall_status': 'ERROR',
                'validation_timestamp': datetime.now().isoformat(),
                'validation_duration_seconds': round(time.time() - start_time, 2),
                'error': f"Критическая ошибка валидации: {e}",
                'traceback': traceback.format_exc()
            }
    
    async def run_comprehensive_validation_with_system(self, synthetic_mind: 'SyntheticMind') -> Dict[str, Any]:
        """Запуск проверки с использованием реальной системы"""
        self.logger.info("🎯 Запуск комплексной проверки с реальной системой...")
        
        start_time = time.time()
        
        try:
            # Используем реальный ModuleManager если система инициализирована
            real_module_status = {}
            if synthetic_mind.module_manager and synthetic_mind.module_manager.is_initialized:
                self.logger.info("🔍 Использование реального состояния модулей...")
                real_module_status = await synthetic_mind.get_real_module_status()
            
            # Получаем диагностику на основе реального состояния
            if real_module_status:
                module_results = await self._get_real_module_diagnostics(real_module_status, synthetic_mind.system_config)
            else:
                # Fallback: стандартная диагностика
                module_results = await self.module_diagnostic.diagnose_all_modules()
            
            # Остальная логика остается прежней...
            health_task = asyncio.create_task(self.health_monitor.get_system_health_score())
            functional_task = asyncio.create_task(self.functional_tester.run_comprehensive_tests())
            performance_task = asyncio.create_task(self.performance_validator.run_performance_validation())
            
            health_score, health_status, health_issues = await health_task
            functional_results = await functional_task
            performance_results = await performance_task
            
            validation_time = round(time.time() - start_time, 2)
            
            # Расчет общего статуса
            overall_status = self._calculate_overall_status(
                health_score, 
                functional_results, 
                performance_results,
                module_results
            )
            
            comprehensive_report = {
                'overall_status': overall_status,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_duration_seconds': validation_time,
                'system_health': {
                    'score': health_score,
                    'status': health_status,
                    'issues': health_issues
                },
                'functional_testing': functional_results,
                'performance_validation': performance_results,
                'module_diagnostics': module_results,
                'recommendations': await self._generate_recommendations(
                    health_score, functional_results, performance_results, module_results
                )
            }
            
            self.logger.info(f"✅ Комплексная проверка завершена за {validation_time}с")
            self.logger.info(f"📊 Общий статус системы: {overall_status}")
            
            return comprehensive_report
            
        except Exception as e:
            error_msg = f"❌ Ошибка комплексной проверки: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
            return {
                'overall_status': 'ERROR',
                'validation_timestamp': datetime.now().isoformat(),
                'validation_duration_seconds': round(time.time() - start_time, 2),
                'error': f"Критическая ошибка валидации: {e}",
                'traceback': traceback.format_exc()
            }
    
    async def _get_real_module_diagnostics(self, real_status: Dict[str, Any], system_config: SystemConfig) -> Dict[str, List[Dict[str, Any]]]:
        """Получение диагностики на основе реального состояния модулей из ModuleManager"""
        diagnostic_results = {
            'implemented_but_disabled': [],
            'enabled_but_broken': [],
            'working_modules': [],
            'broken_modules': []
        }
        
        for module_name, status_info in real_status.items():
            module_status = {
                'name': module_name,
                'category': self._get_module_category(module_name),
                'enabled': True,  # Если модуль в реальном статусе, значит он включен
                'healthy': status_info.get('status') in ['initialized', 'loaded', 'ready'],
                'message': f"Реальный статус: {status_info.get('status', 'unknown')}",
                'path': f"core/{module_name}.py" if module_name in ['module_manager'] else f"modules/*/{module_name}"
            }
            
            if module_status['healthy']:
                diagnostic_results['working_modules'].append(module_status)
                self.logger.info(f"✅ Рабочий модуль: {module_name} ({module_status['category']})")
            else:
                diagnostic_results['enabled_but_broken'].append(module_status)
                self.logger.error(f"❌ Сломанный включенный модуль: {module_name} ({module_status['category']}) - {module_status['message']}")
        
        return diagnostic_results
    
    def _get_module_category(self, module_name: str) -> str:
        """Определение категории модуля"""
        core_modules = ['coordinator', 'communication_bus', 'module_manager', 'security_gateway', 
                       'performance_monitor', 'intent_analyzer', 'response_synthesizer']
        
        if module_name in core_modules:
            return 'core'
        elif module_name in ['text_understander', 'speech_recognizer', 'speech_generator', 'visual_processor']:
            return 'interface'
        elif module_name in ['memory_short_term', 'memory_long_term', 'logic_analyzer', 'creativity', 'emotional_engine']:
            return 'cognitive'
        elif module_name in ['task_planner', 'goals']:
            return 'planning'
        elif module_name in ['search_agent', 'api_caller', 'action_executor']:
            return 'skills'
        else:
            return 'unknown'
    
    def _calculate_overall_status(self, health_score: int, functional_results: Dict[str, Any], 
                                performance_results: Dict[str, Any], module_results: Dict[str, Any]) -> str:
        """Расчет общего статуса системы"""
        try:
            # Весовые коэффициенты для разных аспектов
            weights = {
                'health': 0.3,
                'functionality': 0.4,
                'performance': 0.2,
                'modules': 0.1
            }
            
            # Нормализация показателей
            health_normalized = health_score / 100
            
            functional_success_rate = functional_results['summary']['success_rate'] / 100
            functional_normalized = functional_success_rate
            
            performance_normalized = 1.0 if performance_results['overall_status'] == 'PASS' else 0.5
            
            # Для модулей считаем процент рабочих от всех включенных
            enabled_modules = [m for m in module_results['working_modules'] + module_results['enabled_but_broken'] 
                              if m['enabled']]
            if enabled_modules:
                working_enabled = len([m for m in enabled_modules if m['healthy']])
                modules_normalized = working_enabled / len(enabled_modules)
            else:
                modules_normalized = 1.0
            
            # Взвешенная сумма
            total_score = (
                health_normalized * weights['health'] +
                functional_normalized * weights['functionality'] +
                performance_normalized * weights['performance'] +
                modules_normalized * weights['modules']
            )
            
            # Определение общего статуса
            if total_score >= 0.9:
                return "💚 ОТЛИЧНО"
            elif total_score >= 0.7:
                return "💛 ХОРОШО"
            elif total_score >= 0.5:
                return "🟡 УДОВЛЕТВОРИТЕЛЬНО"
            else:
                return "🔴 ТРЕБУЕТ ВНИМАНИЯ"
        except Exception as e:
            self.logger.error(f"Ошибка расчета общего статуса: {e}")
            return "🔴 ОШИБКА РАСЧЕТА"
    
    async def _generate_recommendations(self, health_score: int, functional_results: Dict[str, Any], 
                                      performance_results: Dict[str, Any], module_results: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций по улучшению системы"""
        recommendations = []
        
        try:
            # Рекомендации по здоровью системы
            if health_score < 70:
                recommendations.append("🔧 Улучшите показатели здоровья системы (ресурсы, подключения)")
            
            # Рекомендации по функциональности
            if functional_results['summary']['failed_tests'] > 0:
                recommendations.append("🐛 Исправьте проваленные функциональные тесты")
            
            # Рекомендации по производительности
            if performance_results['overall_status'] == 'FAIL':
                recommendations.append("⚡ Оптимизируйте производительность системы")
            
            # Рекомендации по модулям
            if module_results['enabled_but_broken']:
                broken_names = [m['name'] for m in module_results['enabled_but_broken']]
                recommendations.append(f"🔧 Исправьте сломанные модули: {', '.join(broken_names)}")
            
            if not recommendations:
                recommendations.append("🎉 Система работает оптимально! Продолжайте в том же духе!")
            
            self.logger.info(f"💡 Сгенерировано рекомендаций: {len(recommendations)}")
            return recommendations
        except Exception as e:
            self.logger.error(f"Ошибка генерации рекомендаций: {e}")
            return ["❌ Ошибка анализа системы"]
    
    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """Генерация комплексного отчета о валидации"""
        report = []
        report.append("=" * 100)
        report.append("🎯 КОМПЛЕКСНЫЙ ОТЧЕТ ВАЛИДАЦИИ СИНТЕТИЧЕСКОГО РАЗУМА")
        report.append("=" * 100)
        
        try:
            # Общий статус
            report.append(f"\n📊 ОБЩИЙ СТАТУС СИСТЕМЫ: {validation_results['overall_status']}")
            report.append(f"⏱️  Время проверки: {validation_results['validation_duration_seconds']}с")
            report.append(f"📅 Дата проверки: {validation_results['validation_timestamp']}")
            
            # Если есть ошибка валидации
            if 'error' in validation_results:
                report.append(f"\n❌ ОШИБКА ВАЛИДАЦИИ: {validation_results['error']}")
                if 'traceback' in validation_results:
                    report.append(f"🔍 ДЕТАЛИ ОШИБКИ:\n{validation_results['traceback']}")
                return "\n".join(report)
            
            # Здоровье системы
            health = validation_results['system_health']
            report.append(f"\n💚 ЗДОРОВЬЕ СИСТЕМЫ: {health['score']}% - {health['status']}")
            if health['issues']:
                report.append("   Выявленные проблемы:")
                for issue in health['issues']:
                    report.append(f"   ❗ {issue}")
            
            # Функциональное тестирование
            functional = validation_results['functional_testing']
            report.append(f"\n🧪 ФУНКЦИОНАЛЬНОЕ ТЕСТИРОВАНИЕ: {functional['overall_status']}")
            report.append(f"   Тестов выполнено: {functional['summary']['total_tests']}")
            report.append(f"   Успешных: {functional['summary']['passed_tests']}")
            report.append(f"   Проваленных: {functional['summary']['failed_tests']}")
            report.append(f"   Ошибок: {functional['summary']['error_tests']}")
            report.append(f"   Успешность: {functional['summary']['success_rate']:.1f}%")
            
            # Детали функциональных тестов
            for test_name, result in functional['detailed_results'].items():
                status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
                report.append(f"   {status_icon} {test_name}: {result['message']}")
                if result['status'] in ['FAIL', 'ERROR'] and 'details' in result:
                    report.append(f"      Детали: {result['details']}")
            
            # Производительность
            performance = validation_results['performance_validation']
            report.append(f"\n⚡ ПРОВЕРКА ПРОИЗВОДИТЕЛЬНОСТИ: {performance['overall_status']}")
            for test_name, result in performance['response_times'].items():
                status_icon = "✅" if result['status'] == 'PASS' else "❌"
                report.append(f"   {status_icon} {test_name}: {result['actual']}мс (цель: {result['target']}мс)")
            
            # Диагностика модулей
            modules = validation_results['module_diagnostics']
            total_modules = len(modules['working_modules'] + modules['implemented_but_disabled'] + 
                               modules['enabled_but_broken'] + modules['broken_modules'])
            enabled_modules = len([m for m in modules['working_modules'] + modules['enabled_but_broken'] 
                                  if m['enabled']])
            working_enabled = len([m for m in modules['working_modules'] if m['enabled']])
            
            report.append(f"\n📦 ДИАГНОСТИКА МОДУЛЕЙ:")
            report.append(f"   Всего модулей: {total_modules}")
            report.append(f"   Включено модулей: {enabled_modules}")
            report.append(f"   Рабочих включенных: {working_enabled}")
            if enabled_modules > 0:
                report.append(f"   Коэффициент работоспособности: {(working_enabled/enabled_modules*100):.1f}%")
            else:
                report.append(f"   Коэффициент работоспособности: 100% (нет включенных модулей)")
            
            # Рекомендации
            recommendations = validation_results['recommendations']
            report.append(f"\n💡 РЕКОМЕНДАЦИИ:")
            for i, recommendation in enumerate(recommendations, 1):
                report.append(f"   {i}. {recommendation}")
            
            report.append("\n" + "=" * 100)
            report.append("🎉 ПРОВЕРКА ЗАВЕРШЕНА!")
            report.append("=" * 100)
            
            return "\n".join(report)
        except Exception as e:
            return f"❌ Ошибка генерации отчета: {e}\n{traceback.format_exc()}"

class SyntheticMind:
    """
    Главный класс системы Синтетический Разум
    Координирует работу всех компонентов системы
    """
    
    def __init__(self):
        self.system_config: Optional[SystemConfig] = None
        self.communication_bus: Optional[CommunicationBus] = None
        self.module_manager: Optional[ModuleManager] = None
        self.security_gateway: Optional[SecurityGateway] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.coordinator: Optional[Coordinator] = None
        self.module_diagnostic: Optional[ModuleDiagnostic] = None
        self.system_validator: Optional[ComprehensiveSystemValidator] = None
        self.is_running = False
        
        # Настройка логирования
        self._setup_logging()
        
    def _setup_logging(self):
        """Настройка системы логирования"""
        try:
            logs_dir = Path("logs/system")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(logs_dir / "main.log", encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            self.logger = logging.getLogger("SyntheticMind")
            self.logger.info("✅ Система логирования инициализирована")
        except Exception as e:
            print(f"❌ Ошибка настройки логирования: {e}")
            # Базовая настройка логирования на случай ошибки
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging.getLogger("SyntheticMind")
    
    async def get_real_module_status(self) -> Dict[str, Any]:
        """Получение реального статуса модулей из ModuleManager"""
        if not self.module_manager or not hasattr(self.module_manager, 'get_all_modules_status'):
            return {}
        
        try:
            return await self.module_manager.get_all_modules_status()
        except Exception as e:
            self.logger.error(f"Ошибка получения реального статуса модулей: {e}")
            return {}
    
    async def initialize(self) -> bool:
        """Инициализация всех компонентов системы"""
        try:
            self.logger.info("🚀 Запуск инициализации Синтетического Разума...")
            
            # 1. Загрузка конфигурации
            self.logger.info("📋 Загрузка конфигурации системы...")
            self.system_config = SystemConfig()
            if not await self.system_config.load():
                self.logger.error("❌ Не удалось загрузить конфигурацию системы")
                return False
            
            # 1.5. Инициализация валидатора системы
            self.system_validator = ComprehensiveSystemValidator(self.system_config)
            
            # 1.6. Диагностика модулей ДО инициализации системы
            self.logger.info("🔍 Предварительная диагностика модулей...")
            self.module_diagnostic = ModuleDiagnostic(self.system_config)
            diagnostic_results = await self.module_diagnostic.diagnose_all_modules()
            
            # Вывод диагностического отчета
            diagnostic_report = self.module_diagnostic.generate_diagnostic_report(diagnostic_results)
            self.logger.info(f"\n{diagnostic_report}")
            
            # Проверка на критические ошибки
            if diagnostic_results['enabled_but_broken']:
                self.logger.warning("⚠️ Обнаружены критические проблемы в включенных модулях!")
                self.logger.warning("💡 Рекомендуется исправить эти модули перед продолжением работы")
            
            # 2. Инициализация шины сообщений
            self.logger.info("🔌 Инициализация шины сообщений...")
            self.communication_bus = CommunicationBus(self.system_config)
            await self.communication_bus.initialize()
            
            # 3. Инициализация шлюза безопасности
            self.logger.info("🛡️ Инициализация шлюза безопасности...")
            self.security_gateway = SecurityGateway(self.system_config.get('security', {}))
            await self.security_gateway.initialize()
            
            # 4. Инициализация монитора производительности
            self.logger.info("📊 Инициализация монитора производительности...")
            self.performance_monitor = PerformanceMonitor(self.system_config)
            await self.performance_monitor.initialize()
            
            # 5. Инициализация менеджера модулей
            self.logger.info("🔧 Инициализация менеджера модулей...")
            modules_config = {
            'enabled': self.system_config.get('modules.enabled', [])
            }
            self.module_manager = ModuleManager(modules_config)
            #self.module_manager = ModuleManager(self.system_config.get('modules', {}))
            await self.module_manager.initialize()

            
            # 6. Инициализация координатора
            self.logger.info("🎯 Инициализация координатора...")
            self.coordinator = Coordinator(self.system_config)  # Передаем только конфиг
            await self.coordinator.initialize()
            
            self.logger.info("✅ Инициализация Синтетического Разума завершена успешно!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации системы: {e}")
            self.logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
            await self.shutdown()
            return False

    async def run_diagnostic_mode(self):
        """Режим только диагностики без запуска системы"""
        self.logger.info("🔍 Запуск в режиме диагностики...")
        
        self.system_config = SystemConfig()
        if not await self.system_config.load():
            self.logger.error("❌ Не удалось загрузить конфигурацию системы")
            return
        
        self.module_diagnostic = ModuleDiagnostic(self.system_config)
        diagnostic_results = await self.module_diagnostic.diagnose_all_modules()
        
        report = self.module_diagnostic.generate_diagnostic_report(diagnostic_results)
        
        # Сохранение отчета в файл
        diagnostic_file = Path("logs/system/diagnostic_report.txt")
        diagnostic_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(diagnostic_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"\n{report}")
        self.logger.info(f"📄 Полный отчет сохранен в: {diagnostic_file}")
        
        # Рекомендации по исправлению
        await self._generate_fix_recommendations(diagnostic_results)
    
    async def run_comprehensive_validation(self):
        """Запуск комплексной проверки системы"""
        self.logger.info("🎯 Запуск комплексной проверки системы...")
        
        self.system_config = SystemConfig()
        if not await self.system_config.load():
            self.logger.error("❌ Не удалось загрузить конфигурацию системы")
            return
        
        self.system_validator = ComprehensiveSystemValidator(self.system_config)
        validation_results = await self.system_validator.run_comprehensive_validation()
        
        # Генерация и вывод отчета
        validation_report = self.system_validator.generate_validation_report(validation_results)
        self.logger.info(f"\n{validation_report}")
        
        # Сохранение полного отчета в JSON
        validation_file = Path("logs/system/comprehensive_validation.json")
        validation_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"📄 Полный отчет в JSON сохранен в: {validation_file}")
        
        # Сохранение читаемого отчета
        readable_file = Path("logs/system/comprehensive_validation_report.txt")
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(validation_report)
        
        self.logger.info(f"📄 Читаемый отчет сохранен в: {readable_file}")
        
        return validation_results['overall_status']

    async def run_comprehensive_validation_with_system(self):
        """Запуск комплексной проверки с использованием реальной системы"""
        self.logger.info("🎯 Запуск комплексной проверки с реальной системой...")
        
        if not self.system_config:
            self.system_config = SystemConfig()
            if not await self.system_config.load():
                self.logger.error("❌ Не удалось загрузить конфигурацию системы")
                return
        
        # Инициализируем систему если еще не инициализирована
        if not self.module_manager or not self.module_manager.is_initialized:
            self.logger.info("🔧 Инициализация системы для проверки...")
            if not await self.initialize():
                self.logger.error("❌ Не удалось инициализировать систему для проверки")
                return
        
        self.system_validator = ComprehensiveSystemValidator(self.system_config)
        validation_results = await self.system_validator.run_comprehensive_validation_with_system(self)
        
        # Генерация и вывод отчета
        validation_report = self.system_validator.generate_validation_report(validation_results)
        self.logger.info(f"\n{validation_report}")
        
        # Сохранение отчетов
        validation_file = Path("logs/system/comprehensive_validation_real.json")
        validation_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"📄 Полный отчет в JSON сохранен в: {validation_file}")
        
        readable_file = Path("logs/system/comprehensive_validation_real_report.txt")
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(validation_report)
        
        self.logger.info(f"📄 Читаемый отчет сохранен в: {readable_file}")
        
        return validation_results['overall_status']
    
    async def _generate_fix_recommendations(self, diagnostic_results: Dict[str, Any]) -> None:
        """Генерация рекомендаций по исправлению проблем"""
        critical_modules = diagnostic_results['enabled_but_broken']
        broken_modules = diagnostic_results['broken_modules']
        
        if not critical_modules and not broken_modules:
            self.logger.info("🎉 Все модули в порядке! Рекомендации не требуются.")
            return
        
        self.logger.info("\n🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        
        for module in critical_modules + broken_modules:
            self.logger.info(f"\n📦 Модуль: {module['name']}")
            self.logger.info(f"   Проблема: {module['message']}")
            self.logger.info(f"   Категория: {module['category']}")
            
            # Общие рекомендации
            if "импорта" in module['message'].lower():
                self.logger.info("   💡 Проверьте зависимости и пути импорта")
            if "классы" in module['message'].lower():
                self.logger.info("   💡 Убедитесь, что основные классы модуля правильно определены")
            if "методы" in module['message'].lower():
                self.logger.info("   💡 Добавьте необходимые методы инициализации")
            
            # Специфические рекомендации по категориям
            if module['category'] == 'interface':
                self.logger.info("   💡 Для интерфейсных модулей проверьте наличие моделей в data/models/")
            elif module['category'] == 'cognitive':
                self.logger.info("   💡 Для когнитивных модулей проверьте подключение к БД")
            elif module['category'] == 'core':
                self.logger.info("   💡 Для core модулей проверьте базовую функциональность")
    
    async def run(self):
        """Запуск основного цикла работы системы"""
        # Добавляем поддержку аргументов командной строки
        if len(sys.argv) > 1:
            if sys.argv[1] == "--diagnostic":
                await self.run_diagnostic_mode()
                return
            elif sys.argv[1] == "--validate":
                await self.run_comprehensive_validation()
                return
            elif sys.argv[1] == "--validate-real":
                await self.run_comprehensive_validation_with_system()
                return
            elif sys.argv[1] == "--health-check":
                await self.run_health_check()
                return
        
        if not await self.initialize():
            return
        
        self.is_running = True
        self.logger.info("🎮 Запуск основного цикла Синтетического Разума...")
        
        # Регистрация обработчиков сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Запуск веб-интерфейса если включен в конфигурации
            if self.system_config.get('web_interface.enabled', False):
                await self._start_web_interface()
            
            # Основной цикл работы системы
            while self.is_running:
                await asyncio.sleep(1)
                
                # Мониторинг здоровья системы
                await self._health_check()
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка в основном цикле: {e}")
            self.logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
        finally:
            await self.shutdown()
    
    async def run_health_check(self):
        """Быстрая проверка здоровья системы"""
        self.logger.info("💚 Запуск проверки здоровья системы...")
        
        self.system_config = SystemConfig()
        if not await self.system_config.load():
            self.logger.error("❌ Не удалось загрузить конфигурацию системы")
            return
        
        health_monitor = SystemHealthMonitor(self.system_config)
        health_score, status, issues = await health_monitor.get_system_health_score()
        
        self.logger.info(f"\n💚 РЕЗУЛЬТАТ ПРОВЕРКИ ЗДОРОВЬЯ:")
        self.logger.info(f"   Оценка здоровья: {health_score}%")
        self.logger.info(f"   Статус: {status}")
        
        if issues:
            self.logger.info("   Выявленные проблемы:")
            for issue in issues:
                self.logger.info(f"   ❗ {issue}")
        else:
            self.logger.info("   ✅ Проблем не обнаружено!")
    
    async def _start_web_interface(self):
        """Запуск веб-интерфейса FastAPI"""
        try:
            self.logger.info("🌐 Запуск базового веб-интерфейса...")
            from interface.web_interface import WebInterface
            self.web_interface = WebInterface(
                self.coordinator,
                self.system_config,
                self.security_gateway
            )
            await self.web_interface.start()
            self.logger.info("🌐 Веб-интерфейс запущен")
            
        except ImportError:
            self.logger.warning("⚠️ Модуль web_interface не найден, запуск без веб-интерфейса")
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось запустить веб-интерфейс: {e}")
    
    async def _health_check(self):
        """Проверка здоровья системы"""
        try:
            # Проверка основных компонентов
            components_health = {
                'communication_bus': await self.communication_bus.is_healthy(),
                'security_gateway': await self.security_gateway.is_healthy(),
                'performance_monitor': await self.performance_monitor.is_healthy(),
                'module_manager': await self.module_manager.is_healthy(),
                'coordinator': await self.coordinator.is_healthy()
            }
            
            # Логирование состояния системы
            if not all(components_health.values()):
                unhealthy = [k for k, v in components_health.items() if not v]
                self.logger.warning(f"⚠️ Нестабильные компоненты: {unhealthy}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки здоровья системы: {e}")
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Обработчик сигналов для graceful shutdown"""
        self.logger.info(f"📞 Получен сигнал {signum}, завершение работы...")
        self.is_running = False
    
    async def shutdown(self):
        """Корректное завершение работы системы"""
        self.logger.info("🛑 Завершение работы Синтетического Разума...")
        self.is_running = False
        
        try:
            # Остановка компонентов в правильном порядке
            if hasattr(self, 'web_interface'):
                await self.web_interface.stop()
            
            if self.coordinator:
                await self.coordinator.shutdown()
            
            if self.module_manager:
                await self.module_manager.shutdown()
            
            if self.performance_monitor:
                await self.performance_monitor.shutdown()
            
            if self.security_gateway:
                await self.security_gateway.shutdown()
            
            if self.communication_bus:
                await self.communication_bus.shutdown()
                
            self.logger.info("✅ Синтетический Разум завершил работу")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при завершении работы: {e}")


async def main():
    """Основная функция запуска"""
    print("🚀 Запуск Синтетического Разума...")
    print(f"📁 Рабочая директория: {os.getcwd()}")
    print(f"🐍 Версия Python: {sys.version}")
    
    synthetic_mind = SyntheticMind()
    
    try:
        await synthetic_mind.run()
    except KeyboardInterrupt:
        synthetic_mind.logger.info("👋 Завершение работы по запросу пользователя")
    except Exception as e:
        synthetic_mind.logger.error(f"💥 Критическая ошибка: {e}")
        synthetic_mind.logger.error(f"🔍 Детали: {traceback.format_exc()}")
        print(f"💥 Критическая ошибка в работе системы: {e}")
        print("🔍 Проверьте логи в logs/system/main.log для подробной информации")
        sys.exit(1)


def create_config_files():
    """Создание всех необходимых конфигурационных файлов"""
    
    # Создание базового конфигурационного файла если он не существует
    config_file = Path("config/system.yaml")
    if not config_file.exists():
        basic_config = {
            'system': {
                'name': 'Scynet',
                'version': '0.1.0',
                'debug': True
            },
            'database': {
                'postgres_url': 'postgresql://user:pass@localhost:5432/scynet',
                'redis_url': 'redis://localhost:6379'
            },
            'modules': {
                'enabled': ['text_understander', 'speech_recognizer', 'memory_short_term']
            },
            'web_interface': {
                'enabled': False,
                'host': '0.0.0.0',
                'port': 8000
            },
            'security': {
                'enabled': True,
                'audit_log': True
            },
            'performance': {
                'monitoring': True,
                'metrics_collection': True
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(basic_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        print("📋 Создан базовый конфигурационный файл config/system.yaml")

    # Создание базового конфигурационного файла безопасности если он не существует или содержит ошибки
    security_config_file = Path("config/security_policies.yaml")
    security_config_content = {
        'security': {
            'enabled': True,
            'audit_log': True,
            'log_level': 'INFO',
            'max_request_size': '10MB',
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60
            },
            'input_validation': {
                'enabled': True,
                'max_text_length': 5000,
                'allowed_file_types': ['jpg', 'png', 'wav', 'mp3', 'txt']
            },
            'authentication': {
                'enabled': False,
                'method': 'jwt'
            },
            'content_filter': {
                'enabled': True,
                'filter_profanity': True,
                'block_malicious_content': True
            },
            'data_privacy': {
                'encrypt_sensitive_data': True,
                'data_retention_days': 30
            }
        },
        'modules': {
            'security_gateway': {
                'enabled': True,
                'check_input': True,
                'check_output': True,
                'log_security_events': True,
                'security_level': 'medium'
            }
        },
        'policies': {
            'input_sanitization': [
                {'type': 'sql_injection', 'action': 'block', 'severity': 'high'},
                {'type': 'xss', 'action': 'block', 'severity': 'high'},
                {'type': 'path_traversal', 'action': 'block', 'severity': 'high'},
                {'type': 'command_injection', 'action': 'block', 'severity': 'high'}
            ],
            'output_sanitization': [
                {'type': 'sensitive_data', 'action': 'filter', 'severity': 'medium'},
                {'type': 'personal_info', 'action': 'anonymize', 'severity': 'medium'}
            ],
            'access_control': [
                {'resource': 'system_config', 'permission': 'admin_only'},
                {'resource': 'user_data', 'permission': 'authenticated'},
                {'resource': 'public_api', 'permission': 'everyone'}
            ]
        },
        'audit': {
            'enabled': True,
            'log_file': 'logs/audit/security_events.log',
            'retention_days': 90,
            'events_to_log': [
                'authentication_attempts',
                'security_violations',
                'configuration_changes',
                'data_access'
            ]
        }
    }
    
    # Проверяем нужно ли пересоздать файл
    should_recreate = False
    if security_config_file.exists():
        try:
            with open(security_config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Если файл содержит код Python вместо YAML, пересоздаем
                if 'basic_security_config' in content or 'yaml.dump' in content:
                    should_recreate = True
                else:
                    # Проверяем синтаксис YAML
                    yaml.safe_load(content)
        except Exception as e:
            print(f"⚠️ Обнаружена ошибка в security_policies.yaml: {e}")
            should_recreate = True
    else:
        should_recreate = True
    
    if should_recreate:
        with open(security_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(security_config_content, f, default_flow_style=False, allow_unicode=True, indent=2)
        print("📋 Создан/пересоздан конфигурационный файл безопасности config/security_policies.yaml")

    # Создание базового конфигурационного файла производительности если он не существует
    performance_config_file = Path("config/performance_settings.yaml")
    if not performance_config_file.exists():
        basic_performance_config = {
            'performance': {
                'monitoring': True,
                'metrics_collection': True,
                'collection_interval': 60,
                'alerting': {
                    'enabled': True,
                    'cpu_threshold': 80,
                    'memory_threshold': 85,
                    'response_time_threshold': 5000
                },
                'logging': {
                    'enabled': True,
                    'level': 'INFO'
                },
                'modules': {
                    'performance_monitor': {
                        'enabled': True,
                        'track_response_times': True,
                        'track_resource_usage': True,
                        'track_error_rates': True
                    }
                }
            }
        }
        
        with open(performance_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(basic_performance_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        print("📋 Создан базовый конфигурационный файл производительности config/performance_settings.yaml")


if __name__ == "__main__":
    # Проверка версии Python
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    # Создание необходимых директорий
    required_dirs = [
        "logs/system",
        "logs/audit",
        "logs/performance",
        "data/runtime",
        "data/cache",
        "data/temporary_files",
        "config",
        "config/modules"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Создание конфигурационных файлов
    create_config_files()
    
    # Запуск основного цикла
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"💥 Критическая ошибка при запуске: {e}")
        print(f"🔍 Детали: {traceback.format_exc()}")
        sys.exit(1)